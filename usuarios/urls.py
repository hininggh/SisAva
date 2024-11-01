from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('home/', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('cadastro/', views.cadastro_view, name='cadastro'),
    path('cadastrovisitante/', views.cadastro_visitante_view, name='cadastrovisitante'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('gerenciarvisitantes/', views.gerenciar_visitantes_view, name='gerenciarvisitantes'),

]
