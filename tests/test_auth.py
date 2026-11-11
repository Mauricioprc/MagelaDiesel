from conftest import login


def test_login_pagina_carrega(client):
    resposta = client.get("/login")
    assert resposta.status_code == 200
    assert "Entrar" in resposta.get_data(as_text=True)


def test_rotas_exigem_login(client):
    for rota in ["/", "/orcamentos"]:
        resposta = client.get(rota)
        assert resposta.status_code == 302
        assert "/login" in resposta.headers["Location"]


def test_login_com_senha_errada(client):
    resposta = login(client, senha="errada")
    assert resposta.status_code == 200
    assert "inválidos" in resposta.get_data(as_text=True)


def test_login_com_sucesso_redireciona_para_home(client):
    resposta = login(client)
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/")


def test_login_sem_csrf_e_rejeitado(client):
    client.get("/login")
    resposta = client.post("/login", data={"usuario": "maria", "senha": "senha123"})
    assert resposta.status_code == 400


def test_logout_limpa_sessao(client):
    login(client)
    resposta_home = client.get("/")
    assert resposta_home.status_code == 200

    html = resposta_home.get_data(as_text=True)
    marcador = 'name="csrf_token" value="'
    inicio = html.index(marcador) + len(marcador)
    fim = html.index('"', inicio)
    token = html[inicio:fim]

    client.post("/logout", data={"csrf_token": token})
    resposta = client.get("/")
    assert resposta.status_code == 302


def test_bloqueio_apos_tentativas_repetidas(client, app):
    max_tentativas = app.config["LOGIN_MAX_TENTATIVAS"]
    for _ in range(max_tentativas):
        login(client, senha="errada")

    resposta = login(client, senha="senha123")
    assert "Muitas tentativas" in resposta.get_data(as_text=True)
