from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from cursos.models import Curso
from .models import Log
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
User = get_user_model()
# Usar strings para referenciar os modelos




def filtrar_logs(request):
    # Filtrar os cursos que o usuário pode gerenciar
    cursos_usuario = Curso.objects.filter(
        Q(criador=request.user) |
        (Q(relatores=request.user) & Q(privilegios=True))
    ).distinct()
    print(cursos_usuario)
    # Captura os parâmetros de filtragem
    cursos_filtrados = request.GET.getlist('cursos')
    acoes_filtradas = request.GET.getlist('acoes')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    # Busca inicial de todos os logs
    logs = Log.objects.all()

    # Filtragem condicional
    if cursos_filtrados:
        logs = logs.filter(curso__id__in=cursos_filtrados)
    if acoes_filtradas:
        logs = logs.filter(acao__in=acoes_filtradas)
    if data_inicio:
        data_inicio = timezone.datetime.strptime(data_inicio, "%Y-%m-%d")
        logs = logs.filter(data_hora__gte=data_inicio)
    if data_fim:
        data_fim = timezone.datetime.strptime(data_fim, "%Y-%m-%d")
        logs = logs.filter(data_hora__lte=data_fim)

    # Paginação: 30 logs por página
    paginator = Paginator(logs, 30)
    page_number = request.GET.get('page')
    logs_page = paginator.get_page(page_number)

    # Formatando os logs para exibir os nomes corretos
    formatted_logs = []
    for log in logs_page:
        formatted_log = {
            'data_hora': log.data_hora,
            'usuario': log.usuario.nome if log.usuario else "Usuário desconhecido",
            'curso': log.curso.nome if log.curso else "Sem curso",
            'acao': log.get_acao_display(),
            'visitante': log.visitante.nome if log.visitante else "Sem visitante",
            'indicador': log.indicadorMan.indicador_info.nome if log.indicadorMan and log.indicadorMan.indicador_info else "Sem indicador",
        }
        formatted_logs.append(formatted_log)

    context = {
        'logs': formatted_logs,
        'cursos_usuario': cursos_usuario,
        'logs_page': logs_page,
        'acoes_choices': Log.ACOES_CHOICES  # Adicione as opções de ações aqui
    }

    return render(request, 'logs/gerenciarlogs.html', context)



# Função genérica para registrar ações no log
def registrar_acao_log(usuario, curso=None, acao=None, indicador=None, visitante=None):
    """
    Função genérica para registrar ações no sistema de logs.
    - `usuario`: O usuário que realizou a ação.
    - `curso`: O curso associado (opcional).
    - `acao`: O código da ação, deve ser um inteiro conforme definido em ACOES_CHOICES.
    - `indicador`: O IndicadorMan associado (opcional).
    - `visitante`: O visitante associado, se houver (opcional).
    """
    if acao is None:
        raise ValueError("O campo 'acao' é obrigatório e deve ser um código inteiro válido.")

    log = Log(
        usuario=usuario,
        curso=curso,
        data_hora=timezone.now(),
        acao=acao,
        indicadorMan=indicador,
        visitante=visitante  # Novo campo de visitante
    )
    log.save()

# Visualizar os logs relacionados a um curso
@login_required
def gerenciar_logs(request):
    # Obter os cursos que o usuário é criador ou está na lista de relatores com privilégios
    cursos = Curso.objects.filter(
        Q(criador=request.user) | Q(relatores=request.user, privilegios=True)
    ).distinct()

    # Aplicar filtragem com base em parâmetros GET, se fornecidos
    filtro_nsa = request.GET.get('filtro_nsa')
    filtro_conceito = request.GET.get('filtro_conceito')
    filtro_relatorio = request.GET.get('filtro_relatorio')

    logs = Log.objects.all()

    if filtro_nsa:
        logs = logs.filter(tipo='NSA')
    elif filtro_conceito:
        logs = logs.filter(tipo='Conceito')
    elif filtro_relatorio:
        logs = logs.filter(tipo='Relatório')

    return render(request, 'logs/gerenciarlogs.html', {
        'cursos': cursos,
        'logs': logs,
    })

def visualizar_logs(request, curso_id):
    curso = get_object_or_404('cursos.Curso', id=curso_id)  # Referência ao modelo Curso como string
    logs = Log.objects.filter(curso=curso).order_by('-data_hora')  # Ordena pelos mais recentes
    return render(request, 'logs/gerenciarlogs.html', {'logs': logs, 'curso': curso})

# Filtrar logs por NSA (Não se Aplica)
@login_required
def filtrar_por_nsa(request, curso_id):
    curso = get_object_or_404('cursos.Curso', id=curso_id)  # Referência ao modelo Curso como string
    logs = Log.objects.filter(curso=curso, acao__icontains="NSA").order_by('-data_hora')
    return render(request, 'logs/gerenciarlogs.html', {'logs': logs, 'curso': curso})

# Filtrar logs por Conceito
@login_required
def filtrar_por_conceito(request, curso_id):
    curso = get_object_or_404('cursos.Curso', id=curso_id)  # Referência ao modelo Curso como string
    logs = Log.objects.filter(curso=curso, acao__icontains="Conceito").order_by('-data_hora')
    return render(request, 'logs/gerenciarlogs.html', {'logs': logs, 'curso': curso})

# Filtrar logs por Relatório
@login_required
def filtrar_por_relatorio(request, curso_id):
    curso = get_object_or_404('cursos.Curso', id=curso_id)  # Referência ao modelo Curso como string
    logs = Log.objects.filter(curso=curso, acao__icontains="Relatório").order_by('-data_hora')
    return render(request, 'logs/gerenciarlogs.html', {'logs': logs, 'curso': curso})
