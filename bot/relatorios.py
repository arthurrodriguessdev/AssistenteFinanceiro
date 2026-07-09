from comum.models import *
from comum.services import calcular_valor_total_registros, converter_valor_inteiro

EXIBICAO_CONFIG = {
    TransacaoChoices.FATURAMENTO : {
        'status_aguardando_mes': StatusUsuario.AGUARDANDO_INFORMAR_MES_FATURAMENTO,
        'status_aguardando_ver': StatusUsuario.AGUARDANDO_VER_FATURAMENTO,
        },
    
    TransacaoChoices.DESPESA : {
        'status_aguardando_mes': StatusUsuario.AGUARDANDO_INFORMAR_MES_DESPESA,
        'status_aguardando_ver': StatusUsuario.AGUARDANDO_VER_DESPESA,
    }
}

class Relatorio():
    @staticmethod
    def exibir(usuario, text, tipo_registro):
        """
        Exibe os faturamentos OU as despesas filtradas pelo usuário
        - Filtragem por mês
        - Pode retornar registros de todos os meses
        """
        
        configuracao = EXIBICAO_CONFIG[tipo_registro]
        response = {}
        if usuario.status == StatusUsuario.AGUARDANDO_MENU:
            usuario.set_status(configuracao['status_aguardando_mes'])
        
        if usuario.status == configuracao['status_aguardando_mes']:
            response['status'] = 'mostrar_meses'

        if usuario.status == configuracao['status_aguardando_ver']:
            numero_mes = converter_valor_inteiro(text)

            if numero_mes is None:
                usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
                response['status'] = 'erro'
                return response
            
            registros = Transacao.objects.filter(
                tipo=tipo_registro, 
                usuario=usuario,
            )

            if numero_mes != 0:
                registros = registros.filter(registrada_em__month=numero_mes)

            valor_total = calcular_valor_total_registros(registros)
            if registros.exists():
                response['registros'] = registros
                response['valor_total'] = valor_total
            response['status'] = 'mostrar_registros'

        return  response