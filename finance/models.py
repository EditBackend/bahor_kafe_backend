from django.db import models

class FinanceAccount(models.Model):
    ACCOUNT_TYPE_CHOICES = (
        ('cash', 'Kassa'),
        ('bank', 'Bank/Karta'),
    )

    title = models.CharField(max_length=255, verbose_name="Hisob nomi")
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, default='cash')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name="Balans")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.get_account_type_display()}) - {self.balance}"

class FinanceCategory(models.Model):
    CATEGORY_TYPE_CHOICES = (
        ('income', 'Daromad'),
        ('expense', 'Xarajat'),
    )

    title = models.CharField(max_length=255, verbose_name="Kategoriya nomi")
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPE_CHOICES, default='expense')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.get_category_type_display()})"