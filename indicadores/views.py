from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from PyPDF2 import PdfMerger
from .models import IndicadorMan, IndicadorInfo
from logs.views import registrar_acao_log
from .forms import NivelSupostoForm, NSAForm, RelatorioPDFForm
import os
import tempfile
from django.contrib import messages
from usuarios.models import Usuario
from cursos.models import Curso
import plotly.graph_objects as go
from django.http import HttpResponseBadRequest
import PyPDF2
from collections import Counter, defaultdict
import plotly.graph_objects as go
import networkx as nx
from .models import RelatorioPDF
from io import BytesIO
import zipfile
from django.http import JsonResponse, HttpResponseForbidden
from django.utils.timezone import now
from datetime import timedelta
import * as docx from 'docx'




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
        relatorio_form = RelatorioPDFForm(request.POST or None, request.FILES or None)

    # Verificar se há relatórios associados (PDFs ou documento compartilhado)
    relatorios_pdfs = indicador_man.relatorios_pdfs.all()
    relatorios_info = [
        {
            "id": relatorio.id,
            "arquivo_nome": os.path.basename(relatorio.arquivo.name),
            "usuario_upload": relatorio.usuario_upload.nome if relatorio.usuario_upload else "Desconhecido",
            "data_upload": relatorio.data_upload,
        }
        for relatorio in relatorios_pdfs
    ]

    tem_documento_compartilhado = bool(indicador_man.documento_tinymce)

    # Status do documento compartilhado
    documento_em_edicao = indicador_man.em_edicao
    usuario_editando_doc = indicador_man.usuario_editando.nome if indicador_man.usuario_editando else None
    edicao_inicio = indicador_man.edicao_inicio.strftime("%d/%m/%Y %H:%M:%S") if indicador_man.edicao_inicio else None

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
        'relatorios_pdfs': relatorios_info,  # Envia apenas as informações necessárias
        'tem_documento_compartilhado': tem_documento_compartilhado,
        'documento_tinymce': indicador_man.documento_tinymce,
        'documento_em_edicao': documento_em_edicao,
        'usuario_editando_doc': usuario_editando_doc,
        'edicao_inicio': edicao_inicio,
    }

    return render(request, 'indicadores/detalhesindicadorrelator.html', context)

#___________ visitante


@login_required
def visualizar_indicador_visitante(request, curso_id, indicador_id):
    curso = get_object_or_404(Curso, id=curso_id)
    indicador_man = get_object_or_404(IndicadorMan, curso=curso, id=indicador_id)

    if request.user.tipo == Usuario.VISITANTE and curso in request.user.cursos_acesso.all():
        indicador_info = indicador_man.indicador_info


        context = {
            'curso': curso,
            'indicador_man': indicador_man,
            'tabela_conceitos': indicador_info.tabela_conceitos,
            'mensagem_aviso': indicador_info.mensagem_aviso,
            'tabela_nome': indicador_info.nome
        }

        return render(request, 'indicadores/detalhesindicadorvisitante.html', context)
    else:
        return render(request, 'cursos/acesso_negado.html', {'curso': curso})

#_________



# Baixar Relatório


@login_required
def baixar_relatorio(request, relatorio_id):
    relatorio = get_object_or_404(RelatorioPDF, id=relatorio_id)

    # Responder com o arquivo PDF
    response = HttpResponse(relatorio.arquivo, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="relatorio_{relatorio.indicador.indicador_info.nome}_{relatorio.id}.pdf"'

    return response


@login_required
def baixar_todos_pdfs(request, curso_id, indicador_id):
    # Obtém o indicador e verifica a permissão do usuário
    curso = get_object_or_404(Curso, id=curso_id)
    indicador = get_object_or_404(IndicadorMan, curso=curso, id=indicador_id)

    # Busca todos os RelatoriosPDF relacionados ao indicador
    relatorios = RelatorioPDF.objects.filter(indicador=indicador)

    if not relatorios.exists():
        return HttpResponse("Nenhum relatório disponível para download.", content_type="text/plain")

    # Cria um arquivo ZIP com os PDFs
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for relatorio in relatorios:
            # Adiciona cada PDF ao ZIP
            if relatorio.arquivo and os.path.exists(relatorio.arquivo.path):
                zip_file.write(relatorio.arquivo.path, os.path.basename(relatorio.arquivo.path))

    # Prepara a resposta com o arquivo ZIP
    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="relatorios_{indicador.indicador_info.nome}.zip"'
    return response



@login_required
def baixar_relatorio_mesclado(request, curso_id, indicador_id):
    curso = get_object_or_404(Curso, id=curso_id)
    indicador = get_object_or_404(IndicadorMan, id=indicador_id)

    merger = PdfMerger()

    # Adicionar a capa do curso (se existir)
    if curso.capa:
        merger.append(curso.capa.path)

    # Adicionar o documento compartilhado como PDF (se existir)
    if indicador.documento_tinymce:
        doc_buffer = BytesIO()
        c = canvas.Canvas(doc_buffer, pagesize=A4)
        c.drawString(1 * cm, 27 * cm, "Documento Compartilhado:")
        c.drawString(1 * cm, 26.5 * cm, indicador.documento_tinymce)
        c.save()
        doc_buffer.seek(0)
        merger.append(doc_buffer)

    # Adicionar relatórios PDFs (se existirem)
    relatorios = indicador.relatorios_pdfs.all()
    for relatorio in relatorios:
        merger.append(relatorio.arquivo.path)

    # Criar o arquivo mesclado
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        merger.write(temp_file)
        mesclado_path = temp_file.name

    # Enviar o arquivo mesclado para download
    with open(mesclado_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="relatorio_mesclado_{indicador.indicador_info.nome}.pdf"'

    # Remover o arquivo temporário
    os.remove(mesclado_path)
    return response



# Deletar Relatório
@login_required
def deletar_relatorio(request, relatorio_id):
    relatorio = get_object_or_404(RelatorioPDF, id=relatorio_id)

    if request.method == 'POST':
        try:
            # Registrar a exclusão no log
            registrar_acao_log(request.user, relatorio.indicador.curso, 14, relatorio.indicador)

            # Deletar o arquivo fisicamente e a entrada no banco de dados
            relatorio.arquivo.delete(save=False)
            relatorio.delete()
        except PermissionError:
            os.remove(relatorio.arquivo.path)  # Força a exclusão em caso de erro de permissão

    # Redirecionar para a visualização do indicador
    return redirect('visualizar_indicador', curso_id=relatorio.indicador.curso.id, indicador_id=relatorio.indicador.id)



# Enviar Relatório

@login_required
def enviar_ou_substituir_relatorio(request, curso_id, indicador_id):
    curso = get_object_or_404(Curso, id=curso_id)
    indicador = get_object_or_404(IndicadorMan, id=indicador_id)

    if request.method == 'POST':
        arquivo = request.FILES.get('arquivo')
        relatorio_id = request.POST.get('relatorio_id')  # ID do relatório para substituição (se fornecido)

        if arquivo:
            if relatorio_id:
                # Substituir um relatório existente
                relatorio = get_object_or_404(RelatorioPDF, id=relatorio_id, indicador=indicador)
                relatorio.arquivo.delete(save=False)  # Remove fisicamente o arquivo antigo
                relatorio.arquivo = arquivo
                relatorio.usuario_upload = request.user  # Atualiza o usuário que fez a substituição
                relatorio.save()
                acao = 13  # Código para substituição de relatório no log
            else:
                # Criar um novo relatório
                novo_relatorio = RelatorioPDF(
                    indicador=indicador,
                    arquivo=arquivo,
                    usuario_upload=request.user
                )
                novo_relatorio.save()
                acao = 12  # Código para novo envio de relatório no log

            # Registrar no log
            registrar_acao_log(request.user, curso, acao, indicador)
        else:
            return HttpResponseBadRequest("Nenhum arquivo foi enviado.")

    # Redirecionar para a visualização do indicador
    return redirect('visualizar_indicador', curso_id=curso.id, indicador_id=indicador.id)



# Aplicar NSA
@login_required
def aplicar_nsa(request, curso_id, indicador_id):
    curso = get_object_or_404(Curso, id=curso_id)
    indicador = get_object_or_404(IndicadorMan, id=indicador_id)

    # Apagar o documento compartilhado
    indicador.documento_tinymce = None
    indicador.em_edicao = False
    indicador.usuario_editando = None
    indicador.edicao_inicio = None
    indicador.save(update_fields=['documento_tinymce', 'em_edicao', 'usuario_editando', 'edicao_inicio'])

    # Apagar todos os relatórios PDFs associados
    relatorios = indicador.relatorios_pdfs.all()
    for relatorio in relatorios:
        relatorio.arquivo.delete(save=False)  # Apaga o arquivo fisicamente
        relatorio.delete()  # Remove o registro do banco de dados

    # Aplicar o NSA
    indicador.NSA = True
    indicador.nivel_suposto = None
    indicador.save(update_fields=['NSA', 'nivel_suposto'])

    # Registrar a ação no log
    acao = 16  # Código de ação para aplicar NSA
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

#----------------novas implementtações-----------------------------

@login_required
def gerenciar_documento_compartilhado(request, indicador_id):
    indicador = get_object_or_404(IndicadorMan, id=indicador_id)
    timeout = timedelta(minutes=10)

    # Expulsar usuário após timeout
    if indicador.em_edicao and indicador.edicao_inicio and now() - indicador.edicao_inicio > timeout:
        indicador.em_edicao = False
        indicador.usuario_editando = None
        indicador.edicao_inicio = None
        indicador.save()
        return redirect('visualizar_indicador', curso_id=indicador.curso.id, indicador_id=indicador.id)

    # Verificar se outro usuário está editando
    if indicador.em_edicao and indicador.usuario_editando != request.user:
        return HttpResponseForbidden("O documento está sendo editado por outro usuário.")

    # Iniciar ou atualizar o estado de edição
    if not indicador.em_edicao:
        indicador.em_edicao = True
        indicador.usuario_editando = request.user
        indicador.edicao_inicio = now()
        indicador.save()

    if request.method == 'POST':
        documento = request.POST.get('documento_tinymce', '')
        if documento:
            indicador.documento_tinymce = documento
            indicador.edicao_inicio = now()  # Atualiza o timestamp a cada alteração
            indicador.save()

        # **Importante**: Remover o estado de edição antes de redirecionar
        indicador.em_edicao = False
        indicador.usuario_editando = None
        indicador.edicao_inicio = None
        indicador.save()

        # Após salvar e remover o estado de edição, redirecionar
        return redirect('visualizar_indicador', curso_id=indicador.curso.id, indicador_id=indicador.id)

    context = {
        'indicador': indicador,
        'documento_tinymce': indicador.documento_tinymce,
    }
    return render(request, 'indicadores/documentocompartilhado.html', context)


@login_required
def sair_documento_compartilhado(request, indicador_id):
    indicador = get_object_or_404(IndicadorMan, id=indicador_id)
    if indicador.usuario_editando == request.user:
        documento = request.POST.get("documento_tinymce", "")
        if documento:
            indicador.documento_tinymce = documento  # Salva as alterações antes de sair
        indicador.em_edicao = False
        indicador.usuario_editando = None
        indicador.edicao_inicio = None
        indicador.save()
    return redirect('visualizar_indicador', curso_id=indicador.curso.id, indicador_id=indicador.id)
















#____________________________analise de dados

def analise_dados(request):
    """
    Exibe a página de seleção de cursos, dimensões e indicadores para análise de dados.
    """
    cursos = Curso.objects.all()
    dimensoes = [choice[0] for choice in IndicadorInfo.DIMENSAO_CHOICES]
    indicadores = IndicadorInfo.objects.all()

    if request.method == "POST":
        # Processar os dados enviados pelo formulário
        cursos_selecionados = request.POST.getlist("cursos")
        dimensoes_selecionadas = request.POST.getlist("dimensoes")
        indicadores_selecionados = request.POST.getlist("indicadores")
        int_param = int(request.POST.get("int_param"))

        # Redirecionar para a view processar_indicadores
        return processar_indicadores(
            request,
            int_param=int_param,
            cursos=cursos_selecionados,
            dimensoes=dimensoes_selecionadas,
            indicadores=indicadores_selecionados,
        )

    return render(
        request,
        "analisededados/analise_dados.html",
        {
            "cursos": cursos,
            "dimensoes": dimensoes,
            "indicadores": indicadores,
        },
    )



def processar_indicadores(request, int_param, cursos=None, dimensoes=None, indicadores=None):
    """
    Processa e chama a view correspondente para uma lista de IndicadorMan filtrados.

    Args:
        request: Objeto HTTP request.
        int_param (int): Define a view a ser chamada.
                        1 - nuvem_palavras
                        2 - classificador_expressoes
        cursos (list or Curso): Um curso ou lista de cursos para análise.
        dimensoes (list): Lista de dimensões específicas para análise.
        indicadores (list): Lista de nomes de indicadores para análise.

    Returns:
        Resposta da view correspondente.
    """
    # Garantir que cursos seja uma lista de objetos Curso
    if cursos:
        cursos = Curso.objects.filter(id__in=cursos)  # Converte IDs para objetos Curso

    # Garantir que dimensões seja uma lista válida
    if dimensoes and not isinstance(dimensoes, list):
        dimensoes = [dimensao for dimensao in dimensoes if dimensao in [choice[0] for choice in IndicadorInfo.DIMENSAO_CHOICES]]

    # Garantir que indicadores seja uma lista
    if indicadores and not isinstance(indicadores, list):
        indicadores = [indicador.lower() for indicador in indicadores]

    # Lista para coletar os IndicadorMan interessados
    indicadores_man_interessados = []

    if cursos:
        for curso in cursos:
            indicadores_curso = IndicadorMan.objects.filter(curso=curso)

            # Filtrar por dimensões, se fornecidas
            if dimensoes:
                indicadores_curso = indicadores_curso.filter(indicador_info__dimensao__in=dimensoes)

            # Filtrar por nomes de indicadores, se fornecidos
            if indicadores:
                indicadores_curso = indicadores_curso.filter(indicador_info__nome__in=indicadores)

            indicadores_man_interessados.extend(indicadores_curso)

    # Verificar se a lista de indicadores está vazia
    if not indicadores_man_interessados:
        return HttpResponseBadRequest("Nenhum indicador correspondente foi encontrado.")

    # Chamar a view correspondente com os indicadores filtrados
    if int_param == 1:
        return nuvem_palavras(request, indicadores_man_interessados)
    elif int_param == 2:
        return classificador_expressoes(request, indicadores_man_interessados)
    else:
        return HttpResponseBadRequest("Parâmetro inválido para int_param. Use 1 ou 2.")


#---------------tratamento  dos pdfs para analise

def extrair_palavras_pdf(pdf_path):
    """
    Extrai as palavras de um arquivo PDF.

    Args:
        pdf_path (str): Caminho do arquivo PDF.

    Returns:
        list: Lista de palavras extraídas.
    """
    palavras = []
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                texto = page.extract_text()
                if texto:
                    palavras.extend(texto.split())
    except Exception as e:
        print(f"Erro ao ler o PDF {pdf_path}: {e}")
    return palavras


def classificar_palavras(palavras):
    """
    Classifica a frequência das palavras.

    Args:
        palavras (list): Lista de palavras.

    Returns:
        dict: Palavras classificadas com suas frequências.
    """
    return dict(Counter(palavras))


def classificar_palavras_antes_depois(palavras):
    """
    Classifica as palavras mais frequentes antes e depois de cada palavra principal.

    Args:
        palavras (list): Lista de palavras do texto.

    Returns:
        dict: Estrutura contendo palavras principais e suas 5 palavras mais frequentes antes e depois.
    """
    contador_palavras = Counter(palavras)
    palavras_frequentes = [palavra for palavra, _ in contador_palavras.most_common(5)]

    palavras_antes_depois = defaultdict(lambda: {"antes": Counter(), "depois": Counter()})

    for idx, palavra in enumerate(palavras):
        if palavra in palavras_frequentes:
            if idx > 0:  # Palavra antes
                palavras_antes_depois[palavra]["antes"][palavras[idx - 1]] += 1
            if idx < len(palavras) - 1:  # Palavra depois
                palavras_antes_depois[palavra]["depois"][palavras[idx + 1]] += 1

    # Selecionar apenas as 5 mais frequentes antes e depois
    resultado = {}
    for palavra, dados in palavras_antes_depois.items():
        resultado[palavra] = {
            "antes": dict(dados["antes"].most_common(5)),
            "depois": dict(dados["depois"].most_common(5))
        }
    return resultado

#------------------tratamento para expressoes


def classificador_expressoes(request, indicadores):
    """
    Processa os PDFs dos indicadores, classifica palavras antes e depois,
    e redireciona internamente para a view de exibição de gráficos.

    Args:
        request: Objeto HTTP request.
        indicadores (list): Lista de objetos IndicadorMan.

    Returns:
        Resposta da view exibir_graficos.
    """
    resultados_por_indicador = {}

    for indicador in indicadores:
        palavras_totais = []
        # Processa todos os relatórios PDFs associados ao indicador
        for relatorio in indicador.relatorios_pdfs.all():
            palavras = extrair_palavras_pdf(relatorio.arquivo.path)
            palavras_totais.extend(palavras)

        if palavras_totais:
            classificacao_antes_depois = classificar_palavras_antes_depois(palavras_totais)
            resultados_por_indicador[indicador.id] = classificacao_antes_depois

    if not resultados_por_indicador:
        return HttpResponseBadRequest("Nenhum PDF válido encontrado nos indicadores fornecidos.")

    # Redirecionar internamente para exibir_graficos
    return exibir_graficos_expressao(request, resultados_por_indicador)


#-------------tratamento dados nuvem


def nuvem_palavras(request, indicadores):
    """
    Processa os PDFs dos indicadores, realiza a classificação de palavras
    e redireciona internamente para a view de exibição de gráficos.

    Args:
        request: Objeto HTTP request.
        indicadores (list): Lista de objetos IndicadorMan.

    Returns:
        Resposta da view exibir_graficos.
    """
    classificacoes_individuais = {}
    todas_palavras = []

    for indicador in indicadores:
        palavras_totais = []
        # Processa todos os relatórios PDFs associados ao indicador
        for relatorio in indicador.relatorios_pdfs.all():
            palavras = extrair_palavras_pdf(relatorio.arquivo.path)
            palavras_totais.extend(palavras)

        if palavras_totais:
            classificacao = classificar_palavras(palavras_totais)
            classificacoes_individuais[indicador.id] = classificacao
            todas_palavras.extend(palavras_totais)

    # Classificação geral combinada
    classificacao_geral = classificar_palavras(todas_palavras)

    if not classificacoes_individuais:
        return HttpResponseBadRequest("Nenhum PDF válido encontrado nos indicadores fornecidos.")

    # Redirecionamento interno para exibir_graficos
    return exibir_graficos(request, classificacoes_individuais, classificacao_geral)



#_________eexibir gráficos nuvem__________
def exibir_graficos(request, classificacoes_individuais=None, classificacao_geral=None):
    """
    Exibe gráficos interativos baseados nos dados fornecidos por `nuvem_palavras` ou `classificador_expressoes`.

    Args:
        request: Objeto HTTP request.
        classificacoes_individuais (dict): Classificações individuais por indicador (opcional).
        classificacao_geral (dict): Classificação geral combinada (opcional).

    Returns:
        Renderiza a página com o gráfico interativo.
    """
    # Verificar se os dados são da nuvem de palavras
    if classificacoes_individuais and classificacao_geral:
        # Dados para o gráfico
        indicadores_opcoes = list(classificacoes_individuais.keys()) + ["Classificação Geral"]

        # Renderizar gráfico inicial com a classificação geral
        palavras = list(classificacao_geral.keys())
        frequencias = list(classificacao_geral.values())

        fig = go.Figure(
            data=[go.Bar(x=palavras, y=frequencias, marker=dict(color="blue"))],
            layout=go.Layout(title="Classificação Geral de Palavras", xaxis_title="Palavras", yaxis_title="Frequência")
        )

        # Converter o gráfico para HTML
        grafico_html = fig.to_html(full_html=False)

        # Renderizar a página
        return render(
            request,
            "analisededados/exibir_graficos.html",
            {
                "grafico_html": grafico_html,
                "indicadores_opcoes": indicadores_opcoes,
                "classificacoes_individuais": classificacoes_individuais,
                "classificacao_geral": classificacao_geral,
            },
        )
    else:
        return HttpResponseBadRequest("Dados inválidos ou insuficientes para exibir gráficos.")



#-----------------grafico expressoes

def exibir_graficos_expressao(request, resultados_por_indicador):
    """
    Exibe gráficos para os dados de expressões fornecidos.

    Args:
        request: Objeto HTTP request.
        resultados_por_indicador (dict): Dicionário com palavras principais e suas palavras antes/depois.

    Returns:
        Renderiza a página com gráficos interativos.
    """
    if not resultados_por_indicador:
        return HttpResponseBadRequest("Dados insuficientes para gerar gráficos.")

    # Preparar dados para gráficos
    relatorios = list(resultados_por_indicador.keys())
    dados_graficos = {}

    for relatorio, classificacao in resultados_por_indicador.items():
        palavras_principais = classificacao.keys()
        antes = [classificacao[p]["antes"] for p in palavras_principais]
        depois = [classificacao[p]["depois"] for p in palavras_principais]
        dados_graficos[relatorio] = {"palavras_principais": palavras_principais, "antes": antes, "depois": depois}

    # Gráfico 1: Barras Empilhadas
    fig_barras = go.Figure()
    for relatorio, dados in dados_graficos.items():
        fig_barras.add_trace(
            go.Bar(
                name=f'{relatorio} - Antes',
                x=list(dados["palavras_principais"]),
                y=[sum(a.values()) for a in dados["antes"]],
                marker_color="blue",
            )
        )
        fig_barras.add_trace(
            go.Bar(
                name=f'{relatorio} - Depois',
                x=list(dados["palavras_principais"]),
                y=[sum(d.values()) for d in dados["depois"]],
                marker_color="green",
            )
        )
    fig_barras.update_layout(
        title="Frequência de Palavras Antes e Depois",
        barmode="stack",
        xaxis_title="Palavras Principais",
        yaxis_title="Frequência",
    )
    grafico_barras_html = fig_barras.to_html(full_html=False)

    # Gráfico 2: Rede
    fig_rede = go.Figure()
    for relatorio, dados in dados_graficos.items():
        G = nx.Graph()
        for i, palavra_principal in enumerate(dados["palavras_principais"]):
            G.add_node(palavra_principal, size=20)
            for antes, freq in dados["antes"][i].items():
                G.add_edge(palavra_principal, antes, weight=freq)
            for depois, freq in dados["depois"][i].items():
                G.add_edge(palavra_principal, depois, weight=freq)

        pos = nx.spring_layout(G)
        edge_x = []
        edge_y = []
        for edge in G.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.append((x0, x1))
            edge_y.append((y0, y1))

        for node, (x, y) in pos.items():
            fig_rede.add_trace(
                go.Scatter(
                    x=[x],
                    y=[y],
                    mode="markers+text",
                    text=[node],
                    marker=dict(size=10),
                )
            )

    fig_rede.update_layout(
        title="Rede de Palavras",
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False),
    )
    grafico_rede_html = fig_rede.to_html(full_html=False)

    return render(
        request,
        "analisededados/exibir_graficos_expressao.html",
        {
            "grafico_barras_html": grafico_barras_html,
            "grafico_rede_html": grafico_rede_html,
        },
    )



