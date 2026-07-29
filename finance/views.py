from rest_framework import generics
from .models import FinanceAccount, FinanceCategory
from .serializers import FinanceAccountSerializer, FinanceCategorySerializer

class FinanceAccountListCreateView(generics.ListCreateAPIView):
    queryset = FinanceAccount.objects.all().order_by('-created_at')
    serializer_class = FinanceAccountSerializer

class FinanceCategoryListCreateView(generics.ListCreateAPIView):
    queryset = FinanceCategory.objects.all().order_by('-created_at')
    serializer_class = FinanceCategorySerializer