from django.urls import path
from bot import api_telegram


urlpatterns = [
    path('webhook/', api_telegram.webhook_bot, name='webhook_bot')
]