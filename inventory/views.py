from rest_framework.viewsets import ModelViewSet
from .models import Ingredient, Recipe, Dish, StockMovement,Unit,StockIn, StockOut
from .serializer import IngredientSerializer, RecipeSerializer, DishSerializer,UnitSerializer,StockOutSerializer, StockInSerializer
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.decorators import action
from decimal import Decimal
from rest_framework.exceptions import ValidationError


class IngredientViewSet(ModelViewSet):
    queryset = Ingredient.objects.filter(is_active=True)
    serializer_class = IngredientSerializer


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer


class DishViewSet(viewsets.ModelViewSet):
    queryset = Dish.objects.all()
    serializer_class = DishSerializer

    #  OVQAT ISHLATISH (OMBORDAN KAMAYTIRISH)
    @action(detail=True, methods=['post'])
    def cook(self, request, pk=None):
        count = int(request.data.get("count", 1))  # nechta ovqat

        dish = self.get_object()

        # tekshirish
        for recipe in dish.recipes.all():
            kerak = recipe.amount * count
            if recipe.ingredient.quantity < kerak:
                raise ValidationError(f"{recipe.ingredient.name} yetarli emas!")

        # kamaytirish
        for recipe in dish.recipes.all():
            ingredient = recipe.ingredient
            ingredient.quantity -= recipe.amount * count
            ingredient.save()

        return Response({"message": "Ombordan ayrildi ✅"})

class UnitViewSet(viewsets.ModelViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer


class StockInViewSet(viewsets.ModelViewSet):
    queryset = StockIn.objects.all().order_by("-id")
    serializer_class = StockInSerializer


class StockOutViewSet(viewsets.ModelViewSet):
    queryset = StockOut.objects.all().order_by("-id")
    serializer_class = StockOutSerializer



class HistoryViewSet(viewsets.ModelViewSet):

    def list(self, request):

        kirimlar = StockIn.objects.all().values(
            'id',
            'product__name',
            'quantity',
            'created_at'
        )

        chiqimlar = StockOut.objects.all().values(
            'id',
            'product__name',
            'quantity',
            'created_at'
        )

        data = []

        # 📥 kirim qo‘shish
        for i in kirimlar:
            data.append({
                "type": "kirim",
                "product": i['product__name'],
                "quantity": i['quantity'],
                "created_at": i['created_at']
            })

        # 📤 chiqim qo‘shish
        for i in chiqimlar:
            data.append({
                "type": "chiqim",
                "product": i['product__name'],
                "quantity": i['quantity'],
                "created_at": i['created_at']
            })

        # 📅 vaqt bo‘yicha tartiblash (eng yangisi yuqorida)
        data = sorted(data, key=lambda x: x['created_at'], reverse=True)

        return Response(data)