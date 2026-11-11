from datetime import date, datetime

from flask import (
    Blueprint,
    abort,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

from auth import login_required
from csrf import validate_csrf_or_abort
from db import get_db, obter_configuracao
from dinheiro import centavos_para_reais, string_para_centavos

bp = Blueprint("orcamentos", __name__, url_prefix="/orcamentos")

BOMBA_DESCRICAO_PADRAO = "Desmontar, montar e regular bomba injetora na bancada de teste"
BOMBA_PRECO_PADRAO_CENTAVOS = 110000
VALIDADE_DIAS_PADRAO = 15


def _quantidade_segura(texto):
    digitos = "".join(c for c in (texto or "") if c.isdigit())
    return max(1, int(digitos)) if digitos else 1


def _data_br(data_iso):
    if not data_iso:
        return ""
    try:
        return datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%y")
    except ValueError:
        return data_iso


def _data_hora_br(texto_iso):
    if not texto_iso:
        return ""
    try:
        return datetime.strptime(texto_iso, "%Y-%m-%dT%H:%M:%S").strftime(
            "%d/%m/%y, às %H:%M"
        )
    except ValueError:
        return texto_iso


def _buscar_sugestoes_itens():
    db = get_db()
    linhas = db.execute(
        """
        SELECT descricao, preco_centavos
        FROM (
            SELECT descricao, preco_centavos,
                   ROW_NUMBER() OVER (PARTITION BY descricao ORDER BY id DESC) AS rn
            FROM itens
        )
        WHERE rn = 1
        ORDER BY descricao COLLATE NOCASE
        LIMIT 300
        """
    ).fetchall()
    return {linha["descricao"]: linha["preco_centavos"] for linha in linhas}


def _buscar_orcamento_ou_404(orcamento_id):
    orcamento = get_db().execute(
        "SELECT * FROM orcamentos WHERE id = ?", (orcamento_id,)
    ).fetchone()
    if orcamento is None:
        abort(404)
    return orcamento


def _buscar_itens(orcamento_id):
    return get_db().execute(
        "SELECT * FROM itens WHERE orcamento_id = ? ORDER BY ordem, id",
        (orcamento_id,),
    ).fetchall()


def _montar_contexto_formulario(modo, orcamento=None, itens=None):
    if orcamento is None:
        orcamento = {
            "id": None,
            "cliente_nome": "",
            "telefone": "",
            "cidade": "",
            "veiculo": "",
            "data": date.today().isoformat(),
            "bomba_incluida": True,
            "bomba_descricao": obter_configuracao(
                "bomba_descricao_padrao", BOMBA_DESCRICAO_PADRAO
            ),
            "bomba_quantidade": 1,
            "bomba_preco_centavos": int(
                obter_configuracao(
                    "bomba_preco_centavos_padrao", BOMBA_PRECO_PADRAO_CENTAVOS
                )
            ),
        }
    else:
        orcamento = dict(orcamento)

    if itens is None:
        itens_contexto = [{"descricao": "", "quantidade": 1, "preco_formatado": ""}]
        subtotal = 0
    else:
        itens_contexto = [
            {
                "descricao": item["descricao"],
                "quantidade": item["quantidade"],
                "preco_formatado": centavos_para_reais(item["preco_centavos"]),
                "total_formatado": centavos_para_reais(
                    item["quantidade"] * item["preco_centavos"]
                ),
            }
            for item in itens
        ]
        subtotal = sum(item["quantidade"] * item["preco_centavos"] for item in itens)
    bomba_total = (
        orcamento["bomba_quantidade"] * orcamento["bomba_preco_centavos"]
        if orcamento["bomba_incluida"]
        else 0
    )

    orcamento["bomba_preco_formatado"] = centavos_para_reais(
        orcamento["bomba_preco_centavos"]
    )
    orcamento["bomba_total_formatado"] = centavos_para_reais(bomba_total)

    return {
        "modo": modo,
        "orcamento": orcamento,
        "itens": itens_contexto,
        "subtotal_formatado": centavos_para_reais(subtotal),
        "total_formatado": centavos_para_reais(subtotal + bomba_total),
        "sugestoes": _buscar_sugestoes_itens(),
    }


@bp.route("")
@login_required
def lista():
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
                "data_formatada": _data_br(linha["data"]),
                "total_formatado": centavos_para_reais(total_centavos),
            }
        )

    return render_template("lista.html", orcamentos=orcamentos, busca=busca)


@bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    if request.method == "POST":
        validate_csrf_or_abort()
        return _salvar(orcamento_id=None)
    return render_template("formulario.html", **_montar_contexto_formulario("novo"))


@bp.route("/<int:orcamento_id>")
@login_required
def detalhe(orcamento_id):
    orcamento = _buscar_orcamento_ou_404(orcamento_id)
    itens = _buscar_itens(orcamento_id)

    subtotal = sum(item["quantidade"] * item["preco_centavos"] for item in itens)
    bomba_total = (
        orcamento["bomba_quantidade"] * orcamento["bomba_preco_centavos"]
        if orcamento["bomba_incluida"]
        else 0
    )

    contexto_orcamento = dict(orcamento)
    contexto_orcamento["data_formatada"] = _data_br(orcamento["data"])
    contexto_orcamento["editado_em_formatado"] = _data_hora_br(orcamento["editado_em"])
    contexto_orcamento["bomba_preco_formatado"] = centavos_para_reais(
        orcamento["bomba_preco_centavos"]
    )
    contexto_orcamento["bomba_total_formatado"] = centavos_para_reais(bomba_total)

    itens_contexto = [
        {
            "descricao": item["descricao"],
            "quantidade": item["quantidade"],
            "preco_formatado": centavos_para_reais(item["preco_centavos"]),
            "total_formatado": centavos_para_reais(
                item["quantidade"] * item["preco_centavos"]
            ),
        }
        for item in itens
    ]

    return render_template(
        "detalhe.html",
        orcamento=contexto_orcamento,
        itens=itens_contexto,
        subtotal_formatado=centavos_para_reais(subtotal),
        total_formatado=centavos_para_reais(subtotal + bomba_total),
    )


@bp.route("/<int:orcamento_id>/editar", methods=["GET", "POST"])
@login_required
def editar(orcamento_id):
    orcamento = _buscar_orcamento_ou_404(orcamento_id)

    if request.method == "POST":
        validate_csrf_or_abort()
        return _salvar(orcamento_id=orcamento_id)

    itens = _buscar_itens(orcamento_id)
    return render_template(
        "formulario.html",
        **_montar_contexto_formulario("editar", orcamento=orcamento, itens=itens),
    )


@bp.route("/<int:orcamento_id>/excluir", methods=["POST"])
@login_required
def excluir(orcamento_id):
    validate_csrf_or_abort()
    _buscar_orcamento_ou_404(orcamento_id)
    db = get_db()
    db.execute("DELETE FROM orcamentos WHERE id = ?", (orcamento_id,))
    db.commit()
    return redirect(url_for("orcamentos.lista"))


def _salvar(orcamento_id):
    form = request.form

    cliente_nome = form.get("nome", "").strip()
    if not cliente_nome:
        contexto = _montar_contexto_formulario(
            "editar" if orcamento_id else "novo",
            orcamento=(
                _buscar_orcamento_ou_404(orcamento_id) if orcamento_id else None
            ),
            itens=(_buscar_itens(orcamento_id) if orcamento_id else None),
        )
        contexto["erro"] = "Informe o nome do cliente."
        return render_template("formulario.html", **contexto), 400

    telefone = form.get("telefone", "").strip()
    cidade = form.get("cidade", "").strip()
    veiculo = form.get("veiculo", "").strip()
    data_str = form.get("data", "").strip() or date.today().isoformat()

    bomba_incluida = form.get("bomba_incluida") == "1"
    bomba_descricao = form.get("bomba_descricao", "").strip()
    bomba_quantidade = _quantidade_segura(form.get("bomba_quantidade", "1"))
    bomba_preco_centavos = string_para_centavos(form.get("bomba_preco", ""))

    descricoes = form.getlist("item_descricao")
    quantidades = form.getlist("item_quantidade")
    precos = form.getlist("item_preco")

    itens = []
    for descricao, quantidade_str, preco_str in zip(descricoes, quantidades, precos):
        descricao = descricao.strip()
        if not descricao:
            continue
        quantidade = _quantidade_segura(quantidade_str)
        preco_centavos = string_para_centavos(preco_str)
        itens.append((descricao, quantidade, preco_centavos))

    db = get_db()
    agora = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    if orcamento_id is None:
        cursor = db.execute(
            """
            INSERT INTO orcamentos
                (cliente_nome, telefone, cidade, veiculo, data, bomba_incluida,
                 bomba_descricao, bomba_quantidade, bomba_preco_centavos,
                 validade_dias, criado_em, criado_por)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cliente_nome,
                telefone,
                cidade,
                veiculo,
                data_str,
                1 if bomba_incluida else 0,
                bomba_descricao,
                bomba_quantidade,
                bomba_preco_centavos,
                int(obter_configuracao("validade_dias_padrao", VALIDADE_DIAS_PADRAO)),
                agora,
                g.usuario["id"],
            ),
        )
        orcamento_id = cursor.lastrowid
    else:
        db.execute(
            """
            UPDATE orcamentos
            SET cliente_nome = ?, telefone = ?, cidade = ?, veiculo = ?, data = ?,
                bomba_incluida = ?, bomba_descricao = ?, bomba_quantidade = ?,
                bomba_preco_centavos = ?, editado_em = ?
            WHERE id = ?
            """,
            (
                cliente_nome,
                telefone,
                cidade,
                veiculo,
                data_str,
                1 if bomba_incluida else 0,
                bomba_descricao,
                bomba_quantidade,
                bomba_preco_centavos,
                agora,
                orcamento_id,
            ),
        )
        db.execute("DELETE FROM itens WHERE orcamento_id = ?", (orcamento_id,))

    for ordem, (descricao, quantidade, preco_centavos) in enumerate(itens):
        db.execute(
            """
            INSERT INTO itens (orcamento_id, descricao, quantidade, preco_centavos, ordem)
            VALUES (?, ?, ?, ?, ?)
            """,
            (orcamento_id, descricao, quantidade, preco_centavos, ordem),
        )

    db.commit()
    return redirect(url_for("orcamentos.detalhe", orcamento_id=orcamento_id))
