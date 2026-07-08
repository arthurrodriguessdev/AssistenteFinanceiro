from comum.models import Usuario
from decimal import Decimal, InvalidOperation
import logging

logger = logging.getLogger(__name__)

def get_usuario(telegram_id):
    return Usuario.objects.filter(telegram_id=telegram_id).first() or None

def calcular_valor_total_despesas(despesas):
    valor = 0
    for despesa in despesas:
        valor += despesa.valor
        
    return valor

def converter_valor_decimal(valor_converter):
    try:
        valor_converter = Decimal(valor_converter)
        return valor_converter
    
    except InvalidOperation:
        logger.exception(f"Erro ao converter o valor R$ {valor_converter}")
        return None