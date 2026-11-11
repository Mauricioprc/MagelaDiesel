import hmac
import secrets

from flask import abort, request, session


def generate_csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]


def validate_csrf_or_abort():
    enviado = request.form.get("csrf_token", "")
    esperado = session.get("_csrf_token", "")
    if not esperado or not hmac.compare_digest(enviado, esperado):
        abort(400, description="Token CSRF inválido.")


def init_app(app):
    app.jinja_env.globals["csrf_token"] = generate_csrf_token
