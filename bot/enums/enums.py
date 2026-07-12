from enum import StrEnum


class TipoMenu(StrEnum):
    PRINCIPAL = "principal"
    FATURAMENTO = "faturamento"
    DESPESA = "despesa"
    RELATORIO = "relatorio"


class TipoAcao(StrEnum):
    MENU_DESPESA = "menu_despesa"
    MENU_FATURAMENTO = "menu_faturamento"
    MENU_RELATORIO = "menu_relatorio"

    # CRUD
    CADASTRO_DESPESA = "cadastro_despesa"
    CADASTRO_FATURAMENTO = "cadastro_faturamento"

    EXCLUSAO_DESPESA = "exclusao_despesa"
    EXCLUSAO_FATURAMENTO = "exclusao_faturamento"

    EXIBIR_DESPESAS = "exibir_despesas"
    EXIBIR_FATURAMENTOS = "exibir_faturamentos"

    RESUMO_MES = "resumo_mes"

    # Mais específicas, usadas como parte de uma ação
    MES = "mes"
    REMOVER = "remover"
    CONFIRMAR = "confirmar"
    CANCELAR = "cancelar"