from django.urls import path
from . import views



urlpatterns = [
    path('<int:curso_id>/<int:indicador_id>/', views.visualizar_indicador, name='visualizar_indicador'),
    path('<int:curso_id>/<int:indicador_id>/enviar_ou_substituir_relatorio/', views.enviar_ou_substituir_relatorio,
         name='enviar_ou_substituir_relatorio'),
    path('<int:relatorio_id>/baixar_relatorio/', views.baixar_relatorio, name='baixar_relatorio_pdf'),
    path('<int:relatorio_id>/deletar_relatorio/', views.deletar_relatorio, name='deletar_relatorio_pdf'),
    path('<int:curso_id>/<int:indicador_id>/aplicar_nivel_suposto/', views.aplicar_nivel_suposto,
         name='aplicar_nivel_suposto'),
    path('<int:curso_id>/<int:indicador_id>/aplicar_nsa/', views.aplicar_nsa, name='aplicar_nsa'),
    path('<int:curso_id>/<int:indicador_id>/remover_nsa/', views.remover_nsa, name='remover_nsa'),
    path('indicadores/visitante/<int:curso_id>/<int:indicador_id>/', views.visualizar_indicador_visitante,
         name='visualizar_indicador_visitante'),
    path('analise-dados/', views.analise_dados, name='analise_dados'),
    path('processar-indicadores/', views.processar_indicadores, name='processar_indicadores'),
    path('graficos/nuvem-palavras/', views.exibir_graficos, name='exibir_graficos'),
    path('graficos/expressao/', views.exibir_graficos_expressao, name='exibir_graficos_expressao'),
    path('<int:curso_id>/<int:indicador_id>/relatorio/<int:relatorio_id>/deletar/', views.deletar_relatorio,
         name='deletar_relatorio'),
    path('curso/<int:curso_id>/indicador/<int:indicador_id>/baixar_todos_pdfs/', views.baixar_todos_pdfs,
         name='baixar_todos_pdfs'),
    path('documento/<int:indicador_id>/', views.gerenciar_documento_compartilhado, name='gerenciar_documento_compartilhado'),
    path('documento/<int:indicador_id>/sair/', views.sair_documento_compartilhado, name='sair_documento_compartilhado'),
]

