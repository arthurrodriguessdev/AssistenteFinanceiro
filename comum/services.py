from comum.models import Usuario
from decimal import Decimal, InvalidOperation
import logging

logger = logging.getLogger(__name__)

def get_usuario(telegram_id):
    return Usuario.objects.filter(telegram_id=telegram_id).first() or None

def get_meses_ano():
    MESES = [
        'Todos', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]

    return MESES

def calcular_valor_total_registros(registros):
    valor = 0
    for registro in registros:
        valor += registro.valor
        
    return valor

def converter_valor_decimal(valor_converter):
    try:
        valor_converter = Decimal(valor_converter)
        return valor_converter
    
    except InvalidOperation:
        logger.exception(f"Erro ao converter o valor R$ {valor_converter}")
        return None

def converter_valor_inteiro(valor_converter):
    try:
        valor_converter = int(valor_converter)
        return valor_converter
    
    except:
        logger.exception(f'Erro ao converter: {valor_converter}')
        return None

def converter_numero_mes(acao_mes):
    if acao_mes is not None:
        acao_mes = acao_mes.split('_')
        numero_mes = acao_mes[1]
        numero_mes = converter_valor_inteiro(numero_mes)
        return numero_mes
    
    return None