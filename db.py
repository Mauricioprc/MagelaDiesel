import sqlite3

import click
from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))


@click.command("init-db")
def init_db_command():
    """Cria as tabelas do banco (não apaga dados existentes)."""
    init_db()
    click.echo("Banco inicializado.")


def obter_configuracao(chave, padrao=None):
    linha = get_db().execute(
        "SELECT valor FROM configuracoes WHERE chave = ?", (chave,)
    ).fetchone()
    return linha["valor"] if linha is not None else padrao


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
