from django.utils import timezone
from rest_framework import serializers
from decimal import Decimal
from .models import KitchenTicket, Department, SemiProductIngredient, SemiProduct, SemiProductRecipe
from order.models import Order
from .models import MenuProduct, MenuProductRecipe,Food,FoodRecipe,Category,SemiProduct


from .models import Recipe

class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class FoodRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodRecipe
        fields = ['id', 'ingredient_name', 'brutto', 'netto', 'cost']


class FoodSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(),write_only=True)
    tannarx = serializers.SerializerMethodField()
    foyda = serializers.SerializerMethodField()
    ustama = serializers.SerializerMethodField()
    bolinma = serializers.SerializerMethodField()
    class Meta:
        model = Food
        fields = [
            'id', 'name', 'category', 'department', 'mxik', 'unit',
            'image', 'is_active', 'selling_price', 'markup_percentage',
            'cost_price', 'is_weight_recipe', 'tannarx', 'foyda', 'ustama', 'bolinma'
        ]
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['category'] = CategorySerializer(instance.category).data if instance.category else None
        return ret
    def get_tannarx(self, obj):
        if hasattr(obj, 'cost_price') and obj.cost_price:
            return float(obj.cost_price)
        return 0.0
    def get_foyda(self, obj):
        selling_price = getattr(obj, 'selling_price', 0) or 0
        cost_price = getattr(obj, 'cost_price', 0) or 0
        foyda_summa = Decimal(str(selling_price)) - Decimal(str(cost_price))
        return float(foyda_summa) if foyda_summa > 0 else 0.0
    def get_ustama(self, obj):
        if hasattr(obj, 'markup_percentage') and obj.markup_percentage:
            return float(obj.markup_percentage)
        selling_price = getattr(obj, 'selling_price', 0) or 0
        cost_price = getattr(obj, 'cost_price', 0) or 0
        if cost_price and cost_price > 0:
            ustama_foiz = ((Decimal(str(selling_price)) - Decimal(str(cost_price))) / Decimal(str(cost_price))) * 100
            return round(float(ustama_foiz), 1)
        return 0.0
    def get_bolinma(self, obj):
        if hasattr(obj, 'department') and obj.department:
            if isinstance(obj.department, str):
                return obj.department
            return getattr(obj.department, 'name', str(obj.department))
        return "--"

class MenuProductRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuProductRecipe
        fields = ['id', 'ingredient_name', 'price_per_unit', 'brutto', 'netto', 'cost']
        read_only_fields = ['cost']


class MenuProductSerializer(serializers.ModelSerializer):
    recipe_ingredients = MenuProductRecipeSerializer(many=True, required=False)
    section_name = serializers.CharField(source='section.name', read_only=True)
    class Meta:
        model = MenuProduct
        fields = [
            'id', 'name', 'category', 'price', 'section', 'section_name',
            'description', 'image', 'is_active', 'total_cost', 'recipe_ingredients'
        ]
        read_only_fields = ['total_cost']
    def create(self, validated_data):
        recipe_data = validated_data.pop('recipe_ingredients', [])
        menu_product = MenuProduct.objects.create(**validated_data)
        total_cost = 0
        for ing_data in recipe_data:
            ing = MenuProductRecipe.objects.create(menu_product=menu_product, **ing_data)
            total_cost += ing.cost
        menu_product.total_cost = total_cost
        menu_product.save()
        return menu_product


class SemiProductRecipeSerializer(serializers.ModelSerializer):
    ingredient_id = serializers.IntegerField(source='ingredient.id')
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    class Meta:
        model = SemiProductRecipe
        fields = ['id', 'ingredient_id', 'ingredient_name', 'amount', 'brutto', 'netto']


class SemiProductSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    ingredients = serializers.ListField(write_only=True, required=False)
    class Meta:
        model = SemiProduct
        fields = ['id', 'name', 'category', 'unit', 'cost', 'recipes', 'ingredients']
        read_only_fields = ['cost']
    def get_recipes(self, obj):
        try:
            if hasattr(obj, 'recipes'):
                recipes = obj.recipes.all()
            else:
                recipes = SemiProductRecipe.objects.filter(semi_product=obj)
            return SemiProductRecipeSerializer(recipes, many=True).data
        except Exception:
            return []
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients', [])
        semi_product = SemiProduct.objects.create(**validated_data)
        InventoryProductModel = apps.get_model('inventory', 'InventoryProduct')
        total_cost = 0
        for ing_data in ingredients_data:
            try:
                prod_id = ing_data.get('ingredient_id') or ing_data.get('id') or ing_data.get('product_id')
                if not prod_id:
                    continue
                product = InventoryProductModel.objects.get(id=prod_id)
                amount_val = ing_data.get('amount') or ing_data.get('quantity', 0)
                brutto_val = ing_data.get('brutto', amount_val)
                netto_val = ing_data.get('netto', amount_val)
                SemiProductRecipe.objects.create(semi_product=semi_product,ingredient=product,amount=amount_val,brutto=brutto_val,netto=netto_val)
                total_cost += float(product.purchase_price) * float(brutto_val)
            except (InventoryProductModel.DoesNotExist, KeyError, TypeError):
                continue
        semi_product.total_cost = total_cost
        semi_product.save()
        return semi_product

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'branch', 'warehouse', 'printer_name', 'is_print_begunok']

class KitchenTicketSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source="order.number", read_only=True)
    order_status = serializers.CharField(source="order.status", read_only=True)
    sent_by_name = serializers.CharField(source="sent_by.name", read_only=True)
    class Meta:
        model = KitchenTicket
        fields = [
            "id",
            "order",
            "order_number",
            "order_status",
            "status",
            "sent_by",
            "sent_by_name",
            "started_at",
            "ready_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "started_at",
            "ready_at",
            "created_at",
            "updated_at",
            "order_number",
            "order_status",
            "sent_by_name",
        ]

    def validate(self, attrs):
        order = attrs.get("order")
        if self.instance is None and order:
            if KitchenTicket.objects.filter(order=order).exists():
                raise serializers.ValidationError({
                    "order": "Bu buyurtma uchun kitchen ticket allaqachon mavjud."
                })
        return attrs


class KitchenTicketStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = KitchenTicket
        fields = ["status"]

    def validate_status(self, value):
        allowed_statuses = {
            KitchenTicket.Status.NEW,
            KitchenTicket.Status.COOKING,
            KitchenTicket.Status.READY,
            KitchenTicket.Status.CANCELLED,
        }
        if value not in allowed_statuses:
            raise serializers.ValidationError("Noto‘g‘ri status.")
        return value
    def update(self, instance, validated_data):
        new_status = validated_data.get("status")
        current_time = timezone.now()
        instance.status = new_status
        if new_status == KitchenTicket.Status.COOKING and not instance.started_at:
            instance.started_at = current_time
        if new_status == KitchenTicket.Status.READY and not instance.ready_at:
            instance.ready_at = current_time
        instance.save(update_fields=["status", "started_at", "ready_at", "updated_at"])
        order = instance.order
        if new_status == KitchenTicket.Status.COOKING:
            order.status = Order.Status.COOKING
            order.save(update_fields=["status", "updated_at"])
        elif new_status == KitchenTicket.Status.READY:
            order.status = Order.Status.READY
            order.ready_at = current_time
            order.save(update_fields=["status", "ready_at", "updated_at"])
        elif new_status == KitchenTicket.Status.CANCELLED:
            order.status = Order.Status.CANCELLED
            order.save(update_fields=["status", "updated_at"])
        elif new_status == KitchenTicket.Status.NEW:
            order.status = Order.Status.SENT_TO_KITCHEN
            order.save(update_fields=["status", "updated_at"])
        return instance