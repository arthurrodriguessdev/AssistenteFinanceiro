from django.contrib import admin
from comum.models import Usuario, Transacao

admin.site.register(Usuario)

class TransacaoAdmin(admin.ModelAdmin):
    list_filter = ('usuario', 'tipo',)
    list_display = ('descricao', 'valor', 'tipo', 'usuario')

admin.site.register(Transacao, TransacaoAdmin)
