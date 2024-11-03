from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
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
        if request.user != curso.criador:
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

    usuarios_disponiveis = Usuario.objects.exclude(id=curso.criador.id) if curso else Usuario.objects.all()
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

        for indicador in indicadores_man:
            dimensao = indicador.indicador_info.dimensao
            if dimensao not in indicadores_por_dimensao:
                indicadores_por_dimensao[dimensao] = []
            indicadores_por_dimensao[dimensao].append(indicador)

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



#-----------------------views capa


@login_required
def enviar_ou_substituir_capa(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)

    # Verificar permissões de acordo com privilégios e relação com o criador
    if (curso.privilegios and request.user in curso.relatores.all()) or (not curso.privilegios and request.user == curso.criador):
        if request.method == 'POST' and request.FILES.get('capa'):
            # Verifica se já existe uma capa
            capa_existente = curso.capa is not None
            curso.capa = request.FILES['capa']
            curso.save()

            # Registrar a ação de acordo com a existência anterior da capa
            acao = "Capa Substituída" if capa_existente else "Capa Enviada"
            registrar_acao_log(request.user, curso, acao)

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


# Substituir Capa
@login_required
def substituir_capa(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    if request.user != curso.criador:
        return redirect('homerelator')  # Apenas o criador pode substituir a capa

    if request.method == 'POST' and request.FILES.get('capa'):
        curso.capa = request.FILES['capa']
        curso.save()

        # Registrar no log
        acao = "Capa Substituída"
        registrar_acao_log(request.user, curso, acao, None)

        return redirect('visualizar_curso', curso_id=curso.id)
    return redirect('visualizar_curso', curso_id=curso.id)


# Deletar Capa
@login_required
def deletar_capa(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
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
    if request.user != curso.criador:
        return redirect('homerelator')  # Somente o criador pode editar as informações complementares

    if request.method == 'POST':
        form = InformacoesComplementaresForm(request.POST, instance=curso)
        if form.is_valid():
            form.save()

            # Registrar no log
            acao = "Informações Complementares Editadas"
            registrar_acao_log(request.user, curso, acao, None)

            return redirect('visualizar_curso', curso_id=curso.id)
    else:
        form = InformacoesComplementaresForm(instance=curso)

    return render(request, 'cursos/editar_informacoes_complementares.html', {'form': form, 'curso': curso})


# Gerar Relatório Geral
@login_required
@login_required
def gerar_relatorio_geral(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)

    # Verifica se o usuário é visitante ou relator
    if request.user not in curso.relatores.all() and request.user.tipo != 'visitante':
        return redirect('homevisitante')  # Caso o usuário não tenha acesso

    # Iniciar o texto do relatório
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.drawString(100, 800, f"Relatório Geral do Curso: {curso.nome}")
    c.drawString(100, 780, f"Data: {timezone.now().strftime('%d/%m/%Y')}")

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

    # Escrever os indicadores divididos por dimensão
    for dimensao, lista_indicadores in dimensoes.items():
        c.showPage()
        c.drawString(100, 800, f"Dimensão: {dimensao}")
        for indicador in lista_indicadores:
            texto_indicador = f"Indicador: {indicador.indicador_info.nome}"
            texto_indicador += f" | NSA: {indicador.NSA}" if indicador.NSA else f" | Nível: {indicador.nivel_suposto}"
            texto_indicador += " | Relatório presente" if indicador.conteudo else " | Relatório ausente"
            c.drawString(100, 760 - (20 * lista_indicadores.index(indicador)), texto_indicador)

    # Adicionar as Informações Complementares
    c.showPage()
    c.drawString(100, 800, "Informações Complementares")
    c.drawString(100, 780, curso.informacoes_complementares or "Sem informações complementares")

    c.save()
    buffer.seek(0)

    # Criar o PDF do relatório (com texto gerado)
    relatorio_gerado = buffer

    # Mesclar a capa (se houver), o relatório gerado, e os relatórios dos indicadores
    merger = PdfMerger()

    if curso.capa:
        merger.append(curso.capa)  # Mesclar a capa primeiro

    merger.append(relatorio_gerado)  # Mesclar o relatório gerado

    # Mesclar os relatórios dos indicadores
    for indicador in indicadores:
        if indicador.conteudo:
            merger.append(indicador.conteudo)  # Mesclar relatórios

    # Salvar o resultado final em um arquivo temporário
    resultado_final = BytesIO()
    merger.write(resultado_final)
    resultado_final.seek(0)

    # Registrar no log
    acao = "Relatório Geral Gerado"
    registrar_acao_log(request.user, curso, acao, None)

    # Retornar o relatório geral finalizado como resposta
    response = HttpResponse(resultado_final, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="relatorio_geral_{curso.nome}.pdf"'

    return response