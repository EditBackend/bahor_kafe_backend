from django.db.models import F
from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from django.contrib.auth import get_user_model
from employee.models import EmployeePermission
from django.db import transaction
from .models import (
    OlchovBirligi,
    Maxsulot,
    OvqatKategoriya,
    Ovqat,
    Kirim,
    Chiqim,
    Retsept, Ombor,
    FinancialAccount,
    Taminotchi,
    Transaction,
    FinancialCategory,
    InventoryProduct,
    Purchase,
    PurchaseItem,
    Realization,
    RealizationItem,
    InventoryProduct,
)
User = get_user_model()
class UserMeSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'role','permissions']
    def get_permissions(self, obj):
        employee = getattr(obj, 'employee', None)
        if not employee:
            if obj.is_superuser or getattr(obj, 'role', None) == 'ADMIN':
                return {
                    "can_cancel_order": True,
                    "can_discount": True,
                    "can_income": True,
                    "can_payment": True
                }
            return {}
        perm = EmployeePermission.objects.filter(employee=employee).first()
        if perm:
            return {
                "can_cancel_order": getattr(perm, 'can_cancel_order', False),
                "can_discount": getattr(perm, 'can_discount', False),
                "can_income": getattr(perm, 'can_income', False),
                "can_payment": getattr(perm, 'can_payment', False),
            }
        return {}



class PurchaseItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    class Meta:
        model = PurchaseItem
        fields = ['id', 'product', 'product_name', 'quantity', 'purchase_price', 'margin_percent', 'selling_price','total_price']


class PurchaseSerializer(serializers.ModelSerializer):
    items = PurchaseItemSerializer(many=True)

    class Meta:
        model = Purchase
        fields = ['id', 'warehouse', 'supplier', 'date', 'document_number', 'contract_number', 'total_amount', 'items','created_at']
        read_only_fields = ['total_amount']
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        purchase = Purchase.objects.create(**validated_data)
        calculated_total = 0
        for item_data in items_data:
            item = PurchaseItem.objects.create(purchase=purchase, **item_data)
            calculated_total += float(item_data['quantity']) * float(item_data['purchase_price'])
            product = item_data['product']
            product.current_stock += float(item_data['quantity'])
            product.purchase_price = item_data['purchase_price']
            product.selling_price = item_data['selling_price']
            product.save()
        purchase.total_amount = calculated_total
        purchase.save()
        return purchase


class RealizationItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    class Meta:
        model = RealizationItem
        fields = ['id', 'product', 'product_name', 'quantity', 'purchase_price', 'selling_price', 'total_price']



class RealizationSerializer(serializers.ModelSerializer):
    items = RealizationItemSerializer(many=True)
    class Meta:
        model = Realization
        fields = ['id', 'warehouse', 'agent', 'date', 'document_number', 'notes', 'total_amount','margin_amount', 'items', 'created_at']
        read_only_fields = ['total_amount', 'margin_amount']
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        realization = Realization.objects.create(**validated_data)
        calculated_total = 0
        calculated_margin = 0
        for item_data in items_data:
            RealizationItem.objects.create(realization=realization, **item_data)
            qty = float(item_data['quantity'])
            s_price = float(item_data['selling_price'])
            p_price = float(item_data['purchase_price'])
            calculated_total += qty * s_price
            calculated_margin += qty * (s_price - p_price)
            product = item_data['product']
            product.current_stock -= qty
            product.save()
        realization.total_amount = calculated_total
        realization.margin_amount = calculated_margin
        realization.save()
        return realization


class RealizationSerializer(serializers.ModelSerializer):
    items = RealizationItemSerializer(many=True)
    class Meta:
        model = Realization
        fields = ['id', 'warehouse', 'agent', 'date', 'document_number', 'notes', 'total_amount', 'margin_amount','items', 'created_at']
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        realization = Realization.objects.create(**validated_data)
        for item_data in items_data:
            RealizationItem.objects.create(realization=realization, **item_data)
            product = item_data['product']
            product.current_stock -= float(item_data['quantity'])
            product.save()
        return realization



class InventoryProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryProduct
        fields = '__all__'


class FinancialCategorySerializer(serializers.ModelSerializer):
    tur_display = serializers.CharField(source='get_category_type_display', read_only=True)
    class Meta:
        model = FinancialCategory
        fields = ['id', 'name', 'category_type', 'tur_display']


class TransactionSerializer(serializers.ModelSerializer):
    hisob_nomi = serializers.CharField(source='account.name', read_only=True)
    tur_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    sana_vaqt = serializers.SerializerMethodField()
    summa = serializers.SerializerMethodField()
    class Meta:
        model = Transaction
        fields = [
            'id', 'account', 'hisob_nomi', 'transaction_type', 'tur_display',
            'source_type', 'category', 'amount', 'summa', 'description', 'sana_vaqt', 'date_created'
        ]
    def get_sana_vaqt(self, obj):
        return obj.date_created.strftime('%d.%m.%Y %H:%M') if obj.date_created else "—"
    def get_summa(self, obj):
        return float(obj.amount)

class FinancialAccountSerializer(serializers.ModelSerializer):
    tur_display = serializers.CharField(source='get_account_type_display', read_only=True)
    balans = serializers.SerializerMethodField()
    class Meta:
        model = FinancialAccount
        fields = ['id', 'name', 'account_type', 'tur_display', 'balans']
    def get_balans(self, obj):
        return float(obj.balance)



class TaminotchiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Taminotchi
        fields = '__all__'


class OmborSerializer(serializers.ModelSerializer):
    maxsulot_nomi = serializers.CharField(source='maxsulot.name', read_only=True)
    harakat_turi = serializers.ChoiceField(choices=['kirim', 'chiqim'], write_only=True)
    olchov_birligi = serializers.CharField(source='maxsulot.unit.name', read_only=True)


    class Meta:
        model = Ombor
        fields = [
            'id',
            'maxsulot',
            'maxsulot_nomi',
            'miqdor',
            'oxirgi_narx',
            'harakat_turi',
            'olchov_birligi'
        ]
    def create(self, validated_data):
        maxsulot = validated_data['maxsulot']
        miqdor_ozgarishi = validated_data['miqdor']
        harakat_turi = validated_data['harakat_turi']
        oxirgi_narx = validated_data.get('oxirgi_narx')
        with transaction.atomic():
            obj, created = Ombor.objects.select_for_update().get_or_create(
                maxsulot=maxsulot,
                defaults={'miqdor': 0}
            )
            if harakat_turi == 'kirim':
                obj.miqdor = F('miqdor') + miqdor_ozgarishi
                if oxirgi_narx:
                    obj.oxirgi_narx = oxirgi_narx
            elif harakat_turi == 'chiqim':
                obj.refresh_from_db()

                if obj.miqdor < miqdor_ozgarishi:
                    raise ValidationError({
                        "error": f"Omborda mahsulot yetarli emas! Hozirgi qoldiq: {obj.miqdor}"
                    })
                obj.miqdor = F('miqdor') - miqdor_ozgarishi
            obj.save()
            obj.refresh_from_db()
            return obj
    def validate_miqdor(self, value):
        if value <= 0:
            raise serializers.ValidationError("Miqdor 0 dan katta bo‘lishi shart!")
        return value


class OlchovBirligiSerializer(serializers.ModelSerializer):
    class Meta:
        model = OlchovBirligi
        fields = ['id', 'name']


class MaxsulotSerializer(serializers.ModelSerializer):
    unit_name = serializers.CharField(source='unit.name', read_only=True)
    class Meta:
        model = Maxsulot
        fields = ['id', 'name', 'unit', 'unit_name', 'qoldiq']
    def get_qoldiq(self, obj):
        kirim = Kirim.objects.filter(product=obj).aggregate(total=models.Sum('quantity'))['total'] or 0
        chiqim = Chiqim.objects.filter(product=obj).aggregate(total=models.Sum('quantity'))['total'] or 0
        return kirim - chiqim

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
    taminotchi_name = serializers.CharField(source='taminotchi.name', read_only=True)
    olchov_birligi = serializers.CharField(source='product.unit.name', read_only=True)
    class Meta:
        model = Kirim
        fields = [
            'id', 'product', 'product_name', 'taminotchi', 'taminotchi_name',
            'quantity', 'price', 'olchov_birligi', 'created_by', 'created_at', 'is_deleted'
        ]
        read_only_fields = ['created_by', 'is_deleted']


class ChiqimSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    olchov_birligi = serializers.CharField(source='product.unit.name', read_only=True)
    class Meta:
        model = Chiqim
        fields = ['id', 'product', 'product_name', 'quantity', 'olchov_birligi', 'created_by', 'created_at', 'is_deleted']
        read_only_fields = ['created_by', 'is_deleted']

class RetseptSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    food_name = serializers.CharField(source='food.name', read_only=True)
    olchov_birligi = serializers.CharField(source='product.unit.name', read_only=True)
    class Meta:
        model = Retsept
        fields = [
            'id',
            'product',
            'product_name',
            'food',
            'food_name',
            'amount',
            'olchov_birligi',
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