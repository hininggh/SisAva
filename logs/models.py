from django.db import models

# Corrigir as referências usando strings
class Log(models.Model):
    ACOES_CHOICES = [
        (1, "Cadastro de Relator"),
        (2, "Edição de Relator"),
        (3, "Cadastro de Visitante"),
        (4, "Edição de Visitante"),
        (5, "Criação de Curso"),
        (6, "Edição de Curso"),
        (7, "Edição de Informações Complementares"),
        (8, "Envio de Capa"),
        (9, "Substituição de Capa"),
        (10, "Deleção de Capa"),
        (11, "Postagem de Mensagem"),
        (12, "Envio de Relatório"),
        (13, "Substituição de Relatório"),
        (14, "Deleção de Relatório"),
        (15, "Edição de Conceito"),
        (16, "Aplicação NSA"),
        (17, "Desapliação do NSA"),
        (18, "Adição de Acesso de Relator ao Curso"),
        (19, "Remoção de Acesso ao Curso"),
        (20, "Adição de Acesso a Visitante ao Curso"),
        (21, "Remoção de Acesso de Visitante ao Curso"),
        (22, "Edição mensagem"),
        (23, "Deleção mensagem"),
        (24, "Deleção visitante"),
    ]

    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE)  # Referência ao modelo Usuario
    visitante = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='logs_visitante')
    curso = models.ForeignKey('cursos.Curso', on_delete=models.CASCADE, null=True, blank=True)  # Permitir nulo
    indicadorMan = models.ForeignKey('indicadores.IndicadorMan', on_delete=models.SET_NULL, null=True, blank=True)  # Referência ao modelo IndicadorMan
    data_hora = models.DateTimeField(auto_now_add=True)
    acao = models.PositiveIntegerField(choices=ACOES_CHOICES)  # Campo inteiro com escolhas predefinidas

    def __str__(self):
        acao_str = dict(self.ACOES_CHOICES).get(self.acao, "Ação Desconhecida")
        return f'{acao_str} - {self.curso.nome if self.curso else "Sem curso"} ({self.data_hora})'
