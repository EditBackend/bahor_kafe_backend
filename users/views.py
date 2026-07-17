import hmac
import hashlib
import json
import random
from urllib.parse import parse_qsl
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from .models import TelegramUser

User = get_user_model()

def verify_telegram_data(init_data, bot_token):
    vals = dict(parse_qsl(init_data))
    hash_value = vals.pop('hash', None)
    if not hash_value:
        return False

    data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(vals.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if calculated_hash == hash_value:
        return json.loads(vals.get('user'))
    return False


class TelegramLoginAPIView(APIView):
    """ Telegram orqali tizimga kirish (O'zgarishsiz qoldi) """
    def post(self, request):
        init_data = request.data.get('initData')
        bot_token = "8605510081:AAF2QRx4ihyCPYjJL3EUps-GX6ONaOY3KME"

        tg_user_data = verify_telegram_data(init_data, bot_token)
        if not tg_user_data:
            return Response({"error": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)

        # Foydalanuvchini bazadan qidiramiz yoki yangi ochamiz
        user, created = TelegramUser.objects.get_or_create(
            telegram_id=tg_user_data['id'],
            defaults={
                'first_name': tg_user_data.get('first_name'),
                'username': tg_user_data.get('username')
            }
        )

        # Bu yerda foydalanuvchi uchun JWT token (SimpleJWT) generatsiya qilib qaytarasiz
        return Response({
            "message": "Muvaffaqiyatli login",
            "user_id": user.id,
            "token": "JWT_TOKEN_GENERATSIYA_QILING"
        })

# users/views.py ichida WebLoginAPIView klassining tegishli qismi

class WebLoginAPIView(APIView):
    permission_classes = []  # Token shartmas, login endpointi

    def post(self, request, *args, **kwargs):
        phone = request.data.get("phone")
        name = request.data.get("name", "")

        if not phone:
            return Response({"error": "Telefon raqam yuborilishi shart."}, status=status.HTTP_400_BAD_REQUEST)

        #  MUAMMO YECHIMI: username o'rniga modeldagi haqiqiy field 'phone' ishlatildi
        user, created = User.objects.get_or_create(
            phone=phone,  # phone orqali qidiramiz va yaratamiz
            defaults={"first_name": name}
        )



        # Agar user oldindan bor bo'lsa va ismi o'zgargan bo'lsa yangilab qo'yamiz
        if not created and name != "Mijoz":
            user.first_name = name
            user.save()

        #  Token yaratamiz yoki borini yuklaymiz (DRF Token Authentication)
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "token": token.key,
            "user": {
                "name": user.first_name or user.username,
                "phone": user.username
            }
        }, status=status.HTTP_200_OK)