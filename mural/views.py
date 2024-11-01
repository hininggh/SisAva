from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .forms import MuralForm  # Importando o formulário MuralForm
from cursos.models import Curso

from .models import Mural  # Importando o modelo Mural

from .models import Mural

@login_required
def atualizar_mural(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)

    # Obter todas as mensagens do mural associadas ao curso, incluindo o autor de cada mensagem
    mensagens = Mural.objects.filter(curso=curso).select_related('usuario').order_by('-id')
    mensagens_data = [
        {
            'id': mensagem.id,
            'autor': mensagem.usuario.nome,
            'mensagem': mensagem.mensagem,
            'pode_editar': mensagem.usuario == request.user
        }
        for mensagem in mensagens
    ]

    return JsonResponse({'mensagens': mensagens_data})

# Postar uma nova mensagem no mural
@login_required
@require_POST
def postar_mensagem(request, curso_id):
    curso = get_object_or_404('cursos.Curso', id=curso_id)  # Referenciar 'Curso' como string
    form = MuralForm(request.POST)
    form = MuralForm(request.POST)

    if form.is_valid():
        mensagem = form.save(commit=False)
        mensagem.usuario = request.user
        mensagem.curso = curso
        mensagem.save()
        return JsonResponse({'status': 'Mensagem postada com sucesso!', 'mensagem': mensagem.mensagem})

    return JsonResponse({'status': 'Erro: ' + str(form.errors)}, status=400)


# Editar uma mensagem no mural
@login_required
@require_POST
def editar_mensagem(request, mensagem_id):
    mensagem = get_object_or_404(Mural, id=mensagem_id)

    # Verifica se o usuário é o autor da mensagem
    if mensagem.usuario != request.user:
        return JsonResponse({'status': 'Erro: Permissão negada.'}, status=403)

    form = MuralForm(request.POST, instance=mensagem)

    if form.is_valid():
        form.save()
        return JsonResponse({'status': 'Mensagem editada com sucesso!', 'mensagem': form.cleaned_data['mensagem']})

    return JsonResponse({'status': 'Erro: ' + str(form.errors)}, status=400)


# Apagar uma mensagem do mural
@login_required
@require_POST
def apagar_mensagem(request, mensagem_id):
    mensagem = get_object_or_404(Mural, id=mensagem_id)

    if mensagem.usuario != request.user:
        return JsonResponse({'status': 'Erro: Permissão negada.'}, status=403)

    mensagem.delete()
    return JsonResponse({'status': 'Mensagem apagada com sucesso!'})
