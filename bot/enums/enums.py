from enum import StrEnum


class TipoMenu(StrEnum):
    PRINCIPAL = "principal"
    FATURAMENTO = "faturamento"
    DESPESA = "despesa"
    RELATORIO = "relatorio"
    CONFIGURACAO = "configuracao"
    CATEGORIA = "categoria"


class TipoAcao(StrEnum):
    # Para identificar qual menu vai chamar
    MENU_DESPESA = "menu_despesa"
    MENU_FATURAMENTO = "menu_faturamento"
    MENU_RELATORIO = "menu_relatorio"
    MENU_CONFIGURACAO = 'menu_configuracao'
    MENU_CATEGORIA = 'menu_categoria'

    # CRUD
    CADASTRO_DESPESA = "cadastro_despesa"
    CADASTRO_FATURAMENTO = "cadastro_faturamento"

    EXCLUSAO_DESPESA = "exclusao_despesa"
    EXCLUSAO_FATURAMENTO = "exclusao_faturamento"

    EXIBIR_DESPESAS = "exibir_despesas"
    EXIBIR_FATURAMENTOS = "exibir_faturamentos"

    RESUMO_MES = "resumo_mes"

    CADASTRO_CATEGORIA = "cadastro_categoria"
    EXCLUSAO_CATEGORIA = "exclusao_categoria"

    # Mais específicas, usadas como parte de uma ação
    MES = "mes"
    REMOVER = "remover"
    CONFIRMAR = "confirmar"
    CANCELAR = "cancelar"