from django.db import models


class StatusUsuario(models.IntegerChoices):
    AGUARDANDO_MENU = 1, "Aguardando Menu"
    AGUARDANDO_BOAS_VINDAS = 2, "Aguardando Boas-vindas"

    AGUARDANDO_INFORMAR_FATURAMENTO = 3, "Aguardando Informar Faturamento"
    INFORMOU_FATURAMENTO = 4, "Informou Despesa"

    AGUARDANDO_INFORMAR_DESPESA = 5, "Aguardando Informar Despesa"
    INFORMOU_DESPESA = 6, "Informou Despesa"
    

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

    def __str__(self):
        return f'{self.descricao} - R$ {self.valor}'