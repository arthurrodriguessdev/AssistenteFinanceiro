import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from bot.services import TelegramService


@csrf_exempt
def webhook_bot(request):
    data = json.loads(request.body)
    chat_id = data["message"]["chat"]["id"]
    text = data["message"]["text"]
    telegram_id = data['message']['from']['id']
    first_name = data['message']['from']['first_name']

    try:
        last_name = data['message']['from']['last_name']
    except:
        last_name = ''

    # Criando o objeto da classe que faz o processamento
    telegram = TelegramService(text, chat_id, telegram_id, first_name, last_name)
    telegram.processar()
    return HttpResponse("ok")
