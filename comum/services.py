import logging
from decimal import Decimal, InvalidOperation
from comum.models import Usuario, Categoria, Transacao

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
    
    except ValueError:
        logger.exception(f'Erro ao converter: {valor_converter}')
        return None

def converter_acao_id(acao):
    """
    Função que pega somente a parte numérica (id) nos padrões:
    - categoria_12
    - mes_1
    - transacao_4
    """
    if acao is not None:
        acao = acao.split('_')
        numero_id = acao[1]
        numero_id = converter_valor_inteiro(numero_id)
        return numero_id
    
    return None

def calcular_percentual(total, parcial):
    """
    Calcula o percentual entre dois valores.
    
    Exemplo:
    Total = 5.000 | Parcial = 2.500
    Resultado = 50%
    """

    if total == 0:
        return 0
    return (parcial * 100) / total

def get_categorias_usuario(usuario):
    categorias = usuario.categorias.all() or None
    return categorias

def get_categorias_padrao():
    return Categoria.objects.filter(usuario__isnull=True, padrao=True)

def get_todas_categorias_usuario(usuario):
    """
    Retorna:
    - Todas categorias cadastradas pelo usuário; E
    - Categorias padrão do sistema
    """
    categorias_usuario = get_categorias_usuario(usuario)
    categorias_padrao = get_categorias_padrao()
    if categorias_usuario is not None:
        return (categorias_usuario | categorias_padrao).distinct()
    return categorias_padrao

def get_ultima_transacao(usuario, tipo_transacao):
    return Transacao.objects.filter( usuario=usuario, tipo=tipo_transacao).last()