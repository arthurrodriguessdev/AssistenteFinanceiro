from comum.models import TransacaoChoices


'''
Classe responsável apenas por montar mensagens
padrões (texto) e botões
'''
class MensagemBot():
    @staticmethod
    def mensagem_boas_vindas(usuario, link_pagamento):
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

        return mensagem_enviar 

    @staticmethod
    def mensagem_exibir_meses():
        MESES = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]

        mensagem_enviar = 'Informe o número referente ao mês desejado para consulta:\n\n'
        for numero, nome_mes in enumerate(MESES, 1):
            mensagem_enviar += f'• {numero} - {nome_mes}\n'
        
        return mensagem_enviar

    @staticmethod
    def mensagem_exibir_gastos(despesas, valor_total):
        if not despesas.exists():
            return (
                'Nenhuma despesa foi encontrada.\n\n'
                'Utilize a opção "Cadastrar Despesa" no menu principal para realizar o primeiro registro'
            )
        
        mensagem_enviar = 'Despesas Cadastradas:\n\n'
        for despesa in despesas:
            data = despesa.registrada_em
            mensagem_enviar += (
                f'• {despesa.descricao}\n'
                f'  Valor: R${despesa.valor}\n'
                f'  Data: {data.strftime("%d/%m/%Y")} às {data.strftime("%H:%M")}\n\n'
            )
        
        mensagem_enviar += f'Valor Total: R${valor_total}'
        return mensagem_enviar
    
    @staticmethod
    def mensagem_informar_valor(tipo_transacao):
        if tipo_transacao == TransacaoChoices.FATURAMENTO:
            mensagem_enviar = (
                'Informe o valor do faturamento.\n\n'
                'Exemplo: 1500,00 ou 1500.00.\n\n'
                'Esse valor será registrado como uma receita na sua movimentação financeira')
        else:
            mensagem_enviar = (
                'Informe o valor da despesa.\n\n'
                'Exemplo: 1500,00 ou 1500.00.\n\n'
                'Esse valor será registrado como uma despesa na sua movimentação financeira')
        
        return mensagem_enviar
    
    @staticmethod    
    def mensagem_informar_descricao(tipo_transacao):
        if tipo_transacao == TransacaoChoices.FATURAMENTO:
            mensagem_enviar = (
                'Perfeito! Agora descreva a origem desse faturamento.\n\n'
                'Exemplo: Salário, Freelance, Venda de produto.')
        else:
            mensagem_enviar = (
                'Perfeito! Agora descreva essa despesa.\n\n'
                'Exemplo: Mercado, Conta de luz, Assinatura da Netflix.')
        
        return mensagem_enviar
    
    @staticmethod
    def mensagem_sucesso_registro(tipo_transacao, valor):
        if tipo_transacao == TransacaoChoices.FATURAMENTO:
            mensagem_enviar = (
                'Faturamento registrado com sucesso.\n\n'
                f'Valor: R${valor}')
        else:
            mensagem_enviar = (
                'Despesa registrado com sucesso.\n\n'
                f'Valor: R${valor}')
        
        return mensagem_enviar
    
    '''
    Mensagens de erro
    '''
    @staticmethod
    def mensagem_erro():
        return (
            "Ocorreu um erro inesperado ao processar sua solicitação.\n\n"
            "Tente novamente em alguns instantes."
        )
    
    @staticmethod
    def mensagem_erro_conversao_valor():
        return (
            "Valor inválido.\n\n"
            "O registro foi cancelado e você voltou ao menu principal.\n"
            "Clique novamente em <strong>Faturamento</strong> ou <strong>Despesa</strong> para iniciar um novo registro.\n\n"
            "Exemplos válidos:\n"
            "• 1500\n"
            "• 1500,00\n"
            "• 1500.00"
        )
    
    '''
    Monta o dicionário com a mensagem e os botões do menu
    '''
    @staticmethod
    def mensagem_menu_principal():    
        botoes = [
            [
                {
                    "text": "Cadastrar Despesa",
                    "callback_data": "despesa"
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

        menu = {
            'botoes': botoes,
            'text': (
                'Olá! Como posso ajudar na sua gestão financeira hoje?\n\n'
                'Escolha uma das opções abaixo para começar:'
            )
        }   

        return menu