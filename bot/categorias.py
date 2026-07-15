import logging
from comum.models import StatusUsuario, Categoria

logger = logging.getLogger('__name__')

class CategoriaService():
    @staticmethod
    def criar(usuario, nome_categoria=None):
        response = {}
        if usuario.status == StatusUsuario.AGUARDANDO_MENU:
            usuario.set_status(StatusUsuario.AGUARDANDO_INFORMAR_NOME_CATEGORIA_CADASTRO)
        
        if usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_NOME_CATEGORIA_CADASTRO and nome_categoria:
            nova_categoria = Categoria()
            nova_categoria.nome = nome_categoria
            nova_categoria.usuario = usuario
            nova_categoria.padrao = False

            try:
                nova_categoria.full_clean()
                nova_categoria.save()
                response['status'] = 'sucesso'
                return response

            except Exception:
                logger.exception('Erro ao registrar uma nova categoria.')
                response['status'] = 'erro'
                return response

        elif usuario.status == StatusUsuario.AGUARDANDO_INFORMAR_NOME_CATEGORIA_CADASTRO:
            response['status'] = 'solicitar_nome'
        
        return response
    
    @staticmethod
    def excluir():
        ...