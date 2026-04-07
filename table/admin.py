from django.contrib import admin
from table.models import Table, Category, Product, StockIn, StockOut

admin.site.register(Table)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(StockIn)
admin.site.register(StockOut)