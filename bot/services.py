import requests
from django.conf import settings
from comum.models import Usuario, StatusUsuario, Transacao, TransacaoChoices
from comum.services import *
from comum.usuario_service import UsuarioService
from mercadopago import services
from bot.mensagem import MensagemBot
from bot.relatorios import Relatorio
from django.http import JsonResponse
from datetime import datetime

URL_ENVIAR_MSG = f'{settings.URL_BASE_TELEGRAM}{settings.TOKEN_BOT}/sendMessage'
URL_CONFIRMAR_CLIQUE_BOTAO = f'{settings.URL_BASE_TELEGRAM}{settings.TOKEN_BOT}/answerCallbackQuery'


class TipoMenu():
    PRINCIPAL = 'principal'
    FATURAMENTO = 'faturamento'
    DESPESA = 'despesa'
    RELATORIO = 'relatorio'


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
                'text': text if text != '' else '',
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
        MensagemBot.mensagem_exibir_meses()
        if self.telegram_id is not None and not UsuarioService.usuario_existe(self.telegram_id):
            dados_usuario = {
                'telegram_id': self.telegram_id,
                'chat_id': self.chat_id,
                'first_name': self.first_name,
                'last_name': self.last_name
            }

            usuario = UsuarioService.criar_usuario(**dados_usuario)
            if usuario is not None:
                return self.boas_vindas(usuario)

        usuario = get_usuario(self.telegram_id)
        if acao is not None and self.callback_query_id is not None:
            if usuario is not None:
                if acao == 'menu_despesa': 
                    return self.menu(usuario, TipoMenu.DESPESA)
                
                elif acao == 'menu_faturamento':
                    return self.menu(usuario, TipoMenu.FATURAMENTO)
                
                elif acao == 'menu_relatorio':
                    return self.menu(usuario, TipoMenu.RELATORIO)
                
                elif acao == 'cadastro_despesa':
                    return self.registrar_transacao(TransacaoChoices.DESPESA, usuario)
                
                elif acao == 'cadastro_faturamento': 
                    return self.registrar_transacao(TransacaoChoices.FATURAMENTO, usuario)
                
                elif acao == 'exibir_despesas': 
                    return self.exibir(TransacaoChoices.DESPESA, usuario)
                
                elif acao == 'exibir_faturamentos':
                    return self.exibir(TransacaoChoices.FATURAMENTO, usuario)
        else:
            if usuario:

                # Faturamento
                msg_usuario = self.text is not None
                if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_VALOR_FATURAMENTO and                    msg_usuario:
                    usuario.set_status(StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_FATURAMENTO)
                    return self.registrar_transacao(TransacaoChoices.FATURAMENTO, usuario)
                
                if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_FATURAMENTO and msg_usuario:
                    usuario.set_status(StatusUsuario.INFORMOU_FATURAMENTO)
                    return self.registrar_transacao(TransacaoChoices.FATURAMENTO, usuario)
                
                # Despesa
                if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_VALOR_DESPESA and msg_usuario:
                    usuario.set_status(StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_DESPESA)
                    return self.registrar_transacao(TransacaoChoices.DESPESA, usuario)
                
                if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_DESPESA and msg_usuario:
                    usuario.set_status(StatusUsuario.INFORMOU_DESPESA)
                    return self.registrar_transacao(TransacaoChoices.DESPESA, usuario)
            
                # Exibição de Gastos
                if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_MES_DESPESA and msg_usuario:
                    usuario.set_status(StatusUsuario.AGUARDANDO_VER_DESPESA)
                    return self.exibir(TransacaoChoices.DESPESA, usuario)
            
                # Exibição de Faturamento
                if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_MES_FATURAMENTO and msg_usuario:
                    usuario.set_status(StatusUsuario.AGUARDANDO_VER_FATURAMENTO)
                    return self.exibir(TransacaoChoices.FATURAMENTO, usuario)
                
                return self.menu(usuario, TipoMenu.PRINCIPAL)
                
            else:
                return self.boas_vindas(usuario)
    
    def boas_vindas(self, usuario):
        response = services.gerar_plano()

        try:
            link_pagamento = response.get('init_point')
        except Exception as e:
            return JsonResponse({'exception': e})
        
        TelegramClient.enviar_mensagem(MensagemBot.mensagem_boas_vindas(usuario, link_pagamento), self.chat_id)
    
    def registrar_transacao(self, tipo_transacao, usuario):
        """ 
        Método que registra todas as transações aceitas pelo sistema:
        - Faturamento
        - Despesa
        """

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

    def exibir(self, tipo_registro, usuario):
        TelegramClient.callback(self.callback_query_id)

        exibir = Relatorio.exibir(usuario, self.text, tipo_registro)
        status = exibir.get('status', None)
        if status and status == 'mostrar_meses':
            return TelegramClient.enviar_mensagem(MensagemBot.mensagem_exibir_meses(), self.chat_id)
        
        elif status and status == 'mostrar_registros':
            registros = exibir.get('registros', None)
            total = exibir.get('valor_total', None)

            msg_gastos = MensagemBot.mensagem_exibir_registros(registros, total, tipo_registro)
            return TelegramClient.enviar_mensagem(msg_gastos, self.chat_id)
        
        elif status and status == 'erro':
            msg_erro = MensagemBot.mensagem_erro_numero_mes()
            return TelegramClient.enviar_mensagem(msg_erro, self.chat_id)
    
    def menu(self, usuario, tipo_menu):
        usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
        menu = None

        if tipo_menu == TipoMenu.PRINCIPAL:
            menu = MensagemBot.mensagem_menu_principal()
        elif tipo_menu == TipoMenu.FATURAMENTO:
            menu = MensagemBot.mensagem_menu_faturamento()
        elif tipo_menu == TipoMenu.DESPESA:
            menu = MensagemBot.mensagem_menu_despesa()
        elif tipo_menu == TipoMenu.RELATORIO:
            menu = MensagemBot.mensagem_menu_relatorio()

        TelegramClient.enviar_mensagens_botoes(menu['text'], self.chat_id, menu['botoes'])