from rest_framework import serializers
from .models import (
    OlchovBirligi,
    Maxsulot,
    OvqatKategoriya,
    Ovqat,
    Kirim,
    Chiqim,
    Retsept, Ombor,
)


class OmborSerializer(serializers.ModelSerializer):
    maxsulot_nomi = serializers.CharField(source='maxsulot.name', read_only=True)
    qoldiq = serializers.SerializerMethodField()

    class Meta:
        model = Ombor
        fields = [
            'id',
            'maxsulot',
            'maxsulot_nomi',
            'miqdor',
            'oxirgi_narx',
            'created_at',
            'qoldiq'
        ]
        read_only_fields = ['created_at']

    # 🔥 umumiy qoldiq (shu mahsulot bo‘yicha)
    def get_qoldiq(self, obj):
        return obj.maxsulot.get_qoldiq()

    # 🔥 VALIDATION (manfiy bo‘lmasin)
    def validate_miqdor(self, value):
        if value < 0:
            raise serializers.ValidationError("Miqdor manfiy bo‘lishi mumkin emas!")
        return value

class OlchovBirligiSerializer(serializers.ModelSerializer):
    class Meta:
        model = OlchovBirligi
        fields = ['id', 'name']



class MaxsulotSerializer(serializers.ModelSerializer):
    unit_name = serializers.CharField(source='unit.name', read_only=True)

    class Meta:
        model = Maxsulot
        fields = ['id', 'name', 'unit', 'unit_name']


class OvqatKategoriyaSerializer(serializers.ModelSerializer):
    class Meta:
        model = OvqatKategoriya
        fields = ['id', 'name']


class OvqatSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Ovqat
        fields = ['id', 'name', 'category', 'category_name']



class KirimSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Kirim
        fields = [
            'id',
            'product',
            'product_name',
            'quantity',
            'price',
            'created_by',
            'created_by_name',
            'created_at'
        ]
        read_only_fields = ['created_by', 'created_at']



class ChiqimSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Chiqim
        fields = [
            'id',
            'product',
            'product_name',
            'quantity',
            'created_by',
            'created_by_name',
            'created_at'
        ]
        read_only_fields = ['created_by', 'created_at']


class RetseptSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    food_name = serializers.CharField(source='food.name', read_only=True)

    class Meta:
        model = Retsept
        fields = [
            'id',
            'product',
            'product_name',
            'food',
            'food_name',
            'amount'
        ]

class OvqatDetailSerializer(serializers.ModelSerializer):
    retseptlar = RetseptSerializer(many=True, read_only=True)

    class Meta:
        model = Ovqat
        fields = [
            'id',
            'name',
            'category',
            'retseptlar'
        ]