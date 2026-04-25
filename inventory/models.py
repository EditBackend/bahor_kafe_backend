from django.db import models
from django.conf import settings


class Ombor(models.Model):
    maxsulot = models.ForeignKey(
        'Maxsulot',
        on_delete=models.CASCADE,
        related_name='omborlar',
        verbose_name="Maxsulot"
    )
    miqdor = models.FloatField("Miqdori")
    oxirgi_narx = models.DecimalField("Oxirgi narxi", max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.maxsulot.name} - {self.miqdor}"


class OlchovBirligi(models.Model):
    name = models.CharField("Nomi", max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "O'lchov birligi"
        verbose_name_plural = "O'lchov birliklari"


class Maxsulot(models.Model):
    name = models.CharField("Nomi", max_length=200)
    unit = models.ForeignKey(
        OlchovBirligi,
        on_delete=models.CASCADE,
        related_name='maxsulotlar',
        verbose_name="O'lchov birligi"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Maxsulot"
        verbose_name_plural = "Maxsulotlar"


class OvqatKategoriya(models.Model):
    name = models.CharField("Nomi", max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Ovqat kategoriyasi"
        verbose_name_plural = "Ovqat kategoriyalari"


class Ovqat(models.Model):
    name = models.CharField("Nomi", max_length=200)
    category = models.ForeignKey(
        OvqatKategoriya,
        on_delete=models.CASCADE,
        related_name='ovqatlar',
        verbose_name="Kategoriya"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Ovqat"
        verbose_name_plural = "Ovqatlar"


class Kirim(models.Model):
    product = models.ForeignKey(
        Maxsulot,
        on_delete=models.CASCADE,
        related_name='kirimlar',
        verbose_name="Maxsulot"
    )
    quantity = models.FloatField("Soni")
    price = models.DecimalField(
        "Narxi",
        max_digits=12,
        decimal_places=2
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Kim tomonidan"
    )
    created_at = models.DateTimeField("Yaratilgan vaqt", auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"

    class Meta:
        verbose_name = "Kirim"
        verbose_name_plural = "Kirimlar"


class Chiqim(models.Model):
    product = models.ForeignKey(
        Maxsulot,
        on_delete=models.CASCADE,
        related_name='chiqimlar',
        verbose_name="Maxsulot"
    )
    quantity = models.FloatField("Soni")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Kim tomonidan"
    )
    created_at = models.DateTimeField("Yaratilgan vaqt", auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"

    class Meta:
        verbose_name = "Chiqim"
        verbose_name_plural = "Chiqimlar"

class Retsept(models.Model):
    product = models.ForeignKey(
        Maxsulot,
        on_delete=models.CASCADE,
        related_name='retseptlar',
        verbose_name="Maxsulot"
    )
    food = models.ForeignKey(
        Ovqat,
        on_delete=models.CASCADE,
        related_name='retseptlar',
        verbose_name="Ovqat"
    )
    amount = models.FloatField("Miqdori")

    def __str__(self):
        return f"{self.food.name} - {self.product.name}"

    class Meta:
        verbose_name = "Retsept"
        verbose_name_plural = "Retseptlar"