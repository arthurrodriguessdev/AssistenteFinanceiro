import requests
from django.conf import settings
from comum.models import Usuario
from mercadopago import services
from django.http import JsonResponse

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
        if not self.usuario_existe():
            usuario = self.criar_usuario()
            if usuario is not None:
                self.boas_vindas(usuario)
        
        self.boas_vindas(Usuario.objects.get(chat_id=self.chat_id))
    
    def usuario_existe(self):
        return Usuario.objects.filter(telegram_id=self.telegram_id).exists()
    
    def usuario_esta_ativo(self):
        return Usuario.objects.filter(telegram_id=self.telegram_id, ativo=True).exists()
    
    def criar_usuario(self):
        novo_usuario = None

        try:
            novo_usuario = Usuario()
            novo_usuario.telegram_id = self.telegram_id
            novo_usuario.chat_id = self.chat_id
            novo_usuario.nome = self.first_name
            novo_usuario.sobrenome = self.last_name
            novo_usuario.ativo = False
            novo_usuario.save()
            return novo_usuario

        except:
            return novo_usuario
    
    def boas_vindas(self, usuario):
        response = services.gerar_plano()

        try:
            link_pagamento = response.get('init_point')
        except Exception as e:
            return JsonResponse({'exception': e})
        
        mensagem_enviar = (
            f"Olá, {usuario.nome} {usuario.sobrenome}!\n\n"
            "Seja bem-vindo ao Assistente Financeiro!\n\n"
            "Com ele você poderá:\n"
            "• Registrar receitas;\n"
            "• Registrar despesas;\n"
            "• Consultar seu saldo;\n"
            "• Acompanhar sua vida financeira de forma simples e prática.\n\n"
            "Percebi que este é o seu primeiro acesso. Para liberar o uso do assistente, "
            "é necessário adquirir uma assinatura.\n\n"
            f"-> Link para pagamento: {link_pagamento}\n"
        ) 

        TelegramClient.enviar_mensagem(self.URL_ENVIAR_MSG, mensagem_enviar, self.chat_id)