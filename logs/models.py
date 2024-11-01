from django.db import models

# Corrigir as referências usando strings
class Log(models.Model):
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE)  # Referência ao modelo Usuario usando string
    curso = models.ForeignKey('cursos.Curso', on_delete=models.CASCADE)  # Referência ao modelo Curso usando string
    data_hora = models.DateTimeField(auto_now_add=True)
    acao = models.CharField(max_length=255)
    indicadorMan = models.ForeignKey('indicadores.IndicadorMan', on_delete=models.SET_NULL, null=True, blank=True)  # Referência ao modelo IndicadorMan usando string

    def __str__(self):
        return f'{self.acao} - {self.curso.nome} ({self.data_hora})'
