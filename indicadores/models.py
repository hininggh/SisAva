from django.db import models
from django.utils.timezone import now
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
    # Relacionamento com o curso e informações do indicador
    curso = models.ForeignKey('cursos.Curso', on_delete=models.CASCADE)
    indicador_info = models.ForeignKey(IndicadorInfo, on_delete=models.CASCADE)

    # Propriedades adicionais
    NSA = models.BooleanField(default=False)
    nivel_suposto = models.IntegerField(null=True, blank=True)

    # Documento editável via TinyMCE
    documento_tinymce = models.TextField(blank=True, null=True)
    em_edicao = models.BooleanField(default=False)  # Indica se o documento está em edição
    usuario_editando = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_em_edicao'
    )
    edicao_inicio = models.DateTimeField(null=True, blank=True)  # Timestamp do início da edição

    def __str__(self):
        return f'{self.curso.nome} - {self.indicador_info.nome}'


class RelatorioPDF(models.Model):
    # Relacionamento com IndicadorMan
    indicador = models.ForeignKey(IndicadorMan, on_delete=models.CASCADE, related_name='relatorios_pdfs')
    arquivo = models.FileField(upload_to='indicadores/relatorios/')
    data_upload = models.DateTimeField(auto_now_add=True)
    usuario_upload = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='relatorios_enviados'
    )

    def __str__(self):
        return f'Relatório {self.id} - {self.indicador.indicador_info.nome}'
