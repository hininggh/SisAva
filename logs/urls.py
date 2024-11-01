from django.urls import path
from . import views

urlpatterns = [
    path('<int:curso_id>/logs/', views.visualizar_logs, name='visualizar_logs'),
    path('<int:curso_id>/logs/nsa/', views.filtrar_por_nsa, name='filtrar_por_nsa'),
    path('<int:curso_id>/logs/conceito/', views.filtrar_por_conceito, name='filtrar_por_conceito'),
    path('<int:curso_id>/logs/relatorio/', views.filtrar_por_relatorio, name='filtrar_por_relatorio'),
]
