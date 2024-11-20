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
import plotly.graph_objects as go
from django.http import HttpResponseBadRequest, HttpResponseRedirect
import PyPDF2
from collections import Counter, defaultdict
import plotly.graph_objects as go
import networkx as nx

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
    nome_relatorio = os.path.basename(indicador_man.conteudo.name) if indicador_man.conteudo else None

    context = {
        'curso': curso,
        'indicador_man': indicador_man,
        'nsa_form': nsa_form,
        'nivel_suposto_form': nivel_suposto_form,
        'relatorio_form': relatorio_form,
        'tabela_conceitos': indicador_info.tabela_conceitos,
        'mensagem_aviso': indicador_info.mensagem_aviso,
        'tabela_nome': indicador_info.nome,
        'nome_relatorio': nome_relatorio  # Adicione o nome do relatório ao contexto
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

#----------------novas implementtações-----------------------------


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
        if indicador.conteudo:
            palavras = extrair_palavras_pdf(indicador.conteudo.path)
            classificacao_antes_depois = classificar_palavras_antes_depois(palavras)
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
        if indicador.conteudo:
            palavras = extrair_palavras_pdf(indicador.conteudo.path)
            classificacao = classificar_palavras(palavras)
            classificacoes_individuais[indicador.id] = classificacao
            todas_palavras.extend(palavras)

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



