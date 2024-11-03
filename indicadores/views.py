from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from PyPDF2 import PdfMerger  # Biblioteca para manipulação de PDFs
from .models import IndicadorMan, IndicadorInfo  # Modelos de Indicadores
from cursos.models import Curso
from logs.views import registrar_acao_log  # Função para registrar logs
from .forms import NivelSupostoForm, NSAForm, RelatorioForm
import os  # Biblioteca para manipular arquivos temporários
from usuarios.models import Usuario  # Modelo de Usuario




# Visualizar Indicador
@login_required
def visualizar_indicador(request, curso_id, indicador_id):
    curso = get_object_or_404(Curso, id=curso_id)
    indicador_man = get_object_or_404(IndicadorMan, curso=curso, indicador_info_id=indicador_id)

    # Formulário para NSA
    nsa_form = NSAForm(request.POST or None, instance=indicador_man)

    # Condicional para verificar o NSA
    nivel_suposto_form = None
    relatorio_form = None
    if not indicador_man.NSA:  # Garantir que o campo é falso para exibir o conceito e o relatório
        nivel_suposto_form = NivelSupostoForm(request.POST or None, instance=indicador_man)
        relatorio_form = RelatorioForm(request.POST or None, request.FILES or None, instance=indicador_man)

    context = {
        'curso': curso,
        'indicador_man': indicador_man,
        'nsa_form': nsa_form,
        'nivel_suposto_form': nivel_suposto_form,
        'relatorio_form': relatorio_form,
        'tabela_conceitos': indicador_man.indicador_info.tabela_conceitos,
        'mensagem_aviso': indicador_man.indicador_info.mensagem_aviso,
    }

    return render(request, 'indicadores/detalhesindicadorrelator.html', context)





# Baixar Relatório
@login_required
def baixar_relatorio(request, curso_id, indicador_id):
    curso = get_object_or_404(Curso, id=curso_id)
    indicador = get_object_or_404(IndicadorMan, id=indicador_id)

    if indicador.conteudo:
        if curso.capa:
            # Caminho dos arquivos
            relatorio_path = indicador.conteudo.path
            capa_path = curso.capa.path

            # Mesclar a capa e o relatório
            merger = PdfMerger()
            merger.append(capa_path)  # Adicionar a capa primeiro
            merger.append(relatorio_path)  # Adicionar o relatório depois

            # Criar um arquivo temporário mesclado
            mesclado_path = f"/tmp/relatorio_mesclado_{curso.nome}_{indicador.indicador_info.nome}.pdf"
            with open(mesclado_path, 'wb') as f_out:
                merger.write(f_out)

            # Registrar no log
            acao = "Relatório Baixado com Capa"
            registrar_acao_log(request.user, curso, acao, indicador)

            # Enviar o arquivo mesclado para o download
            with open(mesclado_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/pdf')
                response[
                    'Content-Disposition'] = f'attachment; filename="relatorio_mesclado_{indicador.indicador_info.nome}.pdf"'

            # Remover o arquivo temporário
            os.remove(mesclado_path)
            return response

        else:
            # Caso não tenha capa, baixar o relatório diretamente
            response = HttpResponse(indicador.conteudo, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="relatorio_{indicador.indicador_info.nome}.pdf"'

            # Registrar no log
            acao = "Relatório Baixado"
            registrar_acao_log(request.user, curso, acao, indicador)

            return response

    return redirect('visualizar_indicador', curso_id=curso_id, indicador_id=indicador_id)


# Deletar Relatório
@login_required
def deletar_relatorio(request, curso_id, indicador_id):
    curso = get_object_or_404(Curso, id=curso_id)
    indicador = get_object_or_404(IndicadorMan, id=indicador_id)

    # Verificar o parâmetro de origem
    origem = request.GET.get('origem', 'indicador')  # padrão para 'indicador' se o parâmetro não for passado

    if indicador.conteudo:
        indicador.conteudo.delete()
    indicador.data_envio = None
    indicador.usuario_relatorio = None
    indicador.save()

    # Registrar no log
    acao = "Relatório Deletado"
    registrar_acao_log(request.user, curso, acao, indicador)

    # Redireciona para a página de origem
    if origem == 'curso':
        return redirect('visualizar_curso', curso_id=curso.id)
    return redirect('visualizar_indicador', curso_id=curso.id, indicador_id=indicador.id)


# Enviar Relatório
@login_required
def enviar_ou_substituir_relatorio(request, curso_id, indicador_id):
    curso = get_object_or_404(Curso, id=curso_id)
    indicador = get_object_or_404(IndicadorMan, id=indicador_id)

    # Verificar o parâmetro de origem
    origem = request.GET.get('origem', 'indicador')  # padrão para 'indicador' se o parâmetro não for passado

    # Verificar se a requisição é POST e contém um arquivo
    if request.method == 'POST' and request.FILES.get('conteudo'):
        acao = "Relatório Substituído" if indicador.conteudo else "Relatório Enviado"
        indicador.conteudo = request.FILES['conteudo']
        indicador.data_envio = timezone.now()
        indicador.usuario_relatorio = request.user
        indicador.save()

        # Registrar no log
        registrar_acao_log(request.user, curso, acao, indicador)

    # Redireciona para a página de origem
    if origem == 'curso':
        return redirect('visualizar_curso', curso_id=curso.id)
    return redirect('visualizar_indicador', curso_id=curso.id, indicador_id=indicador.id)


# Aplicar NSA
@login_required
def aplicar_nsa(request, curso_id, indicador_id):
    curso = get_object_or_404(Curso, id=curso_id)
    indicador = get_object_or_404(IndicadorMan, id=indicador_id)

    indicador.NSA = True
    indicador.nivel_suposto = None
    indicador.conteudo = None
    indicador.save()

    acao = "NSA Atribuído"
    registrar_acao_log(request.user, curso, acao, indicador)

    return redirect('visualizar_indicador', curso_id=curso.id, indicador_id=indicador.id)


@login_required
def remover_nsa(request, curso_id, indicador_id):
    curso = get_object_or_404(Curso, id=curso_id)
    indicador = get_object_or_404(IndicadorMan, id=indicador_id)

    indicador.NSA = False
    indicador.save()

    acao = "NSA Removido"
    registrar_acao_log(request.user, curso, acao, indicador)

    return redirect('visualizar_indicador', curso_id=curso.id, indicador_id=indicador.id)


@login_required
def aplicar_nivel_suposto(request, curso_id, indicador_id):
    curso = get_object_or_404(Curso, id=curso_id)
    indicador_man = get_object_or_404(IndicadorMan, curso=curso, indicador_info_id=indicador_id)

    if request.method == 'POST':
        form = NivelSupostoForm(request.POST, instance=indicador_man)
        if form.is_valid():
            form.save()

            # Registrar no log
            acao = f"Nível Suposto atualizado para {indicador_man.nivel_suposto}"
            registrar_acao_log(request.user, curso, acao, indicador_man)

    # Redirecionar para a página de visualização do indicador
    return redirect('visualizar_indicador', curso_id=curso.id, indicador_id=indicador_man.indicador_info.id)