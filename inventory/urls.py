from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    OlchovBirligiViewSet,
    MaxsulotViewSet,
    OvqatKategoriyaViewSet,
    OvqatViewSet,
    KirimViewSet,
    ChiqimViewSet,
    RetseptViewSet,
    OmborViewSet, TarixViewSet
)


router = DefaultRouter()

router.register(r'unit', OlchovBirligiViewSet)
router.register(r'maxsulot', MaxsulotViewSet)
router.register(r'kategoriya', OvqatKategoriyaViewSet)
router.register(r'ovqat', OvqatViewSet)
router.register(r'kirim', KirimViewSet)
router.register(r'chiqim', ChiqimViewSet)
router.register(r'retsept', RetseptViewSet)
router.register(r'ombor', OmborViewSet)
router.register('tarix', TarixViewSet, basename='tarix')

urlpatterns = [
    path('api/', include(router.urls)),
]