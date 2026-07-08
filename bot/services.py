import requests
from django.conf import settings
from comum.models import Usuario, StatusUsuario, Transacao, TransacaoChoices
from comum.services import *
from mercadopago import services
from bot.mensagem import MensagemBot
from django.http import JsonResponse
from datetime import datetime

URL_ENVIAR_MSG = f'{settings.URL_BASE_TELEGRAM}{settings.TOKEN_BOT}/sendMessage'
URL_CONFIRMAR_CLIQUE_BOTAO = f'{settings.URL_BASE_TELEGRAM}{settings.TOKEN_BOT}/answerCallbackQuery'

class TelegramClient():
    @staticmethod
    def enviar_mensagem(text:str, chat_id:str):
        try:
            json = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
            requests.post(URL_ENVIAR_MSG, json=json)
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
    # Dicionário utilizado no método genérico de transações
    TRANSACAO_CONFIG = {
        TransacaoChoices.FATURAMENTO : {
            'status_valor': StatusUsuario.AGUARDANDO_INFORMAR_VALOR_FATURAMENTO,
            'status_descricao': StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_FATURAMENTO,
            'status_informou': StatusUsuario.INFORMOU_FATURAMENTO
            },
        
        TransacaoChoices.DESPESA : {
            'status_valor': StatusUsuario.AGUARDANDO_INFORMAR_VALOR_DESPESA,
            'status_descricao': StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_DESPESA,
            'status_informou': StatusUsuario.INFORMOU_DESPESA
        }
    }

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

        usuario = get_usuario(self.telegram_id)
        if acao is not None and self.callback_query_id is not None:
            if usuario is not None:
                if acao == 'despesa': 
                    return self.registrar_transacao(TransacaoChoices.DESPESA, usuario)
                elif acao == 'faturamento': 
                    return self.registrar_transacao(TransacaoChoices.FATURAMENTO, usuario)
                elif acao == 'gastos': 
                    return self.exibir_gastos()
        else:
            if usuario:

                # Faturamento
                enviou_despesa_faturamento = self.text is not None
                if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_VALOR_FATURAMENTO and                    enviou_despesa_faturamento:
                    usuario.set_status(StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_FATURAMENTO)
                    return self.registrar_transacao(TransacaoChoices.FATURAMENTO, usuario)
                
                if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_FATURAMENTO and enviou_despesa_faturamento:
                    usuario.set_status(StatusUsuario.INFORMOU_FATURAMENTO)
                    return self.registrar_transacao(TransacaoChoices.FATURAMENTO, usuario)
                
                # Despesa
                if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_VALOR_DESPESA and enviou_despesa_faturamento:
                    usuario.set_status(StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_DESPESA)
                    return self.registrar_transacao(TransacaoChoices.DESPESA, usuario)
                
                if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_DESPESA and enviou_despesa_faturamento:
                    usuario.set_status(StatusUsuario.INFORMOU_DESPESA)
                    return self.registrar_transacao(TransacaoChoices.DESPESA, usuario)
                
                usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
                return self.menu_principal(usuario)
            else:
                return self.boas_vindas(usuario)
    
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
        
        TelegramClient.enviar_mensagem(MensagemBot.mensagem_boas_vindas(usuario, link_pagamento), self.chat_id)
    
    ''' Método que registra todas as transações aceitas pelo sistema:
        - Faturamento
        - Despesa
    '''
    def registrar_transacao(self, tipo_transacao, usuario):
        configuracao = self.TRANSACAO_CONFIG[tipo_transacao]
        mensagem_enviar = ''
        TelegramClient.callback(self.callback_query_id)

        if usuario.status == StatusUsuario.AGUARDANDO_MENU:
            usuario.set_status(configuracao['status_valor'])

        if usuario.status == configuracao['status_valor']:
            mensagem_enviar = MensagemBot.mensagem_informar_valor(tipo_transacao)
            return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)
        
        if usuario.status == configuracao['status_descricao']:
            valor_operacao = str(self.text)

            if ',' in valor_operacao:
                valor_operacao = valor_operacao.replace(',', '.')
            
            valor_operacao = converter_valor_decimal(valor_operacao)

            # Erro na conversão
            if valor_operacao is None:
                mensagem_enviar = MensagemBot.mensagem_erro_conversao_valor()
                usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
                return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)
            
            # Registra o faturamento
            transacao = Transacao.objects.create(
                usuario=usuario,
                tipo=tipo_transacao,
                descricao='',
                registrada_em=datetime.now(),
                valor=float(valor_operacao)
            )

            mensagem_enviar = MensagemBot.mensagem_informar_descricao(tipo_transacao)
            return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)
        
        elif usuario.status == configuracao['status_informou']:
            try:
                transacao = Transacao.objects.filter(
                    usuario=usuario,
                    tipo=tipo_transacao
                ).last()

                transacao.descricao = self.text
                transacao.save()

                usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
                mensagem_enviar = MensagemBot.mensagem_sucesso_registro(
                    tipo_transacao, 
                    transacao.valor
                )

                return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)
            
            except Exception as e:
                usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
                return TelegramClient.enviar_mensagem("Deu erro ao salvar", self.chat_id)

    def exibir_gastos(self):
        TelegramClient.callback(self.callback_query_id)
        
        despesas = Transacao.objects.filter(tipo=TransacaoChoices.DESPESA, usuario=get_usuario(self.telegram_id))
        return TelegramClient.enviar_mensagem(MensagemBot.mensagem_exibir_gastos(despesas, calcular_valor_total_despesas(despesas)), self.chat_id)
        
    def menu_principal(self, usuario):
        usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
        menu = MensagemBot.mensagem_menu_principal()
        TelegramClient.enviar_mensagens_botoes(menu['text'], self.chat_id, menu['botoes'])