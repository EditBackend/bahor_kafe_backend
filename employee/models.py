from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser, BaseUserManager






class SalaryScheme(models.Model):
    SCHEME_TYPE_CHOICES = (
        ('fixed', 'Fiksalangan'),
        ('hourly', 'Soatbay'),
        ('percent', 'Foizli'),
        ('mixed', 'Aralash'),
    )

    employee = models.ForeignKey('employee.User', on_delete=models.CASCADE, related_name='salary_schemes', null=True, blank=True)
    title = models.CharField(max_length=255, verbose_name="Sxema nomi")
    scheme_type = models.CharField(max_length=20, choices=SCHEME_TYPE_CHOICES, default='fixed')
    fixed_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    hourly_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    sales_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.get_scheme_type_display()})"








class AppModules(models.TextChoices):
    DASHBOARD = "dashboard", "Dashboard (Asosiy sahifa)"
    POS_SYSTEM = "pos_system", "Savdo paneli (POS Tizimi)"
    ORDERS = "orders", "Buyurtmalar ro'yxati"
    PRODUCTS = "products", "Taomlar va Menyu"
    INVENTORY = "inventory", "Ombor va Inventar (Xomashyo)"
    EMPLOYEES = "employees", "Xodimlar boshqaruvi"
    SETTINGS = "settings", "Tizim Sozlamalari (Filiallar)"



class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=120, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self):
        return self.label or self.name


class RoleModulePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="module_permissions")
    module = models.CharField(max_length=100, choices=AppModules.choices)
    can_view = models.BooleanField(default=False)
    can_create = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    class Meta:
        unique_together = ('role', 'module')

    def __str__(self):
        return f"{self.role} - {self.module}"


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Telefon raqami kiritilishi shart")
        user = self.model(phone=phone, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user
    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser uchun is_staff=True bo‘lishi kerak")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser uchun is_superuser=True bo‘lishi kerak")
        return self.create_user(phone, password, **extra_fields)

class User(AbstractUser):
    username = None
    phone_validator = RegexValidator(regex=r'^\+998\d{9}$',message="Telefon raqami +998 bilan boshlanishi kerak.")
    phone = models.CharField(max_length=13,unique=True,validators=[phone_validator])
    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []
    objects = UserManager()
    def __str__(self):
        return self.phone

class Employee(models.Model):
    pin_validator = RegexValidator(regex=r'^\d{4}$',message="PIN kod 4 xonali bo‘lishi kerak.")
    user = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="employee")
    first_name = models.CharField(max_length=150, blank=True, default="")
    last_name = models.CharField(max_length=150, blank=True, default="")
    name = models.CharField(max_length=255, blank=True, default="")
    role_name = models.CharField(max_length=20, blank=True, default="")
    role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL, related_name="employees")
    quick_pin = models.CharField(max_length=4, blank=True, default="", validators=[pin_validator])
    pin_is_set = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_full_name(self):
        if self.name:
            return self.name
        full_name = " ".join(filter(None, [self.first_name.strip(), self.last_name.strip()])).strip()
        if full_name:
            return full_name
        if self.user:
            first = getattr(self.user, "first_name", "") or ""
            last = getattr(self.user, "last_name", "") or ""
            return " ".join(filter(None, [first.strip(), last.strip()])).strip() or self.user.phone
        return ""

    def __str__(self):
        full_name = self.get_full_name()
        if self.role and self.role.label:
            return f"{full_name} ({self.role.label})"
        if self.role_name:
            return f"{full_name} ({self.role_name})"
        return full_name


class EmployeePermission(models.Model):
    employee = models.OneToOneField(Employee,on_delete=models.CASCADE,related_name="permissions")
    can_payment = models.BooleanField(default=False)
    can_discount = models.BooleanField(default=False)
    can_cancel_order = models.BooleanField(default=False)
    can_income = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.employee.get_full_name()} permissions"


class SalaryRecord(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Qoralama"
        REVIEW = "review", "Tekshirilmoqda"
        APPROVED = "approved", "Tasdiqlangan"
        PAID = "paid", "To‘langan"

    class SalaryType(models.TextChoices):
        MONTHLY = "monthly", "Oylik"
        HOURLY = "hourly", "Soatlik"
        BONUS = "bonus", "Bonus"
        COMMISSION = "commission", "Komissiya"

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="salaries")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    salary_type = models.CharField(max_length=20, choices=SalaryType.choices, default=SalaryType.MONTHLY)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    period = models.CharField(max_length=50, blank=True, default="")
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee.get_full_name()} {self.period} / {self.get_status_display()}"
