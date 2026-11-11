import os
import sqlite3
import sys
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("SECRET_KEY", "chave-de-teste")

import auth  # noqa: E402
from app import create_app  # noqa: E402


@pytest.fixture(autouse=True)
def limpar_tentativas_login():
    auth._tentativas.clear()
    yield
    auth._tentativas.clear()


@pytest.fixture
def app(tmp_path):
    db_path = tmp_path / "orcamentos-teste.db"
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(db_path),
            "SECRET_KEY": "chave-de-teste",
            "SESSION_COOKIE_SECURE": False,
        }
    )

    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO usuarios (nome_usuario, senha_hash) VALUES (?, ?)",
        ("maria", generate_password_hash("senha123")),
    )
    conn.commit()
    conn.close()

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, usuario="maria", senha="senha123"):
    resposta = client.get("/login")
    token = _extrair_csrf(resposta.get_data(as_text=True))
    return client.post(
        "/login",
        data={"usuario": usuario, "senha": senha, "csrf_token": token},
        follow_redirects=False,
    )


def _extrair_csrf(html):
    marcador = 'name="csrf_token" value="'
    inicio = html.index(marcador) + len(marcador)
    fim = html.index('"', inicio)
    return html[inicio:fim]
