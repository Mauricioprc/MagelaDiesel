from conftest import _extrair_csrf, login
from orcamentos import _nome_arquivo_pdf


def _csrf(client, url):
    resposta = client.get(url)
    return _extrair_csrf(resposta.get_data(as_text=True))


def test_nome_arquivo_pdf_remove_acentos_e_espacos():
    assert _nome_arquivo_pdf("João Pereira") == "orcamento-Joao-Pereira-MagelaDiesel.pdf"


def test_nome_arquivo_pdf_remove_caracteres_especiais():
    assert (
        _nome_arquivo_pdf("Fazenda Boa Vista & Cia.")
        == "orcamento-Fazenda-Boa-Vista-Cia-MagelaDiesel.pdf"
    )


def test_nome_arquivo_pdf_nome_vazio_usa_padrao():
    assert _nome_arquivo_pdf("") == "orcamento-cliente-MagelaDiesel.pdf"


def test_pagina_novo_mostra_bomba_padrao(client):
    login(client)
    resposta = client.get("/orcamentos/novo")
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert "Desmontar, montar e regular bomba injetora" in html
    assert "1.100,00" in html


def test_criar_orcamento_calcula_total_com_bomba(client):
    login(client)
    token = _csrf(client, "/orcamentos/novo")

    resposta = client.post(
        "/orcamentos/novo",
        data={
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
        },
        follow_redirects=False,
    )
    assert resposta.status_code == 302
    assert "/orcamentos/1" in resposta.headers["Location"]

    detalhe = client.get(resposta.headers["Location"])
    html = detalhe.get_data(as_text=True)
    assert "Lucas" in html
    assert "1.864,00" in html  # 4 x 191,00 = 764,00 + bomba 1.100,00


def test_criar_sem_bomba_nao_soma_bomba(client):
    login(client)
    token = _csrf(client, "/orcamentos/novo")

    resposta = client.post(
        "/orcamentos/novo",
        data={
            "csrf_token": token,
            "nome": "José",
            "data": "2026-07-21",
            "item_descricao": "Jogo de arruelas",
            "item_quantidade": "1",
            "item_preco": "66,00",
            "bomba_incluida": "0",
            "bomba_quantidade": "1",
            "bomba_preco": "1.100,00",
        },
    )
    detalhe = client.get(resposta.headers["Location"])
    html = detalhe.get_data(as_text=True)
    assert "66,00" in html
    assert "1.100,00" not in html


def test_criar_sem_nome_retorna_erro(client):
    login(client)
    token = _csrf(client, "/orcamentos/novo")

    resposta = client.post(
        "/orcamentos/novo",
        data={
            "csrf_token": token,
            "nome": "",
            "data": "2026-07-21",
        },
    )
    assert resposta.status_code == 400
    assert "Informe o nome do cliente" in resposta.get_data(as_text=True)


def test_item_sem_descricao_e_ignorado(client):
    login(client)
    token = _csrf(client, "/orcamentos/novo")

    resposta = client.post(
        "/orcamentos/novo",
        data={
            "csrf_token": token,
            "nome": "Maria",
            "data": "2026-07-21",
            "item_descricao": ["", "Bicos"],
            "item_quantidade": ["2", "1"],
            "item_preco": ["50,00", "10,00"],
            "bomba_incluida": "0",
        },
    )
    detalhe = client.get(resposta.headers["Location"])
    html = detalhe.get_data(as_text=True)
    assert "Bicos" in html
    assert "10,00" in html


def test_editar_orcamento_sem_nunca_ter_sido_enviado_nao_mostra_editado_em(client):
    login(client)
    token = _csrf(client, "/orcamentos/novo")
    resposta = client.post(
        "/orcamentos/novo",
        data={
            "csrf_token": token,
            "nome": "Carlos",
            "data": "2026-07-21",
            "item_descricao": "Filtro",
            "item_quantidade": "1",
            "item_preco": "35,00",
            "bomba_incluida": "0",
        },
    )
    url_detalhe = resposta.headers["Location"]
    orcamento_id = url_detalhe.rstrip("/").split("/")[-1]

    token_editar = _csrf(client, f"/orcamentos/{orcamento_id}/editar")
    resposta_editar = client.post(
        f"/orcamentos/{orcamento_id}/editar",
        data={
            "csrf_token": token_editar,
            "nome": "Carlos Alberto",
            "data": "2026-07-22",
            "item_descricao": "Filtro",
            "item_quantidade": "2",
            "item_preco": "35,00",
            "bomba_incluida": "0",
        },
    )
    assert resposta_editar.status_code == 302

    detalhe = client.get(url_detalhe)
    html = detalhe.get_data(as_text=True)
    assert "Carlos Alberto" in html
    # nunca foi enviado pro cliente, então não há "depois do envio" pra marcar
    assert "Editado em" not in html


def test_excluir_orcamento_some_da_lista(client):
    login(client)
    token = _csrf(client, "/orcamentos/novo")
    resposta = client.post(
        "/orcamentos/novo",
        data={
            "csrf_token": token,
            "nome": "Fazenda Teste",
            "data": "2026-07-21",
            "item_descricao": "Item",
            "item_quantidade": "1",
            "item_preco": "10,00",
            "bomba_incluida": "0",
        },
    )
    url_detalhe = resposta.headers["Location"]
    orcamento_id = url_detalhe.rstrip("/").split("/")[-1]

    token_excluir = _csrf(client, url_detalhe)
    resposta_excluir = client.post(
        f"/orcamentos/{orcamento_id}/excluir",
        data={"csrf_token": token_excluir},
    )
    assert resposta_excluir.status_code == 302

    pagina_lista = client.get("/orcamentos")
    assert "Fazenda Teste" not in pagina_lista.get_data(as_text=True)

    pagina_detalhe = client.get(url_detalhe)
    assert pagina_detalhe.status_code == 404


def test_sugestao_usa_ultimo_preco_do_item(client):
    login(client)
    token = _csrf(client, "/orcamentos/novo")
    client.post(
        "/orcamentos/novo",
        data={
            "csrf_token": token,
            "nome": "Cliente 1",
            "data": "2026-07-21",
            "item_descricao": "Bico injetor",
            "item_quantidade": "1",
            "item_preco": "100,00",
            "bomba_incluida": "0",
        },
    )
    token2 = _csrf(client, "/orcamentos/novo")
    client.post(
        "/orcamentos/novo",
        data={
            "csrf_token": token2,
            "nome": "Cliente 2",
            "data": "2026-07-22",
            "item_descricao": "Bico injetor",
            "item_quantidade": "1",
            "item_preco": "150,00",
            "bomba_incluida": "0",
        },
    )

    pagina = client.get("/orcamentos/novo")
    html = pagina.get_data(as_text=True)
    assert '"Bico injetor": 15000' in html
