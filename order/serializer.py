from rest_framework import serializers
from decimal import Decimal
from rest_framework.exceptions import ValidationError
from django.apps import apps
from employee.models import Employee
from .models import Order, OrderItem, OrderType



class OrderItemReportSerializer(serializers.ModelSerializer):
    food_name = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['food_name', 'quantity', 'price', 'total_price']

    def get_food_name(self, obj):
        if getattr(obj, 'product_name_snapshot', None):
            return obj.product_name_snapshot
        if obj.product:
            return obj.product.name
        return "Noma'lum taom"
    def get_quantity(self, obj):
        if hasattr(obj, 'qty') and obj.qty is not None:
            return float(obj.qty)
        for attr in ['quantity', 'count', 'amount', 'soni']:
            if hasattr(obj, attr):
                return float(getattr(obj, attr) or 1)
        return 1.0
    def get_price(self, obj):
        if hasattr(obj, 'unit_price') and obj.unit_price is not None:
            return float(obj.unit_price)
        for attr in ['price', 'cost', 'amount', 'narxi']:
            if hasattr(obj, attr):
                val = getattr(obj, attr)
                if val is not None:
                    return float(val)
        return 0.0
    def get_total_price(self, obj):
        qty = self.get_quantity(obj)
        price = self.get_price(obj)
        return float(qty) * float(price)


class ReportOrderListSerializer(serializers.ModelSerializer):
    ofitsiant = serializers.SerializerMethodField(method_name='get_ofitsiant_ismi')
    stol = serializers.CharField(source='table.name', default='Stol')
    xizmat_haqqi = serializers.DecimalField(source='service_amount', max_digits=12, decimal_places=2, default=0.00)
    jami_summa = serializers.DecimalField(source='total_amount', max_digits=12, decimal_places=2)
    items = OrderItemReportSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'number', 'created_at', 'ofitsiant', 'stol', 'xizmat_haqqi', 'jami_summa', 'items']
    def get_ofitsiant_ismi(self, obj):
        waiter_attr = getattr(obj, 'assigned_waiter', None)
        if waiter_attr:
            if isinstance(waiter_attr, Employee):
                return waiter_attr.name
            if hasattr(waiter_attr, 'name'):
                return waiter_attr.name
            try:
                waiter_id = int(str(waiter_attr))
                employee = Employee.objects.filter(id=waiter_id).first()
                if employee:
                    return employee.name
            except (ValueError, TypeError):
                pass
        waiter_id_raw = getattr(obj, 'assigned_waiter_id', None)
        if waiter_id_raw:
            try:
                employee = Employee.objects.filter(id=int(waiter_id_raw)).first()
                if employee:
                    return employee.name
            except (ValueError, TypeError):
                pass

        return "Admin"



class OrderItemSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id", "order", "product", "product_name_snapshot",
            "kitchen_name_snapshot", "unit_price", "qty", "line_total",
            "status", "note", "created_at", "updated_at", "total_price"
        ]
        read_only_fields = [
            "line_total", "product_name_snapshot", "kitchen_name_snapshot", "created_at", "updated_at"
        ]

    def validate_qty(self, value):
        if value < 1:
            raise serializers.ValidationError("Miqdor kamida 1 bo‘lishi kerak.")
        return value

    def validate_unit_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Narx manfiy bo‘lishi mumkin emas.")
        return value

    def get_total_price(self, obj):
        qty = float(obj.qty or 1)
        unit_price = float(obj.unit_price or 0)
        return qty * unit_price


class OrderItemWriteSerializer(serializers.ModelSerializer):
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)

    class Meta:
        model = OrderItem
        fields = ["product", "qty", "unit_price", "note"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    write_items = OrderItemWriteSerializer(many=True, write_only=True, required=False, source='items_input')
    class Meta:
        model = Order
        fields = [
            "id", "table", "table_part", "type", "number", "status", "guests_count",
            "assigned_waiter", "note", "service_amount", "total_amount",
            "sent_to_kitchen_at", "ready_at", "closed_at", "created_at", "updated_at",
            "items", "write_items"
        ]
        read_only_fields = [
            "number", "total_amount", "service_amount", "sent_to_kitchen_at", "ready_at", "closed_at", "created_at",
            "updated_at"
        ]

    def validate_guests_count(self, value):
        if value < 1:
            raise serializers.ValidationError("Mehmonlar soni kamida 1 bo‘lishi kerak.")
        return value

    def validate(self, attrs):
        order_type = attrs.get("type", getattr(self.instance, "type", None))
        table = attrs.get("table", getattr(self.instance, "table", None))
        assigned_waiter = attrs.get("assigned_waiter", getattr(self.instance, "assigned_waiter", None))

        if order_type == OrderType.DINE_IN and not table:
            raise serializers.ValidationError({"table": "Dine-in buyurtma uchun stol tanlanishi shart."})

        if order_type in [OrderType.TAKEAWAY, OrderType.DELIVERY] and table:
            raise serializers.ValidationError({"table": "Takeaway yoki delivery buyurtmada stol bo‘lmasligi kerak."})
        if assigned_waiter and getattr(assigned_waiter, "role", None) != "WAITER":
            raise serializers.ValidationError({"assigned_waiter": "Mas'ul xodimning roli WAITER bo‘lishi kerak."})
        return attrs

    def _recalculate_totals(self, order):
        items_total = sum(float(item.qty or 1) * float(item.unit_price or 0) for item in order.items.all())
        service_amount = 0.0
        total_amount = items_total

        order.service_amount = service_amount
        order.total_amount = total_amount
        order.save(update_fields=['service_amount', 'total_amount'])

    def create(self, validated_data):
        items_data = validated_data.pop('items_input', [])
        table = validated_data.get('table')
        table_part = validated_data.get('table_part', None)

        # Try to find an existing active order for same table+part
        existing_order = None
        if table:
            qs = Order.objects.filter(table=table)
            if table_part:
                qs = qs.filter(table_part=table_part)
            else:
                qs = qs.filter(table_part__isnull=True)
            existing_order = qs.exclude(status__in=[Order.Status.PAID, Order.Status.CLOSED, Order.Status.CANCELLED]).order_by('-created_at').first()

        ProductIngredient = apps.get_model('table', 'ProductIngredient')
        Inventory = apps.get_model('inventory', 'InventoryProduct')

        needed_ingredients = {}
        for item_data in items_data:
            product = item_data.get('product')
            qty = float(item_data.get('qty', 1))
            ingredients = ProductIngredient.objects.filter(product=product)

            for ing in ingredients:
                required_amount = float(ing.amount) * qty
                # ProductIngredient.maxsulot is a FK to inventory.InventoryProduct
                if hasattr(ing, 'maxsulot') and ing.maxsulot:
                    ing_id = ing.maxsulot.id
                    ing_name = getattr(ing, 'maxsulot').name
                    if ing_id in needed_ingredients:
                        needed_ingredients[ing_id]['amount'] += required_amount
                    else:
                        needed_ingredients[ing_id] = {'amount': required_amount, 'name': ing_name}

        for ing_id, data in needed_ingredients.items():
            try:
                inv_item = Inventory.objects.get(id=ing_id)
            except Inventory.DoesNotExist:
                raise ValidationError({"error": f"Omborda {data['name']} topilmadi (ID: {ing_id})."})

            current_stock = float(getattr(inv_item, 'current_stock', 0))
            if current_stock < data['amount']:
                raise ValidationError({
                    "error": f"Omborda yetarli mahsulot yo'q: {data['name']} (kerak: {data['amount']}, bor: {current_stock})"
                })

        # Decrement inventory after all checks pass
        for ing_id, data in needed_ingredients.items():
            inv_item = Inventory.objects.get(id=ing_id)
            inv_item.current_stock = float(inv_item.current_stock) - data['amount']
            inv_item.save()
        # If there's an existing active order for this table/part, append items to it
        from django.db import transaction
        with transaction.atomic():
            if existing_order:
                order = existing_order
            else:
                order = Order.objects.create(**validated_data)

            for item_data in items_data:
                product = item_data.get('product')
                qty = float(item_data.get('qty', 1))
                unit_price = item_data.get('unit_price')
                if unit_price is None and product and hasattr(product, 'price'):
                    unit_price = product.price
                unit_price = float(unit_price or 0)
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    qty=qty,
                    unit_price=unit_price,
                    product_name_snapshot=product.name if product else "Noma'lum taom",
                    note=item_data.get('note', '')
                )

            # Recalculate totals for the (new or existing) order
            self._recalculate_totals(order)
            return order
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        self._recalculate_totals(instance)
        return instance