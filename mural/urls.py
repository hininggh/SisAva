from django.urls import path
from . import views

urlpatterns = [
    path('postar/<int:curso_id>/', views.postar_mensagem, name='postar_mensagem'),
    path('editar/<int:mensagem_id>/', views.editar_mensagem, name='editar_mensagem'),
    path('apagar/<int:mensagem_id>/', views.apagar_mensagem, name='apagar_mensagem'),
    path('atualizar_mural/<int:curso_id>/', views.atualizar_mural, name='atualizar_mural'),
]
