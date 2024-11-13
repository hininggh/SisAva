from django.urls import path
from . import views

urlpatterns = [
    path('gerenciar-logs/', views.gerenciar_logs, name='gerenciar_logs'),
    path('logs/filtrar/', views.filtrar_logs, name='filtrar_logs'),
]
