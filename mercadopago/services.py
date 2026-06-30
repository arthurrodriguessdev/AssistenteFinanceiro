from django.conf import settings
import requests
from django.http import JsonResponse
from django.conf import settings
import json
from django.views.decorators.csrf import csrf_exempt


def gerar_plano():
    headers = {
        'Authorization': settings.TOKEN_API_MERCADOPAGO,
        'Content-Type': 'application/json'
    }

    parametros_api = {
        "reason": "Fecha a Conta - Bot Financeiro",
        "auto_recurring": {
            "frequency": 1,
            "frequency_type": "months",
            "transaction_amount": 19.90,
            "currency_id": "BRL"
        },

        # "back_url": "https://stasker.onrender.com/dashboard",
        "status": "pending",
        # "notification_url": "https://stasker.onrender.com/planos/notificacoes_pagamentos/"
    }

    response = requests.post(settings.URL_CRIAR_PLANO, json=parametros_api, headers=headers)
    print(response.json())
    return response.json()

@csrf_exempt
def webhook_mercadopago(request):
    try:
        dados_recebidos_webhook = json.loads(request.body)
        id_assinatura = dados_recebidos_webhook['data']['id']

        print(dados_recebidos_webhook)

        return JsonResponse({}, status=200)
    
    except Exception as error:
        return JsonResponse({'error': str(error)}, status=400)