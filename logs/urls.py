from django.urls import path
from . import views

urlpatterns = [
    path('gerenciarlogs/', views.exibir_logs, name='gerenciarlogs'),
    # View para exibir a página inicial com os seletores
    path('filtrarlogs/', views.filtrar_logs, name='filtrar_logs'),  # View para filtrar e exibir os logs
]

