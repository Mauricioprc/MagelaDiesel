import io
import sqlite3
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for

from auth import login_required
from csrf import validate_csrf_or_abort
from db import get_db, obter_configuracao
from dinheiro import centavos_para_reais, string_para_centavos

bp = Blueprint("configuracoes", __name__, url_prefix="/configuracoes")

BOMBA_PRECO_PADRAO_CENTAVOS = 110000
VALIDADE_DIAS_PADRAO = 15

CHAVE_ULTIMO_BACKUP = "ultimo_backup_em"
DIAS_AVISO_BACKUP = 7


def _definir_configuracao(chave, valor):
    db = get_db()
    db.execute(
        """
        INSERT INTO configuracoes (chave, valor) VALUES (?, ?)
        ON CONFLICT (chave) DO UPDATE SET valor = excluded.valor
        """,
        (chave, valor),
    )
    db.commit()


def ultimo_backup_info():
    """Devolve (data_formatada, dias_atras) do último backup baixado, ou (None, None)."""
    valor = obter_configuracao(CHAVE_ULTIMO_BACKUP)
    if not valor:
        return None, None
    momento = datetime.strptime(valor, "%Y-%m-%dT%H:%M:%S")
    dias_atras = (datetime.now() - momento).days
    return momento.strftime("%d/%m/%y, às %H:%M"), dias_atras


@bp.route("", methods=["GET", "POST"])
@login_required
def configuracoes():
    if request.method == "POST":
        validate_csrf_or_abort()

        bomba_preco_centavos = string_para_centavos(request.form.get("bomba_preco", ""))
        validade_str = request.form.get("validade_dias", "").strip()
        validade_dias = (
            int(validade_str) if validade_str.isdigit() and int(validade_str) > 0
            else VALIDADE_DIAS_PADRAO
        )

        _definir_configuracao("bomba_preco_centavos_padrao", str(bomba_preco_centavos))
        _definir_configuracao("validade_dias_padrao", str(validade_dias))

        flash("Configurações salvas.", "sucesso")
        return redirect(url_for("configuracoes.configuracoes"))

    bomba_preco_centavos = int(
        obter_configuracao("bomba_preco_centavos_padrao", BOMBA_PRECO_PADRAO_CENTAVOS)
    )
    validade_dias = int(obter_configuracao("validade_dias_padrao", VALIDADE_DIAS_PADRAO))
    ultimo_backup_formatado, dias_desde_backup = ultimo_backup_info()

    return render_template(
        "configuracoes.html",
        bomba_preco_formatado=centavos_para_reais(bomba_preco_centavos),
        validade_dias=validade_dias,
        ultimo_backup_formatado=ultimo_backup_formatado,
        aviso_backup=dias_desde_backup is None or dias_desde_backup > DIAS_AVISO_BACKUP,
        dias_aviso_backup=DIAS_AVISO_BACKUP,
    )


@bp.route("/backup", methods=["POST"])
@login_required
def backup():
    """Gera uma cópia consistente do banco usando a API de backup do sqlite3
    (não copia o arquivo aberto, que pode estar no meio de uma escrita) e
    devolve o arquivo .db pra download.
    """
    validate_csrf_or_abort()

    origem = get_db()
    copia = sqlite3.connect(":memory:")
    origem.backup(copia)
    dados = copia.serialize()
    copia.close()

    agora = datetime.now()
    _definir_configuracao(CHAVE_ULTIMO_BACKUP, agora.strftime("%Y-%m-%dT%H:%M:%S"))

    nome_arquivo = f"backup-magela-diesel-{agora.strftime('%Y%m%d-%H%M%S')}.db"
    return send_file(
        io.BytesIO(dados),
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name=nome_arquivo,
    )
