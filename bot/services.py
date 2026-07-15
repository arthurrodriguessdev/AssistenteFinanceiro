import logging
import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from mercadopago import services
from bot.mensagem import MensagemBot
from bot.relatorios import Relatorio
from bot.transacoes import TransacaoService
from bot.categorias import CategoriaService
from comum.models import StatusUsuario, Transacao, TransacaoChoices, Categoria, ObjetoChoices
from comum.services import converter_valor_decimal, get_usuario, get_todas_categorias_usuario, converter_acao_id, get_ultima_transacao
from comum.usuario_service import UsuarioService
from bot.enums.enums import TipoMenu

logger = logging.getLogger(__name__)

URL_ENVIAR_MSG = f'{settings.URL_BASE_TELEGRAM}{settings.TOKEN_BOT}/sendMessage'
URL_CONFIRMAR_CLIQUE_BOTAO = f'{settings.URL_BASE_TELEGRAM}{settings.TOKEN_BOT}/answerCallbackQuery'


class TelegramClient():
    @staticmethod
    def post(url, dicionario_dados):
        """
        Faz requisição 'POST' para a API do telegram
        - Recebe URL e dicionário de dados
        """
        try:
            response = requests.post(url=url, json=dicionario_dados, timeout=10)
            response.raise_for_status() # Tratando os erros HTTP
            return response
        
        except requests.RequestException:
            logger.exception("Erro ao fazer 'POST' para a API do Telegram.")
            return None
        
    @staticmethod
    def enviar_mensagem(text:str, chat_id:str):
        json = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
        TelegramClient.post(URL_ENVIAR_MSG, json)
    
    @staticmethod
    def enviar_mensagens_botoes(text:str, chat_id:str, botoes):
        json = {
            'chat_id': chat_id,
            'text': text if text != '' else '',
            'reply_markup':{
                'inline_keyboard':botoes
            }
        }

        TelegramClient.post(URL_ENVIAR_MSG, json)
    
    @staticmethod
    def callback(callback_query_id):
        TelegramClient.post(URL_CONFIRMAR_CLIQUE_BOTAO, {'callback_query_id': callback_query_id})


'''
Classe responsável pelo processamento
de todas as mensagens enviadas e recebidas
pelo bot/usuário.
'''
class TelegramService():
    MENUS = {
        TipoMenu.PRINCIPAL: MensagemBot.mensagem_menu_principal,
        TipoMenu.FATURAMENTO: MensagemBot.mensagem_menu_faturamento,
        TipoMenu.DESPESA: MensagemBot.mensagem_menu_despesa,
        TipoMenu.RELATORIO: MensagemBot.mensagem_menu_relatorio,
        TipoMenu.CONFIGURACAO: MensagemBot.mensagem_menu_configuracao,
        TipoMenu.CATEGORIA: MensagemBot.mensagem_menu_categoria
    }

    # Dicionário utilizado no método genérico de transações
    TRANSACAO_CONFIG = {
        TransacaoChoices.FATURAMENTO : {
            'status_valor': StatusUsuario.AGUARDANDO_INFORMAR_VALOR_FATURAMENTO,
            'status_descricao': StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_FATURAMENTO,
            },
        
        TransacaoChoices.DESPESA : {
            'status_valor': StatusUsuario.AGUARDANDO_INFORMAR_VALOR_DESPESA,
            'status_descricao': StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_DESPESA,
            'status_categoria': StatusUsuario.AGUARDANDO_INFORMAR_CATEGORIA_DESPESA,
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

        acoes_sistema = {
            # Menus
            'menu_despesa': lambda: self.menu(usuario, TipoMenu.DESPESA),
            'menu_faturamento': lambda: self.menu(usuario, TipoMenu.FATURAMENTO),
            'menu_relatorio': lambda: self.menu(usuario, TipoMenu.RELATORIO),
            'menu_configuracao': lambda: self.menu(usuario, TipoMenu.CONFIGURACAO),
            'menu_categoria': lambda: self.menu(usuario, TipoMenu.CATEGORIA),

            'cadastro_despesa': lambda: self.registrar_transacao(TransacaoChoices.DESPESA, usuario),
            'cadastro_faturamento': lambda: self.registrar_transacao(TransacaoChoices.FATURAMENTO, usuario),
            'exclusao_despesa': lambda: self.excluir_transacao(TransacaoChoices.DESPESA, usuario),
            'exclusao_faturamento': lambda: self.excluir_transacao(TransacaoChoices.FATURAMENTO, usuario),
            'exibir_despesas':  lambda: self.exibir(TransacaoChoices.DESPESA, usuario, acao),
            'exibir_faturamentos': lambda: self.exibir(TransacaoChoices.FATURAMENTO, usuario, acao),
            'resumo_mes': lambda: self.resumo_mes(usuario, acao),
            'cadastro_categoria': lambda: self.registrar_categoria(usuario),
            'exclusao_categoria': lambda: self.excluir_categioria(usuario)
        }
        
        # Processa as ações e chama o método equivalente
        if acao is not None and self.callback_query_id is not None:
            if usuario is not None:
                acao_realizar = acoes_sistema.get(acao)
                if acao_realizar:
                    return acao_realizar()
            
        if usuario:
            if self.processar_cadastro(usuario, acao): return True
            elif self.processar_exibicao(usuario, acao): return True
            elif self.processar_exclusao(usuario, acao): return True
            elif self.processar_resumo(usuario, acao): return True
            elif self.processar_cadastro_categoria(usuario): return True
            else: return self.menu(usuario, TipoMenu.PRINCIPAL)
        else:
            return self.boas_vindas(usuario)
    
    def processar_cadastro(self, usuario, acao):
            msg_usuario = self.text is not None

            # Cadastro de faturamento
            if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_VALOR_FATURAMENTO and msg_usuario:
                usuario.set_status(StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_FATURAMENTO)
                self.registrar_transacao(TransacaoChoices.FATURAMENTO, usuario)
                return True
            
            if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_FATURAMENTO and msg_usuario:
                usuario.set_status(StatusUsuario.INFORMOU_FATURAMENTO)
                self.registrar_transacao(TransacaoChoices.FATURAMENTO, usuario)
                return True
            
            # Cadastro de Despesa
            if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_VALOR_DESPESA and msg_usuario:
                usuario.set_status(StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_DESPESA)
                self.registrar_transacao(TransacaoChoices.DESPESA, usuario)
                return True
            
            if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_DESPESA and msg_usuario:
                try:
                    transacao = get_ultima_transacao(usuario, TransacaoChoices.DESPESA)
                    transacao.descricao = self.text
                    transacao.save()
                except Exception:
                    logger.exception("Erro ao salvar descrição da despesa.")
                    usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
                    return TelegramClient.enviar_mensagem(MensagemBot.mensagem_erro(),self.chat_id)
                
                usuario.set_status(StatusUsuario.AGUARDANDO_INFORMAR_CATEGORIA_DESPESA)
                self.registrar_transacao(TransacaoChoices.DESPESA, usuario)
                return True
            
            if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_CATEGORIA_DESPESA and acao:
                self.registrar_transacao(TransacaoChoices.DESPESA, usuario, acao)
                return True
            
            # else:
            #     self.registrar_transacao(TransacaoChoices.DESPESA, usuario)
            #     return True
            
            return False
    
    def processar_exclusao(self, usuario, acao):
        # Exclusão de Despesa
        if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_MES_DESPESA_EXCLUSAO and acao:
            usuario.set_status(StatusUsuario.AGUARDANDO_VER_DESPESA_EXCLUSAO)
            self.excluir_transacao(TransacaoChoices.DESPESA, usuario, acao)
            return True

        elif usuario.status == StatusUsuario.AGUARDANDO_VER_DESPESA_EXCLUSAO:
            usuario.set_status(StatusUsuario.AGUARDANDO_CONFIRMAR_EXCLUSAO_DESPESA)
            self.excluir_transacao(TransacaoChoices.DESPESA, usuario, acao)
            return True
        
        elif usuario.status == StatusUsuario.AGUARDANDO_CONFIRMAR_EXCLUSAO_DESPESA:
            usuario.set_status(StatusUsuario.CONFIRMOU_CANCELOU_EXCLUSAO_DESPESA)
            self.excluir_transacao(TransacaoChoices.DESPESA, usuario, acao)
            return True
        
        # Exclusão de Faturamento
        elif usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_MES_FATURAMENTO_EXCLUSAO and acao:
            usuario.set_status(StatusUsuario.AGUARDANDO_VER_FATURAMENTO_EXCLUSAO)
            self.excluir_transacao(TransacaoChoices.FATURAMENTO, usuario, acao)
            return True

        elif usuario.status == StatusUsuario.AGUARDANDO_VER_FATURAMENTO_EXCLUSAO:
            usuario.set_status(StatusUsuario.AGUARDANDO_CONFIRMAR_EXCLUSAO_FATURAMENTO)
            self.excluir_transacao(TransacaoChoices.FATURAMENTO, usuario, acao)
            return True
        
        elif usuario.status == StatusUsuario.AGUARDANDO_CONFIRMAR_EXCLUSAO_FATURAMENTO:
            usuario.set_status(StatusUsuario.CONFIRMOU_CANCELOU_EXCLUSAO_FATURAMENTO)
            self.excluir_transacao(TransacaoChoices.FATURAMENTO, usuario, acao)
            return True
        
        else:
            return False
            
    def processar_exibicao(self, usuario, acao):
        # Exibição de Despesa
        if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_MES_DESPESA and acao:
            usuario.set_status(StatusUsuario.AGUARDANDO_VER_DESPESA)
            self.exibir(TransacaoChoices.DESPESA, usuario, acao)
            return True
        
        # Exibição de Faturamento
        if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_MES_FATURAMENTO and acao:
            usuario.set_status(StatusUsuario.AGUARDANDO_VER_FATURAMENTO)
            self.exibir(TransacaoChoices.FATURAMENTO, usuario, acao)
            return True
        
        return False

    def processar_resumo(self, usuario, acao):
        if usuario.status == StatusUsuario.AGUARDANDO_MES_RESUMO and acao:
            usuario.set_status(StatusUsuario.AGUARDANDO_VER_RESUMO)
            self.resumo_mes(usuario, acao)
            return True
        return False
    
    def processar_cadastro_categoria(self, usuario):
        if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_NOME_CATEGORIA_CADASTRO:
            self.registrar_categoria(usuario)
            return True
        return False
    
    def boas_vindas(self, usuario):
        response = services.gerar_plano()

        try:
            link_pagamento = response.get('init_point')
        except Exception as e:
            logger.exception('Erro ao gerar o link de pagamento.')
            return JsonResponse({'exception': e})
        
        TelegramClient.enviar_mensagem(MensagemBot.mensagem_boas_vindas(usuario, link_pagamento), self.chat_id)
    
    def registrar_transacao(self, tipo_transacao, usuario, acao=None):
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
        
        elif usuario.status == configuracao['status_categoria']:
            if acao is None:
                categorias = get_todas_categorias_usuario(usuario)
                mensagem_enviar = MensagemBot.mensagem_exibir_categorias(categorias)
                return TelegramClient.enviar_mensagens_botoes(mensagem_enviar['text'], self.chat_id, mensagem_enviar['botoes'])

            else:
                id_categoria = converter_acao_id(acao)
                if id_categoria is not None:
                    try:
                        categoria_selecionada = Categoria.objects.get(pk=id_categoria)
                        
                        transacao = get_ultima_transacao(usuario, tipo_transacao)
                        transacao.categoria = categoria_selecionada
                        transacao.save()

                        usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
                        mensagem_enviar = MensagemBot.mensagem_sucesso_registro(transacao.valor, tipo_transacao, None)
                        return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)

                    except Categoria.DoesNotExist:
                        logger.exception("Erro ao buscar a categoria.")
                        mensagem_enviar = MensagemBot.mensagem_erro()
                        return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)
                 
                    except Exception:
                        logger.exception("Erro ao buscar transação e atualizar categoria e descrição.")
                        mensagem_enviar = MensagemBot.mensagem_erro()
                        return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)
                    
                    finally:
                        usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
                
                usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
                return TelegramClient.enviar_mensagem(MensagemBot.mensagem_erro(), self.chat_id)

    def exibir(self, tipo_registro, usuario, acao):
        self.callback()

        exibir = Relatorio.exibir(usuario, self.text, tipo_registro, acao)
        status = exibir.get('status', None)
        if status and status == 'mostrar_meses':
            mensagem_enviar = MensagemBot.mensagem_exibir_meses()
            return TelegramClient.enviar_mensagens_botoes(mensagem_enviar['text'], self.chat_id, mensagem_enviar['botoes'])
        
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
            return TelegramClient.enviar_mensagens_botoes(mensagem_enviar['text'], self.chat_id, mensagem_enviar['botoes'])

        elif status and status == 'mostrar_registros':
            registros = excluir.get('registros', None)
            mensagem_enviar = MensagemBot.mensagem_exibir_registros_exclusao(registros, tipo_registro)

            if not registros:
                usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
                return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)
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

    def resumo_mes(self, usuario, acao):
        self.callback()

        resumo_mes = Relatorio.resumo_mes(usuario, acao)
        status = resumo_mes.get('status', None)

        if status == 'mostrar_meses':
            mensagem_enviar = MensagemBot.mensagem_exibir_meses()
            return TelegramClient.enviar_mensagens_botoes(mensagem_enviar['text'], self.chat_id, mensagem_enviar['botoes'])

        elif status == 'mostrar_resumo':
            usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
            mensagem_enviar = MensagemBot.mensagem_resumo_mes(resumo_mes)
            return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)

    def registrar_categoria(self, usuario):
        self.callback()

        resultado = CategoriaService.criar(usuario, self.text)
        status = resultado.get('status', None)

        if status == 'solicitar_nome':
            mensagem_enviar = MensagemBot.mensagem_informar_nome_categoria()
            return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)
        
        elif status == 'sucesso':
            mensagem_enviar = MensagemBot.mensagem_sucesso_registro(None, None, ObjetoChoices.CATEGORIA)
            usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
            return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)
        
        return TelegramClient.enviar_mensagem(MensagemBot.mensagem_erro(),self.chat_id)
        
    def excluir_categoria(self, usuario):
        ...

    # Métodos auxiliares (não são funcionalidades)
    def callback(self):
        """
        - Se tiver que fazer o callback (se for ação), chama o método que faz o callback para o usuário
        """
        if self.callback_query_id is not None:
            return TelegramClient.callback(self.callback_query_id)
        return None
    
    def menu(self, usuario, tipo_menu):
        """
        - Recebe o tipo de menu que deve exibir
        - Seleciona no dicionário, chama o método e guarda na variável
        - Passa valores das chaves do dicionário retornado para o método de envio de mensagem
        """
        usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
        menu = self.MENUS[tipo_menu]()
        TelegramClient.enviar_mensagens_botoes(menu['text'], self.chat_id, menu['botoes'])