import requests
from django.conf import settings
from comum.models import Usuario
from mercadopago import services
from django.http import JsonResponse
from django.utils.safestring import mark_safe

URL_ENVIAR_MSG = f'{settings.URL_BASE_TELEGRAM}{settings.TOKEN_BOT}/sendMessage'
URL_CONFIRMAR_CLIQUE_BOTAO = f'{settings.URL_BASE_TELEGRAM}{settings.TOKEN_BOT}/answerCallbackQuery'

class TelegramClient():
    @staticmethod
    def enviar_mensagem(text:str, chat_id:str):
        try:
            json = {'chat_id': chat_id, 'text': text}
            response = requests.post(URL_ENVIAR_MSG, json=json)
            print(response.text)
        except Exception as e:
            print(e)
    
    @staticmethod
    def enviar_mensagens_botoes(text:str, chat_id:str, botoes):
        try:
            json = {
                'chat_id': chat_id,
                'text': text,
                'reply_markup':{
                    'inline_keyboard':botoes
                }
            }
            requests.post(URL_ENVIAR_MSG, json=json)

        except Exception as e:
            print(e)
    
    # Faz o callback do envio de uma opção cliques
    @staticmethod
    def callback(id):
        try:
            json = {'callback_query_id': id}
            requests.post(URL_CONFIRMAR_CLIQUE_BOTAO, json=json)

        except Exception as e:
            print(e)


'''
Classe responsável pelo processamento
de todas as mensagens enviadas e recebidas
pelo bot/usuário.
'''
class TelegramService():   
    def __init__(
            self, 
            text=None, 
            chat_id=None, 
            telegram_id=None, 
            first_name=None, 
            last_name=None, 
            callback_query_id=None
        ):

        self.text = text
        self.chat_id = chat_id
        self.telegram_id = telegram_id
        self.first_name = first_name 
        self.last_name = last_name
        self.callback_query_id = callback_query_id

    def processar(self, acao=None):
        if self.telegram_id is not None and not self.usuario_existe():
            usuario = self.criar_usuario()
            if usuario is not None:
                return self.boas_vindas(usuario)
        
        if acao is not None and self.callback_query_id is not None:
            if acao == 'receita': return self.registrar_despesa()
            elif acao == 'faturamento': return self.registrar_faturamento()
            elif acao == 'gastos': return self.exibir_gastos()

        return self.menu_principal()
    
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

        TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)
    
    def registrar_despesa(self):
        mensagem_enviar = f'Registrando Despesa'
        print('aaa')
        TelegramClient.callback(self.callback_query_id)
        TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)
    
    def registrar_faturamento(self):
        mensagem_enviar = f'Registrando Faturamento'
        TelegramClient.callback(self.callback_query_id)
        TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)

    def exibir_gastos(self):
        mensagem_enviar = f'Exibindo Gastos'
        TelegramClient.callback(self.callback_query_id)
        TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)

    def menu_principal(self):
        mensagem_enviar = (
            'Olá! Como posso ajudar na sua gestão financeira hoje?\n\n'
            'Escolha uma das opções abaixo para começar:'
        )

        botoes = [
            [
                {
                    "text": "Cadastrar Receita",
                    "callback_data": "receita"
                }
            ],
            [
                {
                    "text": "Cadastrar Faturamento",
                    "callback_data": "faturamento"
                }
            ],
            [
                {
                    "text": "Exibir Gastos",
                    "callback_data": "gastos"
                }
            ]
        ]

        TelegramClient.enviar_mensagens_botoes(
            mensagem_enviar, 
            self.chat_id, 
            botoes
        )