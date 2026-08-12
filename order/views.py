from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
# from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.exceptions import ValidationError
from .models import Order, OrderItem
from .serializer import OrderSerializer, OrderItemSerializer,ReportOrderListSerializer, ExpenseTypeSerializer, CashTransactionSerializer
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from django.db.models import Sum, Count
import json
import socket
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import OrderReceipt,CheckSetting
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
def send_to_printer(order_data):
    PRINTER_IP = "192.168.1.10"
    PRINTER_PORT = 9100
    settings, created = CheckSetting.objects.get_or_create(id=1)
    INIT = bytes([0x1B, 0x40])
    BOLD_ON = bytes([0x1B, 0x45, 0x01])
    BOLD_OFF = bytes([0x1B, 0x45, 0x00])
    DOUBLE_SIZE = bytes([0x1B, 0x21, 0x30])
    NORMAL_SIZE = bytes([0x1B, 0x21, 0x00])
    CENTER = bytes([0x1B, 0x61, 0x01])
    LEFT = bytes([0x1B, 0x61, 0x00])
    packet = bytearray()
    packet.extend(INIT)
    if settings.show_cafe_name:
        packet.extend(CENTER + DOUBLE_SIZE + BOLD_ON)
        packet.extend(f"{settings.cafe_name.upper()}\n".encode('utf-8'))
        packet.extend(NORMAL_SIZE + BOLD_OFF + LEFT)  # Standart rejimga qaytamiz
    text_info = ""
    if settings.show_manzil:
        text_info += f"Manzil: {settings.address}\n"
    if settings.show_kontaktlar:
        text_info += f"Telefon: {settings.phone}\n"
    packet.extend(text_info.encode('utf-8'))
    packet.extend(f"------------------------------------------------\n".encode('utf-8'))  # 48 ta chiziq
    text_order = ""
    if settings.show_sotuvchi:
        text_order += f"Kassir: Admin\n"
    text_order += f"Buyurtma: #{order_data.get('order_number', '')}\n"
    text_order += f"Stol: {order_data.get('table_number', '')}\n"
    packet.extend(text_order.encode('utf-8'))
    packet.extend(f"------------------------------------------------\n".encode('utf-8'))
    packet.extend(f"Nomi                   Soni   Narxi      Jami\n".encode('utf-8'))
    packet.extend(f"------------------------------------------------\n".encode('utf-8'))
    items = order_data.get('items', [])
    for item in items:
        name = str(item.get('name', ''))[:20]
        try:
            qty_num = float(item.get('quantity', 1))
            price_num = float(item.get('price', 0))
        except (ValueError, TypeError):
            qty_num, price_num = 1.0, 0.0
        qty_str = f"{qty_num:g}"
        price_str = f"{price_num:g}"
        total_str = f"{qty_num * price_num:g}"
        line = f"{name:<22} {qty_str:<6} {price_str:<10} {total_str}\n"
        packet.extend(line.encode('utf-8'))
    packet.extend(f"------------------------------------------------\n".encode('utf-8'))
    packet.extend(BOLD_ON + DOUBLE_SIZE)
    packet.extend(f"JAMI: {order_data.get('total_amount', 0)} UZS\n".encode('utf-8'))
    packet.extend(NORMAL_SIZE + BOLD_OFF)
    packet.extend(f"To'lov turi: {order_data.get('payment_type', 'NAQD')}\n".encode('utf-8'))
    packet.extend(f"------------------------------------------------\n".encode('utf-8'))
    if settings.show_eslatma:
        packet.extend(CENTER)
        packet.extend(f"{settings.footer_text}\n".encode('utf-8'))
        packet.extend(LEFT)
    packet.extend(f"\n\n\n\n".encode('utf-8'))
    cut_command = bytes([0x1D, 0x56, 0x42, 0x00])
    packet.extend(cut_command)
    try:
        mysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        mysocket.settimeout(5)
        mysocket.connect((PRINTER_IP, PRINTER_PORT))
        mysocket.sendall(packet)
        mysocket.close()
        return True
    except Exception as e:
        print(f"Printer xatosi: {e}")
        return False


@csrf_exempt
def checkout_and_print_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            from django.apps import apps
            InventoryProductModel = apps.get_model('inventory', 'InventoryProduct')
            items = data.get('items', [])
            
            with transaction.atomic():
                for item in items:
                    prod_id = item.get('id') or item.get('product_id')
                    try:
                        qty = float(item.get('quantity', 1))
                    except (ValueError, TypeError):
                        qty = 1.0

                    if prod_id:
                        try:
                            product = InventoryProductModel.objects.select_for_update().get(id=prod_id)
                            if product.current_stock < qty:
                                return JsonResponse({
                                    "status": "error",
                                    "message": f"{product.name} omborda yetarli emas! Qoldiq: {product.current_stock} ta/kg, so'raldi: {qty} ta/kg"
                                }, status=400)
                        except InventoryProductModel.DoesNotExist:
                            return JsonResponse({
                                "status": "error",
                                "message": f"IDsi {prod_id} bo'lgan mahsulot ombordan topilmadi!"
                            }, status=400)

                for item in items:
                    prod_id = item.get('id') or item.get('product_id')
                    try:
                        qty = float(item.get('quantity', 1))
                    except (ValueError, TypeError):
                        qty = 1.0

                    if prod_id:
                        product = InventoryProductModel.objects.get(id=prod_id)
                        product.current_stock = float(product.current_stock) - qty
                        product.save(update_fields=['current_stock'])

                order_num = data.get('order_number', 0)
                table_num = data.get('table_number', 0)
                tot_amt = data.get('total_amount', 0)
                pay_type = data.get('payment_type', 'NAQD')

                receipt = OrderReceipt.objects.create(
                    order_number=order_num,
                    table_number=table_num,
                    total_amount=tot_amt,
                    payment_type=pay_type
                )
            printer_result = send_to_printer(data)
            if printer_result:
                return JsonResponse(
                    {"status": "success", "message": "Buyurtma saqlandi, ombordan kamaytirildi va chek chop etildi!"},
                    status=201)
            else:
                return JsonResponse({"status": "warning","message": "Ma'lumot saqlandi va ombordan kamaytirildi, lekin printer tarmoqda topilmadi."},status=201)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Faqat POST so'rovlar qabul qilinadi"}, status=405)
@csrf_exempt
def check_settings_api(request):
    settings, created = CheckSetting.objects.get_or_create(id=1)
    if request.method == "GET":
        return JsonResponse({
            "cafe_name": settings.cafe_name,
            "address": settings.address,
            "phone": settings.phone,
            "footer_text": settings.footer_text,
            "show_cafe_name": settings.show_cafe_name,
            "show_sana": settings.show_sana,
            "show_ish_vaqti": settings.show_ish_vaqti,
            "show_sotuvchi": settings.show_sotuvchi,
            "show_kassir": settings.show_kassir,
            "show_mijoz": settings.show_mijoz,
            "show_kontaktlar": settings.show_kontaktlar,
            "show_inn": settings.show_inn,
            "show_yuridik_shaxs": settings.show_yuridik_shaxs,
            "show_manzil": settings.show_manzil,
            "show_mijoz_raqami": settings.show_mijoz_raqami,
            "show_eslatma": settings.show_eslatma,
        })
    elif request.method in ["POST", "PUT"]:
        try:
            data = json.loads(request.body)
            settings.cafe_name = data.get("cafe_name", settings.cafe_name)
            settings.address = data.get("address", settings.address)
            settings.phone = data.get("phone", settings.phone)
            settings.footer_text = data.get("footer_text", settings.footer_text)
            settings.show_cafe_name = data.get("show_cafe_name", settings.show_cafe_name)
            settings.show_sana = data.get("show_sana", settings.show_sana)
            settings.show_ish_vaqti = data.get("show_ish_vaqti", settings.show_ish_vaqti)
            settings.show_sotuvchi = data.get("show_sotuvchi", settings.show_sotuvchi)
            settings.show_kassir = data.get("show_kassir", settings.show_kassir)
            settings.show_mijoz = data.get("show_mijoz", settings.show_mijoz)
            settings.show_kontaktlar = data.get("show_kontaktlar", settings.show_kontaktlar)
            settings.show_inn = data.get("show_inn", settings.show_inn)
            settings.show_yuridik_shaxs = data.get("show_yuridik_shaxs", settings.show_yuridik_shaxs)
            settings.show_manzil = data.get("show_manzil", settings.show_manzil)  # <--- Bu ham to'g'rilandi
            settings.show_mijoz_raqami = data.get("show_mijoz_raqami", settings.show_mijoz_raqami)
            settings.show_eslatma = data.get("show_eslatma", settings.show_eslatma)
            settings.save()
            return JsonResponse({"status": "success", "message": "Chek sozlamalari muvaffaqiyatli saqlandi!"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)



# Note: checkout_and_print_api implementation kept earlier (with inventory checks and decrement).




class RestaurantReportAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request, *args, **kwargs):
        orders = Order.objects.all().order_by('-created_at')
        start_date_param = request.query_params.get('dan_sana')
        end_date_param = request.query_params.get('gacha_sana')
        employee_id = request.query_params.get('ofitsiant_id')
        branch_id = request.query_params.get('branch_id') or request.query_params.get('branch')
        if start_date_param:
            start_date = parse_date(start_date_param)
            if start_date:
                orders = orders.filter(created_at__date__gte=start_date)
        if end_date_param:
            end_date = parse_date(end_date_param)
            if end_date:
                orders = orders.filter(created_at__date__lte=end_date)
        if employee_id:
            orders = orders.filter(assigned_waiter_id=employee_id)
        if branch_id:
            orders = orders.filter(branch_id=branch_id)
        totals = orders.aggregate(
            jami_buyurtmalar=Count('id'),
            jami_savdo=Sum('total_amount'),
            jami_xizmat=Sum('service_amount')
        )
        stats = {
            "jami_buyurtmalar": totals['jami_buyurtmalar'] or 0,
            "jami_savdo_summasi": float(totals['jami_savdo'] or 0),
            "jami_xizmat_haqqi": float(totals['jami_xizmat'] or 0),
        }
        serializer = ReportOrderListSerializer(orders, many=True)
        return Response({
            "stats": stats,
            "orders": serializer.data
        })


class OrderPrintReceiptAPIView(APIView):
    def get(self, request, order_id=None, *args, **kwargs):
        from django.apps import apps
        Order = apps.get_model('order', 'Order')
        if order_id is None:
            order = Order.objects.order_by('-id').first()
            if not order:
                return Response(
                    {"error": "Bazada birorta ham buyurtma topilmadi!"},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            order = get_object_or_404(Order, id=order_id)
        items_data = []
        for item in order.items.all():
            qty = float(getattr(item, 'qty', 1))
            unit_price = float(getattr(item, 'unit_price', 0))
            items_data.append({
                "name": item.product.name if hasattr(item, 'product') and item.product else "Noma'lum mahsulot",
                "quantity": qty,
                "price": unit_price,
                "total_price": float(qty * unit_price)
            })
        receipt_payload = {
            "cafe_name": "Bahor Cafe",
            "order_info": {
                "order_id": order.id,
                "table": order.table.name if hasattr(order, 'table') and order.table else "Olib ketish",
                "status": order.status,
                "date": order.created_at.strftime("%d.%m.%Y %H:%M") if hasattr(order, 'created_at') else ""
            },
            "items": items_data,
            "financials": {
                "final_total": float(order.total_amount)
            }
        }
        return Response(receipt_payload, status=status.HTTP_200_OK)


from rest_framework.permissions import AllowAny
class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    def get_queryset(self):
        queryset = (
            Order.objects
            .select_related("table", "assigned_waiter", "branch")
            .prefetch_related("items")
            .all()
            .order_by("-created_at")
        )
        status_param = self.request.query_params.get("status")
        table_param = self.request.query_params.get("table")
        type_param = self.request.query_params.get("type")
        waiter_param = self.request.query_params.get("assigned_waiter")
        branch_param = self.request.query_params.get("branch") or self.request.query_params.get("branch_id")
        if status_param:
            queryset = queryset.filter(status=status_param)
        if table_param:
            queryset = queryset.filter(table_id=table_param)
        if type_param:
            queryset = queryset.filter(type=type_param)
        if waiter_param:
            queryset = queryset.filter(assigned_waiter_id=waiter_param)
        if branch_param:
            queryset = queryset.filter(branch_id=branch_param)
        return queryset


    def perform_create(self, serializer):
        assigned_waiter = serializer.validated_data.get("assigned_waiter")
        if assigned_waiter:
            serializer.save()
            return
        if self.request.user and self.request.user.is_authenticated:
            employee = getattr(self.request.user, "employee", None)
            if employee:
                serializer.save(assigned_waiter=employee)
            else:
                serializer.save(assigned_waiter=self.request.user)
            return
        serializer.save()



    @action(detail=True, methods=["post"])
    def send_to_kitchen(self, request, pk=None):
        order = self.get_object()
        if order.status == Order.Status.CANCELLED:
            return Response(
                {"detail": "Bekor qilingan buyurtmani oshxonaga yuborib bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if order.status == Order.Status.CLOSED:
            return Response(
                {"detail": "Yopilgan buyurtmani oshxonaga yuborib bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not order.items.exists():
            return Response(
                {"detail": "Bo‘sh buyurtmani oshxonaga yuborib bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if order.status == Order.Status.SENT_TO_KITCHEN:
            return Response(
                {"detail": "Buyurtma allaqachon oshxonaga yuborilgan."},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.status = Order.Status.SENT_TO_KITCHEN
        order.save()
        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=status.HTTP_200_OK
        )
    @action(detail=True, methods=["post"])
    def mark_ready(self, request, pk=None):
        order = self.get_object()
        if order.status in [Order.Status.CANCELLED, Order.Status.CLOSED]:
            return Response(
                {"detail": "Bekor qilingan yoki yopilgan buyurtmani READY qilib bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if order.status not in [Order.Status.SENT_TO_KITCHEN, Order.Status.COOKING]:
            return Response(
                {"detail": "Faqat oshxonaga yuborilgan yoki tayyorlanayotgan buyurtma READY bo‘lishi mumkin."},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = Order.Status.READY
        order.save()

        order.items.exclude(status=OrderItem.Status.CANCELLED).update(status=OrderItem.Status.READY)

        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    def mark_served(self, request, pk=None):

        order = self.get_object()

        if order.status != Order.Status.READY:
            return Response(
                {"detail": "Faqat READY holatidagi buyurtma SERVED bo‘lishi mumkin."},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = Order.Status.SERVED
        order.save()

        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    def mark_paid(self, request, pk=None):
        order = self.get_object()
        if order.status in [Order.Status.CANCELLED, Order.Status.CLOSED]:
            return Response(
                {"detail": "Bekor qilingan yoki yopilgan buyurtmani PAID qilib bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if order.total_amount <= 0:
            return Response(
                {"detail": "Jami summa 0 bo‘lgan buyurtmani to‘langan deb belgilab bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = Order.Status.PAID
        order.save()

        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=status.HTTP_200_OK
        )


    @action(detail=True, methods=["post"])
    def close_order(self, request, pk=None):


        order = self.get_object()

        if order.status != Order.Status.PAID:
            return Response(
                {"detail": "Faqat to‘langan buyurtmani yopish mumkin."},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = Order.Status.CLOSED
        order.save()

        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):

        order = self.get_object()

        if order.status in [Order.Status.PAID, Order.Status.CLOSED]:
            return Response(
                {"detail": "To‘langan yoki yopilgan buyurtmani bekor qilib bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = Order.Status.CANCELLED
        order.save()

        order.items.update(status=OrderItem.Status.CANCELLED)

        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=status.HTTP_200_OK
        )

        # POST /api/orders/5/add_item/
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def add_item(self, request, pk=None):
        order = self.get_object()

        if order.status in [Order.Status.CANCELLED, Order.Status.CLOSED]:
            return Response(
                {"detail": "Bekor qilingan yoki yopilgan buyurtmaga item qo‘shib bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data.copy()
        data["order"] = order.id

        # 🟢 OMBOR TEKSHIRUVI (menu mahsulotlari asosida):
        product_id = data.get("product")
        requested_qty = float(data.get("qty", 1))

        if product_id:
            from django.apps import apps
            ProductModel = apps.get_model('table', 'Product')
            ProductIngredient = apps.get_model('table', 'ProductIngredient')
            InventoryProductModel = apps.get_model('inventory', 'InventoryProduct')

            try:
                menu_product = ProductModel.objects.get(id=product_id)
            except ProductModel.DoesNotExist:
                return Response({"detail": "Mahsulot topilmadi."}, status=status.HTTP_404_NOT_FOUND)

            # Collect required ingredient amounts
            required = []
            ingredients = ProductIngredient.objects.filter(product=menu_product)
            for ing in ingredients:
                if not hasattr(ing, 'maxsulot') or not ing.maxsulot:
                    continue
                inv = InventoryProductModel.objects.filter(id=ing.maxsulot.id).first()
                need_amount = float(ing.amount) * requested_qty
                if not inv:
                    return Response({"detail": f"Ingredient omborda topilmadi: {getattr(ing, 'maxsulot', None)}"}, status=status.HTTP_400_BAD_REQUEST)
                if inv.current_stock < need_amount:
                    return Response({"detail": f"{inv.name} omborda yetarli emas. Qoldiq: {inv.current_stock}, kerak: {need_amount}"}, status=status.HTTP_400_BAD_REQUEST)
                required.append((inv, need_amount))

            # All ingredients available — decrement inventory
            for inv, amt in required:
                inv.current_stock = float(inv.current_stock) - amt
                inv.save()

        serializer = OrderItemSerializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        order.refresh_from_db()

        return Response(
            {
                "detail": "Item muvaffaqiyatli qo‘shildi va ombordan kamaytirildi.",
                "order": OrderSerializer(order, context={"request": request}).data,
                "item": serializer.data,
            },
            status=status.HTTP_201_CREATED
        )
    @action(detail=True, methods=["post"], url_path="remove-item/(?P<item_id>[^/.]+)")
    def remove_item(self, request, pk=None, item_id=None):

        order = self.get_object()

        if order.status in [Order.Status.CANCELLED, Order.Status.CLOSED]:
            return Response(
                {"detail": "Bekor qilingan yoki yopilgan buyurtmadan item o‘chirib bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            item = order.items.get(pk=item_id)
        except OrderItem.DoesNotExist:
            return Response(
                {"detail": "Item topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )

        item.delete()
        order.refresh_from_db()

        return Response(
            {
                "detail": "Item muvaffaqiyatli o‘chirildi.",
                "order": OrderSerializer(order, context={"request": request}).data,
            },
            status=status.HTTP_200_OK
        )


class CashTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = CashTransactionSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get_queryset(self):
        from django.apps import apps
        CashTransaction = apps.get_model('order', 'CashTransaction')
        return CashTransaction.objects.select_related('expense_type', 'created_by').all().order_by('-created_at')

    def perform_create(self, serializer):
        employee = getattr(self.request.user, 'employee', None)
        if employee and 'created_by' not in serializer.validated_data:
            serializer.save(created_by=employee)
        else:
            serializer.save()


class FinanceMonitoringAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from django.apps import apps
        CashTransaction = apps.get_model('order', 'CashTransaction')
        # Today's total sales across all waiters (regardless of which waiter sold what)
        valid_sales_statuses = [
            "paid", "closed", "PAID", "CLOSED",
            "To'lov olindi", "To‘lov olindi", "Yopildi",
        ]
        today = timezone.now().date()
        today_sales = Order.objects.filter(status__in=valid_sales_statuses, created_at__date=today).aggregate(total=Sum('total_amount'))['total'] or 0

        # Today's cash transactions summary
        txn_today = CashTransaction.objects.filter(created_at__date=today)
        txn_summary = txn_today.values('transaction_type').annotate(total=Sum('amount'))
        txn_summary_dict = {t['transaction_type']: float(t['total'] or 0) for t in txn_summary}

        # Monthly product cost (expenses by product sold) - last 30 days
        from django.db.models import F
        month_ago = timezone.now().date() - timezone.timedelta(days=30)
        items = OrderItem.objects.filter(order__status__in=valid_sales_statuses, order__created_at__date__gte=month_ago)
        product_costs = {}
        for it in items.select_related('product'):
            pname = it.product.name if it.product else (it.product_name_snapshot or "Noma'lum")
            cost_price = getattr(it.product, 'cost_price', None) if it.product else None
            if not cost_price:
                cost_price = (it.unit_price or Decimal('0')) * Decimal('0.4')
            total_cost = float(cost_price) * float(it.qty or 0)
            product_costs[pname] = product_costs.get(pname, 0) + total_cost

        product_costs_list = [
            {"product": k, "monthly_cost": v} for k, v in sorted(product_costs.items(), key=lambda x: -x[1])
        ]

        return Response({
            "today_sales_total": float(today_sales),
            "cash_transactions_today": txn_summary_dict,
            "monthly_product_costs": product_costs_list
        }, status=status.HTTP_200_OK)


class OrderItemViewSet(viewsets.ModelViewSet):

    serializer_class = OrderItemSerializer
    # permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = (
            OrderItem.objects
            .select_related("order", "product")
            .all()
            .order_by("-created_at")
        )

        order_param = self.request.query_params.get("order")
        status_param = self.request.query_params.get("status")

        if order_param:
            queryset = queryset.filter(order_id=order_param)

        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset
    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save()
    @transaction.atomic
    def perform_update(self, serializer):
        serializer.save()
    @transaction.atomic
    def perform_destroy(self, instance):
        instance.delete()
    @action(detail=True, methods=["post"])
    def mark_cooking(self, request, pk=None):
        item = self.get_object()
        if item.status == OrderItem.Status.CANCELLED:
            return Response(
                {"detail": "Bekor qilingan itemni cooking qilib bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )
        item.status = OrderItem.Status.COOKING
        item.save()
        return Response(
            OrderItemSerializer(item, context={"request": request}).data,
            status=status.HTTP_200_OK
        )
    @action(detail=True, methods=["post"])
    def mark_ready(self, request, pk=None):
        item = self.get_object()
        if item.status == OrderItem.Status.CANCELLED:
            return Response(
                {"detail": "Bekor qilingan itemni ready qilib bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )
        item.status = OrderItem.Status.READY
        item.save()
        return Response(
            OrderItemSerializer(item, context={"request": request}).data,
            status=status.HTTP_200_OK
        )
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        item = self.get_object()

        if item.order.status in [Order.Status.PAID, Order.Status.CLOSED]:
            return Response(
                {"detail": "To‘langan yoki yopilgan buyurtmadagi itemni bekor qilib bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        item.status = OrderItem.Status.CANCELLED
        item.save()

        return Response(
            OrderItemSerializer(item, context={"request": request}).data,
            status=status.HTTP_200_OK
        )