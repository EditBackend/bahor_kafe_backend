from django.contrib import admin
from kitchen.models import KitchenTicket,Category,Food,Department,SemiProduct,FoodRecipe,MenuProduct
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']
@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category', 'selling_price', 'product_type', 'is_active']
    list_filter = ['category', 'product_type', 'is_active']
    search_fields = ['name', 'barcode']
admin.site.register(FoodRecipe)
admin.site.register(SemiProduct)
admin.site.register(Department)
admin.site.register(KitchenTicket)
admin.site.register(MenuProduct)


