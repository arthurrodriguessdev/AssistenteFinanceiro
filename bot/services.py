import requests
from django.conf import settings
from comum.models import Usuario


class TelegramClient():
    def __init__(self):
        self.URL_ENVIAR_MSG = f'{settings.URL_BASE_TELEGRAM}{settings.TOKEN_BOT}/sendMessage'

    @staticmethod
    def enviar_mensagem(URL, text:str, chat_id:str):
        try:
            json = {'chat_id': chat_id, 'text': text}
            requests.post(URL, json=json)
        except Exception as e:
            print(e)


'''
Classe responsável pelo processamento
de todas as mensagens enviadas e recebidas
pelo bot/usuário.
'''
class TelegramService():   
    def __init__(self, text, chat_id, telegram_id, first_name, last_name):
        self.URL_ENVIAR_MSG = f'{settings.URL_BASE_TELEGRAM}{settings.TOKEN_BOT}/sendMessage'

        self.text = text
        self.chat_id = chat_id
        self.telegram_id = telegram_id
        self.first_name = first_name 
        self.last_name = last_name
        
    def processar(self):
        enviar_mensagem = TelegramClient.enviar_mensagem
        texto = ''

        if not self.usuario_existe():
            texto = 'Olá, seja bem-vindo!'
            enviar_mensagem(self.URL_ENVIAR_MSG, texto, self.chat_id)
        enviar_mensagem(self.URL_ENVIAR_MSG, texto, self.chat_id)
    
    def usuario_existe(self):
        return Usuario.objects.filter(telegram_id=self.telegram_id).exists()