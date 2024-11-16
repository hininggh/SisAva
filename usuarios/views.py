from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from cursos.models import Curso
from django.shortcuts import render, redirect, get_object_or_404
from .models import Usuario
from .forms import UsuarioForm, CadastroVisitanteForm, AdicionarCursosForm
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q
from django.http import JsonResponse
from django.contrib import messages
from logs.views import registrar_acao_log
from django.utils import timezone
from django.urls import reverse
import json
from django.db.models.signals import pre_save
from django.dispatch import receiver


# Verifica se o usuário é um relator
def is_relator(user):
    return user.is_authenticated and user.tipo == 'relator'

# Página de Perfil (Edição para Relator, Visualização para Visitante)

@login_required




@login_required
def perfil_view(request):
    if request.user.tipo == 'relator':  # Verifica se o usuário é um relator
        if request.method == 'POST':
            form = UsuarioForm(request.POST, instance=request.user)

            # Executa a verificação da validade do formulário
            if form.is_valid():
                usuario = form.save(commit=False)

                # Verifica se a senha foi preenchida e se é válida
                senha = form.cleaned_data.get('senha')
                if senha:
                    # Se os campos de senha foram preenchidos, execute a verificação
                    if form.errors.get('senha') or form.errors.get('confirmar_senha'):
                        # Se houver erros de senha, renderiza novamente a página com os erros
                        return render(request, 'usuarios/perfil.html', {
                            'form': form,
                            'mostrar_sessao_senha': True  # Mantém a seção de senha aberta
                        })
                    else:
                        # Se a senha for válida, atualiza a senha e mantém o usuário autenticado
                        usuario.set_password(senha)
                        update_session_auth_hash(request, usuario)

                # Salva o usuário e redireciona
                usuario.save()
                print("validou o formulário")
                return redirect('perfil')
            else:
                # Se o formulário for inválido, renderiza novamente com os erros
                return render(request, 'usuarios/perfil.html', {
                    'form': form,
                    'mostrar_sessao_senha': True  # Mantém a seção de senha aberta
                })
        else:
            form = UsuarioForm(instance=request.user)

        return render(request, 'usuarios/perfil.html', {
            'form': form,
            'mostrar_sessao_senha': False
        })
    else:
        return render(request, 'usuarios/perfil.html', {'usuario': request.user})

# Verifica se o usuário é um relator


# Página de Login (não precisa de ajuste)
def login_view(request):
    if request.method == "POST":
        email = request.POST['email']
        senha = request.POST['senha']
        usuario = authenticate(request, email=email, password=senha)

        if usuario is not None:
            # Verifica se o usuário é um visitante
            if usuario.tipo == Usuario.VISITANTE:
                now = timezone.now()
                if usuario.data_final and now > usuario.data_final:
                    # Data atual é depois da data final
                    return render(request, 'usuarios/login.html', {
                        'error': 'Acesso expirado, para voltar a usar o sistema, contate o responsável pela avaliação do curso.'
                    })
                elif usuario.data_inicial and now < usuario.data_inicial:
                    # Data atual é antes da data inicial
                    return render(request, 'usuarios/login.html', {
                        'error': f'Seu acesso será liberado em {usuario.data_inicial.strftime("%d/%m/%Y %H:%M:%S")}.'
                    })

            # Se as datas estiverem corretas ou for um relator, faz o login
            login(request, usuario)
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
    mostrar_sessao_senha = False
    if not request.user.is_authenticated or request.user.tipo != Usuario.RELATOR:
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')

    visitante = None
    if visitante_id:
        visitante = get_object_or_404(Usuario, id=visitante_id, tipo=Usuario.VISITANTE)
        form = CadastroVisitanteForm(request.POST or None, instance=visitante)
        cursos_disponiveis = Curso.objects.filter(Q(criador=request.user) | Q(privilegios=True))
        curso_form = AdicionarCursosForm(request.POST or None, instance=visitante)
        curso_form.fields['cursos_acesso'].queryset = cursos_disponiveis
        curso_form.initial['cursos_acesso'] = visitante.cursos_acesso.all()
    else:
        form = CadastroVisitanteForm(request.POST or None)
        curso_form = None

        mostrar_sessao_senha = True  # Inicialmente, a seção de senha está oculta

    if request.method == 'POST':
        if form.is_valid() and (not curso_form or curso_form.is_valid()):
            visitante = form.save(commit=False)
            visitante.tipo = Usuario.VISITANTE

            senha = form.cleaned_data.get('senha')
            if senha:
                visitante.set_password(senha)

            visitante.save()
            registrar_acao_log(usuario=request.user, curso=None, visitante=visitante,  acao=4)
            if visitante_id:
                messages.success(request, "Visitante editado com sucesso.")
            else:
                messages.success(request, "Visitante cadastrado com sucesso.")

            if curso_form:
                visitante.cursos_acesso.set(curso_form.cleaned_data['cursos_acesso'].intersection(cursos_disponiveis))

            if curso_id:
                return redirect('editar_curso', curso_id=curso_id)
            else:
                return redirect('gerenciarvisitantes')
        else:
            messages.error(request, "Por favor, corrija os erros abaixo.")
            # Mantém a seção de senha aberta se houver erros nos campos de senha
            if form.errors.get('senha') or form.errors.get('confirmar_senha'):
                mostrar_sessao_senha = True

    return render(request, 'usuarios/cadastrovisitante.html', {
        'form': form,
        'curso_form': curso_form,
        'visitante': visitante,
        'data_inicial': visitante.data_inicial.strftime('%Y-%m-%d') if visitante and visitante.data_inicial else None,
        'data_final': visitante.data_final.strftime('%Y-%m-%d') if visitante and visitante.data_final else None,
        'mostrar_sessao_senha': mostrar_sessao_senha
    })







@login_required
def excluir_visitante(request, visitante_id):
    visitante = get_object_or_404(Usuario, id=visitante_id, tipo=Usuario.VISITANTE)

    # Verifique se o visitante tem algum curso em sua lista de acesso
    cursos_acesso = visitante.cursos_acesso.all()
    if cursos_acesso.exists():
        for curso in cursos_acesso:
            if curso.criador != request.user and (request.user not in curso.relatores.all() or not curso.privilegios):
                # Retorna uma resposta JSON com a mensagem de erro
                return JsonResponse({'status': 'error', 'message': "Você não tem permissão para exclusão. O visitante está associado a um curso que você não tem privilégios."})

    if request.method == "GET":
        # Registra a ação de exclusão no log
        registrar_acao_log(usuario=request.user, curso=None, acao=24)
        visitante.delete()
        return JsonResponse({'status': 'success', 'message': f"O visitante {visitante.nome} foi excluído com sucesso."})

    return JsonResponse({'status': 'error', 'message': "Ocorreu um erro ao tentar excluir o visitante."})







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
        return render(request, 'usuarios/homerelator.html', context)

    elif usuario.tipo == 'visitante':
        # Define o contexto para o visitante
        cursos_acesso = Curso.objects.filter(visitantes=usuario)
        context = {
            'cursos_acesso': cursos_acesso,
            'usuario': usuario
        }
        return render(request, 'usuarios/homevisitante.html', context)

    # Redireciona ao login se o tipo de usuário for inesperado
    return redirect('login')



# Logout do Usuário
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')