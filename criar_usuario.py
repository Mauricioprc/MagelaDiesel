"""Cria ou atualiza usuários do sistema de orçamentos.

Dois jeitos de usar:

1) Um usuário por vez, digitando a senha na hora (funciona bem em um
   terminal de verdade, como o Bash console do PythonAnywhere):

    python criar_usuario.py NOME_DE_USUARIO

2) Vários usuários de uma vez, lidos do arquivo .env (não entra no git).
   Defina pares USUARIO_1/SENHA_1, USUARIO_2/SENHA_2 etc. e rode sem
   argumento nenhum:

    python criar_usuario.py

   As senhas só existem em texto puro no .env (do seu jeito de editar);
   no banco elas sempre ficam com hash (werkzeug.security), nunca em
   texto puro.

Não existe tela pública de cadastro: usuários são criados só por este
script.
"""

import argparse
import getpass
import os
import sqlite3
import sys
from pathlib import Path

from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(
    os.environ.get("DATABASE_PATH", str(BASE_DIR / "instance" / "orcamentos.db"))
)
SCHEMA_PATH = BASE_DIR / "schema.sql"

SENHA_MINIMA = 6


def garantir_schema(conn):
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())


def abrir_conexao():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    garantir_schema(conn)
    return conn


def criar_ou_atualizar(conn, nome_usuario, senha):
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


def _usuarios_do_ambiente():
    """Lê USUARIO_1/SENHA_1, USUARIO_2/SENHA_2... até faltar um número."""
    usuarios = []
    i = 1
    while True:
        nome_usuario = os.environ.get(f"USUARIO_{i}")
        senha = os.environ.get(f"SENHA_{i}")
        if not nome_usuario and not senha:
            break
        if not nome_usuario or not senha:
            print(f"USUARIO_{i}/SENHA_{i}: os dois precisam estar definidos. Pulando.")
            i += 1
            continue
        usuarios.append((nome_usuario.strip(), senha))
        i += 1
    return usuarios


def modo_lote_do_env():
    usuarios = _usuarios_do_ambiente()
    if not usuarios:
        print(
            "Nenhum USUARIO_1/SENHA_1 encontrado no ambiente (.env). "
            "Veja o .env.example, ou rode:\n"
            "    python criar_usuario.py NOME_DE_USUARIO"
        )
        sys.exit(1)

    conn = abrir_conexao()
    try:
        for nome_usuario, senha in usuarios:
            if len(senha) < SENHA_MINIMA:
                print(
                    f"Usuário '{nome_usuario}': senha deve ter pelo menos "
                    f"{SENHA_MINIMA} caracteres. Pulando."
                )
                continue
            criar_ou_atualizar(conn, nome_usuario, senha)
    finally:
        conn.close()


def modo_interativo(nome_usuario):
    nome_usuario = nome_usuario.strip()
    if not nome_usuario:
        print("Nome de usuário não pode ser vazio.")
        sys.exit(1)

    senha = getpass.getpass("Senha: ")
    confirmacao = getpass.getpass("Confirme a senha: ")
    if senha != confirmacao:
        print("As senhas não coincidem.")
        sys.exit(1)
    if len(senha) < SENHA_MINIMA:
        print(f"A senha deve ter pelo menos {SENHA_MINIMA} caracteres.")
        sys.exit(1)

    conn = abrir_conexao()
    try:
        criar_ou_atualizar(conn, nome_usuario, senha)
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Cria ou atualiza um ou mais usuários do sistema de orçamentos."
    )
    parser.add_argument(
        "usuario",
        nargs="?",
        help="Nome de usuário para criar com senha digitada na hora. "
        "Se omitido, lê USUARIO_1/SENHA_1, USUARIO_2/SENHA_2... do .env.",
    )
    args = parser.parse_args()

    if args.usuario:
        modo_interativo(args.usuario)
    else:
        modo_lote_do_env()


if __name__ == "__main__":
    main()
