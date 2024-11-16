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
import tempfile
from django.contrib import messages
from usuarios.models import Usuario  # Modelo de Usuario




# Visualizar Indicador
@login_required
def visualizar_indicador(request, curso_id, indicador_id):
    curso = get_object_or_404(Curso, id=curso_id)
    # Buscar o IndicadorMan com o ID fornecido
    indicador_man = get_object_or_404(IndicadorMan, curso=curso, id=indicador_id)

    # Formulário para NSA
    nsa_form = NSAForm(request.POST or None, instance=indicador_man)

    # Condicional para verificar o NSA
    nivel_suposto_form = None
    relatorio_form = None
    if not indicador_man.NSA:  # Garantir que o campo é falso para exibir o conceito e o relatório
        nivel_suposto_form = NivelSupostoForm(request.POST or None, instance=indicador_man)
        relatorio_form = RelatorioForm(request.POST or None, request.FILES or None, instance=indicador_man)

    # Verificar se existe relatório e se nível suposto é None

    # Adicionar as informações do IndicadorInfo associadas
    indicador_info = indicador_man.indicador_info

    context = {
        'curso': curso,
        'indicador_man': indicador_man,
        'nsa_form': nsa_form,
        'nivel_suposto_form': nivel_suposto_form,
        'relatorio_form': relatorio_form,
        'tabela_conceitos': indicador_info.tabela_conceitos,
        'mensagem_aviso': indicador_info.mensagem_aviso,
        'tabela_nome': indicador_info.nome,
    }

    return render(request, 'indicadores/detalhesindicadorrelator.html', context)

#___________ visitante


def visualizar_indicador_visitante(request, curso_id, indicador_id):
    curso = get_object_or_404(Curso, id=curso_id)
    indicador_man = get_object_or_404(IndicadorMan, curso=curso, id=indicador_id)

    if request.user.tipo == Usuario.VISITANTE and curso in request.user.cursos_acesso.all():
        indicador_info = indicador_man.indicador_info
        nome_relatorio = os.path.basename(indicador_man.conteudo.name) if indicador_man.conteudo else None

        context = {
            'curso': curso,
            'indicador_man': indicador_man,
            'tabela_conceitos': indicador_info.tabela_conceitos,
            'mensagem_aviso': indicador_info.mensagem_aviso,
            'tabela_nome': indicador_info.nome,
            'nome_relatorio': nome_relatorio
        }

        return render(request, 'indicadores/detalhesindicadorvisitante.html', context)
    else:
        return render(request, 'cursos/acesso_negado.html', {'curso': curso})
#_________



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
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                mesclado_path = temp_file.name
                merger = PdfMerger()
                merger.append(capa_path)  # Adicionar a capa primeiro
                merger.append(relatorio_path)  # Adicionar o relatório depois
                merger.write(temp_file)
                merger.close()  # Fechar o merger para liberar recursos


            # Enviar o arquivo mesclado para o download
            with open(mesclado_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="relatorio_mesclado_{indicador.indicador_info.nome}.pdf"'

            # Remover o arquivo temporário após o envio
            os.remove(mesclado_path)
            return response

        else:
            # Caso não tenha capa, baixar o relatório diretamente
            response = HttpResponse(indicador.conteudo, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="relatorio_{indicador.indicador_info.nome}.pdf"'


            return response

    return redirect('visualizar_indicador', curso_id=curso_id, indicador_id=indicador_id)


# Deletar Relatório
@login_required
def deletar_relatorio(request, curso_id, indicador_id):
    curso = get_object_or_404(Curso, id=curso_id)
    indicador = get_object_or_404(IndicadorMan, curso=curso, id=indicador_id)

    # Verificar o parâmetro de origem
    origem = request.GET.get('origem', 'indicador')  # padrão para 'indicador' se o parâmetro não for passado

    if request.method == 'POST' and indicador.conteudo:
        try:
            # Registrar a exclusão no log antes da exclusão do arquivo
            acao = 14
            registrar_acao_log(request.user, curso, acao, indicador)

            # Apaga o arquivo fisicamente e remove a referência ao conteúdo
            indicador.conteudo.delete(save=False)
            indicador.conteudo = None
            indicador.save(update_fields=['conteudo'])
        except PermissionError:
            os.remove(indicador.conteudo.path)  # Força a exclusão se houver erro de permissão

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
        acao = 13 if indicador.conteudo else 12
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

    acao = 16
    registrar_acao_log(request.user, curso, acao, indicador)

    return redirect('visualizar_indicador', curso_id=curso.id, indicador_id=indicador.id)


@login_required
def remover_nsa(request, curso_id, indicador_id):
    curso = get_object_or_404(Curso, id=curso_id)
    indicador = get_object_or_404(IndicadorMan, id=indicador_id)

    indicador.NSA = False
    indicador.save()

    acao = 17
    registrar_acao_log(request.user, curso, acao, indicador)

    return redirect('visualizar_indicador', curso_id=curso.id, indicador_id=indicador.id)



@login_required
def aplicar_nivel_suposto(request, curso_id, indicador_id):
    curso = get_object_or_404(Curso, id=curso_id)
    indicador_man = get_object_or_404(IndicadorMan, curso=curso, id=indicador_id)  # Certifique-se de usar 'id=indicador_id'

    if request.method == 'POST':
        nivel_suposto_form = NivelSupostoForm(request.POST, instance=indicador_man)
        if nivel_suposto_form.is_valid():
            nivel_suposto_form.save()
            messages.success(request, "Nível Suposto atualizado com sucesso.")
        else:
            messages.error(request, "Erro ao atualizar o Nível Suposto.")

    return redirect('visualizar_indicador', curso_id=curso.id, indicador_id=indicador_man.id)
