import requests
from django.conf import settings
from comum.models import StatusUsuario, Transacao, TransacaoChoices
from comum.services import *
from comum.usuario_service import UsuarioService
from mercadopago import services
from bot.mensagem import MensagemBot
from bot.relatorios import Relatorio
from bot.transacoes import TransacaoService
from django.http import JsonResponse
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

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
                
                elif acao == 'exclusao_despesa':
                    return self.excluir_transacao(TransacaoChoices.DESPESA, usuario)
                
                elif acao == 'exclusao_faturamento': 
                    return self.excluir_transacao(TransacaoChoices.FATURAMENTO, usuario)
                
                elif acao == 'exibir_despesas': 
                    return self.exibir(TransacaoChoices.DESPESA, usuario)
                
                elif acao == 'exibir_faturamentos':
                    return self.exibir(TransacaoChoices.FATURAMENTO, usuario)
        if usuario:

            # Cadastro de Faturamento
            msg_usuario = self.text is not None
            if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_VALOR_FATURAMENTO and msg_usuario:
                usuario.set_status(StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_FATURAMENTO)
                return self.registrar_transacao(TransacaoChoices.FATURAMENTO, usuario)
            
            if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_FATURAMENTO and msg_usuario:
                usuario.set_status(StatusUsuario.INFORMOU_FATURAMENTO)
                return self.registrar_transacao(TransacaoChoices.FATURAMENTO, usuario)
            
            # Cadastro de Despesa
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
            
            # Exclusão de Despesa
            if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_MES_DESPESA_EXCLUSAO and msg_usuario:
                usuario.set_status(StatusUsuario.AGUARDANDO_VER_DESPESA_EXCLUSAO)
                return self.excluir_transacao(TransacaoChoices.DESPESA, usuario)

            if usuario.status == StatusUsuario.AGUARDANDO_VER_DESPESA_EXCLUSAO:
                usuario.set_status(StatusUsuario.AGUARDANDO_CONFIRMAR_EXCLUSAO_DESPESA)
                return self.excluir_transacao(TransacaoChoices.DESPESA, usuario, acao)
            
            if usuario.status == StatusUsuario.AGUARDANDO_CONFIRMAR_EXCLUSAO_DESPESA:
                usuario.set_status(StatusUsuario.CONFIRMOU_CANCELOU_EXCLUSAO_DESPESA)
                return self.excluir_transacao(TransacaoChoices.DESPESA, usuario, acao)
            
            # Exclusão de Faturamento
            if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_MES_FATURAMENTO_EXCLUSAO and msg_usuario:
                usuario.set_status(StatusUsuario.AGUARDANDO_VER_FATURAMENTO_EXCLUSAO)
                return self.excluir_transacao(TransacaoChoices.FATURAMENTO, usuario)

            if usuario.status == StatusUsuario.AGUARDANDO_VER_FATURAMENTO_EXCLUSAO:
                usuario.set_status(StatusUsuario.AGUARDANDO_CONFIRMAR_EXCLUSAO_FATURAMENTO)
                return self.excluir_transacao(TransacaoChoices.FATURAMENTO, usuario, acao)
            
            if usuario.status == StatusUsuario.AGUARDANDO_CONFIRMAR_EXCLUSAO_FATURAMENTO:
                usuario.set_status(StatusUsuario.CONFIRMOU_CANCELOU_EXCLUSAO_FATURAMENTO)
                return self.excluir_transacao(TransacaoChoices.FATURAMENTO, usuario, acao)

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
        self.callback()

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
            
            # Valida número negativo
            if valor_operacao <= 0:
                mensagem_enviar = MensagemBot.mensagem_erro_valor_negativo()
                usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
                return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)
            
            transacao = Transacao(
                usuario=usuario,
                tipo=tipo_transacao,
                descricao='',
                valor=valor_operacao
            )

            # Registra o faturamento
            try:
                transacao.full_clean()
                transacao.save()

            except ValidationError as e:
                logger.exception("Erro no registro de transação.")
                usuario.set_status(StatusUsuario.AGUARDANDO_MENU)

                if "valor" in e.message_dict:
                    mensagem_enviar = mensagem_enviar = MensagemBot.mensagem_erro_tamanho_valor()
                else:
                    mensagem_enviar = MensagemBot.mensagem_erro()

                return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)

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
            
            except Exception:
                logger.exception("Erro no registro de transação.")
                usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
                mensagem_enviar = MensagemBot.mensagem_erro()
                return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)

    def exibir(self, tipo_registro, usuario):
        self.callback()

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
    
    def excluir_transacao(self, tipo_registro, usuario, acao=None):
        self.callback()

        excluir = TransacaoService.excluir_registro(tipo_registro, usuario, self.text, acao)
        status = excluir.get('status', None)

        if status and status == 'mostrar_meses':
            mensagem_enviar = MensagemBot.mensagem_exibir_meses()
            return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)

        elif status and status == 'mostrar_registros':
            registros = excluir.get('registros', None)
            mensagem_enviar = MensagemBot.mensagem_exibir_registros_exclusao(registros, tipo_registro)
            return TelegramClient.enviar_mensagens_botoes(mensagem_enviar['text'], self.chat_id, mensagem_enviar['botoes'])

        elif status and status == 'mostrar_confirmacao':
            registro_excluir = excluir.get('registro_excluir', None)
            mensagem_enviar = MensagemBot.mensagem_confirmar_exclusao(registro_excluir)
            return TelegramClient.enviar_mensagens_botoes(mensagem_enviar['text'], self.chat_id, mensagem_enviar['botoes'])
        
        elif status and status == 'mostrar_mensagem_excluiu_sucesso':
            mensagem_enviar = MensagemBot.mensagem_exclusao_confirmada(tipo_registro)
            return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)
        
        elif status and status == 'mostrar_mensagem_cancelou_operacao':
            mensagem_enviar = MensagemBot.mensagem_exclusao_cancelada(tipo_registro)
            return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)
        
        elif status and status == 'erro':
            mensagem_enviar = MensagemBot.mensagem_erro_numero_mes()
            return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)

    def callback(self):
        if self.callback_query_id is not None:
            return TelegramClient.callback(self.callback_query_id)
        return None
    
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