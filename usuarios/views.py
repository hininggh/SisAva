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
def cadastrar_ou_editar_visitante(request, visitante_id=None, curso_id=None):
    # Verifica se o usuário atual é um relator e está autenticado
    if not request.user.is_authenticated or request.user.tipo != Usuario.RELATOR:
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')  # Redireciona para a página inicial ou outra página de acesso restrito

    visitante = None
    if visitante_id:
        # Edição de visitante existente
        visitante = get_object_or_404(Usuario, id=visitante_id, tipo=Usuario.VISITANTE)
        form = CadastroVisitanteForm(request.POST or None, instance=visitante)
        curso_form = AdicionarCursosForm(request.POST or None, instance=visitante)
    else:
        # Cadastro de novo visitante
        form = CadastroVisitanteForm(request.POST or None)
        curso_form = AdicionarCursosForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid() and curso_form.is_valid():
            visitante = form.save(commit=False)
            visitante.tipo = Usuario.VISITANTE
            visitante.set_password(form.cleaned_data['senha'])  # Define a senha para o visitante
            visitante.save()

            # Salva os cursos associados, limitando àqueles que o relator pode gerenciar
            cursos_disponiveis = Curso.objects.filter(
                Q(criador=request.user) | Q(privilegios=True)
            )
            visitante.cursos_acesso.set(curso_form.cleaned_data['cursos_acesso'].intersection(cursos_disponiveis))

            messages.success(request, "Visitante salvo com sucesso.")
            # Redireciona para a página adequada, dependendo do contexto
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
def adicionar_curso_visitante(request, visitante_id):
    visitante = get_object_or_404(Usuario, id=visitante_id, tipo=Usuario.VISITANTE)

    if request.method == "POST":
        data = json.loads(request.body)
        curso_id = data.get('curso_id')
        curso = get_object_or_404(Curso, id=curso_id)

        # Adiciona o curso ao visitante
        visitante.cursos_acesso.add(curso)

        # Registra a ação de adição de curso ao visitante no log
        registrar_acao_log(
            usuario=request.user,
            curso=curso,
            acao=f"Curso '{curso.nome}' adicionado ao visitante {visitante.nome}"
        )

        return JsonResponse({'status': 'Curso adicionado com sucesso!', 'curso_nome': curso.nome})

    return JsonResponse({'status': 'Método inválido'}, status=400)


@login_required
def excluir_visitante(request, visitante_id):
    visitante = get_object_or_404(Usuario, id=visitante_id, tipo=Usuario.VISITANTE)

    if request.method == "GET":
        # Registra a ação de exclusão do visitante no log antes da exclusão
        registrar_acao_log(
            usuario=request.user,
            curso=None,  # Não há curso associado para exclusão do visitante
            acao=f"Visitante {visitante.nome} da instituição {visitante.instituicao} excluído"
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