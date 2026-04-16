from django.contrib import admin
from inventory.models import Ingredient, Unit, StockMovement, Recipe, Dish,StockIn, StockOut

admin.site.register(Unit)
admin.site.register(Ingredient)
admin.site.register(StockMovement)
admin.site.register(Recipe)
admin.site.register(Dish)
admin.site.register(StockIn)
admin.site.register(StockOut)