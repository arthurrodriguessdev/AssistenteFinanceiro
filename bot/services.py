import requests
from django.conf import settings
from comum.models import Usuario, StatusUsuario, Transacao, TransacaoChoices
from comum.services import get_usuario, calcular_valor_total_despesas
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
            json = {'chat_id': chat_id, 'text': text}
            response = requests.post(URL_ENVIAR_MSG, json=json)
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

        usuario = get_usuario(self.telegram_id)
        if acao is not None and self.callback_query_id is not None:
            if usuario is not None:
                if acao == 'despesa': return self.registrar_despesa(usuario, self.text)
                elif acao == 'faturamento': return self.registrar_faturamento(usuario, self.text)
                elif acao == 'gastos': return self.exibir_gastos()
        else:
            if usuario:

                # Faturamento
                enviou_despesa_faturamento = self.text is not None
                if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_VALOR_FATURAMENTO and                    enviou_despesa_faturamento:
                    usuario.set_status(StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_FATURAMENTO)
                    return self.registrar_faturamento(usuario, self.text)
                
                if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_FATURAMENTO and enviou_despesa_faturamento:
                    usuario.set_status(StatusUsuario.INFORMOU_FATURAMENTO)
                    return self.registrar_faturamento(usuario, self.text)
                
                # Despesa
                if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_VALOR_DESPESA and enviou_despesa_faturamento:
                    usuario.set_status(StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_DESPESA)
                    return self.registrar_despesa(usuario, self.text)
                
                if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_DESPESA and enviou_despesa_faturamento:
                    usuario.set_status(StatusUsuario.INFORMOU_DESPESA)
                    return self.registrar_despesa(usuario, self.text)
                
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
    
    def registrar_despesa(self, usuario, text):
        mensagem_enviar = f'Registrando Despesa'
        TelegramClient.callback(self.callback_query_id)

        if usuario.status == StatusUsuario.AGUARDANDO_MENU:
            usuario.set_status(StatusUsuario.AGUARDANDO_INFORMAR_VALOR_DESPESA)
        
        if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_VALOR_DESPESA:
            mensagem_enviar = f'Informe o valor da despesa, por favor.'
            return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)
        
        if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_DESPESA:
            despesa = str(text)

            if ',' in despesa:
                despesa = despesa.replace(',', '.')
            
            # Registra o faturamento
            transacao = Transacao.objects.create(
                usuario=usuario,
                tipo=TransacaoChoices.DESPESA,
                descricao='',
                registrada_em=datetime.now(),
                valor=float(despesa)
            )

            mensagem_enviar = f'Informe a descrição da despesa.'
            return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)
        
        elif usuario.status == StatusUsuario.INFORMOU_DESPESA:
            try:
                transacao = Transacao.objects.filter(
                    usuario=usuario,
                    tipo=TransacaoChoices.DESPESA
                ).last()

                transacao.descricao = text
                transacao.save()

                usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
                mensagem_enviar = (f'Despesa de R${transacao.valor} registrado com sucesso!\n')
                return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)
            
            except Exception as e:
                usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
                return TelegramClient.enviar_mensagem("Deu erro ao salvar", self.chat_id)
            
    
    def registrar_faturamento(self, usuario, text):
        mensagem_enviar = ''
        TelegramClient.callback(self.callback_query_id)
        
        # Altera o status se acabou de solicitar o registro de faturamento
        if usuario.status == StatusUsuario.AGUARDANDO_MENU:
            usuario.set_status(StatusUsuario.AGUARDANDO_INFORMAR_VALOR_FATURAMENTO)

        if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_VALOR_FATURAMENTO:
            mensagem_enviar = (
                f'Informe seu faturamento mensal. Exemplo válido: 1500.00\n'
                f'OBS: Insira apenas o valor referente ao mês atual. Ele será adicionado ao saldo acumulado do período.'
            )

            return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)
        
        if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_DESCRICAO_FATURAMENTO:
            mensagem_enviar = f'Bota a descrição filhote'
            faturamento = str(text)

            if ',' in faturamento:
                faturamento = faturamento.replace(',', '.')
            
            # Registra o faturamento
            transacao = Transacao.objects.create(
                usuario=usuario,
                tipo=TransacaoChoices.FATURAMENTO,
                descricao='',
                registrada_em=datetime.now(),
                valor=float(faturamento)
            )

            return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)
        
        elif usuario.status == StatusUsuario.INFORMOU_FATURAMENTO:
            try:
                transacao = Transacao.objects.filter(
                    usuario=usuario,
                    tipo=TransacaoChoices.FATURAMENTO
                ).last()

                transacao.descricao = text
                transacao.save()

                usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
                mensagem_enviar = (f'Faturamento de R${transacao.valor} registrado com sucesso!\n')
                return TelegramClient.enviar_mensagem(mensagem_enviar, self.chat_id)
            
            except:
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