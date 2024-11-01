from django.contrib.auth import authenticate, login, logout  # Importa os métodos de autenticação
from django.http import HttpResponseForbidden
from .forms import UsuarioForm, VisitanteForm  # Certifique-se de importar VisitanteForm
from .models import Usuario
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from cursos.models import Curso






# Verifica se o usuário é um relator
def is_relator(user):
    return user.is_authenticated and user.tipo == 'relator'

# Página de Perfil (Edição para Relator, Visualização para Visitante)
@login_required
def perfil_view(request):
    if is_relator(request.user):
        # Se for relator, permite a edição do perfil
        if request.method == 'POST':
            form = UsuarioForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                return redirect('perfil')
        else:
            form = UsuarioForm(instance=request.user)
        return render(request, 'usuarios/perfil.html', {'form': form, 'is_relator': True})
    else:
        # Se for visitante, apenas visualiza o perfil
        return render(request, 'usuarios/perfil.html', {'usuario': request.user, 'is_relator': False})


# Verifica se o usuário é um relator
def is_relator(user):
    return user.is_authenticated and user.tipo == 'relator'


# Página de Login (não precisa de ajuste)
def login_view(request):
    if request.method == "POST":
        email = request.POST['email']
        senha = request.POST['senha']
        usuario = authenticate(request, email=email, password=senha)
        if usuario is not None:
            login(request, usuario)
            # Redireciona para a view home, que decidirá entre homerelator ou homevisitante
            return redirect('home')
        else:
            return render(request, 'usuarios/login.html', {'error': 'Credenciais inválidas'})
    return render(request, 'usuarios/login.html')


# Cadastro de Relator (não precisa de ajuste)
def cadastro_view(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.set_password(form.cleaned_data['senha'])
            usuario.save()
            # Autenticar e logar automaticamente após o cadastro
            novo_usuario = authenticate(request, email=usuario.email, password=form.cleaned_data['senha'])
            if novo_usuario:
                login(request, novo_usuario)
                return redirect('home')  # Redireciona para a view de home principal
    else:
        form = UsuarioForm()
    return render(request, 'usuarios/cadastro.html', {'form': form})



# Cadastro de Visitante (apenas relatores podem acessar)
@login_required
def cadastro_visitante_view(request):
    if not is_relator(request.user):
        return HttpResponseForbidden("Acesso negado. Apenas relatores podem cadastrar visitantes.")

    if request.method == 'POST':
        form = VisitanteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('gerenciarvisitantes')
    else:
        form = VisitanteForm()
    return render(request, 'usuarios/cadastrovisitante.html', {'form': form})


# Gerenciar Visitantes (apenas relatores podem acessar)
@login_required
def gerenciar_visitantes_view(request):
    if not is_relator(request.user):
        return HttpResponseForbidden("Acesso negado. Apenas relatores podem gerenciar visitantes.")

    visitantes = Usuario.objects.filter(tipo='visitante')
    return render(request, 'usuarios/gerenciarvisitantes.html', {'visitantes': visitantes})





@login_required
def home(request):
    usuario = request.user

    if usuario.tipo == 'relator':
        # Define o contexto para o relator
        cursos_criados = Curso.objects.filter(criador=usuario)
        cursos_participante = Curso.objects.filter(relatores=usuario).exclude(criador=usuario)
        context = {
            'cursos_criados': cursos_criados,
            'cursos_participante': cursos_participante
        }
        return render(request, 'cursos/homerelator.html', context)

    elif usuario.tipo == 'visitante':
        # Define o contexto para o visitante
        cursos_acesso = Curso.objects.filter(visitantes=usuario)
        context = {
            'cursos_acesso': cursos_acesso,
            'usuario': usuario
        }
        return render(request, 'cursos/homevisitante.html', context)

    # Redireciona ao login se o tipo de usuário for inesperado
    return redirect('login')



# Logout do Usuário
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')