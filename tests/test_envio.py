import time

from conftest import _extrair_csrf, login


def _csrf(client, url):
    resposta = client.get(url)
    return _extrair_csrf(resposta.get_data(as_text=True))


def _criar_orcamento(client, **extras):
    token = _csrf(client, "/orcamentos/novo")
    dados = {
        "csrf_token": token,
        "nome": "Lucas",
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
    return resposta.headers["Location"].rstrip("/").split("/")[-1]


def _marcar_enviado(client, orcamento_id):
    token = _csrf(client, f"/orcamentos/{orcamento_id}")
    return client.post(
        f"/orcamentos/{orcamento_id}/marcar-enviado",
        data={"csrf_token": token},
    )


def test_marcar_enviado_exige_login(client):
    resposta = client.post("/orcamentos/1/marcar-enviado")
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_marcar_enviado_404_para_orcamento_inexistente(client):
    login(client)
    token = _csrf(client, "/orcamentos/novo")
    resposta = client.post(
        "/orcamentos/999/marcar-enviado", data={"csrf_token": token}
    )
    assert resposta.status_code == 404


def test_marcar_enviado_grava_copia_e_retorna_json(client):
    login(client)
    orcamento_id = _criar_orcamento(client)

    resposta = _marcar_enviado(client, orcamento_id)
    assert resposta.status_code == 200
    dados = resposta.get_json()
    assert "enviado_em_formatado" in dados
    assert dados["url_pdf_enviado"] == f"/orcamentos/{orcamento_id}/pdf-enviado"


def test_pdf_enviado_sem_envio_da_404(client):
    login(client)
    orcamento_id = _criar_orcamento(client)
    resposta = client.get(f"/orcamentos/{orcamento_id}/pdf-enviado")
    assert resposta.status_code == 404


def test_pdf_enviado_serve_copia_guardada(client):
    login(client)
    orcamento_id = _criar_orcamento(client)
    _marcar_enviado(client, orcamento_id)

    resposta = client.get(f"/orcamentos/{orcamento_id}/pdf-enviado")
    assert resposta.status_code == 200
    assert resposta.mimetype == "application/pdf"
    assert resposta.data.startswith(b"%PDF")


def test_detalhe_mostra_enviado_em_apos_marcar(client):
    login(client)
    orcamento_id = _criar_orcamento(client)

    antes = client.get(f"/orcamentos/{orcamento_id}").get_data(as_text=True)
    assert "Enviado ao cliente em" not in antes

    _marcar_enviado(client, orcamento_id)

    depois = client.get(f"/orcamentos/{orcamento_id}").get_data(as_text=True)
    assert "Enviado ao cliente em" in depois
    assert "Ver PDF enviado" in depois


def test_editado_depois_do_envio_mostra_aviso(client):
    login(client)
    orcamento_id = _criar_orcamento(client)
    _marcar_enviado(client, orcamento_id)

    time.sleep(1.1)  # garante timestamp diferente (granularidade de segundo)
    token_editar = _csrf(client, f"/orcamentos/{orcamento_id}/editar")
    client.post(
        f"/orcamentos/{orcamento_id}/editar",
        data={
            "csrf_token": token_editar,
            "nome": "Lucas Editado",
            "data": "2026-07-22",
            "item_descricao": "Bicos injetores",
            "item_quantidade": "4",
            "item_preco": "191,00",
            "bomba_incluida": "0",
        },
    )

    html = client.get(f"/orcamentos/{orcamento_id}").get_data(as_text=True)
    assert "Editado em" in html


def test_editado_antes_do_envio_nao_mostra_aviso(client):
    login(client)
    orcamento_id = _criar_orcamento(client)

    token_editar = _csrf(client, f"/orcamentos/{orcamento_id}/editar")
    client.post(
        f"/orcamentos/{orcamento_id}/editar",
        data={
            "csrf_token": token_editar,
            "nome": "Lucas Editado",
            "data": "2026-07-22",
            "item_descricao": "Bicos injetores",
            "item_quantidade": "4",
            "item_preco": "191,00",
            "bomba_incluida": "0",
        },
    )
    time.sleep(1.1)
    _marcar_enviado(client, orcamento_id)

    html = client.get(f"/orcamentos/{orcamento_id}").get_data(as_text=True)
    assert "Editado em" not in html
