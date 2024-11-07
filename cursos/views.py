from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Curso
from usuarios.models import Usuario
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
from .forms import CapaCursoForm
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import os


import logging

# Criar ou Editar Curso
@login_required
def criar_ou_editar_curso(request, curso_id=None):
    if curso_id:
        curso = get_object_or_404(Curso, id=curso_id)
        if request.user != curso.criador and not (curso.privilegios and request.user in curso.relatores.all()):
            return redirect('homerelator')
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
                acao = "Curso Criado"
            else:
                curso.save()
                acao = "Curso Editado"
            registrar_acao_log(request.user, curso, acao, None)

            # Redireciona para edição do curso após criar
            return redirect('editar_curso', curso_id=curso.id)
    else:
        form = CursoForm(instance=curso)

    usuarios_disponiveis = Usuario.objects.filter(tipo=Usuario.RELATOR).exclude(id__in=curso.relatores.values_list('id', flat=True)) if curso else Usuario.objects.filter(tipo=Usuario.RELATOR)
    relatores = curso.relatores.all() if curso else []

    # Retorna JSON com lista de relatores em requisições AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        relatores = curso.relatores.values_list('nome', flat=True) if curso else []
        return JsonResponse({'relatores': list(relatores)})

    return render(request, 'cursos/criarcurso.html', {
        'form': form,
        'curso': curso,
        'relatores': relatores,
        'usuarios_disponiveis': usuarios_disponiveis
    })

@login_required
def excluir_curso(request, curso_id):
    # Obtém o curso ou retorna 404 se não for encontrado
    curso = get_object_or_404(Curso, id=curso_id)

    # Remove o curso de todos os visitantes antes de deletar
    visitantes = Usuario.objects.filter(cursos_acesso=curso)
    for visitante in visitantes:
        visitante.cursos_acesso.remove(curso)

    # Deleta o curso
    curso.delete()
    messages.success(request, "Curso deletado com sucesso.")

    # Redireciona para a página inicial
    return redirect('home')


@login_required
def atualizar_lista_relatores(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    relatores = curso.relatores.all()

    # Estrutura do JSON para nome e id
    data = {
        "relator": [{"id": relator.id, "nome": relator.nome} for relator in relatores]
    }
    return JsonResponse(data)



from django.http import JsonResponse


@login_required
def adicionar_relator(request, curso_id):
    # Verifica se é uma requisição AJAX
    print("iniciou")
    curso = get_object_or_404(Curso, id=curso_id)
    print("passou0")
    relator_id = request.POST.get('relator_id')
    print("passou1")
    relator = get_object_or_404(Usuario, id=relator_id)

    if relator not in curso.relatores.all():
        curso.relatores.add(relator)
        print("passou2")
        return JsonResponse({'success': True})
    else:
        print("passou3")
        return JsonResponse({'success': False, 'error': 'Relator já adicionado.'})

# views.py

@login_required
def excluir_relator(request, curso_id, relator_id):
    curso = get_object_or_404(Curso, id=curso_id)
    print("passou0")
    # Verifica se o usuário que está tentando excluir é o criador
    if request.user != curso.criador:
        return JsonResponse({'error': 'Apenas o criador do curso pode excluir relatores'}, status=403)

    # Busca o relator e verifica se ele é o criador
    relator = get_object_or_404(Usuario, id=relator_id)
    if relator == curso.criador:
        return JsonResponse({'error': 'O criador do curso não pode ser removido como relator'}, status=403)

    # Remove o relator dos relatores do curso
    curso.relatores.remove(relator)
    print("passou2")
    return JsonResponse({'success': True})


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
    print('passou0')
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
        print("Indicadores:", indicadores_man)
        print("Agrupamento por dimensão:", indicadores_por_dimensao)
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
            acao = "Capa Substituída" if capa_existente else "Capa Enviada"
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

        # Registrar no log
        acao = "Capa Baixada"
        registrar_acao_log(request.user, curso, acao, None)

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
            acao = "Capa Deletada"
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

        # Redirecionar para a página de visualização do curso
        return redirect('visualizar_curso', curso_id=curso.id)


# Gerar Relatório Geral

@login_required
def gerar_relatorio_geral(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)

    # Verifica se o usuário é relator ou visitante com permissão
    if request.user not in curso.relatores.all() and request.user.tipo != 'visitante':
        return redirect('homevisitante')

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

    acao = "Relatório Geral Gerado"
    registrar_acao_log(request.user, curso, acao, None)

    response = HttpResponse(resultado_final, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="relatorio_geral_{curso.nome}.pdf"'

    return response