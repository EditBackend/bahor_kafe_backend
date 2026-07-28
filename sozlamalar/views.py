from django.shortcuts import render
from rest_framework.viewsets import ViewSet
from rest_framework import viewsets, status,mixins
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from .models import Branch,CheckSettings,TaxSettings, OrderFlowSettings,RestaurantSettings
from .serializer import BranchSerializer,CheckSettingsSerializer,TaxSettingsSerializer,OrderFlowSettingsSerializer,RestaurantSettingsSerializer
from rest_framework.response import Response
from rest_framework.views import APIView


class CheckSettingsAPIView(APIView):
    def get(self, request, *args, **kwargs):
        obj, created = CheckSettings.objects.get_or_create(id=1)
        serializer = CheckSettingsSerializer(obj)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        obj, created = CheckSettings.objects.get_or_create(id=1)
        serializer = CheckSettingsSerializer(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


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


class RestaurantSettingsViewSet(ViewSet):
    def get_object(self):
        """
        Bazadagi birinchi sozlamani oladi.
        Agar baza bo'sh bo'lsa, xatosiz bitta default obyekt ochib beradi.
        """
        obj = RestaurantSettings.objects.first()
        if not obj:
            obj = RestaurantSettings.objects.create(
                name="Bahor Cafe",
                address="Default Address",
                phone="+998"
            )
        return obj

    # GET /sozlamalar/restaurant-settings/
    def list(self, request):
        """Restoran sozlamalarini ko'rish"""
        obj = self.get_object()
        serializer = RestaurantSettingsSerializer(obj)
        return Response(serializer.data)

    # GET /sozlamalar/restaurant-settings/1/
    def retrieve(self, request, pk=None):
        """ID orqali ham so'rov kelsa xuddi shu sozlamani qaytaraveradi"""
        obj = self.get_object()
        serializer = RestaurantSettingsSerializer(obj)
        return Response(serializer.data)

    # POST /sozlamalar/restaurant-settings/
    def create(self, request):
        """Yangi yaratish so'rovi kelsa, eskisini yangilaydi yoki yaratadi (duplicate xatosini oldini oladi)"""
        obj = RestaurantSettings.objects.first()
        if obj:
            serializer = RestaurantSettingsSerializer(obj, data=request.data)
        else:
            serializer = RestaurantSettingsSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    def update(self, request, pk=None):
        """To'liq tahrirlash"""
        obj = self.get_object()
        serializer = RestaurantSettingsSerializer(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # PATCH /sozlamalar/restaurant-settings/1/
    def partial_update(self, request, pk=None):
        """Qisman tahrirlash"""
        obj = self.get_object()
        serializer = RestaurantSettingsSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)