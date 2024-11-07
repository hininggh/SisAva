from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from cursos.models import Curso
from .models import Log
from django.db.models import Q

# Usar strings para referenciar os modelos


# Função genérica para registrar ações no log
def registrar_acao_log(usuario, curso, acao, indicador=None):
    """
    Função genérica para registrar ações no sistema de logs.
    Pode ser chamada a partir de qualquer outro app.
    O campo `indicador` é opcional e pode ser nulo.
    """
    log = Log(
        usuario=usuario,
        curso=curso,
        data_hora=timezone.now(),
        acao=acao,
        indicadorMan=indicador  # Pode ser nulo
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
