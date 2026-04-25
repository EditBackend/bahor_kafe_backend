from django.contrib import admin
from .models import (
    Ombor,
    OlchovBirligi,
    Maxsulot,
    OvqatKategoriya,
    Ovqat,
    Kirim,
    Chiqim,
    Retsept
)

admin.site.register(Ombor)
admin.site.register(OlchovBirligi)
admin.site.register(Maxsulot)
admin.site.register(OvqatKategoriya)
admin.site.register(Ovqat)
admin.site.register(Kirim)
admin.site.register(Chiqim)
admin.site.register(Retsept)