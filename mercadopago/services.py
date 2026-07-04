from django.conf import settings
import requests
from django.http import JsonResponse
from django.conf import settings
import json
from django.views.decorators.csrf import csrf_exempt


def gerar_plano():
    headers = {
        'Authorization': f'Bearer {settings.TOKEN_API_MERCADOPAGO_TEST}',
        'Content-Type': 'application/json'
    }

    parametros_api = {
        "reason": "Fecha a Conta - Bot Financeiro",
        "auto_recurring": {
            "frequency": 1,
            "frequency_type": "months",
            "transaction_amount": 1.00,
            "currency_id": "BRL"
        },

        "back_url": "https://t.me/FechaContaBot",
        "status": "inactive",
        "notification_url": "https://joey-tinnier-cristopher.ngrok-free.dev/mercadopago/webhook/"
    }
    
    
    response = requests.post(settings.URL_CRIAR_PLANO, json=parametros_api, headers=headers)
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