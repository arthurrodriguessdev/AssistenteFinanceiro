from django.contrib import admin
from comum.models import Usuario, Transacao, Categoria
from comum.forms import UsuarioForm


class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'chat_id', 'telegram_id', 'status', 'ativo',)
    list_filter = ('ativo',)
    fieldsets = (
        ("Informações Pessoais", {"fields": ("nome", "sobrenome")}),
        ("Informações Adicionais", {"fields": ("chat_id", "telegram_id", "status", "ativo")}),
    )

    form = UsuarioForm
admin.site.register(Usuario, UsuarioAdmin)


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