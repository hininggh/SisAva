from django.urls import path
from . import views

urlpatterns = [
    path('criar/', views.criar_ou_editar_curso, name='criar_curso'),  # Criação de curso
    path('editar/<int:curso_id>/', views.criar_ou_editar_curso, name='editar_curso'),  # Edição de curso
    path('excluir_curso/<int:curso_id>/', views.excluir_curso, name='excluir_curso'),  # Deletar curso
    path('<int:curso_id>/', views.visualizar_curso, name='visualizar_curso'),  # Visualização de curso
    path('cursos/visitante/<int:curso_id>/', views.visualizar_curso_visitante, name='visualizar_curso_visitante'),
    path('adicionar_relator/<int:curso_id>/', views.adicionar_relator, name='adicionar_relator'),  # Adicionar relator
    path('enviar_ou_substituir_capa/<int:curso_id>/', views.enviar_ou_substituir_capa,
         name='enviar_ou_substituir_capa'), #Envia ou substitui a capa do curso
    path('baixar_capa/<int:curso_id>/', views.baixar_capa, name='baixar_capa'),  # Baixar capa do curso
    path('deletar_capa/<int:curso_id>/', views.deletar_capa, name='deletar_capa'),  # Deletar capa do curso
    path('editar_informacoes/<int:curso_id>/', views.editar_informacoes_complementares, name='editar_informacoes_complementares'),  # Editar informações complementares
    path('gerar_relatorio/<int:curso_id>/', views.gerar_relatorio_geral, name='gerar_relatorio_geral'),  # Gerar relatório geral
    path('atualizar_lista_relatores/<int:curso_id>/', views.atualizar_lista_relatores, name='atualizar_lista_relatores'),
    path('excluir_relator/<int:curso_id>/<int:relator_id>/', views.excluir_relator, name='excluir_relator'),
    path('cursos/<int:curso_id>/visitantes/atualizar/', views.atualizar_lista_visitantes,
         name='atualizar_lista_visitantes'),
    path('cursos/<int:curso_id>/visitantes/adicionar/', views.adicionar_visitante_curso,
         name='adicionar_visitante_curso'),
    path('cursos/<int:curso_id>/visitantes/excluir/<int:visitante_id>/', views.excluir_visitante_curso,
         name='excluir_visitante_curso'),
]


