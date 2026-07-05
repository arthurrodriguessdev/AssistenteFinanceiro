from comum.models import Usuario

def get_usuario(telegram_id):
    return Usuario.objects.filter(telegram_id=telegram_id).first() or None

def calcular_valor_total_despesas(despesas):
    valor = 0
    for despesa in despesas:
        valor += despesa.valor
        
    return valor