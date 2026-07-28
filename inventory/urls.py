from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OlchovBirligiViewSet,
    MaxsulotViewSet,
    OvqatKategoriyaViewSet,
    OvqatViewSet,
    KirimViewSet,
    ChiqimViewSet,
    RetseptViewSet,
    OmborViewSet,
    TarixViewSet,
    TaminotchiViewSet,
    FinancialAccountViewSet,
    TransactionViewSet,
    FinancialCategoryViewSet,
    FinanceMonitoringAPIView,
    InventoryProductViewSet,
    PurchaseViewSet,
    RealizationViewSet,
    SuppliersAPIView,
)
router = DefaultRouter()
router.register(r'unit', OlchovBirligiViewSet)
router.register(r'maxsulot', MaxsulotViewSet)
router.register(r'kategoriya', OvqatKategoriyaViewSet)
router.register(r'ovqat', OvqatViewSet)
router.register(r'kirim', KirimViewSet)
router.register(r'chiqim', ChiqimViewSet)
router.register(r'retsept', RetseptViewSet)
router.register(r'ombor', OmborViewSet)
router.register('tarix', TarixViewSet, basename='tarix')
router.register(r'taminotchilar', TaminotchiViewSet)
router.register(r'accounts', FinancialAccountViewSet, basename='financial-account')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'categories', FinancialCategoryViewSet, basename='financial-category')
router.register(r'products', InventoryProductViewSet, basename='inventory-products')
router.register(r'purchases', PurchaseViewSet, basename='inventory-purchases')
router.register(r'realizations', RealizationViewSet, basename='inventory-realizations')
router.register(r'transaction', PurchaseViewSet, basename='inventory-transaction')
urlpatterns = [
    path('suppliers/', SuppliersAPIView.as_view(), name='inventory-suppliers'),
    path('', include(router.urls)),
    path('monitoring/', FinanceMonitoringAPIView.as_view(), name='finance-monitoring'),
]