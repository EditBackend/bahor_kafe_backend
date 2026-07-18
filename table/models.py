from django.db import models
from django.core.validators import MinValueValidator
from inventory.models import Maxsulot
from django.db.models import Prefetch
from inventory.models import Maxsulot


class RestaurantSection(models.Model):
    name = models.CharField(max_length=255, verbose_name="Bo'linma nomi")  # Masalan: OSHXONA, BAR
    filial = models.CharField(max_length=255, blank=True, null=True, verbose_name="Filial")
    ombor = models.CharField(max_length=255, blank=True, null=True, verbose_name="Ombor (sklad)") # Sklad bilan bog'lanadi
    printer = models.CharField(max_length=255, blank=True, null=True, verbose_name="Printer nomi") # Masalan: Xprinter XP-Q80A
    print_begunok = models.BooleanField(default=True, verbose_name="Begunokni chop etish")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Bo'linma"
        verbose_name_plural = "Bo'linmalar"
        ordering = ['-created_at']

class Table(models.Model):
    class Status(models.TextChoices):
        FREE = "free", "Bo‘sh"
        BUSY = "busy", "Band"
        PAYMENT = "payment", "Hisob jarayonida"

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Stol nomi yoki raqami. Masalan: 1-stol, VIP-1."
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.FREE,
        help_text="Stolning joriy holati."
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Stol faol yoki nofaol ekanini bildiradi."
    )
    x = models.FloatField(
        null=True,
        blank=True,
        help_text="Stolning xaritadagi x koordinatasi."
    )
    y = models.FloatField(
        null=True,
        blank=True,
        help_text="Stolning xaritadagi y koordinatasi."
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Stol yaratilgan vaqt."
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Stol oxirgi marta yangilangan vaqt."
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["status"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name


class TablePart(models.Model):
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name='parts'
    )
    name = models.CharField(max_length=100, help_text="Stolning qismi nomi yoki raqami")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('table', 'name')
        ordering = ['table', 'name']

    def __str__(self):
        return f"{self.table.name} - {self.name}"




class Category(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Kategoriya nomi."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Kategoriya faol yoki nofaol ekanini bildiradi."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Kategoriya yaratilgan vaqt."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Kategoriya oxirgi marta yangilangan vaqt."
    )
    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name


class Product(models.Model):
    UNIT_CHOICES = (
        ("g", "Gram"),
        ("dona", "Dona"),
        ("litr", "Litr"),
    )
    category = models.ForeignKey(
        Category,
        related_name="products",
        on_delete=models.CASCADE
    )
    name = models.CharField(
        max_length=255,
        help_text="Mahsulotning asosiy nomi."
    )
    kitchen_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Oshxonada ko‘rinadigan nom. Bo‘sh bo‘lsa name bilan bir xil bo‘ladi."
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Mahsulot narxi."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Mahsulot sotuvda faol yoki yo‘qligi."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Mahsulot yaratilgan vaqt."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Mahsulot oxirgi marta yangilangan vaqt."
    )
    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["category", "name"],
                name="unique_product_name_per_category"
            )
        ]
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["name"]),
            models.Index(fields=["is_active"]),
        ]

    def save(self, *args, **kwargs):
        if not self.kitchen_name:
            self.kitchen_name = self.name

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductIngredient(models.Model):
    category = models.ForeignKey(
        'Category',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name="ingredients",
        verbose_name="Qaysi taomga tegishli",
        null=True,
        blank=True
    )
    maxsulot = models.ForeignKey('inventory.InventoryProduct', on_delete=models.CASCADE,
                                 related_name='product_ingredients')
    amount = models.FloatField(verbose_name="Miqdori (Nechta ketishi)")
    def __str__(self):
        product_name = self.product.name if self.product else "Noma'lum taom"
        return f"{product_name} -> {self.maxsulot.name} ({self.amount})"