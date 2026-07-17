from django.db import models

class Branch(models.Model):
    name = models.CharField(max_length=255, verbose_name="Filial nomi")
    city = models.CharField(max_length=255, verbose_name="Shahar")
    cash_desk_count = models.PositiveIntegerField(default=0)
    kitchen_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.city}"



class CheckSettings(models.Model):
    header_text = models.CharField(
        max_length=255,
        default="RESTERP CAFE",
        verbose_name="Sarlavha matni"
    )
    footer_text = models.CharField(
        max_length=255,
        default="Xaridingiz uchun rahmat!",
        verbose_name="Pastki matn"
    )
    printer_name = models.CharField(
        max_length=255,
        default="Epson TM-T20",
        verbose_name="Printer"
    )
    auto_print = models.BooleanField(
        default=True,
        verbose_name="Avto chiqarish"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return "Check sozlamalari"


class TaxSettings(models.Model):
    tax_percent = models.PositiveIntegerField(
        default=12,
        verbose_name="QQS (%)"
    )
    service_percent = models.PositiveIntegerField(
        default=10,
        verbose_name="Servis haqi (%)"
    )
    CALCULATION_TYPE = (
        ('auto', 'Avtomatik'),
        ('manual', 'Qo‘lda'),
    )
    calculation_type = models.CharField(
        max_length=10,
        choices=CALCULATION_TYPE,
        default='auto',
        verbose_name="Hisoblash turi"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return "Soliq sozlamalari"
    def save(self, *args, **kwargs):
        if not self.pk and TaxSettings.objects.exists():
            raise ValueError("Faqat bitta TaxSettings bo'lishi mumkin!")
        return super().save(*args, **kwargs)



class OrderFlowSettings(models.Model):
    auto_send_to_kitchen = models.BooleanField(
        default=True,
        verbose_name="Ofitsiant → Oshxona avtomatik"
    )
    notify_when_ready = models.BooleanField(
        default=True,
        verbose_name="Tayyor bo‘lsa signal berish"
    )
    show_payment_button = models.BooleanField(
        default=True,
        verbose_name="Hisob so‘rash tugmasi ko‘rinsin"
    )
    enable_served_stage = models.BooleanField(
        default=False,
        verbose_name="Taom berildi bosqichi"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Buyurtma oqimi sozlamalari"


class RestaurantSettings(models.Model):
    name = models.CharField(max_length=255, verbose_name="Restoran nomi")
    address = models.CharField(max_length=255, verbose_name="Manzil")
    phone = models.CharField(max_length=20, verbose_name="Telefon")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.pk:
            mavjud_sozlama = RestaurantSettings.objects.first()
            if mavjud_sozlama:
                self.pk = mavjud_sozlama.pk
        super().save(*args, **kwargs)