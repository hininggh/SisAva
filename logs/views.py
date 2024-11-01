from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required

# Usar strings para referenciar os modelos
from .models import Log

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
