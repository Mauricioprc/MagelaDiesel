import sqlite3

import criar_usuario
from werkzeug.security import check_password_hash


def test_usuarios_do_ambiente_le_pares_sequenciais(monkeypatch):
    monkeypatch.setenv("USUARIO_1", "maria")
    monkeypatch.setenv("SENHA_1", "senha123456")
    monkeypatch.setenv("USUARIO_2", "joao")
    monkeypatch.setenv("SENHA_2", "outrasenha789")
    monkeypatch.delenv("USUARIO_3", raising=False)
    monkeypatch.delenv("SENHA_3", raising=False)

    usuarios = criar_usuario._usuarios_do_ambiente()
    assert usuarios == [("maria", "senha123456"), ("joao", "outrasenha789")]


def test_usuarios_do_ambiente_para_no_primeiro_numero_faltando(monkeypatch):
    monkeypatch.setenv("USUARIO_1", "maria")
    monkeypatch.setenv("SENHA_1", "senha123456")
    monkeypatch.delenv("USUARIO_2", raising=False)
    monkeypatch.delenv("SENHA_2", raising=False)
    monkeypatch.setenv("USUARIO_3", "joao")
    monkeypatch.setenv("SENHA_3", "outrasenha789")

    usuarios = criar_usuario._usuarios_do_ambiente()
    assert usuarios == [("maria", "senha123456")]


def test_usuarios_do_ambiente_vazio_sem_variaveis(monkeypatch):
    monkeypatch.delenv("USUARIO_1", raising=False)
    monkeypatch.delenv("SENHA_1", raising=False)
    assert criar_usuario._usuarios_do_ambiente() == []


def test_modo_lote_cria_usuarios_com_senha_em_hash(tmp_path, monkeypatch):
    monkeypatch.setattr(criar_usuario, "DB_PATH", tmp_path / "orcamentos.db")
    monkeypatch.setenv("USUARIO_1", "maria")
    monkeypatch.setenv("SENHA_1", "senha123456")
    monkeypatch.delenv("USUARIO_2", raising=False)
    monkeypatch.delenv("SENHA_2", raising=False)

    criar_usuario.modo_lote_do_env()

    conn = sqlite3.connect(tmp_path / "orcamentos.db")
    linha = conn.execute(
        "SELECT senha_hash FROM usuarios WHERE nome_usuario = ?", ("maria",)
    ).fetchone()
    conn.close()

    assert linha is not None
    assert linha[0] != "senha123456"  # nunca em texto puro
    assert check_password_hash(linha[0], "senha123456")


def test_modo_lote_pula_senha_curta(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(criar_usuario, "DB_PATH", tmp_path / "orcamentos.db")
    monkeypatch.setenv("USUARIO_1", "maria")
    monkeypatch.setenv("SENHA_1", "123")
    monkeypatch.delenv("USUARIO_2", raising=False)
    monkeypatch.delenv("SENHA_2", raising=False)

    criar_usuario.modo_lote_do_env()

    conn = sqlite3.connect(tmp_path / "orcamentos.db")
    linha = conn.execute(
        "SELECT * FROM usuarios WHERE nome_usuario = ?", ("maria",)
    ).fetchone()
    conn.close()

    assert linha is None
    assert "pelo menos" in capsys.readouterr().out


def test_modo_lote_atualiza_quando_ja_existe(tmp_path, monkeypatch):
    monkeypatch.setattr(criar_usuario, "DB_PATH", tmp_path / "orcamentos.db")
    monkeypatch.setenv("USUARIO_1", "maria")
    monkeypatch.setenv("SENHA_1", "senha-antiga-123")
    monkeypatch.delenv("USUARIO_2", raising=False)
    monkeypatch.delenv("SENHA_2", raising=False)
    criar_usuario.modo_lote_do_env()

    monkeypatch.setenv("SENHA_1", "senha-nova-456")
    criar_usuario.modo_lote_do_env()

    conn = sqlite3.connect(tmp_path / "orcamentos.db")
    linhas = conn.execute(
        "SELECT senha_hash FROM usuarios WHERE nome_usuario = ?", ("maria",)
    ).fetchall()
    conn.close()

    assert len(linhas) == 1  # não duplicou
    assert check_password_hash(linhas[0][0], "senha-nova-456")
