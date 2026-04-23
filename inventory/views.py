from rest_framework import viewsets
from .models import (
    OlchovBirligi,
    Maxsulot,
    OvqatKategoriya,
    Ovqat,
    Kirim,
    Chiqim,
    Retsept,
    Ombor
)

from .serializer import (
    OlchovBirligiSerializer,
    MaxsulotSerializer,
    OvqatKategoriyaSerializer,
    OvqatSerializer,
    KirimSerializer,
    ChiqimSerializer,
    RetseptSerializer,
    OmborSerializer
)



class OlchovBirligiViewSet(viewsets.ModelViewSet):
    queryset = OlchovBirligi.objects.all()
    serializer_class = OlchovBirligiSerializer


class MaxsulotViewSet(viewsets.ModelViewSet):
    queryset = Maxsulot.objects.all()
    serializer_class = MaxsulotSerializer



class OvqatKategoriyaViewSet(viewsets.ModelViewSet):
    queryset = OvqatKategoriya.objects.all()
    serializer_class = OvqatKategoriyaSerializer



class OvqatViewSet(viewsets.ModelViewSet):
    queryset = Ovqat.objects.all()
    serializer_class = OvqatSerializer



class KirimViewSet(viewsets.ModelViewSet):
    queryset = Kirim.objects.all()
    serializer_class = KirimSerializer

    def perform_create(self, serializer):
        kirim = serializer.save(created_by=None)

        Ombor.objects.create(
            maxsulot=kirim.product,
            miqdor=kirim.quantity,
            oxirgi_narx=kirim.price
        )


class ChiqimViewSet(viewsets.ModelViewSet):
    queryset = Chiqim.objects.all()
    serializer_class = ChiqimSerializer

    def perform_create(self, serializer):
        chiqim = serializer.save(created_by=None)

        product = chiqim.product

        # ❗ QOLDIQ TEKSHIRISH
        if product.get_qoldiq() < chiqim.quantity:
            raise Exception("Omborda yetarli mahsulot yo‘q!")

        Ombor.objects.create(
            maxsulot=product,
            miqdor=-chiqim.quantity,
            oxirgi_narx=0
        )



class RetseptViewSet(viewsets.ModelViewSet):
    queryset = Retsept.objects.all()
    serializer_class = RetseptSerializer


class OmborViewSet(viewsets.ModelViewSet):
    queryset = Ombor.objects.all()
    serializer_class = OmborSerializer
    http_method_names = ['get']