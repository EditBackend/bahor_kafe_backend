from django.contrib import admin
from sozlamalar.models import Branch, CheckSettings, TaxSettings, OrderFlowSettings, RestaurantSettings

admin.site.register(Branch)
admin.site.register(CheckSettings)
admin.site.register(TaxSettings)
admin.site.register(OrderFlowSettings)
admin.site.register(RestaurantSettings)