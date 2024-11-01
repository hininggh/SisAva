from django.db import models



class Curso(models.Model):
    nome = models.CharField(max_length=255)
    inscricao = models.TextField(blank=True)
    detalhes = models.TextField(blank=True)
    informacoes_complementares = models.TextField(blank=True)
    capa = models.FileField(upload_to='cursos/capas/', null=True, blank=True)
    privilegios = models.BooleanField(default=False)

    # Referência ao modelo Usuario como string
    relatores = models.ManyToManyField('usuarios.Usuario', related_name='cursos', blank=True)
    criador = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE, related_name='cursos_criados')

    def __str__(self):
        return self.nome
