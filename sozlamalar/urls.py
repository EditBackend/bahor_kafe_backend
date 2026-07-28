from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BranchViewSet, CheckSettingsViewSet, TaxSettingsViewSet, OrderFlowSettingsViewSet, RestaurantSettingsViewSet, CheckSettingsAPIView

router = DefaultRouter()
router.register(r'branches', BranchViewSet, basename='branches'),
router.register(r'tax-settings', TaxSettingsViewSet, basename='tax-settings'),
router.register(r'settings', OrderFlowSettingsViewSet, basename='settings'),
router.register(r'restaurant-settings', RestaurantSettingsViewSet, basename='restaurant-settings')

urlpatterns = [
    path('check-settings/', CheckSettingsAPIView.as_view(), name='check-settings'),
    path('', include(router.urls)),
]