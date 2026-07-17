from django.urls import path
from .views import TelegramLoginAPIView, WebLoginAPIView  # 🟢 WebLoginAPIView ni ham import qilamiz

urlpatterns = [
    path('telegram-login/', TelegramLoginAPIView.as_view(), name='telegram_login'),
    path('web-login/', WebLoginAPIView.as_view(), name='web-login'),
]