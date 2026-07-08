import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from bot.services import TelegramService, TelegramClient
from bot.mensagem import MensagemBot
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def webhook_bot(request):
    telegram = None
    chat_id = None

    try:
        # Processando mensagens
        data = json.loads(request.body)
        if 'message' in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"]["text"]
            telegram_id = data['message']['from']['id']
            first_name = data['message']['from']['first_name']

            try:
                last_name = data['message']['from']['last_name']
            except:
                last_name = ''
            
            telegram = TelegramService(text, chat_id, telegram_id, first_name, last_name)
            telegram.processar()

        # Processando seleção de opções (botões)
        elif 'callback_query' in data:
            dados = data['callback_query']
            botao_clicado = dados['data']

            # Parâmetros
            telegram_id = dados["from"]["id"]
            chat_id = dados["message"]["chat"]["id"]
            callback_query_id = dados["message"]["chat"]["id"]
            telegram = TelegramService(telegram_id=telegram_id, chat_id=chat_id, callback_query_id=callback_query_id)

            telegram.processar(botao_clicado)
        
    except:
        logger.exception('Erro no webhook do telegram (tentativa de acessar os dados).')
        if telegram:
            TelegramClient.enviar_mensagem(MensagemBot.mensagem_erro(), telegram.chat_id)
        elif chat_id:
            TelegramClient.enviar_mensagem(MensagemBot.mensagem_erro(), chat_id)
    
    return HttpResponse("ok")
