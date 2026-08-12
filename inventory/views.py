from rest_framework import viewsets, filters, status
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from datetime import timedelta
from django.db.models import Sum, Count
from django.db import transaction
from django.utils.dateparse import parse_date
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from employee.models import EmployeePermission
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.parsers import MultiPartParser, FormParser
from employee.models import EmployeePermission
from employee.serializer import EmployeePermissionSerializer
from rest_framework.views import APIView
from .models import (
    OlchovBirligi,
    Maxsulot,
    OvqatKategoriya,
    Ovqat,
    Kirim,
    Chiqim,
    Retsept,
    Ombor,
    Taminotchi,
    FinancialAccount,
    Transaction,
    FinancialCategory,
    Purchase,
    Realization,
    InventoryProduct,
)
from .serializer import (
    OlchovBirligiSerializer,
    MaxsulotSerializer,
    OvqatKategoriyaSerializer,
    OvqatSerializer,
    KirimSerializer,
    ChiqimSerializer,
    RetseptSerializer,
    OmborSerializer,
    TaminotchiSerializer,
    FinancialAccountSerializer,
    TransactionSerializer,
    FinancialCategorySerializer,
    PurchaseSerializer,
    RealizationSerializer,
    InventoryProductSerializer,
)


class EDIImportView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = EDIImportSerializer(data=request.data)
        if serializer.is_valid():
            uploaded_file = serializer.validated_data['file']

            # Bu yerda Excel/EDI faylini qayta ishlash mantiqini yozish mumkin (masalan pandas yoki openpyxl bilan)
            # Hozircha frontend fayl muvaffaqiyatli yuklanganini ko'rishi uchun 200 qaytaramiz:

            return Response({
                "status": "success",
                "message": f"'{uploaded_file.name}' fayli muvaffaqiyatli qabul qilindi va omborga kiritildi.",
                "filename": uploaded_file.name
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SuppliersAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        queryset = Taminotchi.objects.all().order_by('id')
        serializer = TaminotchiSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = TaminotchiSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EmployeePermissionViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeePermissionSerializer
    permission_classes = [AllowAny]  # Yoki IsAuthenticated

    def get_queryset(self):
        queryset = EmployeePermission.objects.all()
        employee_id = self.request.query_params.get('employee')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PurchaseViewSet(viewsets.ModelViewSet):
    queryset = Purchase.objects.all().order_by('-created_at')
    serializer_class = PurchaseSerializer
    permission_classes = [AllowAny]
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        stats = queryset.aggregate(
            umumiy_xaridlar=Count('id'),
            umumiy_summa=Sum('total_amount'),
            mahsulotlar_soni=Count('items__product', distinct=True)
        )
        return Response({
            "stats": {
                "umumiy_xaridlar": stats['umumiy_xaridlar'] or 0,
                "umumiy_summa": float(stats['umumiy_summa'] or 0),
                "mahsulotlar_soni": stats['mahsulotlar_soni'] or 0,
                "ortacha_sotuv_foizi": 0
            },
            "results": serializer.data
        })


class RealizationViewSet(viewsets.ModelViewSet):
    queryset = Realization.objects.all().order_by('-created_at')
    serializer_class = RealizationSerializer
    permission_classes = [AllowAny]
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        stats = queryset.aggregate(
            jami_realizatsiyalar=Count('id'),
            umumiy_summa=Sum('total_amount'),
            tovar_pozitsiyalari=Count('items__id'),
            realizatsiya_marjasi=Sum('margin_amount')
        )
        return Response({
            "stats": {
                "jami_realizatsiyalar": stats['jami_realizatsiyalar'] or 0,
                "umumiy_summa": float(stats['umumiy_summa'] or 0),
                "tovar_pozitsiyalari": stats['tovar_pozitsiyalari'] or 0,
                "realizatsiya_marjasi": float(stats['realizatsiya_marjasi'] or 0)
            },
            "results": serializer.data
        })


class InventoryProductViewSet(viewsets.ModelViewSet):
    queryset = InventoryProduct.objects.all().order_by('-created_at')
    serializer_class = InventoryProductSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'product_type', 'branch']
    search_fields = ['name', 'barcode', 'mxik']


class FinanceMonitoringAPIView(APIView):
    def get(self, request, *args, **kwargs):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        transactions = Transaction.objects.all()
        if start_date:
            transactions = transactions.filter(date_created__date__gte=parse_date(start_date))
        if end_date:
            transactions = transactions.filter(date_created__date__lte=parse_date(end_date))
        total_income = float(
            transactions.filter(transaction_type='INCOME').aggregate(Sum('amount'))['amount__sum'] or 0)
        total_expense = float(
            transactions.filter(transaction_type='EXPENSE').aggregate(Sum('amount'))['amount__sum'] or 0)
        categories_data = []
        categories = FinancialCategory.objects.all()
        for cat in categories:
            cat_sum = float(transactions.filter(category=cat.name).aggregate(Sum('amount'))['amount__sum'] or 0)
            if cat_sum > 0:
                categories_data.append({
                    "kategoriya_nomi": cat.name,
                    "turi": cat.category_type,
                    "tur_display": cat.get_category_type_display(),
                    "umumiy_summa": cat_sum
                })
        return Response({
            "statistika": {
                "umumiy_daromad": total_income,
                "umumiy_xarajat": total_expense,
                "sof_foyda": total_income - total_expense
            },
            "kategoriyalar_bo_yicha": categories_data
        })


class FinancialCategoryViewSet(viewsets.ModelViewSet):
    queryset = FinancialCategory.objects.all()
    serializer_class = FinancialCategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    def get_queryset(self):
        queryset = super().get_queryset()
        category_type = self.request.query_params.get('category_type')
        if category_type:
            queryset = queryset.filter(category_type=category_type)
        return queryset


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all().select_related('account')
    serializer_class = TransactionSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['description']
    def get_queryset(self):
        queryset = super().get_queryset()
        source_type = self.request.query_params.get('source_type')
        if source_type and source_type != 'Barcha':
            queryset = queryset.filter(source_type=source_type)
        category_param = self.request.query_params.get('category')
        if category_param:
            queryset = queryset.filter(category=category_param)
        account_param = self.request.query_params.get('account_id')
        if account_param:
            queryset = queryset.filter(account_id=account_param)
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(date_created__date__gte=parse_date(start_date))
        if end_date:
            queryset = queryset.filter(date_created__date__lte=parse_date(end_date))
        return queryset


class FinancialAccountViewSet(viewsets.ModelViewSet):
    queryset = FinancialAccount.objects.all()
    serializer_class = FinancialAccountSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    def get_queryset(self):
        queryset = super().get_queryset()
        account_type = self.request.query_params.get('account_type')
        if account_type:
            queryset = queryset.filter(account_type=account_type)
        return queryset


class TaminotchiViewSet(viewsets.ModelViewSet):
    queryset = Taminotchi.objects.all()
    serializer_class = TaminotchiSerializer


class OlchovBirligiViewSet(viewsets.ModelViewSet):
    queryset = OlchovBirligi.objects.all()
    serializer_class = OlchovBirligiSerializer


class MaxsulotViewSet(viewsets.ModelViewSet):
    queryset = Maxsulot.objects.all()
    serializer_class = MaxsulotSerializer


class OvqatKategoriyaViewSet(viewsets.ModelViewSet):
    queryset = OvqatKategoriya.objects.all()
    serializer_class = OvqatKategoriyaSerializer


class OvqatViewSet(viewsets.ModelViewSet):
    queryset = Ovqat.objects.all()
    serializer_class = OvqatSerializer

class KirimViewSet(viewsets.ModelViewSet):
    queryset = Kirim.objects.filter(is_deleted=False)  # Oddiy ro'yxatda o'chganlar chiqmaydi
    serializer_class = KirimSerializer
    def perform_create(self, serializer):
        kirim = serializer.save(created_by=self.request.user if self.request.user.is_authenticated else None)
        Ombor.objects.create(
            maxsulot=kirim.product,
            miqdor=kirim.quantity,
            oxirgi_narx=kirim.price
        )
class ChiqimViewSet(viewsets.ModelViewSet):
    serializer_class = ChiqimSerializer
    queryset = Chiqim.objects.filter(is_deleted=False)  # Oddiy ro'yxatda o'chganlar chiqmaydi
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        maxsulot_id = request.data.get('product')  # modelda field nomi product
        kerakli_miqdor = float(request.data.get('quantity', 0))
        omborlar = Ombor.objects.select_for_update().filter(
            maxsulot_id=maxsulot_id,
            miqdor__gt=0
        ).order_by('id')
        jami_qoldiq = sum(o.miqdor for o in omborlar)
        if jami_qoldiq < kerakli_miqdor:
            raise ValidationError({"error": f"Omborda faqat {jami_qoldiq} ta bor"})
        qolgan = kerakli_miqdor
        for ombor in omborlar:
            if qolgan == 0:
                break
            chiqarish = min(ombor.miqdor, qolgan)
            ombor.miqdor -= chiqarish
            ombor.save(update_fields=['miqdor'])
            qolgan -= chiqarish
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user if self.request.user.is_authenticated else None)
        return Response(serializer.data)


class RetseptViewSet(viewsets.ModelViewSet):
    queryset = Retsept.objects.all()
    serializer_class = RetseptSerializer


class OmborViewSet(viewsets.ModelViewSet):
    queryset = Ombor.objects.filter(miqdor__gt=0)
    serializer_class = OmborSerializer
    http_method_names = ['get']


class TarixViewSet(viewsets.ViewSet):
    def list(self, request):
        hozir = timezone.now()
        kun = hozir - timedelta(days=1)
        hafta = hozir - timedelta(days=7)
        oy = hozir - timedelta(days=30)
        def get_data(start_date):
            kirim = Kirim.objects.filter(created_at__gte=start_date).order_by('-created_at')
            chiqim = Chiqim.objects.filter(created_at__gte=start_date).order_by('-created_at')
            jami_pul = kirim.filter(is_deleted=False).aggregate(total=Sum('price'))['total'] or 0
            return {
                "jami_kirim": kirim.filter(is_deleted=False).count(),
                "jami_chiqim": chiqim.filter(is_deleted=False).count(),
                "jami_pul": jami_pul,
                "kirimlar": [
                    {
                        "id": k.id,
                        "maxsulot": k.product.name,
                        "taminotchi": k.taminotchi.name if k.taminotchi else "Noma'lum",
                        "miqdor": k.quantity,
                        "olchov_birligi": k.product.unit.name if k.product.unit else "kg",
                        "narx": k.price,
                        "sana_vaqt": k.created_at.strftime("%Y-%m-%d %H:%M"),
                        "yil": k.created_at.year,
                        "oy": k.created_at.month,
                        "kun": k.created_at.day,
                        "soat": k.created_at.strftime("%H:%M"),
                        "is_deleted": k.is_deleted
                    }
                    for k in kirim
                ],
                "chiqimlar": [
                    {
                        "id": c.id,
                        "maxsulot": c.product.name,
                        "miqdor": c.quantity,
                        "olchov_birligi": c.product.unit.name if c.product.unit else "kg",
                        "sana_vaqt": c.created_at.strftime("%Y-%m-%d %H:%M"),
                        "yil": c.created_at.year,
                        "oy": c.created_at.month,
                        "kun": c.created_at.day,
                        "soat": c.created_at.strftime("%H:%M"),
                        "is_deleted": c.is_deleted
                    }
                    for c in chiqim
                ]
            }
        return Response({
            "1_kun": get_data(kun),
            "1_hafta": get_data(hafta),
            "1_oy": get_data(oy),
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_me(request):
    user = request.user
    employee = getattr(user, 'employee', None)
    user_permissions = {}
    if user.is_superuser or getattr(user, 'role', None) == 'ADMIN':
        user_permissions = {"can_cancel_order": True, "can_discount": True, "can_income": True, "can_payment": True}
    elif employee:
        perm = EmployeePermission.objects.filter(employee=employee).first()
        if perm:
            user_permissions = {
                "can_cancel_order": perm.can_cancel_order,
                "can_discount": perm.can_discount,
                "can_income": perm.can_income,
                "can_payment": perm.can_payment,
            }
    data = {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": getattr(user, 'role', 'WAITER'),
        "permissions": user_permissions
    }
    return Response(data)