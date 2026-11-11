from flask import Blueprint, render_template, request

from auth import login_required
from db import get_db

bp = Blueprint("main", __name__)


def _centavos_para_reais(centavos):
    return f"{centavos / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


@bp.route("/")
@login_required
def home():
    return render_template("home.html")


@bp.route("/orcamentos")
@login_required
def lista_orcamentos():
    busca = request.args.get("q", "").strip()
    db = get_db()

    sql = """
        SELECT o.id, o.cliente_nome, o.telefone, o.cidade, o.veiculo, o.data,
               o.bomba_incluida, o.bomba_quantidade, o.bomba_preco_centavos,
               COALESCE((
                   SELECT SUM(quantidade * preco_centavos) FROM itens WHERE orcamento_id = o.id
               ), 0) AS subtotal_centavos
        FROM orcamentos o
    """
    params = []
    if busca:
        sql += """
            WHERE o.cliente_nome LIKE ? OR o.telefone LIKE ?
               OR o.cidade LIKE ? OR o.veiculo LIKE ?
        """
        termo = f"%{busca}%"
        params = [termo, termo, termo, termo]
    sql += " ORDER BY o.data DESC, o.id DESC"

    linhas = db.execute(sql, params).fetchall()

    orcamentos = []
    for linha in linhas:
        bomba_centavos = (
            linha["bomba_quantidade"] * linha["bomba_preco_centavos"]
            if linha["bomba_incluida"]
            else 0
        )
        total_centavos = linha["subtotal_centavos"] + bomba_centavos
        orcamentos.append(
            {
                "id": linha["id"],
                "cliente_nome": linha["cliente_nome"],
                "telefone": linha["telefone"],
                "cidade": linha["cidade"],
                "veiculo": linha["veiculo"],
                "data": linha["data"],
                "total_formatado": _centavos_para_reais(total_centavos),
            }
        )

    return render_template("lista.html", orcamentos=orcamentos, busca=busca)
