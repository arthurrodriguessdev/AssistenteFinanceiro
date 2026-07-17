import logging
from comum.models import StatusUsuario, Categoria
from comum.services import converter_acao_id

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
    def excluir(usuario, acao):
        response = {}
        primeira_acao = False
        if usuario.status == StatusUsuario.AGUARDANDO_MENU:
            primeira_acao = True
            usuario.set_status(StatusUsuario.AGUARDANDO_EXCLUIR_CATEGORIA)

        if usuario.status == StatusUsuario.AGUARDANDO_EXCLUIR_CATEGORIA and acao:
            response['status'] = 'mostrar_confirmacao'
            id_categoria = converter_acao_id(acao)

            if not id_categoria:
                
                response['status'] = 'erro'
                return response
            
            try:
                categoria = Categoria.objects.get(pk=id_categoria)
                response['categoria'] = categoria
                usuario.set_status(StatusUsuario.CONFIRMOU_CANCELOU_EXCLUSAO_CATEGORIA)

            except Categoria.DoesNotExist:
                response['status'] = 'erro'
                return response
            
        elif usuario.status == StatusUsuario.AGUARDANDO_EXCLUIR_CATEGORIA:
            response['status'] = 'mostrar_categorias'

        elif usuario.status == StatusUsuario.CONFIRMOU_CANCELOU_EXCLUSAO_CATEGORIA and acao:
            if acao.startswith('confirmar'):
                id_categoria = converter_acao_id(acao)

                if not id_categoria:
                    usuario.set_status(StatusUsuario.AGUARDANDO_MENU)
                    response['status'] = 'erro'
                    return response

                try:
                    Categoria.objects.get(id=id_categoria).delete()
                    response['status'] = 'mostrar_mensagem_excluiu_sucesso'
                    usuario.set_status(StatusUsuario.AGUARDANDO_MENU)

                except Categoria.DoesNotExist:
                    logger.exception('A categoria não existe para ser excluída.')
                    response['status'] = 'erro'
                    usuario.set_status(StatusUsuario.AGUARDANDO_MENU) 

                except Exception:
                    logger.exception('Erro ao tentar excluir a categoria')
                    response['status'] = 'erro'
                    usuario.set_status(StatusUsuario.AGUARDANDO_MENU) 
            else:
                response['status'] = 'mostrar_mensagem_cancelou_operacao'
                usuario.set_status(StatusUsuario.AGUARDANDO_MENU)

        return response