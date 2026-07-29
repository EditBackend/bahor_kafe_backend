

from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from order.views import OrderPrintReceiptAPIView

# from branch.views import get_token

schema_view = get_schema_view(
    openapi.Info(
        title="Bahor kafe",
        default_version='v1',
        description="Bu API hujjatlari Swagger va Redoc orqali ko'rsatiladi",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="support@example.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('employee/', include('employee.urls')),
    path('finance/', include('finance.urls')),
    path('kitchen/', include('kitchen.urls')),
    path('order/', include('order.urls')),
    path('table/', include('table.urls')),
    path('inventory/', include('inventory.urls')),
    path('sozlamalar/', include('sozlamalar.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('users/', include('users.urls')),
    # 1. Frontendchi ID bersa ham, bermasa ham shu view'ga kelaversin:
    path('receipts/print/', OrderPrintReceiptAPIView.as_view(), name='print-receipt-default'),
    path('receipts/print/<int:order_id>/', OrderPrintReceiptAPIView.as_view(), name='print-receipt-by-id'),
]
