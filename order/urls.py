from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, OrderItemViewSet
from .views import CashTransactionViewSet, FinanceMonitoringAPIView

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='orders')
router.register(r'order-items', OrderItemViewSet, basename='order-items')
router.register(r'transactions', CashTransactionViewSet, basename='transactions')

urlpatterns = [
	path('', include(router.urls)),
	path('finance-monitoring/', FinanceMonitoringAPIView.as_view(), name='finance-monitoring'),
]

