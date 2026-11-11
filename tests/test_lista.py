import sqlite3

from conftest import login


def _inserir_orcamento(db_path, **kwargs):
    dados = {
        "cliente_nome": "Lucas",
        "telefone": "9.9726-1741",
        "cidade": "Guapé - MG",
        "veiculo": "Trator Agrale",
        "data": "2026-07-21",
        "bomba_incluida": 1,
        "bomba_descricao": "Desmontar, montar e regular bomba injetora na bancada de teste",
        "bomba_quantidade": 1,
        "bomba_preco_centavos": 110000,
        "validade_dias": 15,
        "criado_em": "2026-07-21T14:00:00",
        "criado_por": 1,
    }
    dados.update(kwargs)

    conn = sqlite3.connect(db_path)
    cur = conn.execute(
        """
        INSERT INTO orcamentos
            (cliente_nome, telefone, cidade, veiculo, data, bomba_incluida,
             bomba_descricao, bomba_quantidade, bomba_preco_centavos,
             validade_dias, criado_em, criado_por)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            dados["cliente_nome"],
            dados["telefone"],
            dados["cidade"],
            dados["veiculo"],
            dados["data"],
            dados["bomba_incluida"],
            dados["bomba_descricao"],
            dados["bomba_quantidade"],
            dados["bomba_preco_centavos"],
            dados["validade_dias"],
            dados["criado_em"],
            dados["criado_por"],
        ),
    )
    orcamento_id = cur.lastrowid
    conn.execute(
        "INSERT INTO itens (orcamento_id, descricao, quantidade, preco_centavos, ordem) "
        "VALUES (?, ?, ?, ?, ?)",
        (orcamento_id, "Bicos injetores", 4, 19100, 1),
    )
    conn.commit()
    conn.close()
    return orcamento_id


def test_lista_vazia(client, app):
    login(client)
    resposta = client.get("/orcamentos")
    assert resposta.status_code == 200
    assert "Nenhum orçamento salvo ainda" in resposta.get_data(as_text=True)


def test_lista_mostra_orcamento_com_total_calculado(client, app):
    _inserir_orcamento(app.config["DATABASE"])
    login(client)
    resposta = client.get("/orcamentos")
    html = resposta.get_data(as_text=True)
    assert "Lucas" in html
    # subtotal 4 x 191,00 = 764,00 + bomba 1 x 1.100,00 = 1.864,00
    assert "1.864,00" in html


def test_busca_filtra_por_cidade(client, app):
    _inserir_orcamento(app.config["DATABASE"], cliente_nome="Lucas", cidade="Guapé - MG")
    _inserir_orcamento(app.config["DATABASE"], cliente_nome="José Carlos", cidade="Campos Gerais - MG")
    login(client)

    resposta = client.get("/orcamentos?q=Guapé")
    html = resposta.get_data(as_text=True)
    assert "Lucas" in html
    assert "José Carlos" not in html


def test_busca_sem_resultado(client, app):
    _inserir_orcamento(app.config["DATABASE"])
    login(client)
    resposta = client.get("/orcamentos?q=inexistente")
    assert "Nenhum orçamento encontrado" in resposta.get_data(as_text=True)
