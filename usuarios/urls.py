from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('home/', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('cadastro/', views.cadastro_view, name='cadastro'),
    path('cadastrar_ou_editar_visitante/', views.cadastrar_ou_editar_visitante, name='cadastrar_ou_editar_visitante'),
    path('/<int:visitante_id>/', views.cadastrar_ou_editar_visitante,
         name='cadastrar_ou_editar_visitante'),
    path('cadastrar_ou_editar_visitante/<int:curso_id>/<int:visitante_id>/', views.cadastrar_ou_editar_visitante,
         name='cadastrar_ou_editar_visitante'),
    path('excluir_visitante/<int:visitante_id>/', views.excluir_visitante, name='excluir_visitante'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('adicionar_curso_visitante/<int:visitante_id>/', views.adicionar_curso_visitante, name='adicionar_curso_visitante'),
    path('gerenciarvisitantes/', views.gerenciarvisitantes, name='gerenciarvisitantes'),

]
