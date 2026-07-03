from comum.models import Usuario

def get_usuario(telegram_id):
    return Usuario.objects.filter(telegram_id=telegram_id).first() or None