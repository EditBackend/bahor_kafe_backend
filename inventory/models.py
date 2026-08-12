from django.db import models
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
class Purchase(models.Model):
    warehouse = models.CharField(max_length=255, verbose_name="Ombor")
    supplier = models.CharField(max_length=255, verbose_name="Ta'minotchi")
    date = models.DateTimeField(default=timezone.now, verbose_name="Sana")
    document_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Hujjat raqami")
    contract_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Shartnoma raqami")
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name="Tushum summasi")
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, blank=True, null=True,verbose_name="Tushum summasi")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Xarid #{self.id} - {self.supplier}"



class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('InventoryProduct', on_delete=models.CASCADE, verbose_name="Mahsulot")
    quantity = models.FloatField(verbose_name="Soni")
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Sotib olish narxi")
    margin_percent = models.FloatField(default=0.0, verbose_name="Ustama %")
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Sotish narxi")
    @property
    def total_price(self):
        return float(self.quantity) * float(self.purchase_price)


class Realization(models.Model):
    warehouse = models.CharField(max_length=255, verbose_name="Ombor")
    agent = models.CharField(max_length=255, blank=True, null=True, verbose_name="Agent / Kontragent")
    date = models.DateTimeField(default=timezone.now, verbose_name="Sana")
    document_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Hujjat raqami")
    notes = models.TextField(blank=True, null=True, verbose_name="Eslatmalar")
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name="Umumiy summa")
    margin_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00,verbose_name="Realizatsiya marjasi")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Realizatsiya #{self.id} - {self.warehouse}"


class RealizationItem(models.Model):
    realization = models.ForeignKey(Realization, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('InventoryProduct', on_delete=models.CASCADE, verbose_name="Mahsulot")
    quantity = models.FloatField(verbose_name="Soni")
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Sotib olish narxi")
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Sotish narxi")
    @property
    def total_price(self):
        return float(self.quantity) * float(self.selling_price)


class InventoryProduct(models.Model):
    name = models.CharField(max_length=255, verbose_name="Mahsulot nomi")
    barcode = models.CharField(max_length=100, blank=True, null=True, verbose_name="Shtrix-kod")
    mxik = models.CharField(max_length=100, blank=True, null=True, verbose_name="MXIK")
    unit = models.CharField(max_length=50, verbose_name="O'lchov birligi")
    category = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bo'lim / Kategoriya")
    product_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="Mahsulot turi")
    image = models.ImageField(upload_to='inventory_products/', blank=True, null=True, verbose_name="Mahsulot rasmi")
    is_selected = models.BooleanField(default=False, verbose_name="Tanlangan")
    is_measured = models.BooleanField(default=False, verbose_name="O'lchovli")
    is_marked = models.BooleanField(default=False, verbose_name="Markirovka")
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Sotish narxi")
    wholesale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Ulgurji narx")
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00,verbose_name="Sotib olish narxi")
    margin_percent = models.FloatField(default=0.0, verbose_name="Ustama %")
    qqs_rate = models.CharField(max_length=50, blank=True, null=True, verbose_name="QQS stavkasi")
    min_wholesale_qty = models.FloatField(default=0.0, verbose_name="Ulgurji sotuv uchun minimal miqdor")
    min_stock = models.FloatField(default=0.0, verbose_name="Minimal qoldiq")
    max_stock = models.FloatField(default=0.0, verbose_name="Maksimal qoldiq")
    manufacturer = models.CharField(max_length=255, blank=True, null=True, verbose_name="Ishlab chiqaruvchi")
    country = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ishlab chiqarilgan davlat")
    atc_code = models.CharField(max_length=100, blank=True, null=True, verbose_name="ATC")
    mhh_code = models.CharField(max_length=100, blank=True, null=True, verbose_name="MHH")
    pack_quantity = models.FloatField(default=0.0, verbose_name="Qadoqdagi miqdor")
    allow_piece_sale = models.BooleanField(default=False, verbose_name="Donalab sotishga ruxsat berish")
    by_recipe = models.BooleanField(default=False, verbose_name="Retsept bo'yicha")
    is_commission = models.BooleanField(default=False, verbose_name="Komissiya")
    description = models.TextField(blank=True, null=True, verbose_name="Tavsif")
    current_stock = models.FloatField(default=0.0, verbose_name="Ombordagi joriy zaxira")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name
  


class InventoryTransaction(models.Model):
    TRANSACTION_TYPE = (
        ('PURCHASE', 'Xarid (Kirim)'),
        ('SALE', 'Realizatsiya (Chiqim)'),
    )
    ingredient = models.ForeignKey('inventory.Ingredient', on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        ing_name = self.ingredient.name if hasattr(self.ingredient, 'name') else "Maxsulot"
        return f"{self.transaction_type} - {ing_name} ({self.quantity})"


class FinancialCategory(models.Model):
    CATEGORY_TYPES = [
        ('INCOME', 'Daromad'),
        ('EXPENSE', 'Xarajat'),
    ]
    name = models.CharField(max_length=255, verbose_name="Kategoriya nomi")
    category_type = models.CharField(max_length=50, choices=CATEGORY_TYPES, verbose_name="Kategoriya turi")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"
    class Meta:
        verbose_name = "Moliyaviy Kategoriya"
        verbose_name_plural = "Moliyaviy Kategoriyalar"
        ordering = ['-created_at']


class FinancialAccount(models.Model):
    ACCOUNT_TYPES = [
        ('CASH', 'Naqd'),
        ('BANK', 'Naqd pulsiz'),
    ]
    name = models.CharField(max_length=255, verbose_name="Hisob nomi")
    account_type = models.CharField(max_length=50, choices=ACCOUNT_TYPES, default='CASH', verbose_name="Hisob turi")
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name="Qoldiq")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Moliyaviy Hisob"
        verbose_name_plural = "Moliyaviy Hisoblar"
        ordering = ['-created_at']


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('INCOME', 'Daromad'),
        ('EXPENSE', 'Xarajat'),
    ]
    SOURCE_TYPES = [
        ('KASSA', 'Kassa'),
        ('MANUAL', 'Qo\'lda kiritilgan'),
        ('BANK', 'Bank'),
     ]
    account = models.ForeignKey(FinancialAccount, on_delete=models.CASCADE, related_name='transactions', verbose_name="Hisobga")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, verbose_name="Tranzaksiya turi")
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES, default='MANUAL', verbose_name="Manba turi")
    category = models.CharField(max_length=255, blank=True, null=True, verbose_name="Kategoriya")
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Summa")
    description = models.TextField(blank=True, null=True, verbose_name="Izoh")
    date_created = models.DateTimeField(default=timezone.now, verbose_name="Sana va vaqt")
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount}"
    def save(self, *args, **kwargs):
        if not self.pk:
            if self.transaction_type == 'INCOME':
                self.account.balance += self.amount
            elif self.transaction_type == 'EXPENSE':
                self.account.balance -= self.amount
            self.account.save()
        super().save(*args, **kwargs)
    class Meta:
        verbose_name = "Tranzaksiya"
        verbose_name_plural = "Tranzaksiyalar"
        ordering = ['-date_created']


class Ingredient(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey('FinancialCategory', on_delete=models.SET_NULL, null=True, blank=True)
    barcode = models.CharField(max_length=100, null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    unit = models.CharField(max_length=50)
    min_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.name


class Taminotchi(models.Model):
    name = models.CharField("Ta'minotchi nomi", max_length=200)
    telefon = models.CharField("Telefon raqami", max_length=20, blank=True, null=True)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Ta'minotchi"
        verbose_name_plural = "Ta'minotchilar"


class OlchovBirligi(models.Model):
    name = models.CharField("Nomi", max_length=100)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "O'lchov birligi"
        verbose_name_plural = "O'lchov birliklari"


class Maxsulot(models.Model):
    name = models.CharField("Nomi", max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    unit = models.ForeignKey(OlchovBirligi, on_delete=models.CASCADE, related_name='maxsulotlar', verbose_name="O'lchov birligi")
    @property
    def qoldiq(self):
        return self.omborlar.aggregate(total=Sum('miqdor'))['total'] or 0

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Maxsulot"
        verbose_name_plural = "Maxsulotlar"


class Ombor(models.Model):
    maxsulot = models.ForeignKey(Maxsulot, on_delete=models.CASCADE, related_name='omborlar', verbose_name="Maxsulot")
    miqdor = models.FloatField("Miqdori")
    oxirgi_narx = models.DecimalField("Oxirgi narxi", max_digits=12, decimal_places=2)
    def __str__(self):
        return f"{self.maxsulot.name} - {self.miqdor}"


class OvqatKategoriya(models.Model):
    name = models.CharField("Nomi", max_length=100)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Ovqat kategoriyasi"
        verbose_name_plural = "Ovqat kategoriyalari"


class Ovqat(models.Model):
    name = models.CharField("Nomi", max_length=200)
    category = models.ForeignKey(OvqatKategoriya, on_delete=models.CASCADE, related_name='ovqatlar', verbose_name="Kategoriya")
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Ovqat"
        verbose_name_plural = "Ovqatlar"


class Kirim(models.Model):
    product = models.ForeignKey(Maxsulot, on_delete=models.CASCADE, related_name='kirimlar', verbose_name="Maxsulot")
    taminotchi = models.ForeignKey(Taminotchi, on_delete=models.SET_NULL, null=True, blank=True, related_name='kirimlar', verbose_name="Ta'minotchi")
    quantity = models.FloatField("Soni")
    price = models.DecimalField("Narxi", max_digits=12, decimal_places=2)
    unit = models.ForeignKey(OlchovBirligi, on_delete=models.SET_NULL, null=True, blank=True, related_name='kirimlar', verbose_name="O'lchov birligi")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Kim tomonidan")
    created_at = models.DateTimeField("Yaratilgan vaqt", auto_now_add=True)
    is_deleted = models.BooleanField("O'chirilgan", default=False)
    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()
    def save(self, *args, **kwargs):
        if not self.unit and self.product and self.product.unit:
            self.unit = self.product.unit
        super().save(*args, **kwargs)
    def __str__(self):
        unit_name = self.unit.name if self.unit else (self.product.unit.name if self.product.unit else "")
        return f"{self.product.name} - {self.quantity} {unit_name}"
    class Meta:
        verbose_name = "Kirim"
        verbose_name_plural = "Kirimlar"


class Chiqim(models.Model):
    product = models.ForeignKey(Maxsulot, on_delete=models.CASCADE, related_name='chiqimlar', verbose_name="Maxsulot")
    quantity = models.FloatField("Soni")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Kim tomonidan")
    created_at = models.DateTimeField("Yaratilgan vaqt", auto_now_add=True)
    is_deleted = models.BooleanField("O'chirilgan", default=False)
    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()
    def __str__(self):
        return f"{self.product.name} - {self.quantity}"
    class Meta:
        verbose_name = "Chiqim"
        verbose_name_plural = "Chiqimlar"


class Retsept(models.Model):
    product = models.ForeignKey(Maxsulot, on_delete=models.CASCADE, related_name='retseptlar', verbose_name="Maxsulot")
    food = models.ForeignKey(Ovqat, on_delete=models.CASCADE, related_name='retseptlar', verbose_name="Ovqat")
    amount = models.FloatField("Miqdori")
    def __str__(self):
        return f"{self.food.name} - {self.product.name}"
    class Meta:
        verbose_name = "Retsept"
        verbose_name_plural = "Retseptlar"