from comum.models import Usuario


class UsuarioService():
    @staticmethod
    def usuario_existe(telegram_id):
        return Usuario.objects.filter(telegram_id=telegram_id).exists()
    
    @staticmethod
    def usuario_esta_ativo(telegram_id):
        return Usuario.objects.filter(telegram_id=telegram_id, ativo=True).exists()
    
    @staticmethod
    def criar_usuario(telegram_id, chat_id, first_name, last_name):
        novo_usuario = None

        try:
            novo_usuario = Usuario()
            novo_usuario.telegram_id = telegram_id
            novo_usuario.chat_id = chat_id
            novo_usuario.nome = first_name
            novo_usuario.sobrenome = last_name
            novo_usuario.ativo = False
            novo_usuario.save()
            return novo_usuario

        except:
            return novo_usuario