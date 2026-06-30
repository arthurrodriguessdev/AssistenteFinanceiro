from django.urls import path
from mercadopago import services

urlpatterns = [
    path('/webhook/', services.webhook_mercadopago, name='webhook_mercadopago')
]