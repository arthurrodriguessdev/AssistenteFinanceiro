from datetime import datetime
class MensagemBot():
    @staticmethod
    def mensagem_exibir_gastos(despesas, valor_total):
        if not despesas.exists():
            return 'Você ainda não possui despesas cadastradas.'
        
        mensagem_enviar = 'Exibição de Gastos:\n\n'
        for despesa in despesas:
            mensagem_enviar += (
                f'R${despesa.valor} - {despesa.descricao}: Registrada em: {despesa.registrada_em.strftime("%d/%m/%Y")} às '
                f'{despesa.registrada_em.strftime("%H:%M:%S")}\n\n'
            )
        
        mensagem_enviar += f'Valor Total: R${valor_total}'
        return mensagem_enviar
    
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