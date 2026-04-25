from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TableViewSet, ProductViewSet, CategoryViewSet, MenuViewSet, ProductCreateUpdateAPIView, \
     ProductIngredientViewSet
from rest_framework.authtoken.views import obtain_auth_token

router = DefaultRouter()
router.register(r'table', TableViewSet, basename='table')
router.register(r'category', CategoryViewSet, basename='category')
router.register(r'product', ProductViewSet, basename='product')
router.register(r'product-ingredients', ProductIngredientViewSet,basename="product-ingredients")
router.register(r'menu', MenuViewSet,basename='menu')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', obtain_auth_token, name='api_token_auth'),
    path("product/create/", ProductCreateUpdateAPIView.as_view()),
    path("product/<int:pk>/update/", ProductCreateUpdateAPIView.as_view())
]
