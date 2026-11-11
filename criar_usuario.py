"""Cria ou atualiza a senha de um usuário do sistema de orçamentos.

Uso:
    python criar_usuario.py NOME_DE_USUARIO

Não existe tela pública de cadastro: usuários são criados só por este script,
rodado direto no servidor (ou localmente, apontando pro mesmo banco).
"""

import argparse
import getpass
import sqlite3
import sys
from pathlib import Path

from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(
    __import__("os").environ.get(
        "DATABASE_PATH", str(BASE_DIR / "instance" / "orcamentos.db")
    )
)
SCHEMA_PATH = BASE_DIR / "schema.sql"


def garantir_schema(conn):
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())


def main():
    parser = argparse.ArgumentParser(
        description="Cria ou atualiza um usuário do sistema de orçamentos."
    )
    parser.add_argument("usuario", help="Nome de usuário para login")
    args = parser.parse_args()

    nome_usuario = args.usuario.strip()
    if not nome_usuario:
        print("Nome de usuário não pode ser vazio.")
        sys.exit(1)

    senha = getpass.getpass("Senha: ")
    confirmacao = getpass.getpass("Confirme a senha: ")
    if senha != confirmacao:
        print("As senhas não coincidem.")
        sys.exit(1)
    if len(senha) < 6:
        print("A senha deve ter pelo menos 6 caracteres.")
        sys.exit(1)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    garantir_schema(conn)

    senha_hash = generate_password_hash(senha)
    try:
        conn.execute(
            "INSERT INTO usuarios (nome_usuario, senha_hash) VALUES (?, ?)",
            (nome_usuario, senha_hash),
        )
        conn.commit()
        print(f"Usuário '{nome_usuario}' criado com sucesso.")
    except sqlite3.IntegrityError:
        conn.execute(
            "UPDATE usuarios SET senha_hash = ? WHERE nome_usuario = ?",
            (senha_hash, nome_usuario),
        )
        conn.commit()
        print(f"Usuário '{nome_usuario}' já existia; senha atualizada.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
