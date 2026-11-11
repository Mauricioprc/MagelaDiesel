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


def test_erro_sem_nome_preserva_o_que_foi_digitado(client):
    login(client)
    token = _csrf(client, "/orcamentos/novo")

    resposta = client.post(
        "/orcamentos/novo",
        data={
            "csrf_token": token,
            "nome": "",
            "telefone": "9.9999-0000",
            "cidade": "Boa Esperança - MG",
            "veiculo": "Trator Valtra BH180",
            "data": "2026-07-21",
            "item_descricao": "Bico injetor",
            "item_quantidade": "3",
            "item_preco": "80,00",
            "bomba_incluida": "1",
            "bomba_descricao": "Desmontar, montar e regular bomba injetora na bancada de teste",
            "bomba_quantidade": "1",
            "bomba_preco": "1.100,00",
        },
    )
    assert resposta.status_code == 400
    html = resposta.get_data(as_text=True)
    assert "9.9999-0000" in html
    assert "Boa Esperança - MG" in html
    assert "Trator Valtra BH180" in html
    assert "Bico injetor" in html
    assert "80,00" in html


def test_editar_sem_nome_preserva_o_que_foi_digitado(client):
    login(client)
    token = _csrf(client, "/orcamentos/novo")
    resposta = client.post(
        "/orcamentos/novo",
        data={
            "csrf_token": token,
            "nome": "Pedro",
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
            "nome": "",
            "veiculo": "Trator Massey Ferguson",
            "data": "2026-07-21",
            "item_descricao": "Jogo de juntas",
            "item_quantidade": "2",
            "item_preco": "45,00",
            "bomba_incluida": "0",
        },
    )
    assert resposta_editar.status_code == 400
    html = resposta_editar.get_data(as_text=True)
    assert "Trator Massey Ferguson" in html
    assert "Jogo de juntas" in html
    assert "45,00" in html


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


def test_pagina_novo_mostra_sugestao_de_cliente_e_veiculo(client):
    login(client)
    token = _csrf(client, "/orcamentos/novo")
    client.post(
        "/orcamentos/novo",
        data={
            "csrf_token": token,
            "nome": "Fazenda Santa Rita",
            "telefone": "9.8888-1111",
            "cidade": "Guapé - MG",
            "veiculo": "Trator New Holland TL75",
            "data": "2026-07-21",
            "item_descricao": "Bico injetor",
            "item_quantidade": "1",
            "item_preco": "90,00",
            "bomba_incluida": "0",
        },
    )

    pagina = client.get("/orcamentos/novo")
    html = pagina.get_data(as_text=True)
    assert "Fazenda Santa Rita" in html
    assert "9.8888-1111" in html
    assert "Trator New Holland TL75" in html


def test_selecionar_cliente_conhecido_preenche_telefone_e_cidade(client):
    login(client)
    token = _csrf(client, "/orcamentos/novo")
    client.post(
        "/orcamentos/novo",
        data={
            "csrf_token": token,
            "nome": "Joao Pereira",
            "telefone": "9.7777-2222",
            "cidade": "Campo Belo - MG",
            "data": "2026-07-21",
            "item_descricao": "Filtro",
            "item_quantidade": "1",
            "item_preco": "20,00",
            "bomba_incluida": "0",
        },
    )

    pagina = client.get("/orcamentos/novo")
    html = pagina.get_data(as_text=True)
    assert '"Joao Pereira"' in html
    assert '"telefone": "9.7777-2222"' in html
    assert '"cidade": "Campo Belo - MG"' in html


def test_buscar_por_veiculo_exige_login(client):
    resposta = client.get("/orcamentos/buscar-por-veiculo?veiculo=Trator")
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_buscar_por_veiculo_encontra_de_qualquer_cliente(client):
    login(client)
    token = _csrf(client, "/orcamentos/novo")
    client.post(
        "/orcamentos/novo",
        data={
            "csrf_token": token,
            "nome": "Cliente A",
            "veiculo": "Trator Agrale 4230",
            "data": "2026-07-21",
            "item_descricao": "Bico injetor",
            "item_quantidade": "2",
            "item_preco": "90,00",
            "bomba_incluida": "0",
        },
    )
    token2 = _csrf(client, "/orcamentos/novo")
    client.post(
        "/orcamentos/novo",
        data={
            "csrf_token": token2,
            "nome": "Cliente B",
            "veiculo": "Trator Agrale 4230",
            "data": "2026-07-22",
            "item_descricao": "Jogo de anéis",
            "item_quantidade": "1",
            "item_preco": "150,00",
            "bomba_incluida": "0",
        },
    )

    resposta = client.get("/orcamentos/buscar-por-veiculo?veiculo=Agrale")
    assert resposta.status_code == 200
    dados = resposta.get_json()
    nomes = [r["cliente_nome"] for r in dados["resultados"]]
    assert "Cliente A" in nomes
    assert "Cliente B" in nomes
    # mais recente primeiro
    assert dados["resultados"][0]["cliente_nome"] == "Cliente B"
    assert dados["resultados"][0]["itens"][0]["descricao"] == "Jogo de anéis"


def test_buscar_por_veiculo_texto_curto_nao_busca(client):
    login(client)
    resposta = client.get("/orcamentos/buscar-por-veiculo?veiculo=A")
    assert resposta.get_json() == {"resultados": []}


def test_buscar_por_veiculo_exclui_o_proprio_orcamento(client):
    login(client)
    token = _csrf(client, "/orcamentos/novo")
    resposta = client.post(
        "/orcamentos/novo",
        data={
            "csrf_token": token,
            "nome": "Cliente C",
            "veiculo": "Trator Valtra BH180",
            "data": "2026-07-21",
            "item_descricao": "Correia",
            "item_quantidade": "1",
            "item_preco": "60,00",
            "bomba_incluida": "0",
        },
    )
    orcamento_id = resposta.headers["Location"].rstrip("/").split("/")[-1]

    resposta_busca = client.get(
        f"/orcamentos/buscar-por-veiculo?veiculo=Valtra&excluir_id={orcamento_id}"
    )
    assert resposta_busca.get_json() == {"resultados": []}


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
