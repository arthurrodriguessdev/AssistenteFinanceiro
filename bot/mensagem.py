from comum.models import TransacaoChoices
from bot import emojis
from bot.enums.enums import TipoAcao
from comum.services import get_meses_ano

BOTOES_POR_LINHA = 2


class MensagemBot():
    """
    Classe responsável apenas por montar mensagens
    padrões (texto) e botões
    """

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
        MESES = get_meses_ano()

        botoes = []
        linha = []
        for numero, nome in enumerate(MESES):
            linha.append({
                'text': nome,
                'callback_data': f'{TipoAcao.MES}_{numero}'
            })

            if len(linha) == BOTOES_POR_LINHA:
                botoes.append(linha)
                linha = []
        
        if linha:
            botoes.append(linha)

        menu_meses = {
            'botoes': botoes,
            'text': f'Selecione o mês desejado para consulta:\n\n'
        }   

        return menu_meses

    # Formatação e auxílio
    @staticmethod
    def get_tipo_transacao(tipo_transacao) -> str:
        return 'despesa' if tipo_transacao == TransacaoChoices.DESPESA else 'faturamento'
    
    # Relatórios
    @staticmethod
    def mensagem_exibir_registros(registros, valor_total, tipo_registro):
        tipo = MensagemBot.get_tipo_transacao(tipo_registro)
        if not registros:
            return (
                f'Nenhum registro de {tipo} foi encontrado.\n\n'
                f'Utilize a opção "Cadastrar {tipo.capitalize()}" no menu principal para realizar o primeiro registro.'
            )
        
        mensagem_enviar = 'Despesas Cadastradas:\n\n' if tipo == 'despesa' else 'Faturamentos Cadastrados\n\n'
        for registro in registros:
            data = registro.registrada_em
            mensagem_enviar += (
                f'{emojis.EMOJI_ANOTACAO} {registro.descricao.capitalize()}\n'
                f'{emojis.EMOJI_DINHEIRO} Valor: R${registro.valor}\n'
                f'{emojis.EMOJI_DATA} Data: {data.strftime("%d/%m/%Y")} às {data.strftime("%H:%M")}\n\n'
            )
        
        mensagem_enviar += f'<strong>Valor Total:</strong> R${valor_total}'
        return mensagem_enviar
    
    @staticmethod
    def mensagem_resumo_mes(resumo_mes):
        if not resumo_mes['status'] == 'mostrar_resumo':
            return 'Erro Resumo'
        
        valor_faturamento = resumo_mes['valor_faturamento'] 
        valor_despesa = resumo_mes['valor_despesa']
        quantidade_despesa = resumo_mes['quantidade_despesa']
        quantidade_faturamento = resumo_mes['quantidade_faturamento']
        saldo = resumo_mes['saldo']
        nome_mes = resumo_mes['nome_mes']
        percentual = resumo_mes['percentual']
        maior_despesa = resumo_mes['maior_despesa']

        # Trata o nome do mês OU todos
        if nome_mes != 'Todos':
            mensagem_enviar = f'{emojis.EMOJI_DATA} Resumo do Mês de <strong>{nome_mes}</strong>:\n\n'
        else:
            mensagem_enviar = f'{emojis.EMOJI_DATA} Resumo de <strong>Todos os Meses</strong>:\n\n'

        mensagem_enviar += (
            f'{emojis.EMOJI_FATURAMENTO} Faturamento: R$ {valor_faturamento}\n'
            f'{emojis.EMOJI_DESPESA} Despesa: R$ {valor_despesa}\n'
        )

        # Trata o saldo
        if saldo > 0:
            mensagem_enviar += f'{emojis.EMOJI_BOLA_VERDE} Saldo: R$ {saldo}\n\n'

        elif saldo < 0:
            mensagem_enviar += (
                f'{emojis.EMOJI_BOLA_VERMELHA} Saldo: -R$ {abs(saldo)}\n'
                f'{emojis.EMOJI_ATENCAO} <strong>Atenção:</strong> '
                'Suas despesas foram maiores que seus faturamentos neste mês.\n\n'
            )

        else:
            mensagem_enviar += (
                f'{emojis.EMOJI_ATENCAO} Saldo: R$ 0,00\n'
                'Você teve gastos equilibrados neste mês.\n\n'
            )
            
        mensagem_enviar += (
            f'{emojis.EMOJI_RELATORIO} Controle Financeiro:\n'
            f'• <strong>{percentual:.2f}%</strong> do faturamento foi utilizado em despesas.\n\n'
        )

        if maior_despesa:
            mensagem_enviar += (
                f'{emojis.EMOJI_FOGO} Maior Despesa:\n'
                f'• <strong>{maior_despesa.descricao.capitalize()}</strong> - R$ {maior_despesa.valor:.2f}\n\n'
            )

        mensagem_enviar += (
            f'{emojis.EMOJI_ANOTACAO} Lançamentos:\n'
            f'• {quantidade_despesa} despesas\n'
            f'• {quantidade_faturamento} faturamentos'
        )

        return mensagem_enviar

    # Operações CRUD
    @staticmethod
    def mensagem_exibir_registros_exclusao(registros, tipo_registro):
        tipo = MensagemBot.get_tipo_transacao(tipo_registro)

        if not registros:
            return (
                f'Nenhum registro de {tipo} foi encontrado.\n\n'
                f'Utilize a opção "Cadastrar {tipo.capitalize()}" no menu principal para realizar o primeiro registro.'
            )
        
        mensagem_enviar = 'Selecione a despesa a ser excluída:\n\n' if tipo == 'despesa' else 'Selecione o faturamento a ser excluído:\n\n'
        botoes = []
        for registro in registros:
            data = registro.registrada_em
            mensagem_enviar += (
                f'{emojis.EMOJI_ANOTACAO} {registro.descricao.capitalize()}\n'
                f'{emojis.EMOJI_DINHEIRO} Valor: R${registro.valor}\n'
                f'{emojis.EMOJI_DATA} Data: {data.strftime("%d/%m/%Y")} às {data.strftime("%H:%M")}\n\n'
            )

            botoes.append([
                {
                    "text": f"{emojis.EMOJI_LIXEIRA} {registro.descricao.capitalize()}",
                    "callback_data": f"{TipoAcao.REMOVER}_{registro.id}"
                }
            ])
        
        return {'text': mensagem_enviar, 'botoes': botoes}

    @staticmethod
    def mensagem_confirmar_exclusao(registro):
        tipo = 'despesa' if registro.tipo == TransacaoChoices.DESPESA else 'faturamento'
        data = registro.registrada_em
        mensagem_enviar = (
            f'Tem certeza que deseja excluir o registro de {tipo} abaixo?\n\n'
            f'{emojis.EMOJI_ANOTACAO} {registro.descricao.capitalize()}\n'
            f'{emojis.EMOJI_DINHEIRO} Valor: R${registro.valor}\n'
            f'{emojis.EMOJI_DATA} Data: {data.strftime("%d/%m/%Y")} às {data.strftime("%H:%M")}\n\n'
        )

        botoes = []
        botoes.append([
            {
                "text": f"{emojis.EMOJI_SUCESSO} Confirmar",
                "callback_data": f"{TipoAcao.CONFIRMAR}_{registro.pk}"
            }
        ])

        botoes.append([
            {
                "text": f"{emojis.EMOJI_ERRO} Cancelar",
                "callback_data": TipoAcao.CANCELAR
            }
        ])

        return {'text': mensagem_enviar, 'botoes': botoes}

    @staticmethod
    def mensagem_exclusao_confirmada(tipo_registro):
        """
        Retorna 'despesa' ou 'faturamento' verificando o tipo dela
        """
        tipo = 'despesa' if tipo_registro == TransacaoChoices.DESPESA else 'faturamento'
        return (f'{emojis.EMOJI_SUCESSO} O registro de {tipo} foi excluído com sucesso!')
    
    @staticmethod
    def mensagem_exclusao_cancelada(tipo_registro):
        return (f'{emojis.EMOJI_ERRO} A exclusão do registro de {MensagemBot.get_tipo_transacao(tipo_registro)} foi cancelada.')
        
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
    
    '''
    Mensagens de sucesso
    '''
    @staticmethod
    def mensagem_sucesso_registro(tipo_transacao, valor):
        if tipo_transacao == TransacaoChoices.FATURAMENTO:
            mensagem_enviar = (
                f'{emojis.EMOJI_SUCESSO} Faturamento registrado com sucesso.\n\n'
                f'Valor: R${valor}')
        else:
            mensagem_enviar = (
                f'{emojis.EMOJI_SUCESSO} Despesa registrado com sucesso.\n\n'
                f'Valor: R${valor}')
        
        return mensagem_enviar
    
    '''
    Mensagens de erro
    '''
    @staticmethod
    def mensagem_erro():
        return (
            f"{emojis.EMOJI_ERRO} Ocorreu um erro inesperado ao processar sua solicitação.\n\n"
            "Tente novamente em alguns instantes."
        )
    
    @staticmethod
    def mensagem_erro_conversao_valor():
        return (
            f"{emojis.EMOJI_ERRO} Valor inválido.\n\n"
            "O registro foi cancelado e você voltou ao menu principal.\n"
            "Clique novamente em <strong>Faturamento</strong> ou <strong>Despesa</strong> para iniciar um novo registro.\n\n"
            "Exemplos válidos:\n"
            "• 1500\n"
            "• 1500,00\n"
            "• 1500.00"
        )

    @staticmethod
    def mensagem_erro_valor_negativo():
        return (
            f"{emojis.EMOJI_ERRO} Valor inválido. Apenas valores positivos são aceitos.\n\n"
            "O registro foi cancelado e você voltou ao menu principal.\n"
            "Clique novamente em <strong>Faturamento</strong> ou <strong>Despesa</strong> para iniciar um novo registro.\n\n"
            "Exemplos válidos:\n"
            "• 1500\n"
            "• 1500,00\n"
            "• 1500.00"
        )
    
    @staticmethod
    def mensagem_erro_tamanho_valor():
        return (
            f"{emojis.EMOJI_ERRO} O valor informado é muito grande.\n\n"
            "O máximo permitido é R$ 99.999.999,99."
        )

    @staticmethod
    def mensagem_erro_numero_mes():
        return (
            f'{emojis.EMOJI_ERRO} Número inválido.\n\n'
            'A operação foi cancelada e você voltou ao menu principal.\n'
            'Informe um número de <strong>0</strong> a <strong>12</strong> para selecionar o mês.'
        )
    
    # Menus
    @staticmethod
    def mensagem_menu_principal():    
        botoes = [
            [
                {
                    "text": f"{emojis.EMOJI_DESPESA} Despesa",
                    "callback_data": TipoAcao.MENU_DESPESA
                }
            ],
            [
                {
                    "text": f"{emojis.EMOJI_FATURAMENTO} Faturamento",
                    "callback_data": TipoAcao.MENU_FATURAMENTO
                }
            ],
            [
                {
                    "text": f"{emojis.EMOJI_RELATORIO} Relatórios",
                    "callback_data": TipoAcao.MENU_RELATORIO
                }
            ],
        ]

        menu = {
            'botoes': botoes,
            'text': (
                'Olá! Como posso ajudar na sua gestão financeira hoje?\n\n'
                'Escolha uma das opções abaixo para começar:'
            )
        }   

        return menu

    @staticmethod
    def mensagem_menu_faturamento():    
        botoes = [
            [
                {
                    "text": "Cadastrar Faturamento",
                    "callback_data": TipoAcao.CADASTRO_FATURAMENTO
                }
            ],
            [
                {
                    "text": "Excluir Faturamento",
                    "callback_data": TipoAcao.EXCLUSAO_FATURAMENTO
                }
            ],
        ]

        menu = {
            'botoes': botoes,
            'text': (
                f'{emojis.EMOJI_FATURAMENTO} Faturamento\n\n'
                'O que você deseja fazer?'
            )
        }   

        return menu
    
    @staticmethod
    def mensagem_menu_despesa():    
        botoes = [
            [
                {
                    "text": "Cadastrar Despesa",
                    "callback_data": TipoAcao.CADASTRO_DESPESA
                }
            ],
            [
                {
                    "text": "Excluir Despesa",
                    "callback_data": TipoAcao.EXCLUSAO_DESPESA
                }
            ],
        ]

        menu = {
            'botoes': botoes,
            'text': (
                f'{emojis.EMOJI_DESPESA} Despesa\n\n'
                'O que você deseja fazer?'
            )
        }   

        return menu
    
    @staticmethod
    def mensagem_menu_relatorio():    
        botoes = [
            [
                {
                    "text": "Exibir Despesas",
                    "callback_data": TipoAcao.EXIBIR_DESPESAS
                }
            ],
            [
                {
                    "text": "Exibir Faturamentos",
                    "callback_data": TipoAcao.EXIBIR_FATURAMENTOS
                }
            ],
            [
                {
                    'text': 'Resumo do Mês',
                    'callback_data': TipoAcao.RESUMO_MES
                }
            ]
        ]

        menu = {
            'botoes': botoes,
            'text': (
                f'{emojis.EMOJI_RELATORIO} Relatórios\n\n'
                'O que você deseja fazer?'
            )
        }   

        return menu