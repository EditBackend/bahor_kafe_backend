from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IngredientViewSet, RecipeViewSet, UnitViewSet,StockInViewSet, StockOutViewSet,HistoryViewSet

router = DefaultRouter()
router.register(r'ingredients', IngredientViewSet),
router.register(r'recipes', RecipeViewSet),
router.register(r'unit',UnitViewSet)
router.register("kirim", StockInViewSet)
router.register("chiqim", StockOutViewSet)
router.register(r'history', HistoryViewSet, basename='history')

urlpatterns = [
    path('', include(router.urls)),
]