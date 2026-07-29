from django.db import models
from django.utils import timezone
from inventory.models import Ingredient
class Category(models.Model):
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name

class Recipe(models.Model):
    product = models.ForeignKey('table.Product', on_delete=models.CASCADE, related_name='recipes', verbose_name="Taom/Mahsulot", null=True, blank=True)
    ingredient_name = models.CharField(max_length=255, verbose_name="Masalliq nomi")
    quantity = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="Miqdori/Sarfi")
    unit = models.CharField(max_length=50, default='kg', verbose_name="O'lchov birligi (kg, litr, dona)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ingredient_name} - {self.quantity} {self.unit}"
class Food(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    department = models.CharField(max_length=100)
    mxik = models.CharField(max_length=50, blank=True, null=True)
    unit = models.CharField(max_length=50)
    image = models.ImageField(upload_to="foods/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2)
    markup_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_weight_recipe = models.BooleanField(default=False)
    product_type = models.CharField(max_length=100,default="Taom",verbose_name="Turi")
    barcode = models.CharField(max_length=100,blank=True,null=True,verbose_name="Shtrix-kod")
    def __str__(self):
        return self.name




class FoodRecipe(models.Model):
    food = models.ForeignKey(Food, on_delete=models.CASCADE, related_name="ingredients")
    ingredient_name = models.CharField(max_length=255)
    brutto = models.FloatField()
    netto = models.FloatField()
    cost = models.DecimalField(max_digits=12, decimal_places=2)


class SemiProduct(models.Model):
    name = models.CharField(max_length=255, verbose_name="Yarim tayyor mahsulot nomi")
    category = models.ForeignKey('inventory.FinancialCategory', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kategoriya")
    unit = models.CharField(max_length=50, verbose_name="O'lchov birligi")
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Umumiy Tannarxi")
    created_at = models.DateTimeField(auto_now_add=True)
    @property
    def cost(self):
        total = 0
        for item in self.recipes.all():
            if item.ingredient and hasattr(item.ingredient, 'purchase_price'):
                total += float(item.ingredient.purchase_price) * float(item.brutto)
        return total
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Yarim tayyor mahsulot"
        verbose_name_plural = "Yarim tayyor mahsulotlar"
        ordering = ['-created_at']


class SemiProductRecipe(models.Model):
    semi_product = models.ForeignKey('SemiProduct', on_delete=models.CASCADE, related_name='recipes')
    ingredient = models.ForeignKey('inventory.InventoryProduct', on_delete=models.CASCADE, verbose_name="Masalliq (Ombor)")
    amount = models.FloatField(verbose_name="Miqdori")
    brutto = models.DecimalField(max_digits=10, decimal_places=3, default=0.000)
    netto = models.DecimalField(max_digits=10, decimal_places=3, default=0.000)

    def __str__(self):
        return f"{self.semi_product.name} - {self.ingredient.name if self.ingredient else 'No name'}"

class SemiProductIngredient(models.Model):
    semi_product = models.ForeignKey(SemiProduct, on_delete=models.CASCADE, related_name='ingredients_old', verbose_name="Qaysi mahsulotga tegishli")
    ingredient_name = models.CharField(max_length=255, verbose_name="Masalliq nomi")
    price_per_unit = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="O'lchov birligi uchun narx")
    brutto = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="Brutto (vazni)")
    netto = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="Netto (vazni)")
    cost = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Tannarxi")

    def save(self, *args, **kwargs):
        self.cost = self.brutto * self.price_per_unit
        super().save(*args, **kwargs)
        total = self.semi_product.ingredients_old.aggregate(models.Sum('cost'))['cost__sum'] or 0
        self.semi_product.total_cost = total
        self.semi_product.save()

    def __str__(self):
        return f"{self.ingredient_name} -> {self.semi_product.name}"


class Department(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nomi")
    branch = models.CharField(max_length=255, blank=True, null=True, verbose_name="Filial")
    warehouse = models.CharField(max_length=255, blank=True, null=True, verbose_name="Ombor")
    printer_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Printer")
    is_print_begunok = models.BooleanField(default=True, verbose_name="Begunokni chop etish")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Bo'linma"
        verbose_name_plural = "Bo'linmalar"
        ordering = ['-created_at']


class KitchenTicket(models.Model):
    class Status(models.TextChoices):
        NEW = "NEW", "Yangi"
        COOKING = "COOKING", "Tayyorlanmoqda"
        READY = "READY", "Tayyor"
        CANCELLED = "CANCELLED", "Bekor qilindi"
    order = models.OneToOneField("order.Order", on_delete=models.CASCADE, related_name="kitchen_ticket", help_text="Bog‘langan buyurtma.")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW, help_text="Oshxona jarayon holati.")
    sent_by = models.ForeignKey("employee.Employee", on_delete=models.SET_NULL, null=True, blank=True, related_name="sent_kitchen_tickets", help_text="Ticketni yuborgan xodim.")
    started_at = models.DateTimeField(null=True, blank=True, help_text="Oshxona tayyorlashni boshlagan vaqt.")
    ready_at = models.DateTimeField(null=True, blank=True, help_text="Taom tayyor bo‘lgan vaqt.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Ticket yaratilgan vaqt.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Oxirgi yangilanish.")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.   Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]
    def __str__(self):
        return f"Ticket #{self.id} | Order {self.order.number} | {self.status}"


class MenuProduct(models.Model):
    name = models.CharField(max_length=255, verbose_name="Taom nomi")
    category = models.CharField(max_length=255, verbose_name="Kategoriya")
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Sotuv narxi")
    section = models.ForeignKey('table.RestaurantSection', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bo'linma (Oshxona/Bar)")
    description = models.TextField(blank=True, null=True, verbose_name="Izoh")
    image = models.ImageField(upload_to="menu_products/", blank=True, null=True, verbose_name="Rasm")
    is_active = models.BooleanField(default=True, verbose_name="Status (Aktiv/Pasiv)")
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Taom Tannarxi")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Menyu taomi"
        verbose_name_plural = "Menyu taomlari"
        ordering = ['-created_at']


class MenuProductRecipe(models.Model):
    menu_product = models.ForeignKey(MenuProduct, on_delete=models.CASCADE, related_name='recipe_ingredients', verbose_name="Qaysi taomga tegishli")
    ingredient_name = models.CharField(max_length=255, verbose_name="Masalliq/Yarim tayyor mahsulot nomi")
    price_per_unit = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="O'lchov birligi narxi")
    brutto = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="Brutto")
    netto = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="Netto")
    cost = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Tannarxi")

    def save(self, *args, **kwargs):
        self.cost = self.brutto * self.price_per_unit
        super().save(*args, **kwargs)
        total = self.menu_product.recipe_ingredients.aggregate(models.Sum('cost'))['cost__sum'] or 0
        self.menu_product.total_cost = total
        self.menu_product.save()

    def __str__(self):
        return f"{self.ingredient_name} -> {self.menu_product.name}"