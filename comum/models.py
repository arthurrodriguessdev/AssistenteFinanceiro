from django.db import models


class Usuario(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    chat_id = models.BigIntegerField()
    nome = models.CharField(max_length=100)
    sobrenome = models.CharField(max_length=100, blank=True)
    
    # Este campo diz se o usuário já pagou a assinatura PELO MENOS uma vez
    ativo = models.BooleanField(default=False) 

    def __str__(self):
        return f'{self.nome} {self.sobrenome}'


class Transacao(models.Model):
    TRANSACAO_CHOICES = [
        ('despesa', 'Despesa'),
        ('faturamento', 'Faturamento')
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='transacoes')
    tipo = models.CharField(choices=TRANSACAO_CHOICES)
    descricao = models.CharField(max_length=250)
    registrada_em = models.DateTimeField(auto_now_add=True)
    valor = models.DecimalField(decimal_places=2, max_digits=10)