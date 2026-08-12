from datetime import date
import random
from decimal import Decimal
from django.db import transaction
from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.db import models
from order.utils import send_telegram_notification
from table.models import Product


class CheckSetting(models.Model):
    cafe_name = models.CharField(max_length=100, default="BAHOR CAFE")
    address = models.CharField(max_length=255, default="Toshkent sh., Mustaqillik ko'chasi")
    phone = models.CharField(max_length=20, default="+998901234567")
    footer_text = models.CharField(max_length=255, default="Telegram kanalimizga obuna bo'ling!")
    show_cafe_name = models.BooleanField(default=True)
    show_sana = models.BooleanField(default=True)
    show_ish_vaqti = models.BooleanField(default=True)
    show_sotuvchi = models.BooleanField(default=True)
    show_kassir = models.BooleanField(default=True)
    show_mijoz = models.BooleanField(default=True)
    show_kontaktlar = models.BooleanField(default=True)
    show_inn = models.BooleanField(default=True)
    show_yuridik_shaxs = models.BooleanField(default=True)
    show_manzil = models.BooleanField(default=True)
    show_mijoz_raqami = models.BooleanField(default=True)
    show_eslatma = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.cafe_name} - Chek Sozlamalari"



class OrderReceipt(models.Model):
    order_number = models.IntegerField(unique=True)
    table_number = models.IntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chek #{self.order_number}"


class ExpenseType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Expense Type"
        verbose_name_plural = "Expense Types"

    def __str__(self):
        return self.name


class CashTransaction(models.Model):
    class TransactionType(models.TextChoices):
        INCOME = "income", "Kirim (Tushum)"
        EXPENSE = "expense", "Chiqim (Harajat)"

    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    expense_type = models.ForeignKey(ExpenseType, null=True, blank=True, on_delete=models.SET_NULL, related_name="transactions")
    created_by = models.ForeignKey("employee.Employee", null=True, blank=True, on_delete=models.SET_NULL, related_name="cash_transactions")
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_transaction_type_display()} {self.amount} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"



class OrderType(models.TextChoices):
    DINE_IN = "dine_in", "Dine in (zalda)"
    TAKEAWAY = "takeaway", "Takeaway (olib ketish)"
    DELIVERY = "delivery", "Delivery (yetkazib berish)"



class Order(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SENT_TO_KITCHEN = "sent_to_kitchen", "Oshxonaga yuborildi"
        COOKING = "cooking", "Tayyorlanmoqda"
        READY = "ready", "Tayyor"
        SERVED = "served", "Berildi"
        PAYMENT_PENDING = "payment_pending", "To‘lov kutilmoqda"
        PAID = "paid", "To‘lov olindi"
        CLOSED = "closed", "Yopildi"
        CANCELLED = "cancelled", "Bekor qilindi"
    table = models.ForeignKey(
        "table.Table",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        help_text="Stol (faqat dine-in bo'lsa to'ladi).",
    )
    branch = models.ForeignKey(
        "sozlamalar.Branch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        help_text="Buyurtma tegishli bo'lgan filial.",
    )
    table_part = models.ForeignKey(
        "table.TablePart",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders_by_part",
        help_text="Stolning qismi (agar stol qismiga bo'lingan bo'lsa).",
    )
    type = models.CharField(
        max_length=20,
        choices=OrderType.choices,
        default=OrderType.DINE_IN,
        help_text="Buyurtma turi.",
    )
    number = models.CharField(
        max_length=20,
        help_text="Buyurtma raqami. Bir kun ichida takrorlanmaydi.",
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="Buyurtmaning joriy holati.",
    )
    guests_count = models.PositiveIntegerField(
        default=1,
        help_text="Mehmonlar soni.",
    )
    assigned_waiter = models.ForeignKey(
        "employee.Employee",
        on_delete=models.PROTECT,
        related_name="assigned_orders",
        null=True,
        blank=True,
        help_text="Mas'ul ofitsiant.",
    )
    note = models.TextField(
        blank=True,
        default="",
        help_text="Buyurtmaga umumiy izoh.",
    )
    service_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Servis haqi.",
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Yakuniy to'lanadigan summa.",
    )
    sent_to_kitchen_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Buyurtma oshxonaga yuborilgan vaqt.",
    )
    ready_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Buyurtma tayyor bo'lgan vaqt.",
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Buyurtma yopilgan vaqt.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Buyurtma yaratilgan vaqt.",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Buyurtma oxirgi marta yangilangan vaqt.",
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["number"],
                name="unique_order_number"
            )
        ]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.number} ({self.get_status_display()})"

    def generate_daily_number(self) -> str:
        today = date.today()
        existing_numbers = set(
            Order.objects.filter(
                created_at__date=today
            ).values_list("number", flat=True)
        )

        for _ in range(1000):
            rand_number = f"{random.randint(1, 999):03}"
            if rand_number not in existing_numbers:
                return rand_number

        raise ValueError("Bugun uchun bo'sh order raqami qolmadi.")

    def calculate_total(self) -> Decimal:
        items_total = self.items.aggregate(
            total=Coalesce(Sum("line_total"), Decimal("0.00"))
        )["total"]
        return items_total + self.service_amount

    def recalculate_total(self, save=True):
        self.total_amount = self.calculate_total()
        if save and self.pk:
            Order.objects.filter(pk=self.pk).update(
                total_amount=self.total_amount,
                updated_at=timezone.now(),
            )

    def send_to_telegram_bot(self):
        text = f"🛒 <b>YANGI SAVDO!</b>\n\n"
        text += f"📄 <b>Chek:</b> {self.number}\n\n"

        for item in self.items.all():
            item_name = item.product_name_snapshot or (item.product.name if item.product else "O'chirilgan mahsulot")
            text += f"📦 {item_name}\n"
            text += f"⚖️ {item.qty} x {item.unit_price} = {item.line_total} so'm\n\n"
        text += f"💰 <b>Jami:</b> {self.total_amount} so'm"
        send_telegram_notification(text)
    def save(self, *args, **kwargs):
        old_status = None
        if self.pk:
            old_status = Order.objects.filter(pk=self.pk).values_list("status", flat=True).first()
        if not self.number:
            self.number = self.generate_daily_number()
        current_time = timezone.now()
        if self.status == self.Status.SENT_TO_KITCHEN and not self.sent_to_kitchen_at:
            self.sent_to_kitchen_at = current_time
        if self.status == self.Status.READY and not self.ready_at:
            self.ready_at = current_time
        if self.status == self.Status.CLOSED and not self.closed_at:
            self.closed_at = current_time
        # Note: previous logic referenced non-existent attributes (`dish`, `quantity`) and
        # incorrectly modified Product quantities. That logic has been removed to avoid
        # accidental inventory corruption. Inventory adjustments are handled in
        # serializers/views that create Order/OrderItem records.
        super().save(*args, **kwargs)
        if self.status == self.Status.PAID and old_status != self.Status.PAID:
            try:
                self.send_to_telegram_bot()
            except Exception as e:
                print(f"Telegram botga chek yuborishda xatolik: {e}")


class OrderItem(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Yangi"
        COOKING = "cooking", "Tayyorlanmoqda"
        READY = "ready", "Tayyor"
        CANCELLED = "cancelled", "Bekor qilindi"
    order = models.ForeignKey(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="items",
        help_text="Qaysi buyurtmaga tegishli.",
    )
    product = models.ForeignKey(
        "table.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        help_text="Mahsulot o'chsa NULL bo'ladi.",
    )
    product_name_snapshot = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Mahsulot nomining buyurtma paytidagi nusxasi.",
    )
    kitchen_name_snapshot = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Oshxona uchun ko'rinadigan nomning nusxasi.",
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Bir dona narxi.",
    )
    qty = models.PositiveIntegerField(
        default=1,
        help_text="Mahsulot soni.",
    )
    line_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        editable=False,
        default=Decimal("0.00"),
        help_text="Umumiy summa = unit_price x qty.",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        help_text="Item holati.",
    )
    note = models.TextField(
        blank=True,
        default="",
        help_text="Aynan shu item uchun izoh.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Yaratilgan vaqt.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Oxirgi yangilangan vaqt.",
    )
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order", "status"]),
        ]
    def __str__(self):
        item_name = self.product_name_snapshot or (self.product.name if self.product else "Deleted product")
        return f"{item_name} x {self.qty}"
    def save(self, *args, **kwargs):
        if self.product:
            if not self.product_name_snapshot:
                self.product_name_snapshot = getattr(self.product, "name", "") or ""
            if not self.kitchen_name_snapshot:
                self.kitchen_name_snapshot = getattr(self.product, "kitchen_name", "") or getattr(self.product, "name", "") or ""
        self.line_total = self.unit_price * self.qty
        super().save(*args, **kwargs)
        if self.order_id:
            self.order.recalculate_total()
    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        if order:
            order.recalculate_total()