from django.contrib.auth import authenticate, login, logout  # Importa os métodos de autenticação
from django.http import HttpResponseForbidden  # Certifique-se de importar VisitanteForm
from django.contrib.auth.decorators import login_required
from cursos.models import Curso
from django.shortcuts import render, redirect, get_object_or_404
from .models import Usuario
from .forms import UsuarioForm, CadastroVisitanteForm, AdicionarCursosForm
import json
from django.db.models import Q  # Adicione esta importação
from django.http import JsonResponse
from django.urls import reverse
from django.contrib import messages
from logs.views import registrar_acao_log


# Verifica se o usuário é um relator
def is_relator(user):
    return user.is_authenticated and user.tipo == 'relator'

# Página de Perfil (Edição para Relator, Visualização para Visitante)
@login_required
def perfil_view(request):
    if request.user.tipo == 'relator':  # Verifica se o usuário é um relator
        if request.method == 'POST':
            form = UsuarioForm(request.POST, instance=request.user)
            senha = request.POST.get('senha')
            confirmar_senha = request.POST.get('confirmar_senha')
            print(form.errors)
            print('ppassou')# Adicione esta linha para imprimir os erros do formulário
            if form.is_valid():
                usuario = form.save(commit=False)

                # Verificar se as senhas foram fornecidas e são iguais
                if senha and confirmar_senha:
                    if senha == confirmar_senha:
                        usuario.set_password(senha)
                    else:
                        form.add_error('confirmar_senha', "As senhas não coincidem.")
                        return render(request, 'usuarios/perfil.html', {'form': form, 'is_relator': True})

                usuario.save()
                return redirect('perfil')
        else:
            form = UsuarioForm(instance=request.user)

        return render(request, 'usuarios/perfil.html', {'form': form, 'is_relator': True})
    else:  # Se o usuário for um visitante
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
            usuario.tipo = Usuario.RELATOR  # Define o tipo de usuário como relator
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
def cadastrar_ou_editar_visitante(request, visitante_id=None, curso_id=None):
    if not request.user.is_authenticated or request.user.tipo != Usuario.RELATOR:
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    visitante = None

    if visitante_id:
        # Código para edição, incluindo a definição de `curso_form`
        visitante = get_object_or_404(Usuario, id=visitante_id, tipo=Usuario.VISITANTE)
        form = CadastroVisitanteForm(request.POST or None, instance=visitante)
        #remove o campo de senha
        form.fields.pop('senha', None)
        form.fields.pop('confirmar_senha', None)
        # Filtra os cursos disponíveis para o relator e marca os cursos que o visitante já tem
        cursos_disponiveis = Curso.objects.filter(Q(criador=request.user) | Q(privilegios=True))
        curso_form = AdicionarCursosForm(request.POST or None, instance=visitante)
        curso_form.fields['cursos_acesso'].queryset = cursos_disponiveis
        curso_form.initial['cursos_acesso'] = visitante.cursos_acesso.all()
    else:
        # Código para criação
        form = CadastroVisitanteForm(request.POST or None)
        curso_form = None  # Não inicializa `curso_form` no modo de criação
        if request.method == 'POST':
            if form.is_valid():
                visitante = form.save(commit=False)
                visitante.tipo = Usuario.VISITANTE
                visitante.set_password(form.cleaned_data['senha'])
                visitante.save()
                # Registra a ação de criação de visitante no log
                registrar_acao_log(
                    usuario=request.user,
                    curso=None,
                    acao= 3, visitante = visitante
                )
                if curso_id:
                    return redirect('cadastrar_ou_editar_visitante', curso_id=curso_id)
                else:
                    return redirect('cadastrar_ou_editar_visitante', visitante_id=visitante.id)

    if request.method == 'POST':
        if form.is_valid() and curso_form.is_valid():
            visitante = form.save(commit=False)
            visitante.tipo = Usuario.VISITANTE
            if 'senha' in form.cleaned_data and form.cleaned_data['senha']:
                visitante.set_password(form.cleaned_data['senha'])
            visitante.save()
            # Registra a ação de edição do visitante no log
            registrar_acao_log(
                usuario=request.user,
                curso=None,
                acao= 4, visitante = visitante
            )
            cursos_disponiveis = Curso.objects.filter(Q(criador=request.user) | Q(privilegios=True))
            visitante.cursos_acesso.set(curso_form.cleaned_data['cursos_acesso'].intersection(cursos_disponiveis))

            messages.success(request, "Visitante salvo com sucesso.")

            if curso_id:
                return redirect('editar_curso', curso_id=curso_id)
            else:
                return redirect('gerenciarvisitantes')
        else:
            messages.error(request, "Por favor, corrija os erros abaixo.")

    return render(request, 'usuarios/cadastrovisitante.html', {
        'form': form,
        'curso_form': curso_form,
        'visitante': visitante,
    })





@login_required
def excluir_visitante(request, visitante_id):
    visitante = get_object_or_404(Usuario, id=visitante_id, tipo=Usuario.VISITANTE)

    # Verifique se o visitante tem algum curso em sua lista de acesso
    cursos_acesso = visitante.cursos_acesso.all()
    if cursos_acesso.exists():
        # Itere por cada curso na lista de acesso do visitante
        for curso in cursos_acesso:
            # Verifique se o usuário logado não é o criador do curso ou não tem privilégios como relator
            if curso.criador != request.user and (request.user not in curso.relatores.all() or not curso.privilegios):
                # Se o usuário logado não tiver permissão, negue a exclusão
                messages.error(request, "Você não tem permissão para excluir este visitante, pois ele está vinculado a cursos em que você não é o criador ou não tem privilégios como relator.")
                return redirect('gerenciarvisitantes')

    if request.method == "GET":
        # Registra a ação de exclusão do visitante no log antes da exclusão
        registrar_acao_log(
            usuario=request.user,
            curso=None,  # Não há curso associado para exclusão do visitante
            acao= 24
        )

        visitante.delete()
        messages.success(request, f"O visitante {visitante.nome} foi excluído com sucesso.")

    return redirect('gerenciarvisitantes')







@login_required
def gerenciarvisitantes(request):
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