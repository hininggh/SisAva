from django.db import models
from cursos.models import Curso



class IndicadorInfo(models.Model):
    ORGANIZACAO = 'Organização Didático-Pedagógica'
    CORPO_DOCENTE = 'Corpo Docente e Tutorial'
    INFRAESTRUTURA = 'Infraestrutura'

    DIMENSAO_CHOICES = [
        (ORGANIZACAO, 'Organização Didático-Pedagógica'),
        (CORPO_DOCENTE, 'Corpo Docente e Tutorial'),
        (INFRAESTRUTURA, 'Infraestrutura'),
    ]

    nome = models.CharField(max_length=255)
    dimensao = models.CharField(max_length=50, choices=DIMENSAO_CHOICES)
    mensagem_aviso = models.TextField(blank=True)
    tabela_conceitos = models.JSONField()

    def __str__(self):
        return self.nome


class IndicadorMan(models.Model):
    # Referências ao modelo Curso e Usuario por string
    curso = models.ForeignKey('cursos.Curso', on_delete=models.CASCADE)
    indicador_info = models.ForeignKey(IndicadorInfo, on_delete=models.CASCADE)
    NSA = models.BooleanField(default=False)
    nivel_suposto = models.IntegerField(null=True, blank=True)
    data_envio = models.DateTimeField(null=True, blank=True)
    conteudo = models.FileField(upload_to='indicadores/relatorios/', null=True, blank=True)
    usuario_relatorio = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'{self.curso.nome} - {self.indicador_info.nome}'
