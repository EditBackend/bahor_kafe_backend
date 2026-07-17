from rest_framework import serializers
from inventory.serializer import MaxsulotSerializer
from .models import Table, Category, Product, ProductIngredient,RestaurantSection, TablePart

class RestaurantSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantSection
        fields = ['id', 'name', 'filial', 'ombor', 'printer', 'print_begunok']

class TableSerializer(serializers.ModelSerializer):
    parts = serializers.SerializerMethodField()
    class Meta:
        model = Table
        fields = [
            "id",
            "name",
            "parts",
            "status",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
        ]
    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Stol nomi bo‘sh bo‘lishi mumkin emas.")
        return value

    def get_parts(self, obj):
        parts = getattr(obj, 'parts', None)
        if parts is None:
            return []
        return TablePartSerializer(parts.all(), many=True).data


class TablePartSerializer(serializers.ModelSerializer):
    table_name = serializers.CharField(source='table.name', read_only=True)

    class Meta:
        model = TablePart
        fields = ['id', 'table', 'table_name', 'name', 'is_active', 'created_at']
        read_only_fields = ['created_at']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
        ]
    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Kategoriya nomi bo‘sh bo‘lishi mumkin emas.")
        return value


class ProductIngredientSerializer(serializers.ModelSerializer):
    maxsulot_name = serializers.CharField(source='maxsulot.name', read_only=True)
    olchov_birligi = serializers.CharField(source='maxsulot.unit.name', read_only=True)

    class Meta:
        model = ProductIngredient
        fields = ['id', 'product', 'category', 'maxsulot', 'maxsulot_name', 'amount', 'olchov_birligi']
        extra_kwargs = {
            'category': {'required': False, 'allow_null': True}
        }

    def create(self, validated_data):
        product = validated_data.get('product')
        if product and not validated_data.get('category'):
            validated_data['category'] = product.category
        return super().create(validated_data)


# TO'G'RILANDI: Klasslar orasi ajratildi, endi xato bermaydi!
class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    ingredients = ProductIngredientSerializer(
        source="inventory_ingredients",
        many=True,
        read_only=True
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "category_name",
            "name",
            "kitchen_name",
            "price",
            "is_active",
            "created_at",
            "updated_at",
            "ingredients",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "category_name",
        ]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Mahsulot nomi bo‘sh bo‘lishi mumkin emas.")
        return value

    def validate_kitchen_name(self, value):
        value = value.strip()
        return value

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Narx manfiy bo‘lishi mumkin emas.")
        return value

    def validate(self, attrs):
        name = attrs.get("name")
        kitchen_name = attrs.get("kitchen_name", "")

        if name:
            attrs["name"] = name.strip()

        if kitchen_name is not None:
            attrs["kitchen_name"] = kitchen_name.strip()

        return attrs


class ProductMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class CategoryMenuSerializer(serializers.ModelSerializer):
    products = ProductMenuSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "products"]


class ProductFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "price",
            "is_active",
            "kitchen_name",
        ]

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Nom bo‘sh bo‘lmasin")
        return value

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Narx manfiy bo‘lmaydi")
        return value
