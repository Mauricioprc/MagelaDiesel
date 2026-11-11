import re

from conftest import _extrair_csrf, login

from pdf import gerar_pdf_orcamento


def _contar_paginas(pdf_bytes):
    return len(re.findall(rb"/Type\s*/Page[^s]", pdf_bytes))


def _csrf(client, url):
    resposta = client.get(url)
    return _extrair_csrf(resposta.get_data(as_text=True))


def _criar_orcamento(client, **extras):
    token = _csrf(client, "/orcamentos/novo")
    dados = {
        "csrf_token": token,
        "nome": "Lucas",
        "telefone": "9.9726-1741",
        "cidade": "Guapé - MG",
        "veiculo": "Trator Agrale",
        "data": "2026-07-21",
        "item_descricao": "Bicos injetores",
        "item_quantidade": "4",
        "item_preco": "191,00",
        "bomba_incluida": "1",
        "bomba_descricao": "Desmontar, montar e regular bomba injetora na bancada de teste",
        "bomba_quantidade": "1",
        "bomba_preco": "1.100,00",
    }
    dados.update(extras)
    resposta = client.post("/orcamentos/novo", data=dados)
    return resposta.headers["Location"]


def test_pdf_exige_login(client):
    resposta = client.get("/orcamentos/1/pdf")
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_pdf_gera_arquivo_valido(client):
    login(client)
    url_detalhe = _criar_orcamento(client)
    orcamento_id = url_detalhe.rstrip("/").split("/")[-1]

    resposta = client.get(f"/orcamentos/{orcamento_id}/pdf")
    assert resposta.status_code == 200
    assert resposta.mimetype == "application/pdf"
    assert resposta.data.startswith(b"%PDF")
    assert "orcamento-Lucas-MagelaDiesel.pdf" in resposta.headers["Content-Disposition"]


def test_pdf_de_orcamento_inexistente_da_404(client):
    login(client)
    resposta = client.get("/orcamentos/999/pdf")
    assert resposta.status_code == 404


class _Linha(dict):
    def __getitem__(self, chave):
        return dict.__getitem__(self, chave)


def _orcamento_fake(bomba_incluida=True, **extras):
    base = {
        "cliente_nome": "Lucas",
        "telefone": "9.9726-1741",
        "cidade": "Guapé - MG",
        "veiculo": "Trator Agrale",
        "data": "2026-07-21",
        "bomba_incluida": bomba_incluida,
        "bomba_descricao": "Desmontar, montar e regular bomba injetora na bancada de teste",
        "bomba_quantidade": 1,
        "bomba_preco_centavos": 110000,
        "validade_dias": 15,
    }
    base.update(extras)
    return _Linha(base)


def _itens_fake(qtd):
    return [
        _Linha(descricao=f"Item {i + 1}", quantidade=(i % 4) + 1, preco_centavos=1000 + i)
        for i in range(qtd)
    ]


def test_orcamento_com_5_itens_cabe_em_uma_pagina():
    pdf_bytes = gerar_pdf_orcamento(_orcamento_fake(), _itens_fake(5))
    assert pdf_bytes.startswith(b"%PDF")
    assert _contar_paginas(pdf_bytes) == 1


def test_orcamento_com_23_itens_cabe_em_uma_pagina():
    pdf_bytes = gerar_pdf_orcamento(_orcamento_fake(), _itens_fake(23))
    assert _contar_paginas(pdf_bytes) == 1


def test_orcamento_com_29_itens_cabe_em_uma_pagina():
    pdf_bytes = gerar_pdf_orcamento(_orcamento_fake(), _itens_fake(29))
    assert _contar_paginas(pdf_bytes) == 1


def test_orcamento_com_40_itens_pagina_em_duas_paginas():
    pdf_bytes = gerar_pdf_orcamento(_orcamento_fake(), _itens_fake(40))
    assert _contar_paginas(pdf_bytes) == 2


def test_sem_itens_nao_quebra():
    pdf_bytes = gerar_pdf_orcamento(_orcamento_fake(bomba_incluida=False), [])
    assert pdf_bytes.startswith(b"%PDF")
    assert _contar_paginas(pdf_bytes) == 1


def test_validade_dias_do_orcamento_aparece_no_rodape():
    pdf_30_dias = gerar_pdf_orcamento(_orcamento_fake(validade_dias=30), _itens_fake(1))
    pdf_15_dias = gerar_pdf_orcamento(_orcamento_fake(validade_dias=15), _itens_fake(1))
    assert pdf_30_dias != pdf_15_dias
