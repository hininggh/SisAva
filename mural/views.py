from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .forms import MuralForm  # Importando o formulário MuralForm
from cursos.models import Curso
from logs.views import registrar_acao_log
from .models import Mural  # Importando o modelo Mural



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
    curso = get_object_or_404(Curso, id=curso_id)  # Use Curso diretamente

    # Verifique se o usuário é relator associado ao curso
    if request.user not in curso.relatores.all():
        return JsonResponse({'status': 'Erro: Você não tem permissão para postar no mural deste curso.'}, status=403)

    # Tente buscar uma mensagem existente do relator para o curso
    mensagem_existente = Mural.objects.filter(curso=curso, usuario=request.user).first()

    # Se existir, inicialize o formulário com a mensagem existente; caso contrário, crie uma nova
    form = MuralForm(request.POST, instance=mensagem_existente)

    if form.is_valid():
        mensagem = form.save(commit=False)
        mensagem.usuario = request.user
        mensagem.curso = curso
        mensagem.save()
        # Registrar a a postagem
        acao = 11
        registrar_acao_log(request.user, curso, acao)
        return JsonResponse({'status': 'Mensagem postada com sucesso!', 'mensagem': mensagem.mensagem})

    return JsonResponse({'status': 'Erro: ' + str(form.errors)}, status=400)



# Apagar uma mensagem do mural
@login_required
@require_POST
def apagar_mensagem(request, mensagem_id):
    mensagem = get_object_or_404(Mural, id=mensagem_id)

    if mensagem.usuario != request.user:
        return JsonResponse({'status': 'Erro: Permissão negada.'}, status=403)

    curso = mensagem.curso  # Obtém o curso associado à mensagem

    mensagem.delete()
    acao = 23
    registrar_acao_log(request.user, curso, acao)  # Passa o curso como argumento
    return JsonResponse({'status': 'Mensagem apagada com sucesso!'})
