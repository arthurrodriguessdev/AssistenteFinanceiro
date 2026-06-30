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