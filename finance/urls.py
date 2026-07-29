from django.urls import path
from .views import FinanceAccountListCreateView, FinanceCategoryListCreateView

urlpatterns = [
    path('accounts/', FinanceAccountListCreateView.as_view(), name='finance-accounts'),
    path('categories/', FinanceCategoryListCreateView.as_view(), name='finance-categories'),
]