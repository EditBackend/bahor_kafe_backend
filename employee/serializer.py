from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Employee, EmployeePermission, Role, RoleModulePermission, SalaryRecord

User = get_user_model()


class RoleModulePermissionSerializer(serializers.ModelSerializer):
    role_label = serializers.CharField(source='role.label', read_only=True)
    class Meta:
        model = RoleModulePermission
        fields = [
            'id',
            'role',
            'role_label',
            'module',
            'can_view',
            'can_create',
            'can_edit',
            'can_delete',
        ]


class RoleSerializer(serializers.ModelSerializer):
    module_permissions = RoleModulePermissionSerializer(many=True, read_only=True)

    class Meta:
        model = Role
        fields = [
            'id',
            'name',
            'label',
            'is_active',
            'created_at',
            'updated_at',
            'module_permissions',
        ]


class EmployeePermissionSerializer(serializers.ModelSerializer):
    employee = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all())

    class Meta:
        model = EmployeePermission
        fields = [
            'id',
            'employee',
            'can_payment',
            'can_discount',
            'can_cancel_order',
            'can_income',
        ]


class EmployeeSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source='user.phone', read_only=True)
    oxirgi_kirish = serializers.DateTimeField(source='last_login', format='%Y-%m-%d %H:%M', read_only=True)
    role = RoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.filter(is_active=True),
        source='role',
        write_only=True,
        required=False,
        allow_null=True,
    )
    full_name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id',
            'first_name',
            'last_name',
            'name',
            'full_name',
            'username',
            'phone',
            'role',
            'role_id',
            'role_name',
            'quick_pin',
            'pin_is_set',
            'is_active',
            'created_at',
            'updated_at',
            'oxirgi_kirish',
            'permissions',
        ]
        read_only_fields = ['pin_is_set', 'created_at', 'updated_at', 'phone', 'full_name', 'username']
        extra_kwargs = {'quick_pin': {'write_only': True}}

    def get_full_name(self, obj):
        if obj.name:
            return obj.name
        if obj.first_name or obj.last_name:
            return ' '.join(filter(None, [obj.first_name.strip(), obj.last_name.strip()])).strip()
        user = getattr(obj, 'user', None)
        if not user:
            return ''
        first = getattr(user, 'first_name', '') or ''
        last = getattr(user, 'last_name', '') or ''
        if first or last:
            return f'{first} {last}'.strip()
        if hasattr(user, 'get_username'):
            return user.get_username()
        return getattr(user, 'phone', '')

    def get_username(self, obj):
        user = getattr(obj, 'user', None)
        if not user:
            return ''
        if hasattr(user, 'get_username'):
            return user.get_username()
        return getattr(user, 'username', '') or getattr(user, 'phone', '')

    def get_permissions(self, obj):
        perm = EmployeePermission.objects.filter(employee=obj).first()
        if perm:
            return {
                'can_payment': getattr(perm, 'can_payment', False),
                'can_discount': getattr(perm, 'can_discount', False),
                'can_cancel_order': getattr(perm, 'can_cancel_order', False),
                'can_income': getattr(perm, 'can_income', False),
            }
        return {
            'can_payment': False,
            'can_discount': False,
            'can_cancel_order': False,
            'can_income': False,
        }

    def validate(self, attrs):
        first_name = attrs.get('first_name', '') or ''
        last_name = attrs.get('last_name', '') or ''
        name = attrs.get('name', '') or ''
        if not any([name.strip(), first_name.strip(), last_name.strip()]):
            raise serializers.ValidationError('Xodimning ismi yoki familiyasi kiritilishi shart.')
        return attrs


class MeSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source='user.phone', read_only=True)
    full_name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    role = RoleSerializer(read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id',
            'first_name',
            'last_name',
            'name',
            'full_name',
            'username',
            'phone',
            'role',
            'pin_is_set',
            'is_active',
            'permissions',
        ]

    def get_full_name(self, obj):
        if obj.name:
            return obj.name
        if obj.first_name or obj.last_name:
            return ' '.join(filter(None, [obj.first_name.strip(), obj.last_name.strip()])).strip()
        user = getattr(obj, 'user', None)
        if not user:
            return ''
        first = getattr(user, 'first_name', '') or ''
        last = getattr(user, 'last_name', '') or ''
        if first or last:
            return f'{first} {last}'.strip()
        if hasattr(user, 'get_username'):
            return user.get_username()
        return getattr(user, 'phone', '')

    def get_username(self, obj):
        user = getattr(obj, 'user', None)
        if not user:
            return ''
        if hasattr(user, 'get_username'):
            return user.get_username()
        return getattr(user, 'username', '') or getattr(user, 'phone', '')

    def get_permissions(self, obj):
        perm = EmployeePermission.objects.filter(employee=obj).first()
        if perm:
            return {
                'can_payment': getattr(perm, 'can_payment', False),
                'can_discount': getattr(perm, 'can_discount', False),
                'can_cancel_order': getattr(perm, 'can_cancel_order', False),
                'can_income': getattr(perm, 'can_income', False),
            }
        return {
            'can_payment': False,
            'can_discount': False,
            'can_cancel_order': False,
            'can_income': False,
        }


class EmployeeCreateSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=4)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.filter(is_active=True),
        source='role',
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Employee
        fields = [
            'id',
            'first_name',
            'last_name',
            'name',
            'phone',
            'password',
            'role_id',
            'is_active',
            'role_name',
        ]
        extra_kwargs = {
            'role_name': {'read_only': True},
        }

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError('Bu telefon raqam allaqachon mavjud.')
        return value

    def validate(self, attrs):
        first_name = attrs.get('first_name', '') or ''
        last_name = attrs.get('last_name', '') or ''
        name = attrs.get('name', '') or ''
        if not any([name.strip(), first_name.strip(), last_name.strip()]):
            raise serializers.ValidationError('Xodimning ismi yoki familiyasi kiritilishi shart.')
        return attrs

    def create(self, validated_data):
        phone = validated_data.pop('phone')
        password = validated_data.pop('password')
        user_data = {}
        if 'first_name' in validated_data:
            user_data['first_name'] = validated_data['first_name']
        if 'last_name' in validated_data:
            user_data['last_name'] = validated_data['last_name']
        user = User.objects.create(phone=phone, **user_data)
        user.set_password(password)
        user.save()
        employee = Employee.objects.create(user=user, **validated_data)
        return employee


class SalaryRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)

    class Meta:
        model = SalaryRecord
        fields = [
            'id',
            'employee',
            'employee_name',
            'amount',
            'salary_type',
            'status',
            'period',
            'note',
            'created_at',
            'updated_at',
        ]


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        phone = attrs.get('phone')
        password = attrs.get('password')
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError({'detail': 'Telefon yoki parol noto‘g‘ri.'})
        if not user.check_password(password):
            raise serializers.ValidationError({'detail': 'Telefon yoki parol noto‘g‘ri.'})
        if not user.is_active:
            raise serializers.ValidationError({'detail': 'Foydalanuvchi faol emas.'})
        try:
            employee = user.employee
        except Employee.DoesNotExist:
            raise serializers.ValidationError({'detail': 'Xodim profili topilmadi.'})
        if not employee.is_active:
            raise serializers.ValidationError({'detail': 'Xodim faol emas.'})
        attrs['user'] = user
        attrs['employee'] = employee
        return attrs


class PinSetSerializer(serializers.Serializer):
    quick_pin = serializers.CharField(max_length=4, min_length=4, write_only=True)
    confirm_pin = serializers.CharField(max_length=4, min_length=4, write_only=True)

    def validate_quick_pin(self, value):
        if not value.isdigit():
            raise serializers.ValidationError('PIN faqat raqamlardan iborat bo‘lishi kerak.')
        return value

    def validate(self, attrs):
        quick_pin = attrs.get('quick_pin')
        confirm_pin = attrs.get('confirm_pin')
        if quick_pin != confirm_pin:
            raise serializers.ValidationError({'confirm_pin': 'PIN lar mos emas.'})
        return attrs


class PinLoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    quick_pin = serializers.CharField(max_length=4, min_length=4, write_only=True)

    def validate(self, attrs):
        phone = attrs.get('phone')
        quick_pin = attrs.get('quick_pin')
        if not quick_pin.isdigit():
            raise serializers.ValidationError({'quick_pin': 'PIN faqat 4 ta raqam bo‘lishi kerak.'})
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError({'detail': 'Telefon yoki PIN noto‘g‘ri.'})
        if not user.is_active:
            raise serializers.ValidationError({'detail': 'Foydalanuvchi faol emas.'})
        try:
            employee = user.employee
        except Employee.DoesNotExist:
            raise serializers.ValidationError({'detail': 'Xodim profili topilmadi.'})
        if not employee.is_active:
            raise serializers.ValidationError({'detail': 'Xodim faol emas.'})
        if not employee.pin_is_set:
            raise serializers.ValidationError({'detail': 'Bu xodim hali PIN o‘rnatmagan.'})
        if employee.quick_pin != quick_pin:
            raise serializers.ValidationError({'detail': 'Telefon yoki PIN noto‘g‘ri.'})
        attrs['user'] = user
        attrs['employee'] = employee
        return attrs
