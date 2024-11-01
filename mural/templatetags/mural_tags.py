from django import template
from mural.models import Mural

register = template.Library()

@register.filter
def get_user_message(mensagens, user):
    # Certifica-se de que `mensagens` seja um queryset antes de chamar o filtro
    if hasattr(mensagens, 'filter'):
        return mensagens.filter(usuario=user).first()
    return None
