from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from .models import Employee,EmployeePermission,EmployeePermission
class EmployeePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeePermission
        fields = ['id', 'role', 'module', 'can_view', 'can_create', 'can_edit', 'can_delete']
User = get_user_model()
class EmployeeSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source="user.phone", read_only=True)
    oxirgi_kirish = serializers.DateTimeField(source='last_login', format="%Y-%m-%d %H:%M", read_only=True)
    permissions = serializers.SerializerMethodField() # 🟢 To'g'ri permissions maydoni
    class Meta:
        model = Employee
        fields = [
            "id",
            "name",
            "phone",
            "role",
            "quick_pin",
            "pin_is_set",
            "is_active",
            "created_at",
            "updated_at",
            "oxirgi_kirish",
            "permissions",
        ]
        read_only_fields = ["pin_is_set", "created_at", "updated_at", "phone"]
        extra_kwargs = {"quick_pin": {"write_only": True}}
    def get_permissions(self, obj):
        perm = EmployeePermission.objects.filter(employee=obj).first()
        if perm:
            return {
                "can_payment": getattr(perm, "can_payment", False),
                "can_discount": getattr(perm, "can_discount", False),
                "can_cancel_order": getattr(perm, "can_cancel_order", False),
                "can_income": getattr(perm, "can_income", False),
            }
        return {
            "can_payment": False,
            "can_discount": False,
            "can_cancel_order": False,
            "can_income": False
        }
    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Xodim ismi bo‘sh bo‘lishi mumkin emas.")
        return value


class MeSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source="user.phone", read_only=True)
    permissions = serializers.SerializerMethodField() # 🟢 /me/ uchun ham to'g'rilandi
    class Meta:
        model = Employee
        fields = [
            "id",
            "name",
            "phone",
            "role",
            "pin_is_set",
            "is_active",
            "permissions",
        ]
    def get_permissions(self, obj):
        perm = EmployeePermission.objects.filter(employee=obj).first()
        if perm:
            return {
                "can_payment": getattr(perm, "can_payment", False),
                "can_discount": getattr(perm, "can_discount", False),
                "can_cancel_order": getattr(perm, "can_cancel_order", False),
                "can_income": getattr(perm, "can_income", False),
            }
        return {
            "can_payment": False,
            "can_discount": False,
            "can_cancel_order": False,
            "can_income": False
        }
class EmployeeCreateSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=4)
    class Meta:
        model = Employee
        fields = [
            "id",
            "name",
            "phone",
            "password",
            "role",
            "is_active",
        ]
    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Bu telefon raqam allaqachon mavjud.")
        return value
    def create(self, validated_data):
        phone = validated_data.pop("phone")
        password = validated_data.pop("password")
        user = User.objects.create(phone=phone)
        user.set_password(password)
        user.save()
        employee = Employee.objects.create(user=user, **validated_data)
        return employee


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)
    def validate(self, attrs):
        phone = attrs.get("phone")
        password = attrs.get("password")
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError({"detail": "Telefon yoki parol noto‘g‘ri."})
        if not user.check_password(password):
            raise serializers.ValidationError({"detail": "Telefon yoki parol noto‘g‘ri."})
        if not user.is_active:
            raise serializers.ValidationError({"detail": "Foydalanuvchi faol emas."})
        try:
            employee = user.employee
        except Employee.DoesNotExist:
            raise serializers.ValidationError({"detail": "Xodim profili topilmadi."})
        if not employee.is_active:
            raise serializers.ValidationError({"detail": "Xodim faol emas."})
        attrs["user"] = user
        attrs["employee"] = employee
        return attrs

class PinSetSerializer(serializers.Serializer):
    quick_pin = serializers.CharField(max_length=4, min_length=4, write_only=True)
    confirm_pin = serializers.CharField(max_length=4, min_length=4, write_only=True)
    def validate_quick_pin(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("PIN faqat raqamlardan iborat bo‘lishi kerak.")
        return value
    def validate(self, attrs):
        quick_pin = attrs.get("quick_pin")
        confirm_pin = attrs.get("confirm_pin")
        if quick_pin != confirm_pin:
            raise serializers.ValidationError({"confirm_pin": "PIN lar mos emas."})
        return attrs


class PinLoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    quick_pin = serializers.CharField(max_length=4, min_length=4, write_only=True)
    def validate(self, attrs):
        phone = attrs.get("phone")
        quick_pin = attrs.get("quick_pin")
        if not quick_pin.isdigit():
            raise serializers.ValidationError({"quick_pin": "PIN faqat 4 ta raqam bo‘lishi kerak."})
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError({"detail": "Telefon yoki PIN noto‘g‘ri."})
        if not user.is_active:
            raise serializers.ValidationError({"detail": "Foydalanuvchi faol emas."})
        try:
            employee = user.employee
        except Employee.DoesNotExist:
            raise serializers.ValidationError({"detail": "Xodim profili topilmadi."})
        if not employee.is_active:
            raise serializers.ValidationError({"detail": "Xodim faol emas."})
        if not employee.pin_is_set:
            raise serializers.ValidationError({"detail": "Bu xodim hali PIN o‘rnatmagan."})
        if employee.quick_pin != quick_pin:
            raise serializers.ValidationError({"detail": "Telefon yoki PIN noto‘g‘ri."})
        attrs["user"] = user
        attrs["employee"] = employee
        return attrs

class EmployeePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeePermission
        fields = [
            "can_payment",
            "can_discount",
            "can_cancel_order",
            "can_income"
        ]