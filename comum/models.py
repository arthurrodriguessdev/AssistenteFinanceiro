from django.db import models


class StatusUsuario(models.IntegerChoices):
    # Geral (1-50)
    AGUARDANDO_MENU = 1, "Aguardando Menu"
    AGUARDANDO_BOAS_VINDAS = 2, "Aguardando Boas-vindas"

    # Faturamento (51-100)
    AGUARDANDO_INFORMAR_VALOR_FATURAMENTO = 51, "Aguardando Informar Valor Faturamento"
    AGUARDANDO_INFORMAR_DESCRICAO_FATURAMENTO = 52, "Aguardando Informar Descrição Faturamento"
    INFORMOU_FATURAMENTO = 53, "Informou Despesa"

    AGUARDANDO_INFORMAR_MES_FATURAMENTO_EXCLUSAO = 54, "Aguardando Informar Mês Faturamento Exclusão"
    AGUARDANDO_CONFIRMAR_EXCLUSAO_FATURAMENTO = 55, "Aguardando Confirmar Exclusão Faturamento"
    AGUARDANDO_VER_FATURAMENTO_EXCLUSAO = 56, "Aguardando Visualizar Faturamento Exclusão"
    CONFIRMOU_CANCELOU_EXCLUSAO_FATURAMENTO = 57, "Confirmou ou Cancelou Exclusão Faturamento"

    # Despesa (101-150)
    AGUARDANDO_INFORMAR_VALOR_DESPESA = 101, "Aguardando Informar Despesa"
    AGUARDANDO_INFORMAR_DESCRICAO_DESPESA = 102, "Aguardando Informar Descrição Despesa"
    INFORMOU_DESPESA = 103, "Informou Despesa"

    AGUARDANDO_INFORMAR_MES_DESPESA_EXCLUSAO = 104, "Aguardando Informar Mês Despesa Exclusão"
    AGUARDANDO_CONFIRMAR_EXCLUSAO_DESPESA = 105, "Aguardando Confirmar Exclusão Despesa"
    AGUARDANDO_VER_DESPESA_EXCLUSAO = 106, "Aguardando Visualizar Despesa Exclusão"
    CONFIRMOU_CANCELOU_EXCLUSAO_DESPESA = 107, "Confirmou ou Cancelou Exclusão Despesa"

    AGUARDANDO_INFORMAR_CATEGORIA_DESPESA = 108, "Aguardando Informar Categoria Despesa"

    # Relatórios (151-200)
    AGUARDANDO_INFORMAR_MES_DESPESA = 151, "Aguardando Informar Mês Despesa"
    AGUARDANDO_INFORMAR_MES_FATURAMENTO = 152, "Aguardando Informar Mês Faturamento"

    AGUARDANDO_VER_DESPESA = 153, "Aguardando Visualizar Despesa"
    AGUARDANDO_VER_FATURAMENTO = 154, "Aguardando Visualizar Faturamento"
    AGUARDANDO_MES_RESUMO = 155, "Aguardando Mês Resumo"
    AGUARDANDO_VER_RESUMO = 156, "Aguardando Ver Resumo"

    # Categorias (201-250)
    AGUARDANDO_INFORMAR_NOME_CATEGORIA_CADASTRO = 201, "Aguardando Informar Nome Categoria"
    AGUARDANDO_EXCLUIR_CATEGORIA = 202, "Aguardando Excluir Categoria"
    CONFIRMOU_CANCELOU_EXCLUSAO_CATEGORIA = 203, "Confirmou Cancelou Exclusão Categoria"


class TransacaoChoices(models.IntegerChoices):
    FATURAMENTO = 1, "Faturamento"
    DESPESA = 2, "Despesa"


class ObjetoChoices(models.IntegerChoices):
    CATEGORIA = 1, "Categoria"


class Usuario(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    chat_id = models.BigIntegerField()
    nome = models.CharField(max_length=100)
    sobrenome = models.CharField(max_length=100, blank=True)
    status = models.IntegerField(
        choices=StatusUsuario.choices,
        default=StatusUsuario.AGUARDANDO_BOAS_VINDAS
    )
    
    # Este campo diz se o usuário já pagou a assinatura PELO MENOS uma vez
    ativo = models.BooleanField(default=False) 

    class Meta:
        verbose_name='Usuário'
        verbose_name_plural='Usuários'

    def __str__(self):
        return f'{self.nome} {self.sobrenome}'
    
    def set_status(self, status):
        self.status = status
        self.save()

    def aguardar_menu(self):
        self.set_status(StatusUsuario.AGUARDANDO_MENU)


class Categoria(models.Model):
    nome = models.CharField(max_length=100, null=False, blank=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='categorias', null=True, blank=True)
    padrao = models.BooleanField(default=False) # Categorias criadas automaticamente pelo sistema: true e usuario: null

    class Meta:
        verbose_name='Categoria'
        verbose_name_plural='Categorias'
    
    def __str__(self):
        return f'Categoria: {self.nome}'
    

class Transacao(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='transacoes')
    tipo = models.IntegerField(choices=TransacaoChoices)
    descricao = models.CharField(max_length=250, blank=True)
    registrada_em = models.DateTimeField(auto_now_add=True)
    valor = models.DecimalField(decimal_places=2, max_digits=10)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='transacoes', null=True, blank=True)

    class Meta:
        verbose_name='Transação'
        verbose_name_plural='Transações'

    def __str__(self):
        return f'{self.descricao} - R$ {self.valor}'