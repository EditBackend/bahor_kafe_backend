from rest_framework import serializers
from .models import FinanceAccount, FinanceCategory

class FinanceAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinanceAccount
        fields = '__all__'

class FinanceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FinanceCategory
        fields = '__all__'