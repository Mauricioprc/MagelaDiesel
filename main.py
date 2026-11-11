from flask import Blueprint, render_template

from auth import login_required
from configuracoes import DIAS_AVISO_BACKUP, ultimo_backup_info

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def home():
    _, dias_desde_backup = ultimo_backup_info()
    aviso_backup = dias_desde_backup is None or dias_desde_backup > DIAS_AVISO_BACKUP
    return render_template("home.html", aviso_backup=aviso_backup)
