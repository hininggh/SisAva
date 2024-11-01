from django.db import models

class Mural(models.Model):
    # Referências ao modelo Usuario por string
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE)
    curso = models.ForeignKey('cursos.Curso', on_delete=models.CASCADE)
    mensagem = models.CharField(max_length=400)

    def __str__(self):
        return f'Mural de {self.curso.nome}'
