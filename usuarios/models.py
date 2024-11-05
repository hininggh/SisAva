from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class UsuarioManager(BaseUserManager):
    def create_user(self, email, nome, senha=None):
        if not email:
            raise ValueError('O usuário deve ter um endereço de email')
        user = self.model(email=self.normalize_email(email), nome=nome)
        user.set_password(senha)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nome, senha):
        user = self.create_user(email=email, nome=nome, senha=senha)
        user.is_admin = True
        user.save(using=self._db)
        return user


from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class Usuario(AbstractBaseUser):
    # Tipos de usuário
    RELATOR = 'relator'
    VISITANTE = 'visitante'

    TIPO_USUARIO_CHOICES = [
        (RELATOR, 'Relator'),
        (VISITANTE, 'Visitante'),
    ]

    nome = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20, blank=True)
    titulacao = models.CharField(max_length=255, blank=True)  # Somente para relatores
    funcao = models.CharField(max_length=255, blank=True)  # Função desempenhada (somente relatores)
    instituicao = models.CharField(max_length=255, blank=True)  # Somente visitantes
    tipo = models.CharField(max_length=10, choices=TIPO_USUARIO_CHOICES)
    data_inicial = models.DateTimeField(null=True, blank=True)  # Para visitantes
    data_final = models.DateTimeField(null=True, blank=True)  # Para visitantes
    cursos_acesso = models.ManyToManyField('cursos.Curso', blank=True, related_name='visitantes')  # Adiciona lista de cursos para visitantes
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome']

    def __str__(self):
        return self.nome

    @property
    def is_staff(self):
        return self.is_admin