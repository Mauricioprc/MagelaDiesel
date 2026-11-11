"""Geração do PDF do orçamento, igual ao modelo de papel.

Desenhado direto num Canvas do reportlab (sem Platypus) porque a regra de
ajuste de fonte/paginação (ver CLAUDE.md) precisa medir a altura real do
conteúdo pra decidir entre tamanho normal, compacto ou várias páginas —
mais fácil de controlar desenhando à mão do que deixando o reportlab
"fluir" o conteúdo sozinho.
"""

import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from dinheiro import centavos_para_reais

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONTES_DIR = os.path.join(BASE_DIR, "static", "fonts")
IMG_DIR = os.path.join(BASE_DIR, "static", "img")

FONTE = "Vera"
FONTE_NEGRITO = "Vera-Bold"
FONTE_ITALICO = "Vera-Italic"
FONTE_NEGRITO_ITALICO = "Vera-BoldItalic"

_FONTES_REGISTRADAS = False


def _registrar_fontes():
    global _FONTES_REGISTRADAS
    if _FONTES_REGISTRADAS:
        return
    pdfmetrics.registerFont(TTFont(FONTE, os.path.join(FONTES_DIR, "Vera.ttf")))
    pdfmetrics.registerFont(TTFont(FONTE_NEGRITO, os.path.join(FONTES_DIR, "VeraBd.ttf")))
    pdfmetrics.registerFont(TTFont(FONTE_ITALICO, os.path.join(FONTES_DIR, "VeraIt.ttf")))
    pdfmetrics.registerFont(
        TTFont(FONTE_NEGRITO_ITALICO, os.path.join(FONTES_DIR, "VeraBI.ttf"))
    )
    _FONTES_REGISTRADAS = True


PAGINA_W, PAGINA_H = A4
MARGEM_X = 42
MARGEM_TOPO = 34
MARGEM_BASE = 34
LARGURA_UTIL = PAGINA_W - 2 * MARGEM_X

COL_QTD = 55
COL_UNIT = 85
COL_TOTAL = 85
COL_DESC = LARGURA_UTIL - COL_QTD - COL_UNIT - COL_TOTAL
LARGURAS_COLUNAS = [COL_QTD, COL_DESC, COL_UNIT, COL_TOTAL]

MODO_NORMAL = {"fonte": 10, "linha": 18}
MODO_COMPACTO = {"fonte": 8, "linha": 14}

ALTURA_CABECALHO_TABELA = 18
ALTURA_GARANTIA = 20
ALTURA_RODAPE = 24
ENDERECO_LINHA_1 = "Av. Joaquim Três Pontas, n° 430, Bairro: Santa Terezinha"
ENDERECO_LINHA_2 = "Boa Esperança - MG 37170-000 · Tel.: (35) 3851-2837"

LOGOS_MARCAS = [
    ("LogoCat.png", "CAT"),
    ("Logodelphi.png", "Delphi"),
    ("Logonew-holland.png", "New Holland Agriculture"),
    ("logoBosch.png", "Bosch"),
    ("Logocase.png", "Case IH Agriculture"),
]


def _quebrar_linhas(texto, fonte, tamanho, largura_max):
    """Quebra um texto em linhas que cabem em largura_max, em pontos."""
    palavras = (texto or "").split()
    if not palavras:
        return [""]

    linhas = []
    linha_atual = ""
    for palavra in palavras:
        candidata = (linha_atual + " " + palavra).strip()
        if pdfmetrics.stringWidth(candidata, fonte, tamanho) <= largura_max:
            linha_atual = candidata
            continue

        if linha_atual:
            linhas.append(linha_atual)

        # a própria palavra não cabe sozinha: quebra por caractere
        if pdfmetrics.stringWidth(palavra, fonte, tamanho) > largura_max:
            pedaco = ""
            for caractere in palavra:
                candidata_pedaco = pedaco + caractere
                if pdfmetrics.stringWidth(candidata_pedaco, fonte, tamanho) > largura_max and pedaco:
                    linhas.append(pedaco)
                    pedaco = caractere
                else:
                    pedaco = candidata_pedaco
            linha_atual = pedaco
        else:
            linha_atual = palavra

    if linha_atual:
        linhas.append(linha_atual)
    return linhas or [""]


class _LinhaTabela:
    """Uma linha pronta pra desenhar: valores já formatados + altura real."""

    def __init__(self, quantidade, descricao, unitario, total, modo):
        self.quantidade = quantidade
        self.unitario = unitario
        self.total = total
        self.linhas_descricao = _quebrar_linhas(
            descricao, FONTE, modo["fonte"], COL_DESC - 16
        )
        self.altura = max(modo["linha"], len(self.linhas_descricao) * modo["linha"])


def _montar_linhas_itens(itens, modo):
    linhas = []
    for item in itens:
        linhas.append(
            _LinhaTabela(
                quantidade=f"{item['quantidade']:02d}",
                descricao=(item["descricao"] or "").upper(),
                unitario=centavos_para_reais(item["preco_centavos"]),
                total=centavos_para_reais(item["quantidade"] * item["preco_centavos"]),
                modo=modo,
            )
        )
    return linhas


def _altura_bloco_final(orcamento, modo, incluir_subtotal=True):
    """Altura (em pontos) do que vem depois dos itens: subtotal (logo
    abaixo do último item), 3 linhas em branco + bomba (se incluída),
    total, garantia e rodapé. Só aparece na última página.
    """
    altura = 0
    if incluir_subtotal:
        altura += modo["linha"]
    if orcamento["bomba_incluida"]:
        altura += 3 * modo["linha"]  # pula 3 linhas antes do serviço padrão
        linha_bomba = _LinhaTabela(
            quantidade="01",
            descricao=orcamento["bomba_descricao"],
            unitario="",
            total="",
            modo=modo,
        )
        altura += linha_bomba.altura
    altura += modo["linha"]  # linha do total
    altura += ALTURA_GARANTIA + ALTURA_RODAPE
    return altura


def _altura_disponivel_para_itens(modo, com_bloco_final, orcamento=None):
    topo_fixo = MARGEM_TOPO + ALTURA_CABECALHO + ALTURA_INFO_CLIENTE + ALTURA_CABECALHO_TABELA
    disponivel = PAGINA_H - topo_fixo - MARGEM_BASE
    if com_bloco_final:
        disponivel -= _altura_bloco_final(orcamento, modo)
    return disponivel


ALTURA_CABECALHO = 70
ALTURA_INFO_CLIENTE = 54


def _cabe_em_uma_pagina(linhas, orcamento, modo):
    disponivel = _altura_disponivel_para_itens(modo, com_bloco_final=True, orcamento=orcamento)
    altura_itens = sum(linha.altura for linha in linhas)
    return altura_itens <= disponivel, disponivel, altura_itens


def _paginar(linhas, orcamento, modo):
    """Distribui as linhas de item pelas páginas. A última página reserva
    espaço pro subtotal/bomba/total/garantia/rodapé; as anteriores usam
    toda a altura só com itens.
    """
    disponivel_normal = _altura_disponivel_para_itens(modo, com_bloco_final=False)
    paginas = []
    pagina_atual = []
    altura_atual = 0
    for linha in linhas:
        if pagina_atual and altura_atual + linha.altura > disponivel_normal:
            paginas.append(pagina_atual)
            pagina_atual = []
            altura_atual = 0
        pagina_atual.append(linha)
        altura_atual += linha.altura
    paginas.append(pagina_atual)

    # garante espaço pro bloco final na última página; se não couber,
    # empurra o excedente pra uma página nova.
    disponivel_ultima = _altura_disponivel_para_itens(
        modo, com_bloco_final=True, orcamento=orcamento
    )
    while paginas and sum(l.altura for l in paginas[-1]) > disponivel_ultima:
        excedente = paginas[-1].pop()
        if not paginas[-1]:
            paginas[-1].append(excedente)
            break
        paginas.append([excedente])

    return paginas


def _desenhar_cabecalho(c, orcamento):
    y = PAGINA_H - MARGEM_TOPO
    logo_md = os.path.join(IMG_DIR, "LogoMD.png")
    altura_logo = 34
    largura_logo = altura_logo * ImageReader(logo_md).getSize()[0] / ImageReader(logo_md).getSize()[1]
    c.drawImage(
        logo_md,
        MARGEM_X,
        y - altura_logo,
        width=largura_logo,
        height=altura_logo,
        mask="auto",
    )

    texto_x = MARGEM_X + largura_logo + 10
    c.setFont(FONTE_NEGRITO, 9)
    texto_y = y - 9
    c.drawString(texto_x, texto_y, "MAGELA DIESEL")
    largura_titulo = pdfmetrics.stringWidth("MAGELA DIESEL", FONTE_NEGRITO, 9)
    c.line(texto_x, texto_y - 1.5, texto_x + largura_titulo, texto_y - 1.5)

    c.setFont(FONTE_ITALICO, 8)
    c.drawString(texto_x, texto_y - 12, ENDERECO_LINHA_1)
    c.drawString(texto_x, texto_y - 22, ENDERECO_LINHA_2)

    # logos das marcas, alinhados à direita, todas na caixa do tamanho da CAT
    altura_caixa_logo = 16
    espaco = 8
    x_direita = MARGEM_X + LARGURA_UTIL

    caminho_cat = os.path.join(IMG_DIR, LOGOS_MARCAS[0][0])
    cat_lw, cat_lh = ImageReader(caminho_cat).getSize()
    caixa_largura = altura_caixa_logo * cat_lw / cat_lh

    largura_total = caixa_largura * len(LOGOS_MARCAS) + espaco * (len(LOGOS_MARCAS) - 1)

    x = x_direita - largura_total
    for arquivo, _nome in LOGOS_MARCAS:
        caminho = os.path.join(IMG_DIR, arquivo)
        lw, lh = ImageReader(caminho).getSize()
        escala = min(caixa_largura / lw, altura_caixa_logo / lh)
        largura_img = lw * escala
        altura_img = lh * escala
        c.drawImage(
            caminho,
            x + (caixa_largura - largura_img) / 2,
            y - altura_caixa_logo + (altura_caixa_logo - altura_img) / 2,
            width=largura_img,
            height=altura_img,
            mask="auto",
        )
        x += caixa_largura + espaco

    linha_y = y - altura_logo - 6
    c.setLineWidth(1)
    c.line(MARGEM_X, linha_y, MARGEM_X + LARGURA_UTIL, linha_y)
    return linha_y - 14


def _data_br(data_iso):
    try:
        ano, mes, dia = data_iso.split("-")
        return f"{dia} / {mes} / {ano[2:]}"
    except (ValueError, AttributeError):
        return data_iso or ""


def _desenhar_info_cliente(c, orcamento, y):
    tamanho = 11
    c.setFont(FONTE, tamanho)
    c.drawString(MARGEM_X, y, f"NOME = {(orcamento['cliente_nome'] or '').upper()}")
    c.setFont(FONTE_NEGRITO, 13)
    titulo = "ORÇAMENTO"
    largura_titulo = pdfmetrics.stringWidth(titulo, FONTE_NEGRITO, 13)
    c.drawString(MARGEM_X + LARGURA_UTIL - largura_titulo, y - 1, titulo)

    y -= 15
    c.setFont(FONTE, tamanho)
    c.drawString(MARGEM_X, y, f"TEL = {orcamento['telefone'] or '—'}")
    c.drawString(MARGEM_X + 240, y, f"CIDADE = {(orcamento['cidade'] or '—').upper()}")

    y -= 15
    c.drawString(MARGEM_X, y, f"VEÍCULO = {(orcamento['veiculo'] or '—').upper()}")
    c.drawString(MARGEM_X + 240, y, f"DATA = {_data_br(orcamento['data'])}")

    return y - 20


def _desenhar_cabecalho_tabela(c, y, modo):
    x = MARGEM_X
    c.setFont(FONTE_NEGRITO_ITALICO, modo["fonte"])
    titulos = ["QUANT", "DESCRIÇÃO", "UNIT", "TOTAL"]
    for titulo, largura in zip(titulos, LARGURAS_COLUNAS):
        c.rect(x, y - ALTURA_CABECALHO_TABELA, largura, ALTURA_CABECALHO_TABELA)
        largura_texto = pdfmetrics.stringWidth(titulo, FONTE_NEGRITO_ITALICO, modo["fonte"])
        c.drawString(
            x + (largura - largura_texto) / 2,
            y - ALTURA_CABECALHO_TABELA + (ALTURA_CABECALHO_TABELA - modo["fonte"]) / 2 + 2,
            titulo,
        )
        x += largura
    return y - ALTURA_CABECALHO_TABELA


def _desenhar_linha(c, y, altura, valores, modo, negrito_total=False, italico_rotulo=None):
    """valores = [quantidade, linhas_descricao(list), unitario, total]."""
    x = MARGEM_X
    quantidade, linhas_descricao, unitario, total = valores
    c.setFont(FONTE, modo["fonte"])

    for largura in LARGURAS_COLUNAS:
        c.rect(x, y - altura, largura, altura)
        x += largura

    x = MARGEM_X
    if quantidade:
        c.drawString(x + 6, y - modo["fonte"] - 3, quantidade)
    x += COL_QTD

    for i, linha_texto in enumerate(linhas_descricao):
        c.drawString(x + 6, y - modo["fonte"] - 3 - i * modo["linha"], linha_texto)
    x += COL_DESC

    if italico_rotulo:
        c.setFont(FONTE_ITALICO, modo["fonte"])
        c.drawString(x + 6, y - modo["fonte"] - 3, italico_rotulo)
    elif unitario:
        c.drawString(x + 6, y - modo["fonte"] - 3, unitario)
    x += COL_UNIT

    if total:
        c.setFont(FONTE_NEGRITO if negrito_total else FONTE, modo["fonte"])
        c.drawString(x + 6, y - modo["fonte"] - 3, total)

    return y - altura


def _desenhar_garantia_e_rodape(c, y):
    c.setFont(FONTE_NEGRITO, 10)
    c.drawString(MARGEM_X, y - 14, "Garantia de 90 dias por Defeito de Fábrica")

    rodape_y = MARGEM_BASE
    c.setFont(FONTE_ITALICO, 9)
    c.setFillGray(0.55)
    c.drawString(MARGEM_X, rodape_y, "Orçamento válido por 15 dias")
    c.setFillGray(0)
    texto_direita = "Obrigado! Volte Sempre!"
    largura = pdfmetrics.stringWidth(texto_direita, FONTE_ITALICO, 9)
    c.drawString(MARGEM_X + LARGURA_UTIL - largura, rodape_y, texto_direita)


def gerar_pdf_orcamento(orcamento, itens):
    """orcamento: sqlite3.Row da tabela orcamentos. itens: lista de sqlite3.Row da tabela itens.

    Devolve os bytes do PDF pronto.
    """
    _registrar_fontes()

    import io

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setTitle(f"Orçamento - {orcamento['cliente_nome']}")

    subtotal_centavos = sum(item["quantidade"] * item["preco_centavos"] for item in itens)
    bomba_total_centavos = (
        orcamento["bomba_quantidade"] * orcamento["bomba_preco_centavos"]
        if orcamento["bomba_incluida"]
        else 0
    )
    total_centavos = subtotal_centavos + bomba_total_centavos

    linhas_normal = _montar_linhas_itens(itens, MODO_NORMAL)
    cabe_normal, disponivel_normal, altura_normal = _cabe_em_uma_pagina(
        linhas_normal, orcamento, MODO_NORMAL
    )

    if cabe_normal:
        modo = MODO_NORMAL
        linhas = linhas_normal
        paginas = [linhas]
    else:
        linhas_compacto = _montar_linhas_itens(itens, MODO_COMPACTO)
        cabe_compacto, disponivel_compacto, altura_compacto = _cabe_em_uma_pagina(
            linhas_compacto, orcamento, MODO_COMPACTO
        )
        if cabe_compacto:
            modo = MODO_COMPACTO
            linhas = linhas_compacto
            paginas = [linhas]
        else:
            modo = MODO_NORMAL
            linhas = linhas_normal
            paginas = _paginar(linhas, orcamento, MODO_NORMAL)

    total_paginas = len(paginas)

    for indice, linhas_pagina in enumerate(paginas):
        pagina_num = indice + 1
        e_ultima = pagina_num == total_paginas

        y = _desenhar_cabecalho(c, orcamento)
        y = _desenhar_info_cliente(c, orcamento, y)

        if total_paginas > 1:
            c.setFont(FONTE_ITALICO, 9)
            c.drawRightString(
                MARGEM_X + LARGURA_UTIL, y + 14, f"Pág. {pagina_num}/{total_paginas}"
            )

        y = _desenhar_cabecalho_tabela(c, y, modo)

        for linha in linhas_pagina:
            y = _desenhar_linha(
                c,
                y,
                linha.altura,
                [linha.quantidade, linha.linhas_descricao, linha.unitario, linha.total],
                modo,
            )

        if e_ultima:
            # o subtotal vai logo na linha de baixo do último item, sem
            # preencher o espaço sobrando com linhas em branco
            y = _desenhar_linha(
                c,
                y,
                modo["linha"],
                ["", [""], "", centavos_para_reais(subtotal_centavos)],
                modo,
                negrito_total=True,
                italico_rotulo="SUBTOTAL",
            )

            if orcamento["bomba_incluida"]:
                for _ in range(3):  # pula 3 linhas antes do serviço padrão
                    y = _desenhar_linha(c, y, modo["linha"], ["", [""], "", ""], modo)

                linha_bomba = _LinhaTabela(
                    quantidade="01",
                    descricao=orcamento["bomba_descricao"],
                    unitario=centavos_para_reais(orcamento["bomba_preco_centavos"]),
                    total=centavos_para_reais(bomba_total_centavos),
                    modo=modo,
                )
                y = _desenhar_linha(
                    c,
                    y,
                    linha_bomba.altura,
                    [
                        linha_bomba.quantidade,
                        linha_bomba.linhas_descricao,
                        linha_bomba.unitario,
                        linha_bomba.total,
                    ],
                    modo,
                )

            y = _desenhar_linha(
                c,
                y,
                modo["linha"],
                ["", [""], "", centavos_para_reais(total_centavos)],
                modo,
                negrito_total=True,
                italico_rotulo="TOTAL",
            )

            _desenhar_garantia_e_rodape(c, y)

        c.showPage()

    c.save()
    return buffer.getvalue()
