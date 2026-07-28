from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TableViewSet, ProductViewSet, CategoryViewSet,ProductCreateUpdateAPIView,ProductIngredientViewSet, MenuViewSet,RestaurantSectionViewSet, TablePartViewSet, TableLayoutAPIView
from rest_framework.authtoken.views import obtain_auth_token

router = DefaultRouter()
router.register(r'table', TableViewSet, basename='table')
router.register(r'category', CategoryViewSet, basename='category')
router.register(r'product', ProductViewSet, basename='product')
router.register(r'product-ingredients', ProductIngredientViewSet,basename="product-ingredients")
router.register(r'menu', MenuViewSet,basename='menu')
router.register(r'sections', RestaurantSectionViewSet, basename='restaurant-section')
router.register(r'table-part', TablePartViewSet, basename='table-part')
urlpatterns = [
    path('table-layout/', TableLayoutAPIView.as_view(), name='table-layout'),
    path('', include(router.urls)),
    path('token/', obtain_auth_token, name='api_token_auth'),
    path("product/create/", ProductCreateUpdateAPIView.as_view()),
    path("product/<int:pk>/update/", ProductCreateUpdateAPIView.as_view())
]
