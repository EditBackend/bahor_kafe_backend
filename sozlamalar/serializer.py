from rest_framework import serializers
from .models import Branch, CheckSettings, TaxSettings, OrderFlowSettings, RestaurantSettings


class BranchSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = [
            'id',
            'name',
            'city',
            'cash_desk_count',
            'kitchen_count',
            'is_active',
            'status'
        ]

    def get_status(self, obj):
        return "Faol" if obj.is_active else "Nofaol"


class CheckSettingsSerializer(serializers.Serializer):
    cafe_name = serializers.CharField(required=False, allow_blank=True, default="Bahor Cafe")
    phone = serializers.CharField(required=False, allow_blank=True, default="")
    address = serializers.CharField(required=False, allow_blank=True, default="")
    footer_text = serializers.CharField(required=False, allow_blank=True, default="Telegram kanalimizga obuna bo'ling!")
    show_cafe_name = serializers.BooleanField(required=False, default=True)
    show_sana = serializers.BooleanField(required=False, default=True)
    show_ish_vaqti = serializers.BooleanField(required=False, default=True)
    show_sotuvchi = serializers.BooleanField(required=False, default=True)
    show_kassir = serializers.BooleanField(required=False, default=True)
    show_mijoz = serializers.BooleanField(required=False, default=True)
    show_kontaktlar = serializers.BooleanField(required=False, default=True)
    show_inn = serializers.BooleanField(required=False, default=True)
    show_yuridik_shaxs = serializers.BooleanField(required=False, default=True)
    show_manzil = serializers.BooleanField(required=False, default=False)
    show_mijoz_raqami = serializers.BooleanField(required=False, default=True)
    show_eslatma = serializers.BooleanField(required=False, default=True)

    def to_representation(self, instance):
        payload = getattr(instance, '_check_settings_payload', None)
        if isinstance(payload, dict):
            return payload
        return {
            'cafe_name': getattr(instance, 'header_text', 'Bahor Cafe') or 'Bahor Cafe',
            'phone': '',
            'address': '',
            'footer_text': getattr(instance, 'footer_text', 'Telegram kanalimizga obuna bo\'ling!') or 'Telegram kanalimizga obuna bo\'ling!',
            'show_cafe_name': True,
            'show_sana': True,
            'show_ish_vaqti': True,
            'show_sotuvchi': True,
            'show_kassir': True,
            'show_mijoz': True,
            'show_kontaktlar': True,
            'show_inn': True,
            'show_yuridik_shaxs': True,
            'show_manzil': False,
            'show_mijoz_raqami': True,
            'show_eslatma': True,
        }

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        instance._check_settings_payload = validated_data
        instance.header_text = validated_data.get('cafe_name') or instance.header_text
        instance.footer_text = validated_data.get('footer_text') or instance.footer_text
        instance.save(update_fields=['header_text', 'footer_text'])
        return validated_data


class TaxSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxSettings
        fields = '__all__'


class OrderFlowSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderFlowSettings
        fields = "__all__"


class RestaurantSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantSettings
        fields = '__all__'