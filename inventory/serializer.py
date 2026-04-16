from rest_framework import serializers
from .models import Ingredient, Recipe, Dish, StockMovement,Unit,StockOut, StockIn
from employee.models import Employee



class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = "__all__"


class RecipeSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    unit = serializers.CharField(source='ingredient.unit.name', read_only=True)

    class Meta:
        model = Recipe
        fields = ['ingredient', 'ingredient_name', 'unit', 'quantity']


class DishSerializer(serializers.ModelSerializer):
    recipes = RecipeSerializer(many=True)

    class Meta:
        model = Dish
        fields = ['id', 'name', 'recipes']

    def create(self, validated_data):
        recipes_data = validated_data.pop('recipes')
        dish = Dish.objects.create(**validated_data)

        for recipe in recipes_data:
            Recipe.objects.create(dish=dish, **recipe)

        return dish



class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = ['id', 'ingredient', 'type', 'quantity', 'reason', 'created_by', 'created_at']


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ["name"]

class StockInSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockIn
        fields = "__all__"
        read_only_fields = ["created_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        if not user.is_authenticated:
            raise serializers.ValidationError("User login qilmagan")
        employee = Employee.objects.get(user=user)

        validated_data["created_by"] = employee
        return super().create(validated_data)


class StockOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockOut
        fields = "__all__"
        read_only_fields = ["created_at", "created_by"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)