from enum import StrEnum


class TipoMenu(StrEnum):
    PRINCIPAL = "principal"
    FATURAMENTO = "faturamento"
    DESPESA = "despesa"
    RELATORIO = "relatorio"