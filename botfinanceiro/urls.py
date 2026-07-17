from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('bot/', include('bot.urls')),
    path('mercadopago/', include('mercadopago.urls')),
    path("select2/", include("django_select2.urls")), # Select2
]
