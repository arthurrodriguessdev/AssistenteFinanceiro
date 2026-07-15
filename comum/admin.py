from django.contrib import admin
from comum.models import Usuario, Transacao, Categoria

admin.site.register(Usuario)

class TransacaoAdmin(admin.ModelAdmin):
    list_filter = ('usuario', 'tipo',)
    list_display = ('descricao', 'valor', 'tipo', 'usuario')

admin.site.register(Transacao, TransacaoAdmin)

class CategoriaAdmin(admin.ModelAdmin):
    list_filter = ('usuario', 'nome',)
    list_display = ('nome', 'usuario',)
    fieldsets = (
        ("Informações da Categoria", {
            "fields": ( "nome", "usuario", "padrao"),
        }),
    )

admin.site.register(Categoria, CategoriaAdmin)
