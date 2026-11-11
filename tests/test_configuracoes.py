import sqlite3

from conftest import _extrair_csrf, login


def _csrf(client, url):
    resposta = client.get(url)
    return _extrair_csrf(resposta.get_data(as_text=True))


def test_configuracoes_exige_login(client):
    resposta = client.get("/configuracoes")
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_configuracoes_mostra_padroes(client):
    login(client)
    resposta = client.get("/configuracoes")
    assert resposta.status_code == 200
    html = resposta.get_data(as_text=True)
    assert "1.100,00" in html
    assert 'value="15"' in html
    assert "nunca" in html


def test_salvar_configuracoes_atualiza_padroes(client):
    login(client)
    token = _csrf(client, "/configuracoes")
    resposta = client.post(
        "/configuracoes",
        data={
            "csrf_token": token,
            "bomba_preco": "1.200,00",
            "validade_dias": "30",
        },
    )
    assert resposta.status_code == 302

    resposta = client.get("/configuracoes")
    html = resposta.get_data(as_text=True)
    assert "1.200,00" in html
    assert 'value="30"' in html


def test_salvar_configuracoes_sem_csrf_falha(client):
    login(client)
    resposta = client.post(
        "/configuracoes", data={"bomba_preco": "1.200,00", "validade_dias": "30"}
    )
    assert resposta.status_code == 400


def test_novo_orcamento_usa_preco_e_validade_padrao_configurados(client):
    login(client)
    token = _csrf(client, "/configuracoes")
    client.post(
        "/configuracoes",
        data={"csrf_token": token, "bomba_preco": "1.300,00", "validade_dias": "20"},
    )

    html_novo = client.get("/orcamentos/novo").get_data(as_text=True)
    assert "1.300,00" in html_novo

    token = _csrf(client, "/orcamentos/novo")
    resposta = client.post(
        "/orcamentos/novo",
        data={
            "csrf_token": token,
            "nome": "Carlos",
            "data": "2026-01-10",
            "bomba_incluida": "1",
            "bomba_descricao": "Desmontar, montar e regular bomba injetora na bancada de teste",
            "bomba_quantidade": "1",
            "bomba_preco": "1.300,00",
        },
    )
    orcamento_id = resposta.headers["Location"].rstrip("/").split("/")[-1]

    conn = sqlite3.connect(client.application.config["DATABASE"])
    validade_dias = conn.execute(
        "SELECT validade_dias FROM orcamentos WHERE id = ?", (orcamento_id,)
    ).fetchone()[0]
    conn.close()
    assert validade_dias == 20


def test_backup_exige_login(client):
    resposta = client.post("/configuracoes/backup")
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_backup_sem_csrf_falha(client):
    login(client)
    resposta = client.post("/configuracoes/backup")
    assert resposta.status_code == 400


def test_backup_gera_arquivo_sqlite_valido_e_atualiza_data(client, tmp_path):
    login(client)

    resposta = client.get("/configuracoes")
    assert "nunca" in resposta.get_data(as_text=True)

    token = _csrf(client, "/configuracoes")
    resposta = client.post("/configuracoes/backup", data={"csrf_token": token})
    assert resposta.status_code == 200
    assert resposta.mimetype == "application/octet-stream"
    assert "attachment" in resposta.headers["Content-Disposition"]
    assert ".db" in resposta.headers["Content-Disposition"]

    caminho = tmp_path / "copia-backup.db"
    caminho.write_bytes(resposta.data)
    conn = sqlite3.connect(str(caminho))
    linhas = conn.execute("SELECT nome_usuario FROM usuarios").fetchall()
    conn.close()
    assert linhas == [("maria",)]

    resposta = client.get("/configuracoes")
    html = resposta.get_data(as_text=True)
    assert "nunca" not in html
