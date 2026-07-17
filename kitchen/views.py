from django.db import transaction
from rest_framework import viewsets, status, filters, serializers
# from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import KitchenTicket, Department, Category, Food
from .serializer import KitchenTicketSerializer, KitchenTicketStatusSerializer, DepartmentSerializer, \
    SemiProductSerializer, MenuProductSerializer, CategorySerializer, FoodSerializer
from rest_framework.views import APIView
from django.db.models import Sum, F, Count, Avg,Q
from order.models import OrderItem, Order
from django.utils.dateparse import parse_date
from django.db.models.functions import ExtractHour, TruncDate
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import SemiProduct,MenuProduct
from django_filters.rest_framework import DjangoFilterBackend
from inventory.models import Ingredient
from kitchen.models import Food, SemiProduct
from order.models import Order, OrderItem
from rest_framework.permissions import AllowAny
from rest_framework.serializers import ModelSerializer
from order.models import Order
from kitchen.models import Food
from inventory.models import Maxsulot
from employee.models import Employee
from rest_framework import generics
from kitchen.models import Category


class CategorySelectSerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySelectSerializer
    permission_classes = []


class SyncStatusAPIView(APIView):
    def get(self, request):
        now = timezone.now()
        last_order = Order.objects.order_by('-created_at').first()
        kassa_time = last_order.created_at.strftime('%H:%M') if last_order else "--:--"
        kassa_date = last_order.created_at.strftime('%d %b, %Y') if last_order else "Hali yo'q"
        last_inventory = Maxsulot.objects.order_by('-id').first()
        inventory_time = now.strftime('%H:%M') if last_inventory else "--:--"  # yoki model vaqti
        inventory_date = "Faol" if last_inventory else "Hali yo'q"
        last_food = Food.objects.order_by('-id').first()
        menyu_time = now.strftime('%H:%M') if last_food else "--:--"
        menyu_date = "Faol" if last_food else "Hali yo'q"
        last_emp = Employee.objects.order_by('-id').first()
        xodim_time = now.strftime('%H:%M') if last_emp else "--:--"
        xodim_date = "Faol" if last_emp else "Hali yo'q"
        data = {
            "oxirgi_tekshiruv": now.strftime('%H:%M'),
            "sana": now.strftime('%d %b, %Y'),
            "bo_limlar": {
                "dashboard": {
                    "status": "Kutilmoqda" if last_order else "Hali yo'q",
                    "vaqt": kassa_time,
                    "sana": kassa_date,
                    "url": "/order/orders/"
                },
                "ombor": {
                    "status": "Kutilmoqda",
                    "vaqt": inventory_time,
                    "sana": inventory_date,
                    "url": "/inventory/stocks/"
                },
                "sozlamalar": {
                    "status": "Kutilmoqda",
                    "vaqt": now.strftime('%H:%M'),
                    "sana": "Faol",
                    "url": "/sozlamalar/settings/"
                },
                "menyu": {
                    "status": "Kutilmoqda",
                    "vaqt": menyu_time,
                    "sana": menyu_date,
                    "url": "/table/product/"
                },
                "xodimlar": {
                    "status": "Kutilmoqda",
                    "vaqt": xodim_time,
                    "sana": xodim_date,
                    "url": "/employees/employees/"
                },
                "kassa": {
                    "status": "Kutilmoqda",
                    "vaqt": kassa_time,
                    "sana": kassa_date,
                    "url": "/order/orders/"
                },
                "hisobotlar": {
                    "status": "Kutilmoqda",
                    "vaqt": kassa_time,
                    "sana": kassa_date,
                    "url": "/order/orders/"
                }
            }
        }
        return Response(data, status=status.HTTP_200_OK)



class RecipeSelectableItemsAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
        data = []
        ingredients = Ingredient.objects.all()
        for ing in ingredients:
            data.append({
                "id": ing.id,
                "name": f"{ing.name} (Masalliq)",
                "type": "ingredient",
                "price": float(getattr(ing, 'price', 0) or 0)
            })
        foods = Food.objects.filter(is_active=True)
        for food in foods:
            data.append({
                "id": food.id,
                "name": f"{food.name} (Taom)",
                "type": "food",
                "price": float(getattr(food, 'cost_price', 0) or 0) # Tannarxi
            })
        semis = SemiProduct.objects.all()
        for semi in semis:
            data.append({
                "id": semi.id,
                "name": f"{semi.name} (Yarim tayyor)",
                "type": "semi_product",
                "price": float(semi.total_cost or 0)
            })
        return Response(data)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class FoodViewSet(viewsets.ModelViewSet):
    queryset = Food.objects.filter(is_active=True).order_by('-id')
    serializer_class = FoodSerializer
    filterset_fields = ['category', 'department', 'is_active']
    search_fields = ['name']
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response({"message": "Taom muvaffaqiyatli arxivlandi (o'chirildi)."}, status=status.HTTP_200_OK)


class MenuProductViewSet(viewsets.ModelViewSet):
    queryset = MenuProduct.objects.all().select_related('section').prefetch_related('recipe_ingredients')
    serializer_class = MenuProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']
    def get_queryset(self):
        queryset = super().get_queryset()
        category_param = self.request.query_params.get('category')
        if category_param:
            queryset = queryset.filter(category=category_param)
        is_active_param = self.request.query_params.get('is_active')
        if is_active_param is not None:
            is_active = is_active_param.lower() in ['true', '1']
            queryset = queryset.filter(is_active=is_active)
        return queryset

class SemiProductViewSet(viewsets.ModelViewSet):
    queryset = SemiProduct.objects.all().prefetch_related('recipes__ingredient')
    serializer_class = SemiProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    def get_queryset(self):
        queryset = super().get_queryset()
        category_param = self.request.query_params.get('category')
        if category_param:
            queryset = queryset.filter(category=category_param)
        return queryset

class OrderHistoryAPIView(APIView):
    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        waiter_id = request.query_params.get("waiter_id")
        status_param = request.query_params.get("status")
        search_query = request.query_params.get("search")
        orders = Order.objects.all().select_related('assigned_waiter')
        if start_date:
            orders = orders.filter(created_at__date__gte=parse_date(start_date))
        if end_date:
            orders = orders.filter(created_at__date__lte=parse_date(end_date))
        if waiter_id:
            orders = orders.filter(assigned_waiter_id=waiter_id)
        if status_param:
            orders = orders.filter(status=status_param)
        if search_query:
            orders = orders.filter(id__icontains=search_query)
        cards_aggregation = orders.aggregate(
            total_count=Count('id'),
            total_revenue=Sum('total_amount'),
            avg_check=Avg('total_amount')
        )
        canceled_count = orders.filter(status="CANCELED").count()
        cards = {
            "barcha_buyurtmalar": int(cards_aggregation['total_count'] or 0),
            "umumiy_tushum": float(cards_aggregation['total_revenue'] or 0),
            "bekor_qilinganlar": int(canceled_count),
            "ortacha_chek": round(float(cards_aggregation['avg_check'] or 0), 2)
        }
        jadval_list = []
        for o in orders:
            sana_vaqt_str = o.created_at.strftime('%d.%m.%Y %H:%M') if o.created_at else "—"
            jadval_list.append({
                "buyurtma_raqami": o.id,
                "joylashuv": "Olib ketish" if getattr(o, 'delivery_type', '') == 'TAKEAWAY' else "Zalda / Stol",
                "ofitsiant": o.assigned_waiter.name if o.assigned_waiter else "—",
                "mehmonlar_soni": getattr(o, 'guests_count', 1) or 1,
                "status": o.status,
                "sana_vaqt": sana_vaqt_str,
                "summa": float(o.total_amount or 0)
            })
        return Response({
            "cards": cards,
            "orders_table": jadval_list
        }, status=status.HTTP_200_OK)


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class DashboardAPIView(APIView):
    def get(self, request):
        start_date_param = request.query_params.get("start_date")
        end_date_param = request.query_params.get("end_date")
        date_preset = request.query_params.get("date_preset", "today")
        valid_sales_statuses = [
            "paid", "closed", "PAID", "CLOSED",
            "To'lov olindi", "To‘lov olindi", "Yopildi", "1"
        ]
        orders = Order.objects.filter(status__in=valid_sales_statuses)
        if date_preset == "all":
            pass
        elif date_preset == "yesterday":
            kecha = timezone.now().date() - timedelta(days=1)
            orders = orders.filter(created_at__date=kecha)
        elif date_preset == "week":
            hafta_oldingi = timezone.now().date() - timedelta(days=7)
            orders = orders.filter(created_at__date__gte=hafta_oldingi)
        elif date_preset == "month":
            oy_oldingi = timezone.now().date() - timedelta(days=30)
            orders = orders.filter(created_at__date__gte=oy_oldingi)
        else:
            if start_date_param:
                orders = orders.filter(created_at__date__gte=parse_date(start_date_param))
            if end_date_param:
                orders = orders.filter(created_at__date__lte=parse_date(end_date_param))
            if not start_date_param and not end_date_param and date_preset == "today":
                orders = orders.filter(created_at__date=timezone.now().date())
        totals = orders.aggregate(
            jami_savdo=Sum('total_amount'),
            buyurtmalar_soni=Count('id'),
            ortacha_chek=Avg('total_amount')
        )
        jami_savdo = totals['jami_savdo'] or 0
        buyurtmalar_soni = totals['buyurtmalar_soni'] or 0
        ortacha_chek = totals['ortacha_chek'] or 0
        daily_sales = (
            orders.annotate(kun=TruncDate('created_at'))
            .values('kun')
            .annotate(tushum=Sum('total_amount'))
            .order_by('kun')
        )
        savdo_dinamikasi = []
        for d in daily_sales:
            if d['kun']:
                savdo_dinamikasi.append({
                    "sana": d['kun'].strftime('%d %b'),
                    "daromad": float(d['tushum'] or 0),
                    "foyda": float(d['tushum'] or 0)
                })
        if not savdo_dinamikasi:
            savdo_dinamikasi.append({
                "sana": timezone.now().date().strftime('%d %b'),
                "daromad": float(jami_savdo),
                "foyda": float(jami_savdo)
            })
        hourly_flows = (
            orders.annotate(soat=ExtractHour('created_at'))
            .values('soat')
            .annotate(soni=Count('id'))
            .order_by('soat')
        )
        soatbay_oqim = {f"{h}:00": 0 for h in range(24)}
        for h_data in hourly_flows:
            if h_data['soat'] is not None:
                soatbay_oqim[f"{h_data['soat']}:00"] = h_data['soni']
        kitchen_statuses = ["sent_to_kitchen", "cooking", "Oshxonaga yuborildi", "Tayyorlanmoqda", "2", "3"]
        oshxona_tayyorlanmoqda = Order.objects.filter(status__in=kitchen_statuses).count()
        yigirma_daqiqa_oldingi_vaqt = timezone.now() - timedelta(minutes=20)
        oshxona_kechikkan = Order.objects.filter(
            status__in=kitchen_statuses,
            created_at__lt=yigirma_daqiqa_oldingi_vaqt
        ).count()
        bugun = timezone.now().date()
        bugungi_tushum = Order.objects.filter(
            status__in=valid_sales_statuses,
            created_at__date=bugun
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        active_order_statuses = ["sent_to_kitchen", "cooking", "ready", "served", "payment_pending", "Tayyorlanmoqda","Tayyor", "Berildi"]
        band_stollar = Order.objects.filter(
            status__in=active_order_statuses,
            table__isnull=False
        ).values('table').distinct().count()
        top_products_query = (
            OrderItem.objects.filter(order__status__in=valid_sales_statuses)
            .values(nomi=F('product__name'))
            .annotate(tushum=Sum(F('qty') * F('unit_price')))
            .order_by('-tushum')[:5]
        )
        top_sotilganlar = [
            {
                "nomi": p['nomi'] or "Noma'lum",
                "tushum": float(p['tushum'] or 0)
            } for p in top_products_query
        ]
        return Response({
            "cards": {
                "jami_savdo": float(jami_savdo),
                "daromad": float(jami_savdo),
                "foyda": float(jami_savdo),
                "marja_foiz": 100.0,
                "ortacha_chek": round(float(ortacha_chek), 1),
                "buyurtmalar_soni": int(buyurtmalar_soni)
            },
            "savdo_dinamikasi": savdo_dinamikasi,
            "soatbay_mijozlar_oqimi": [{"soat": k, "qiymat": int(v)} for k, v in soatbay_oqim.items()],
            "jonli_holat": {
                "oshxona_tayyorlanmoqda": int(oshxona_tayyorlanmoqda),
                "oshxona_kechikkan": int(oshxona_kechikkan),
                "band_stollar_ochiq": int(band_stollar),
                "bugungi_pul_tushumi": float(bugungi_tushum)
            },
            "top_sotilganlar": top_sotilganlar
        }, status=status.HTTP_200_OK)

class SotuvHisobotiAPIView(APIView):
    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        order_items = OrderItem.objects.all().select_related('order', 'product', 'product__category')
        if start_date:
            order_items = order_items.filter(order__created_at__date__gte=parse_date(start_date))
        if end_date:
            order_items = order_items.filter(order__created_at__date__lte=parse_date(end_date))
        products_stats = (
            order_items.values(
                nomi=F('product__name'),
                kategoriya=F('product__category__name'),
            )
            .annotate(
                jami_soni=Sum('qty'),
                jami_tushum=Sum('line_total'),
            )
            .order_by('-jami_tushum')
        )
        total_revenue = sum(p['jami_tushum'] or 0 for p in products_stats)
        tafsilotlar_list = []
        for p in products_stats:
            tushum = p['jami_tushum'] or 0
            soni = p['jami_soni'] or 0
            item_sample = order_items.filter(product__name=p['nomi']).first()
            if item_sample and item_sample.order and item_sample.order.created_at is not None:
                sana_str = item_sample.order.created_at.strftime('%Y-%m-%d %H:%M')
            else:
                sana_str = "——"
            tannarx_dona = 0
            if item_sample and item_sample.product:
                tannarx_dona = getattr(item_sample.product, 'cost_price', 0) or 0
                if not tannarx_dona:
                    tannarx_dona = (item_sample.unit_price or Decimal('0')) * Decimal('0.4')
            jami_tannarx = float(tannarx_dona) * float(soni)
            sof_foyda = float(tushum) - jami_tannarx
            marja = f"{round((sof_foyda / float(tushum)) * 100, 1)}%" if tushum > 0 else "0%"
            tafsilotlar_list.append({
                "sana": sana_str,
                "kategoriya": p['kategoriya'] or "Taomlar",
                "nomi": p['nomi'] or "Noma'lum mahsulot",
                "tushum": tushum,
                "soni": soni,
                "sof_tushum": tushum,
                "foyda": round(sof_foyda, 1),
                "marja": marja
            })
        return Response({
            "jami": total_revenue,
            "tafsilotlar": tafsilotlar_list
        }, status=status.HTTP_200_OK)


class UmumiyHisobotAPIView(APIView):
    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        orders = Order.objects.all()
        if start_date:
            orders = orders.filter(created_at__date__gte=parse_date(start_date))
        if end_date:
            orders = orders.filter(created_at__date__lte=parse_date(end_date))
        daily_stats = (
            orders.annotate(kun=TruncDate('created_at'))
            .values('kun', kassa_nomi=F('assigned_waiter__name'))
            .annotate(
                savdolar_soni=Count('id'),
                jami_tushum=Sum('total_amount'),
                jami_chegirma=Sum(F('service_amount') * 0),
                jami_qaytarish=Sum(F('total_amount') * 0),
            )
            .order_by('-kun')
        )
        dinamika_list = []
        total_revenue = 0
        for d in daily_stats:
            tushum = d['jami_tushum'] or 0
            savdolar = d['savdolar_soni'] or 0
            chegirma = d['jami_chegirma'] or 0
            qaytarish = d['jami_qaytarish'] or 0
            sof_tushum = tushum - chegirma - qaytarish
            kunlik_tannarx = 0
            current_date = d['kun']
            if current_date is not None:
                day_items = OrderItem.objects.filter(order__created_at__date=current_date).select_related('product')
                for item in day_items:
                    t_dona = getattr(item.product, 'cost_price', 0) if item.product else 0
                    if not t_dona:
                        t_dona = (item.unit_price or Decimal('0')) * Decimal('0.4')
                    kunlik_tannarx += (float(t_dona) * float(item.qty or 0))
                sana_str = current_date.strftime('%Y-%m-%d')
            else:
                sana_str = "——"
            sof_foyda = float(sof_tushum) - kunlik_tannarx
            marja_foiz = round((sof_foyda / float(sof_tushum)) * 100, 1) if sof_tushum > 0 else 0.0
            total_revenue += tushum
            dinamika_list.append({
                "sana": sana_str,
                "kassa": d['kassa_nomi'] or "Noma'lum Xodim",
                "savdolar_soni": int(savdolar),
                "tushum": float(tushum),
                "chegirma": float(chegirma),
                "chegirma_foiz": 0.0,
                "qaytarish": float(qaytarish),
                "sof_tushum": float(sof_tushum),
                "foyda": round(sof_foyda, 1),
                "marja": marja_foiz
            })
        cashier_stats = (
            orders.values(kassa_nomi=F('assigned_waiter__name'))
            .annotate(tushum=Sum('total_amount'))
            .order_by('-tushum')
        )
        kassa_list = []
        for c in cashier_stats:
            c_tushum = c['tushum'] or 0
            percentage = round((c_tushum / total_revenue) * 100, 2) if total_revenue > 0 else 0.0
            kassa_list.append({
                "kassa": c['kassa_nomi'] or "Nomalum Xodim",
                "tushum": float(c_tushum),
                "ulush_foiz": percentage
            })
        return Response({
            "jami_tushum": float(total_revenue),
            "dinamika": dinamika_list,
            "kassalar_statistikasi": kassa_list
        }, status=status.HTTP_200_OK)

class AbcAnalysisAPIView(APIView):
    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        category_id = request.query_params.get("category_id")
        order_items = OrderItem.objects.all().select_related('order', 'product')
        if start_date:
            order_items = order_items.filter(order__created_at__date__gte=parse_date(start_date))
        if end_date:
            order_items = order_items.filter(order__created_at__date__lte=parse_date(end_date))
        if category_id:
            order_items = order_items.filter(product__category_id=category_id)
        products_stats = (
            order_items.values(nomi=F('product__name'))
            .annotate(
                tushum=Sum('line_total'),
                sotuv_soni=Sum('qty')
            )
            .order_by('-tushum')
        )
        total_revenue = sum(p['tushum'] or 0 for p in products_stats)
        abc_list = []
        running_sum = 0
        for p in products_stats:
            tushum = p['tushum'] or 0
            sotuv_soni = p['sotuv_soni'] or 0
            share_percent = (tushum / total_revenue) * 100 if total_revenue > 0 else 0
            running_sum += share_percent
            if running_sum <= 80:
                kategoriya_abc = "A"
            elif running_sum <= 95:
                kategoriya_abc = "B"
            else:
                kategoriya_abc = "C"
            item_sample = order_items.filter(product__name=p['nomi']).first()
            tannarx_dona = getattr(item_sample.product, 'cost_price', 0) if item_sample and item_sample.product else 0
            if not tannarx_dona and item_sample:
                tannarx_dona = (item_sample.unit_price or Decimal('0')) * Decimal('0.4')
            jami_tannarx = float(tannarx_dona) * float(sotuv_soni)
            foyda = float(tushum) - jami_tannarx
            abc_list.append({
                "artikul": getattr(item_sample.product, 'artikul', '—') if item_sample and item_sample.product else "—",
                "nomi": p['nomi'] or "Noma'lum mahsulot",
                "tushum": tushum,
                "sotuv": f"{sotuv_soni} dona.",
                "foyda": round(foyda, 1),
                "tushumdan": f"{round(share_percent, 2)}%",
                "kategoriya_abc": kategoriya_abc
            })
        return Response({
            "jami_tushum": total_revenue,
            "abc_analiz": abc_list
        }, status=status.HTTP_200_OK)


class UmumiyHisobotAPIView(APIView):
    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        orders = Order.objects.all()
        if start_date:
            orders = orders.filter(created_at__date__gte=parse_date(start_date))
        if end_date:
            orders = orders.filter(created_at__date__lte=parse_date(end_date))
        daily_stats = (
            orders.annotate(kun=TruncDate('created_at'))
            .values('kun', kassa_nomi=F('assigned_waiter__name'))
            .annotate(
                savdolar_soni=Count('id'),
                jami_tushum=Sum('total_amount'),
                jami_chegirma=Sum(F('service_amount') * 0),
                jami_qaytarish=Sum(F('total_amount') * 0),
            )
            .order_by('-kun')
        )
        dinamika_list = []
        total_revenue = 0
        for d in daily_stats:
            tushum = d['jami_tushum'] or 0
            savdolar = d['savdolar_soni'] or 0
            chegirma = d['jami_chegirma'] or 0
            qaytarish = d['jami_qaytarish'] or 0
            sof_tushum = tushum - chegirma - qaytarish
            kunlik_tannarx = 0
            current_date = d['kun']
            if current_date is not None:
                day_items = OrderItem.objects.filter(order__created_at__date=current_date).select_related('product')
                for item in day_items:
                    t_dona = getattr(item.product, 'cost_price', 0) if item.product else 0
                    if not t_dona:
                        t_dona = (item.unit_price or Decimal('0')) * Decimal('0.4')
                    kunlik_tannarx += (float(t_dona) * float(item.qty or 0))
                sana_str = current_date.strftime('%Y-%m-%d')
            else:
                sana_str = "——"
            sof_foyda = float(sof_tushum) - kunlik_tannarx
            marja_foiz = round((sof_foyda / float(sof_tushum)) * 100, 1) if sof_tushum > 0 else 0
            total_revenue += tushum
            dinamika_list.append({
                "sana": sana_str,
                "kassa": d['kassa_nomi'] or "Noma'lum Xodim",
                "savdolar_soni": f"{savdolar} dona.",
                "tushum": tushum,
                "chegirma": chegirma if chegirma > 0 else "—",
                "chegirma_foiz": "—",
                "qaytarish": f"-{qaytarish}" if qaytarish > 0 else "—",
                "sof_tushum": sof_tushum,
                "foyda": round(sof_foyda, 1),
                "marja": f"{marja_foiz}%"
            })
        cashier_stats = (
            orders.values(kassa_nomi=F('assigned_waiter__name'))
            .annotate(tushum=Sum('total_amount'))
            .order_by('-tushum')
        )
        kassa_list = []
        for c in cashier_stats:
            c_tushum = c['tushum'] or 0
            percentage = round((c_tushum / total_revenue) * 100, 2) if total_revenue > 0 else 0
            kassa_list.append({
                "kassa": c['kassa_nomi'] or "Nomalum Xodim",
                "tushum": c_tushum,
                "ulush_foiz": percentage
            })
        return Response({
            "jami_tushum": total_revenue,
            "dinamika": dinamika_list,
            "kassalar_statistikasi": kassa_list
        }, status=status.HTTP_200_OK)


class AbcAnalysisAPIView(APIView):
    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        category_id = request.query_params.get("category_id")
        order_items = OrderItem.objects.all().select_related('order', 'product', 'product__category')
        if start_date:
            order_items = order_items.filter(order__created_at__date__gte=parse_date(start_date))
        if end_date:
            order_items = order_items.filter(order__created_at__date__lte=parse_date(end_date))
        if category_id:
            order_items = order_items.filter(product__category_id=category_id)
        products_stats = (
            order_items.values(
                nomi=F('product__name'),
                kategoriya_nomi=F('product__category__name')
            )
            .annotate(
                tushum=Sum('line_total'),
                sotuv_soni=Sum('qty')
            )
            .order_by('-tushum')
        )
        total_revenue = sum(p['tushum'] or 0 for p in products_stats)
        kategoriyalar_bunch = {}
        running_sum = 0
        for p in products_stats:
            tushum = p['tushum'] or 0
            sotuv_soni = p['sotuv_soni'] or 0
            share_percent = (tushum / total_revenue) * 100 if total_revenue > 0 else 0
            running_sum += share_percent
            if running_sum <= 80:
                kategoriya_abc = "A"
            elif running_sum <= 95:
                kategoriya_abc = "B"
            else:
                kategoriya_abc = "C"
            item_sample = order_items.filter(product__name=p['nomi']).first()
            tannarx_dona = getattr(item_sample.product, 'cost_price', 0) if item_sample and item_sample.product else 0
            if not tannarx_dona and item_sample:
                tannarx_dona = (item_sample.unit_price or Decimal('0')) * Decimal('0.4')
            jami_tannarx = float(tannarx_dona) * float(sotuv_soni)
            foyda = float(tushum) - jami_tannarx
            mahsulot_mahlumoti = {
                "artikul": getattr(item_sample.product, 'artikul', '—') if item_sample and item_sample.product else "—",
                "nomi": p['nomi'] or "Noma'lum mahsulot",
                "tushum": tushum,
                "sotuv": f"{sotuv_soni} dona.",
                "foyda": round(foyda, 1),
                "tushumdan": f"{round(share_percent, 2)}%",
                "kategoriya_abc": kategoriya_abc
            }
            kat_nomi = p['kategoriya_nomi'] or "Kategoriyasiz"
            if kat_nomi not in kategoriyalar_bunch:
                kategoriyalar_bunch[kat_nomi] = []
            kategoriyalar_bunch[kat_nomi].append(mahsulot_mahlumoti)
        guruhlangan_abc_list = []
        for kat_name, products in kategoriyalar_bunch.items():
            guruhlangan_abc_list.append({
                "kategoriya": kat_name,
                "mahsulotlar": products
            })
        return Response({
            "jami_tushum": total_revenue,
            "abc_analiz_guruhlangan": guruhlangan_abc_list
        }, status=status.HTTP_200_OK)




class KitchenTicketViewSet(viewsets.ModelViewSet):
    # permission_classes = [IsAuthenticated]
    def get_queryset(self):
        queryset = (
            KitchenTicket.objects
            .select_related("order", "sent_by")
            .all()
            .order_by("-created_at")
        )
        status_param = self.request.query_params.get("status")
        order_param = self.request.query_params.get("order")
        if status_param:
            queryset = queryset.filter(status=status_param)
        if order_param:
            queryset = queryset.filter(order_id=order_param)
        return queryset
    def get_serializer_class(self):
        if self.action == "update_status":
            return KitchenTicketStatusSerializer
        return KitchenTicketSerializer
    @transaction.atomic
    def perform_create(self, serializer):
        employee = getattr(self.request.user, "employee", None)
        if employee and "sent_by" not in serializer.validated_data:
            serializer.save(sent_by=employee)
        else:
            serializer.save()
    @transaction.atomic
    def perform_update(self, serializer):
        serializer.save()
    @transaction.atomic
    def perform_destroy(self, instance):
        instance.delete()
    @action(detail=True, methods=["patch"])
    @transaction.atomic
    def update_status(self, request, pk=None):
        ticket = self.get_object()
        serializer = self.get_serializer(
            ticket,
            data=request.data,
            partial=True,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            KitchenTicketSerializer(ticket, context={"request": request}).data,
            status=status.HTTP_200_OK
        )
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def mark_cooking(self, request, pk=None):
        ticket = self.get_object()
        serializer = KitchenTicketStatusSerializer(
            ticket,
            data={"status": KitchenTicket.Status.COOKING},
            partial=True,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            KitchenTicketSerializer(ticket, context={"request": request}).data,
            status=status.HTTP_200_OK
        )
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def mark_ready(self, request, pk=None):
        ticket = self.get_object()
        serializer = KitchenTicketStatusSerializer(
            ticket,
            data={"status": KitchenTicket.Status.READY},
            partial=True,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            KitchenTicketSerializer(ticket, context={"request": request}).data,
            status=status.HTTP_200_OK
        )
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def cancel(self, request, pk=None):
        ticket = self.get_object()
        serializer = KitchenTicketStatusSerializer(
            ticket,
            data={"status": KitchenTicket.Status.CANCELLED},
            partial=True,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            KitchenTicketSerializer(ticket, context={"request": request}).data,
            status=status.HTTP_200_OK
        )


class XodimlarHisobotiAPIView(APIView):
    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        waiter_id = request.query_params.get("waiter_id")
        orders = Order.objects.all()
        if start_date:
            orders = orders.filter(created_at__date__gte=parse_date(start_date))
        if end_date:
            orders = orders.filter(created_at__date__lte=parse_date(end_date))
        if waiter_id:
            orders = orders.filter(assigned_waiter_id=waiter_id)
        total_revenue = orders.aggregate(jami=Sum('total_amount'))['jami'] or 0
        daily_employee_stats = (
            orders.annotate(kun=TruncDate('created_at'))
            .values('kun', xodim_nomi=F('assigned_waiter__name'))
            .annotate(
                tushum=Sum('total_amount'),
                chek_soni=Count('id'),
                chegirma=Sum(F('service_amount') * 0),
                qaytarish=Sum(F('total_amount') * 0),
                qaytarish_soni=Count('id', filter=Q(total_amount__lt=0))
            )
            .order_by('-kun', '-tushum')
        )
        jadval_list = []
        for item in daily_employee_stats:
            item_tushum = item['tushum'] or 0
            item_chek_soni = item['chek_soni'] or 0
            item_chegirma = item['chegirma'] or 0
            item_qaytarish = item['qaytarish'] or 0
            ortacha_chek = round(item_tushum / item_chek_soni, 1) if item_chek_soni > 0 else 0
            if item['kun'] is not None:
                sana_str = item['kun'].strftime('%Y-%m-%d')
            else:
                sana_str = "——"
            jadval_list.append({
                "sana": sana_str,
                "sotuvchi": item['xodim_nomi'] or "Noma'lum Xodim",
                "kassa": item['xodim_nomi'] or "Noma'lum Kassa",
                "tushum": item_tushum,
                "chegirma": item_chegirma if item_chegirma > 0 else "—",
                "qaytarish": f"-{item_qaytarish}" if item_qaytarish > 0 else "—",
                "qaytarish_soni": f"{item['qaytarish_soni']} dona" if item['qaytarish_soni'] > 0 else "—",
                "chek_soni": f"{item_chek_soni} dona.",
                "ortacha_chek": ortacha_chek
            })
        cashier_stats = (
            orders.values(kassa_nomi=F('assigned_waiter__name'))
            .annotate(tushum=Sum('total_amount'))
            .order_by('-tushum')
        )
        kassa_list = []
        for c in cashier_stats:
            c_tushum = c['tushum'] or 0
            percentage = round((c_tushum / total_revenue) * 100, 2) if total_revenue > 0 else 0
            kassa_list.append({
                "xodim": c['kassa_nomi'] or "Noma'lum Xodim",
                "tushum": c_tushum,
                "ulush_foiz": percentage
            })
        return Response({
            "jami_umumiy_tushum": total_revenue,
            "xodimlar_statistikasi": kassa_list,
            "jadval_mahlumotlari": jadval_list
        }, status=status.HTTP_200_OK)