from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from csrf import validate_csrf_or_abort
from db import get_db

bp = Blueprint("auth", __name__)

# Controle de tentativas de login em memória: chave (ip, usuário) -> dados.
# Simples e suficiente para 2-3 usuários; zera se o processo reiniciar.
_tentativas = {}


def _chave_tentativa(nome_usuario):
    return (request.remote_addr, nome_usuario.strip().lower())


def _bloqueado(chave):
    info = _tentativas.get(chave)
    if not info:
        return False
    bloqueado_at = info.get("bloqueado_at")
    agora = datetime.now(timezone.utc)
    if bloqueado_at and agora < bloqueado_at:
        return True
    if bloqueado_at and agora >= bloqueado_at:
        _tentativas.pop(chave, None)
    return False


def _registrar_falha(chave):
    max_tentativas = current_app.config["LOGIN_MAX_TENTATIVAS"]
    minutos_bloqueio = current_app.config["LOGIN_BLOQUEIO_MINUTOS"]
    info = _tentativas.setdefault(chave, {"falhas": 0, "bloqueado_at": None})
    info["falhas"] += 1
    if info["falhas"] >= max_tentativas:
        info["bloqueado_at"] = datetime.now(timezone.utc) + timedelta(
            minutes=minutos_bloqueio
        )


def _limpar_tentativas(chave):
    _tentativas.pop(chave, None)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


@bp.before_app_request
def carregar_usuario_logado():
    usuario_id = session.get("usuario_id")
    g.usuario = None
    if usuario_id is not None:
        db = get_db()
        g.usuario = db.execute(
            "SELECT id, nome_usuario FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        if g.usuario is None:
            session.clear()


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        validate_csrf_or_abort()
        nome_usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")
        chave = _chave_tentativa(nome_usuario)

        if _bloqueado(chave):
            minutos = current_app.config["LOGIN_BLOQUEIO_MINUTOS"]
            flash(
                f"Muitas tentativas. Tente novamente em até {minutos} minutos.",
                "erro",
            )
            return render_template("login.html")

        db = get_db()
        usuario = db.execute(
            "SELECT id, nome_usuario, senha_hash FROM usuarios WHERE nome_usuario = ?",
            (nome_usuario,),
        ).fetchone()

        senha_ok = usuario is not None and check_password_hash(
            usuario["senha_hash"], senha
        )

        if not senha_ok:
            _registrar_falha(chave)
            flash("Usuário ou senha inválidos.", "erro")
            return render_template("login.html")

        _limpar_tentativas(chave)
        session.clear()
        session.permanent = True
        session["usuario_id"] = usuario["id"]

        destino = request.args.get("next")
        if not destino or not destino.startswith("/") or destino.startswith("//"):
            destino = url_for("main.home")
        return redirect(destino)

    return render_template("login.html")


@bp.route("/logout", methods=["POST"])
def logout():
    validate_csrf_or_abort()
    session.clear()
    return redirect(url_for("auth.login"))
