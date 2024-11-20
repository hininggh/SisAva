from django.urls import path
from . import views



urlpatterns = [
    path('<int:curso_id>/<int:indicador_id>/', views.visualizar_indicador, name='visualizar_indicador'),
    path('<int:curso_id>/<int:indicador_id>/enviar_ou_substituir_relatorio/', views.enviar_ou_substituir_relatorio,
         name='enviar_ou_substituir_relatorio'),
    path('<int:curso_id>/<int:indicador_id>/baixar_relatorio/', views.baixar_relatorio, name='baixar_relatorio'),
    path('<int:curso_id>/<int:indicador_id>/deletar_relatorio/', views.deletar_relatorio, name='deletar_relatorio'),
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

]

