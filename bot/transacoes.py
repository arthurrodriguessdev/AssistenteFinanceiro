from comum.models import *
from comum.services import calcular_valor_total_registros, converter_valor_inteiro

TRANSACOES_CONFIG = {
    TransacaoChoices.FATURAMENTO : {
        'status_aguardando_mes': StatusUsuario.AGUARDANDO_INFORMAR_MES_FATURAMENTO_EXCLUSAO,
        'status_aguardando_ver': StatusUsuario.AGUARDANDO_VER_FATURAMENTO_EXCLUSAO,
        'status_aguardando_confirmar_exclusao': StatusUsuario.AGUARDANDO_CONFIRMAR_EXCLUSAO_FATURAMENTO,
        'status_confirmou_ou_cancelou_exclusao': StatusUsuario.CONFIRMOU_CANCELOU_EXCLUSAO_FATURAMENTO
        },
    
    TransacaoChoices.DESPESA : {
        'status_aguardando_mes': StatusUsuario.AGUARDANDO_INFORMAR_MES_DESPESA_EXCLUSAO,
        'status_aguardando_ver': StatusUsuario.AGUARDANDO_VER_DESPESA_EXCLUSAO,
        'status_aguardando_confirmar_exclusao': StatusUsuario.AGUARDANDO_CONFIRMAR_EXCLUSAO_DESPESA,
        'status_confirmou_ou_cancelou_exclusao': StatusUsuario.CONFIRMOU_CANCELOU_EXCLUSAO_DESPESA
    }
}


class TransacaoService():
    @staticmethod
    def excluir_registro(tipo_registro, usuario, text, acao=None):
        configuracao = TRANSACOES_CONFIG[tipo_registro]
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

            response['status'] = 'mostrar_registros'
            response['registros'] = registros
            response['valor_total'] = calcular_valor_total_registros(registros)
        
        if usuario.status == configuracao['status_aguardando_confirmar_exclusao']:
            if acao is not None:
                acao = acao.split('_')
                id_registro = acao[1]
                id_registro = converter_valor_inteiro(id_registro)

                if id_registro is None:
                    response['status'] = 'erro'
                    return response
                
                response['status'] = 'mostrar_confirmacao'
                response['registro_excluir'] = Transacao.objects.get(id=id_registro)
        
        if usuario.status == configuracao['status_confirmou_ou_cancelou_exclusao']:
            if acao is not None:
                if acao.startswith('confirmar'):
                    acao = acao.split('_')
                    id_registro = acao[1]

                    id_registro = converter_valor_inteiro(id_registro)
                    usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
                    if id_registro is None:
                        response['status'] = 'erro'
                        return response
                    
                    try:
                        Transacao.objects.get(id=id_registro).delete()
                        response['status'] = 'mostrar_mensagem_excluiu_sucesso'

                    except:
                        response['status'] = 'erro' 
                else:
                    usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
                    response['status'] = 'mostrar_mensagem_cancelou_operacao'

        return response
        