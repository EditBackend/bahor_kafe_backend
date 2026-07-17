from django.db import models

class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} ({self.telegram_id})"

class UserAddress(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name='addresses')
    address_name = models.CharField(max_length=255) # Masalan: "Uy", "Ofis"
    lat = models.FloatField()
    lon = models.FloatField()