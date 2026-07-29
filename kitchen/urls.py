from django.urls import path, include
from rest_framework.routers import DefaultRouter
from kitchen.views import FoodViewSet, CategoryViewSet, RecipeSelectableItemsAPIView, SyncStatusAPIView, \
    CategoryListAPIView, RecipeListCreateView
from .views import (
    KitchenTicketViewSet,
    AbcAnalysisAPIView,
    SotuvHisobotiAPIView,
    UmumiyHisobotAPIView,
    XodimlarHisobotiAPIView,
    DashboardAPIView,
    DepartmentViewSet,
    OrderHistoryAPIView,
    SemiProductViewSet,
    MenuProductViewSet,
    FoodViewSet,
    CategoryViewSet,
)
router = DefaultRouter()
router.register(r"kitchen-tickets", KitchenTicketViewSet, basename="kitchen-tickets")
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'semi-products', SemiProductViewSet, basename='semi-product')
router.register(r'menu-products', MenuProductViewSet, basename='menu-product')
router.register(r'foods', FoodViewSet)
router.register(r'categories', CategoryViewSet)
urlpatterns = [
    path('abc-analysis/', AbcAnalysisAPIView.as_view(), name='abc-analysis'),
    path('order-history/', OrderHistoryAPIView.as_view(), name='order-history'),
    path('sotuv-hisoboti/', SotuvHisobotiAPIView.as_view(), name='sotuv-hisoboti'),
    path('umumiy-hisobot/', UmumiyHisobotAPIView.as_view(), name='umumiy-hisobot'),
    path('xodimlar-hisoboti/', XodimlarHisobotiAPIView.as_view(), name='xodimlar-hisoboti'),
    path('dashboard/', DashboardAPIView.as_view(), name='dashboard-analysis'),
    path('recipe-items/', RecipeSelectableItemsAPIView.as_view(), name='recipe-selectable-items'),
    path("", include(router.urls)),
    path('sync-status/', SyncStatusAPIView.as_view(), name='sync-status'),
    path('categories/select/', CategoryListAPIView.as_view(), name='category-select'),
    path('recipes/', RecipeListCreateView.as_view(), name='kitchen-recipes'),
]