from django.db import models


class StatusUsuario(models.IntegerChoices):
    # Geral
    AGUARDANDO_MENU = 1, "Aguardando Menu"
    AGUARDANDO_BOAS_VINDAS = 2, "Aguardando Boas-vindas"

    # Faturamento
    AGUARDANDO_INFORMAR_VALOR_FATURAMENTO = 3, "Aguardando Informar Valor Faturamento"
    AGUARDANDO_INFORMAR_DESCRICAO_FATURAMENTO = 4, "Aguardando Informar Descrição Faturamento"
    INFORMOU_FATURAMENTO = 5, "Informou Despesa"

    # Despesa
    AGUARDANDO_INFORMAR_VALOR_DESPESA = 6, "Aguardando Informar Despesa"
    AGUARDANDO_INFORMAR_DESCRICAO_DESPESA = 7, "Aguardando Informar Descrição Despesa"
    INFORMOU_DESPESA = 8, "Informou Despesa"
    

class TransacaoChoices(models.IntegerChoices):
    FATURAMENTO = 1, "Faturamento"
    DESPESA = 2, "Despesa"


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


class Transacao(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='transacoes')
    tipo = models.IntegerField(choices=TransacaoChoices)
    descricao = models.CharField(max_length=250)
    registrada_em = models.DateTimeField(auto_now_add=True)
    valor = models.DecimalField(decimal_places=2, max_digits=10)

    class Meta:
        verbose_name='Transação'
        verbose_name_plural='Transações'

    def __str__(self):
        return f'{self.descricao} - R$ {self.valor}'