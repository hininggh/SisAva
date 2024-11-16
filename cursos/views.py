from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from indicadores.models import IndicadorInfo, IndicadorMan
from logs.views import registrar_acao_log
from cursos.forms import CursoForm, InformacoesComplementaresForm
from django.http import HttpResponse
from io import BytesIO
from PyPDF2 import PdfMerger
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from mural.forms import MuralForm
from mural.models import Mural
from reportlab.lib.units import cm
from django.contrib.auth import get_user_model
from .forms import CapaCursoForm
from django.views.decorators.http import require_POST
from .models import Curso
from usuarios.models import Usuario
import os
import logging
from django.contrib import messages








Usuario = get_user_model()



# Criar ou Editar Curso
@login_required
def criar_ou_editar_curso(request, curso_id=None):
    if curso_id:
        curso = get_object_or_404(Curso, id=curso_id)
        if request.user != curso.criador and not (curso.privilegios and request.user in curso.relatores.all()):
            return redirect('home')
    else:
        curso = None

    if request.method == 'POST':
        form = CursoForm(request.POST, request.FILES, instance=curso)
        if form.is_valid():
            curso = form.save(commit=False)
            if not curso_id:
                curso.criador = request.user
                curso.save()
                curso.relatores.add(request.user)
                indicadores_info = IndicadorInfo.objects.all()
                for indicador_info in indicadores_info:
                    IndicadorMan.objects.create(curso=curso, indicador_info=indicador_info)
                acao = 5
            else:
                curso.save()
                acao = 6
            registrar_acao_log(request.user, curso, acao)

            # Redireciona para edição do curso após criar
            return redirect('editar_curso', curso_id=curso.id)
    else:
        form = CursoForm(instance=curso)

    visitantes_disponiveis = Usuario.objects.filter(tipo=Usuario.VISITANTE).exclude(
        cursos_acesso=curso) if curso else Usuario.objects.filter(tipo=Usuario.VISITANTE)
    visitantes = Usuario.objects.filter(tipo=Usuario.VISITANTE, cursos_acesso=curso) if curso else []

    # Mantendo os relatores e usuários disponíveis da forma original
    usuarios_disponiveis = Usuario.objects.filter(tipo=Usuario.RELATOR).exclude(
        id__in=curso.relatores.values_list('id', flat=True)) if curso else Usuario.objects.filter(tipo=Usuario.RELATOR)
    relatores = curso.relatores.all() if curso else []

    # Retorna JSON com lista de relatores em requisições AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        relatores = curso.relatores.values_list('nome', flat=True) if curso else []
        return JsonResponse({'relatores': list(relatores)})

    # Adicione visitantes_com_acesso e visitantes_disponiveis ao contexto do template
    return render(request, 'cursos/criarcurso.html', {
        'form': form,
        'curso': curso,
        'relatores': relatores,
        'usuarios_disponiveis': usuarios_disponiveis,
        'visitantes_disponiveis': visitantes_disponiveis,
        'visitantes': visitantes
    })




@login_required
def ceder_criacao_curso(request, curso_id, novo_relator_id):
    # Obtém o curso e verifica se o usuário logado é o criador
    curso = get_object_or_404(Curso, id=curso_id)
    if request.user != curso.criador:
        return JsonResponse({'success': False, 'error': "Você não tem permissão para ceder a criação deste curso."})

    # Obtém o novo relator e verifica se ele é um relator do curso
    novo_relator = get_object_or_404(Usuario, id=novo_relator_id, tipo=Usuario.RELATOR)
    if not curso.relatores.filter(id=novo_relator.id).exists():
        return JsonResponse({'success': False, 'error': "O usuário selecionado não é um relator deste curso."})

    # Atualiza o criador do curso para o novo relator
    curso.criador = novo_relator
    curso.save()

    # Verifica se o relator antigo está na lista de relatores; se não, adiciona
    if not curso.relatores.filter(id=request.user.id).exists():
        curso.relatores.add(request.user)

    return JsonResponse({'success': True})





@login_required
def excluir_curso(request, curso_id):
    # Obtém o curso ou retorna 404 se não for encontrado
    curso = get_object_or_404(Curso, id=curso_id)

    # Verifica se o usuário logado é o criador do curso
    if request.user != curso.criador:
        return JsonResponse({'success': False, 'error': "Somente o criador pode excluir uma avaliação."})

    # Remove o curso de todos os visitantes antes de deletar
    visitantes = Usuario.objects.filter(cursos_acesso=curso)
    for visitante in visitantes:
        visitante.cursos_acesso.remove(curso)

    # Deleta o curso
    curso.delete()
    return JsonResponse({'success': True, 'message': "Curso deletado com sucesso."})



@login_required
def atualizar_lista_relatores(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    relatores_adicionados = curso.relatores.all()

    # Excluir os relatores que já estão no curso da lista de disponíveis
    relatores_disponiveis = Usuario.objects.filter(tipo='relator').exclude(id__in=relatores_adicionados)

    # Estrutura do JSON para nome e id
    data = {
        "relator": [{"id": relator.id, "nome": relator.nome} for relator in relatores_adicionados],
        "relatorDisponiveis": [{"id": relator.id, "nome": relator.nome} for relator in relatores_disponiveis]
    }

    return JsonResponse(data)






@login_required
def adicionar_relator(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    relator_id = request.POST.get('relator_id')
    relator = get_object_or_404(Usuario, id=relator_id)
    if relator not in curso.relatores.all():
        curso.relatores.add(relator)
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'Relator já adicionado.'})

# views.py

@login_required
def excluir_relator(request, curso_id, relator_id):
    curso = get_object_or_404(Curso, id=curso_id)
    # Verifica se o usuário que está tentando excluir é o criador
    if request.user != curso.criador:
        return JsonResponse({'error': 'Apenas o criador do curso pode excluir relatores'}, status=403)

    # Busca o relator e verifica se ele é o criador
    relator = get_object_or_404(Usuario, id=relator_id)
    if relator == curso.criador:
        return JsonResponse({'error': 'O criador do curso não pode ser removido como relator'}, status=403)

    # Remove o relator dos relatores do curso
    curso.relatores.remove(relator)
    return JsonResponse({'success': True})

#----------------------------------------

@login_required
def atualizar_lista_visitantes(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    # Visitantes que têm acesso a este curso
    visitantes_adicionados = Usuario.objects.filter(cursos_acesso=curso, tipo=Usuario.VISITANTE)

    # Visitantes disponíveis que ainda não têm acesso a este curso
    visitantes_disponiveis = Usuario.objects.filter(tipo=Usuario.VISITANTE).exclude(cursos_acesso=curso)

    # Estrutura do JSON para nome e id
    data = {
        "visitante": [{"id": visitante.id, "nome": visitante.nome} for visitante in visitantes_adicionados],
        "visitanteDisponiveis": [{"id": visitante.id, "nome": visitante.nome} for visitante in visitantes_disponiveis]
    }

    return JsonResponse(data)

@login_required
def adicionar_visitante_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    visitante_id = request.POST.get('visitante_id')
    visitante = get_object_or_404(Usuario, id=visitante_id, tipo=Usuario.VISITANTE)

    # Adiciona o curso à lista de cursos do visitante, se ainda não estiver presente
    if curso not in visitante.cursos_acesso.all():
        visitante.cursos_acesso.add(curso)
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'O visitante já tem acesso a este curso.'})

@login_required
def excluir_visitante_curso(request, curso_id, visitante_id):
    curso = get_object_or_404(Curso, id=curso_id)
    visitante = get_object_or_404(Usuario, id=visitante_id, tipo=Usuario.VISITANTE)

    # Remove o curso da lista de cursos do visitante
    if curso in visitante.cursos_acesso.all():
        visitante.cursos_acesso.remove(curso)
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'O visitante não tinha acesso a este curso.'})



#-------------------------------------------------
# Visualizar Curso
@login_required
def visualizar_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)

    # Verificar se o usuário é relator ou visitante
    if request.user in curso.relatores.all():
        # Obter os indicadores associados ao curso agrupados por dimensão
        indicadores_por_dimensao = {}
        indicadores_man = IndicadorMan.objects.filter(curso=curso).select_related('indicador_info')
        indicadores_info = {indicador.indicador_info for indicador in indicadores_man}  # Coletar todos os IndicadorInfo relacionados

        for indicador_info in indicadores_info:
            dimensao = indicador_info.dimensao
            if dimensao not in indicadores_por_dimensao:
                indicadores_por_dimensao[dimensao] = {
                    'indicador_info': indicador_info,
                    'indicadores_man': []
                }
            # Adiciona os IndicadorMan correspondentes
            indicadores_por_dimensao[dimensao]['indicadores_man'].extend(
                [indicador for indicador in indicadores_man if indicador.indicador_info == indicador_info]
            )

        # Obter as mensagens do mural relacionadas ao curso
        mensagens = Mural.objects.filter(curso=curso).order_by('-id')
        form_mural = MuralForm()

        context = {
            'curso': curso,
            'indicadores_por_dimensao': indicadores_por_dimensao,
            'mensagens': mensagens,
            'privilegios': curso.privilegios,  # Passa a condição de privilégios ao template
            'form_mural': form_mural,
            'usuario_autorizado': (curso.privilegios and request.user in curso.relatores.all()) or (
                not curso.privilegios and request.user == curso.criador)
        }

        return render(request, 'cursos/detalhescursorelator.html', context)
    else:
        return render(request, 'cursos/detalhescursovisitante.html', {'curso': curso})


#---------visualizarcurso visitante

def visualizar_curso_visitante(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    # Verificar se o usuário visitante tem acesso ao curso
    if request.user.tipo == Usuario.VISITANTE and curso in request.user.cursos_acesso.all():
        # Obter os indicadores associados ao curso agrupados por dimensão
        print('passou1')
        indicadores_por_dimensao = {}
        indicadores_man = IndicadorMan.objects.filter(curso=curso).select_related('indicador_info')
        indicadores_info = {indicador.indicador_info for indicador in indicadores_man}
        print('passou2')
        for indicador_info in indicadores_info:
            dimensao = indicador_info.dimensao
            if dimensao not in indicadores_por_dimensao:
                indicadores_por_dimensao[dimensao] = {
                    'indicador_info': indicador_info,
                    'indicadores_man': []
                }
            # Adiciona os IndicadorMan correspondentes
            indicadores_por_dimensao[dimensao]['indicadores_man'].extend(
                [indicador for indicador in indicadores_man if indicador.indicador_info == indicador_info]
            )

        context = {
            'curso': curso,
            'indicadores_por_dimensao': indicadores_por_dimensao,
        }

        return render(request, 'cursos/detalhescursovisitante.html', context)

    else:
        # Redireciona ou mostra uma página de erro se o visitante não tiver acesso ao curso
        return render(request, 'cursos/acesso_negado.html', {'curso': curso})

#-----------------------views capa


@login_required
def enviar_ou_substituir_capa(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)

    # Verificar permissões de acordo com privilégios e relação com o criador
    if (request.user == curso.criador) or (curso.privilegios and request.user in curso.relatores.all()):
        if request.method == 'POST' and request.FILES.get('capa'):
            # Verifica se já existe uma capa
            capa_existente = curso.capa is not None
            curso.capa = request.FILES['capa']
            curso.save()

            # Registrar a ação de acordo com a existência anterior da capa
            acao = 9 if capa_existente else 8
            registrar_acao_log(request.user, curso, acao)

            # Adicionar mensagem de sucesso
            messages.success(request, f"{acao} com sucesso.")

            # Redirecionar para a página de visualização do curso após o upload
            return redirect('visualizar_curso', curso_id=curso.id)

    # Redireciona para visualização do curso caso não tenha permissão
    return redirect('visualizar_curso', curso_id=curso.id)


# Baixar Capa
@login_required
def baixar_capa(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    if curso.capa:
        response = HttpResponse(curso.capa, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="capa_{curso.nome}.pdf"'

        return response
    return redirect('visualizar_curso', curso_id=curso.id)


# Deletar Capa
@login_required
def deletar_capa(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    if (request.user == curso.criador) or (curso.privilegios and request.user in curso.relatores.all()):
        if curso.capa:
            curso.capa.delete()
            curso.save()

            # Registrar no log
            acao = 10
            registrar_acao_log(request.user, curso, acao, None)

        return redirect('visualizar_curso', curso_id=curso.id)
    return redirect('visualizar_curso', curso_id=curso.id)


# Editar Informações Complementares
@login_required
def editar_informacoes_complementares(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)

    # Verificar permissões
    if not ((request.user == curso.criador) or (curso.privilegios and request.user in curso.relatores.all())):
        return redirect('visualizar_curso', curso_id=curso.id)

    if request.method == 'POST':
        informacoes_complementares = request.POST.get('informacoes_complementares', '')
        curso.informacoes_complementares = informacoes_complementares
        curso.save()
        acao = 7
        registrar_acao_log(request.user, curso, acao)
        # Redirecionar para a página de visualização do curso
        return redirect('visualizar_curso', curso_id=curso.id)


# Gerar Relatório Geral

@login_required
def gerar_relatorio_geral(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)

    # Verifica se o usuário é relator ou visitante com permissão
    if request.user not in curso.relatores.all() and request.user.tipo != 'visitante':
        return redirect('home')

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    # Margens
    left_margin = 1 * cm
    right_margin = 0.5 * cm
    cont_margin = 0.5 * cm  # Margem esquerda para linhas de continuação

    # Data e hora na primeira página
    c.drawString(left_margin, 27 * cm, f"Relatório Geral do Curso: {curso.nome}")
    c.drawString(left_margin, 26.5 * cm, f"Data e Hora: {timezone.now().strftime('%d/%m/%Y %H:%M')}")

    # Agrupar os indicadores por dimensão
    dimensoes = {
        'Organização Didático-Pedagógica': [],
        'Corpo Docente e Tutorial': [],
        'Infraestrutura': []
    }
    indicadores = curso.indicadorman_set.all()

    for indicador in indicadores:
        dimensao = indicador.indicador_info.get_dimensao_display()
        dimensoes[dimensao].append(indicador)

    # Escrever os indicadores com quebra de linha e margens ajustadas
    line_height = 0.7 * cm
    y_position = 25 * cm

    for dimensao, lista_indicadores in dimensoes.items():
        # Nova página para cada dimensão se necessário
        if y_position < 2 * cm:
            c.showPage()
            y_position = 27 * cm

        # Título da dimensão
        c.drawString(left_margin, y_position, f"Dimensão: {dimensao}")
        y_position -= line_height

        for indicador in lista_indicadores:
            # Condicional para formatar o texto do indicador conforme o valor de NSA e nivel_suposto
            if indicador.NSA:
                texto = f"Indicador: {indicador.indicador_info.nome} | NSA"
            else:
                nivel_texto = f"Nível: {indicador.nivel_suposto or 'vazio'}"
                relatorio_texto = " | Relatório presente" if indicador.conteudo else " | Relatório ausente"
                texto = f"Indicador: {indicador.indicador_info.nome} | {nivel_texto}{relatorio_texto}"

            # Ajustar a linha e a posição no PDF
            max_width = 19 * cm
            words = texto.split()
            current_line = ""
            for word in words:
                if c.stringWidth(current_line + word + " ") < max_width:
                    current_line += word + " "
                else:
                    c.drawString(left_margin if y_position == 25 * cm else cont_margin, y_position, current_line)
                    y_position -= line_height
                    current_line = word + " "
            c.drawString(left_margin if y_position == 25 * cm else cont_margin, y_position, current_line)
            y_position -= line_height

    # Informações Complementares em uma nova página
    c.showPage()
    c.drawString(left_margin, 27 * cm, "Informações Complementares")
    y_position = 26.5 * cm
    informacoes_texto = curso.informacoes_complementares or "Sem informações complementares"
    for line in informacoes_texto.splitlines():
        c.drawString(left_margin, y_position, line)
        y_position -= line_height

    c.save()
    buffer.seek(0)
    relatorio_gerado = buffer

    # Mesclar a capa (se houver), o relatório gerado, e os relatórios dos indicadores
    merger = PdfMerger()

    if curso.capa:
        merger.append(curso.capa)

    merger.append(relatorio_gerado)

    for indicador in indicadores:
        if indicador.conteudo:
            merger.append(indicador.conteudo)

    resultado_final = BytesIO()
    merger.write(resultado_final)
    resultado_final.seek(0)


    response = HttpResponse(resultado_final, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="relatorio_geral_{curso.nome}.pdf"'

    return response