from comum.models import *
from comum.services import calcular_valor_total_registros, converter_numero_mes, get_meses_ano

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
    def exibir(usuario, text, tipo_registro, acao=None):
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
            if acao is not None:
                numero_mes = converter_numero_mes(acao)

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

            else:
                usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
                response['status'] = 'erro'
                return response

        return  response
    
    @staticmethod
    def resumo_mes(usuario, acao):
        if usuario.status == StatusUsuario.AGUARDANDO_MENU:
            usuario.set_status(StatusUsuario.AGUARDANDO_MES_RESUMO)
        
        response = {}
        if usuario.status == StatusUsuario.AGUARDANDO_MES_RESUMO:
            response['status'] = 'mostrar_meses'
        
        if usuario.status == StatusUsuario.AGUARDANDO_VER_RESUMO:
            if acao is not None:
                meses = get_meses_ano()
                numero_mes = converter_numero_mes(acao)

                if numero_mes is None:
                    usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
                    response['status'] = 'erro'
                    return response
            
                registros = Transacao.objects.filter(usuario=usuario)

                if numero_mes != 0:
                    registros = registros.filter(registrada_em__month=numero_mes)

                valor_faturamento = calcular_valor_total_registros(registros.filter(tipo=TransacaoChoices.FATURAMENTO))
                valor_despesa = calcular_valor_total_registros(registros.filter(tipo=TransacaoChoices.DESPESA))
                quantidade_despesa = registros.filter(tipo=TransacaoChoices.DESPESA).count()
                quantidade_faturamento = registros.filter(tipo=TransacaoChoices.FATURAMENTO).count()

                saldo = 0
                if valor_despesa and valor_faturamento:
                    saldo = valor_faturamento - valor_despesa

                if registros.exists():
                    response['valor_faturamento'] = valor_faturamento
                    response['valor_despesa'] = valor_despesa
                    response['quantidade_despesa'] = quantidade_despesa
                    response['quantidade_faturamento'] = quantidade_faturamento
                    response['saldo'] = saldo
                    response['status'] = 'mostrar_resumo'
                    response['nome_mes'] = meses[numero_mes]
                else:
                    usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
                    response['status'] = 'erro'
                    return response
        return response