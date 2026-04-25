from django.db import models
from django.core.validators import MinValueValidator
from inventory.models import Maxsulot
from django.db.models import Prefetch
# =========================
# TABLE
# =========================
class Table(models.Model):
    """
    Table = restorandagi stol modeli.

    Vazifasi:
    - Ofitsiant buyurtma qabul qilayotganda qaysi stolga buyurtma ochilganini bilish
    - Kassir stol bo‘yicha buyurtmani topishi
    - Stolning joriy holatini ko‘rsatish

    Hozircha branch ulanmagan.
    Keyingi bosqichda filial qo‘shilsa, shu modelga branch FK qo‘shiladi.
    """

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


# =========================
# CATEGORY
# =========================
class Category(models.Model):
    """
    Category = mahsulot kategoriyasi.

    Misol:
    - Pitsa
    - Burger
    - Ichimlik
    - Desert

    Vazifasi:
    - Mahsulotlarni guruhlarga ajratish
    - Ofitsiant ekranida kategoriyalarni chiqarish
    - Menyu boshqaruvida tartibni saqlash
    """

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


# =========================
# PRODUCT
# =========================
class Product(models.Model):
    UNIT_CHOICES = (
        ("g", "Gram"),
        ("dona", "Dona"),
        ("litr", "Litr"),
    )
    # """
    # Product = menyudagi mahsulot yoki taom.
    #
    # Misol:
    # - Margherita
    # - Cola
    # - Cheeseburger
    #
    # Vazifasi:
    # - Ofitsiant oynasida tanlanadigan taomlar ro‘yxati
    # - Oshxonaga ketadigan mahsulot nomlari
    # - Kassada hisoblanadigan narx
    # """

    category = models.ForeignKey(Category,related_name="products", on_delete=models.CASCADE)

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
        """
        Maqsad:
        - Agar kitchen_name bo‘sh bo‘lsa, avtomatik ravishda name ni kitchen_name ga yozish.

        Nega kerak:
        - Har safar kitchen_name ni qo‘lda yozish shart bo‘lmaydi
        - Oshxona uchun nom bo‘sh qolib ketmaydi
        """
        if not self.kitchen_name:
            self.kitchen_name = self.name

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name







class ProductIngredient(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="inventory_ingredients")
    maxsulot = models.ForeignKey(
        Maxsulot,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    amount = models.FloatField()  # nechta ketadi

    def __str__(self):
        return f"{self.product} - {self.ingredient}"