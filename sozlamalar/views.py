from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action

from .models import Branch,CheckSettings,TaxSettings, OrderFlowSettings,RestaurantSettings
from .serializer import BranchSerializer,CheckSettingsSerializer,TaxSettingsSerializer,OrderFlowSettingsSerializer,RestaurantSettingsSerializer
from rest_framework.response import Response

class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all().order_by('-id')
    serializer_class = BranchSerializer


class CheckSettingsViewSet(viewsets.ViewSet):

    def get_object(self):
        obj, created = CheckSettings.objects.get_or_create(id=1)
        return obj

    @action(detail=False, methods=['get'], url_path='check-settings')
    def check_settings(self, request):
        serializer = CheckSettingsSerializer(self.get_object())
        return Response(serializer.data)


    def list(self, request):
        serializer = CheckSettingsSerializer(self.get_object())
        return Response(serializer.data)

    def create(self, request):
        serializer = CheckSettingsSerializer(self.get_object())
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        serializer = CheckSettingsSerializer(self.get_object())
        return Response(serializer.data)

    def update(self, request, pk=None):
        obj = self.get_object()
        serializer = CheckSettingsSerializer(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def partial_update(self, request, pk=None):
        obj = self.get_object()
        serializer = CheckSettingsSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)



class TaxSettingsViewSet(viewsets.ViewSet):

    def get_object(self):
        obj, created = TaxSettings.objects.get_or_create(id=1)
        return obj

    # GET /tax-settings/
    def list(self, request):
        serializer = TaxSettingsSerializer(self.get_object())
        return Response(serializer.data)

    # GET /tax-settings/1/
    def retrieve(self, request, pk=None):
        serializer = TaxSettingsSerializer(self.get_object())
        return Response(serializer.data)

    # PUT /tax-settings/1/
    def update(self, request, pk=None):
        obj = self.get_object()
        serializer = TaxSettingsSerializer(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def get_object(self):
        obj, created = TaxSettings.objects.get_or_create(id=1)
        return obj

        # POST /tax-settings/

    def create(self, request):
        obj = self.get_object()  # id=1 doim shu
        serializer = TaxSettingsSerializer(obj, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

    # PATCH /tax-settings/1/
    def partial_update(self, request, pk=None):
        obj = self.get_object()
        serializer = TaxSettingsSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class OrderFlowSettingsViewSet(viewsets.ModelViewSet):
    queryset = OrderFlowSettings.objects.all()
    serializer_class = OrderFlowSettingsSerializer

    def get_queryset(self):
        # Har doim bitta object bo‘lishini ta’minlaymiz
        qs = super().get_queryset()
        if not qs.exists():
            OrderFlowSettings.objects.create()
        return qs


class RestaurantSettingsViewSet(viewsets.ViewSet):

    def get_object(self):
        obj, created = RestaurantSettings.objects.get_or_create(
            id=2,
            defaults={
                "name": "Bahor Cafe",
                "address": "Farg'ona",
                "phone": "+998"
            }
        )
        return obj

    # GET /restaurant-settings/
    def list(self, request):
        serializer = RestaurantSettingsSerializer(self.get_object())
        return Response(serializer.data)

    # GET /restaurant-settings/1/
    def retrieve(self, request, pk=None):
        serializer = RestaurantSettingsSerializer(self.get_object())
        return Response(serializer.data)

    # PUT
    def update(self, request, pk=None):
        obj = self.get_object()
        serializer = RestaurantSettingsSerializer(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # PATCH
    def partial_update(self, request, pk=None):
        obj = self.get_object()
        serializer = RestaurantSettingsSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)