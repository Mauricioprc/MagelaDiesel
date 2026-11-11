import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    """Configuração lida de variáveis de ambiente. Nunca colocar segredos aqui."""

    SECRET_KEY = os.environ.get("SECRET_KEY")
    DATABASE = os.environ.get(
        "DATABASE_PATH", os.path.join(BASE_DIR, "instance", "orcamentos.db")
    )

    # Sessão
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Em desenvolvimento local sem HTTPS, defina SESSION_COOKIE_SECURE=0 no ambiente.
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "1") != "0"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # Login: limite de tentativas
    LOGIN_MAX_TENTATIVAS = int(os.environ.get("LOGIN_MAX_TENTATIVAS", "5"))
    LOGIN_BLOQUEIO_MINUTOS = int(os.environ.get("LOGIN_BLOQUEIO_MINUTOS", "10"))
