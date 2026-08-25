from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Usuário do FutCarreira. Estende o usuário padrão do Django para permitir
    customizações futuras (avatar, preferências, etc.) sem precisar migrar
    de model de usuário mais tarde.
    """

    tema_preferido = models.CharField(
        max_length=20,
        choices=[("dark", "Escuro"), ("light", "Claro")],
        default="dark",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username
