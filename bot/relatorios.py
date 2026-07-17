from comum.models import StatusUsuario, Transacao, TransacaoChoices
from comum.services import calcular_valor_total_registros, converter_acao_id, get_meses_ano, calcular_percentual

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
                numero_mes = converter_acao_id(acao)

                if numero_mes is None:
                    usuario.aguardar_menu()
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
                usuario.aguardar_menu()
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
                numero_mes = converter_acao_id(acao)

                if numero_mes is None:
                    usuario.aguardar_menu()
                    response['status'] = 'erro'
                    return response
            
                registros = Transacao.objects.filter(usuario=usuario)
                if numero_mes != 0:
                    registros = registros.filter(registrada_em__month=numero_mes)

                faturamentos = registros.filter(tipo=TransacaoChoices.FATURAMENTO)
                despesas = registros.filter(tipo=TransacaoChoices.DESPESA)

                # Campos a serem retornados no dicionário
                valor_faturamento = calcular_valor_total_registros(faturamentos)
                valor_despesa = calcular_valor_total_registros(despesas)
                quantidade_despesa = despesas.count()
                quantidade_faturamento = faturamentos.count()
                percentual = calcular_percentual(valor_faturamento, valor_despesa)
                maior_despesa = despesas.order_by('-valor').first()
                saldo = valor_faturamento - valor_despesa

                if registros.exists():
                    response['valor_faturamento'] = valor_faturamento
                    response['valor_despesa'] = valor_despesa
                    response['quantidade_despesa'] = quantidade_despesa
                    response['quantidade_faturamento'] = quantidade_faturamento
                    response['saldo'] = saldo
                    response['status'] = 'mostrar_resumo'
                    response['nome_mes'] = meses[numero_mes]
                    response['percentual'] = percentual
                    response['maior_despesa'] = None

                    if maior_despesa:
                        response['maior_despesa'] = maior_despesa
                        
                else:
                    usuario.aguardar_menu()
                    response['status'] = 'erro'
                    return response
        return response