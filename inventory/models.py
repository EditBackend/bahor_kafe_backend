from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import ValidationError

from employee.models import Employee
from table.models import Product
from rest_framework import status
from rest_framework.response import Response
from django.db.models import Sum

User = get_user_model()


class Unit(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name

class Ingredient(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='ingredients')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

class StockMovement(models.Model):
    TYPE = (
        ('IN', 'Kirim'),
        ('OUT', 'Chiqim'),
        ('SALE', 'Sotuv'),
    )

    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT)
    type = models.CharField(max_length=10, choices=TYPE)

    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255, null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)



class Recipe(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="recipes")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name="recipe_items")
    quantity = models.FloatField()  # nechta ingredient ketadi

    def __str__(self):
        return f"{self.product.name} -> {self.ingredient.name} ({self.quantity})"


class Dish(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name



class StockIn(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_ins")
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name="stock_emp")

    def save(self, *args, **kwargs):
        if not self.pk:  # faqat create paytida
            with transaction.atomic():
                product = Product.objects.select_for_update().get(id=self.product.id)

                product.quantity += self.quantity
                product.last_price = self.price
                product.save()

        super().save(*args, **kwargs)


class StockOut(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_outs")
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def create(self, request, *args, **kwargs):
        product_id = request.data.get("product")
        quantity = float(request.data.get("quantity"))

        kirim = StockIn.objects.filter(product_id=product_id).aggregate(total=Sum('quantity'))['total'] or 0
        chiqim = StockOut.objects.filter(product_id=product_id).aggregate(total=Sum('quantity'))['total'] or 0

        qoldiq = kirim - chiqim

        if quantity > qoldiq:
            return Response({
                "error": "Omborda yetarli mahsulot yo‘q!"
            }, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)