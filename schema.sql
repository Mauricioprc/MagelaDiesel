-- Esquema do banco de orçamentos. Valores monetários sempre em centavos (inteiro).

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_usuario TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orcamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_nome TEXT NOT NULL,
    telefone TEXT,
    cidade TEXT,
    veiculo TEXT,
    data TEXT NOT NULL,
    bomba_incluida INTEGER NOT NULL DEFAULT 0,
    bomba_descricao TEXT,
    bomba_quantidade INTEGER NOT NULL DEFAULT 1,
    bomba_preco_centavos INTEGER NOT NULL DEFAULT 0,
    validade_dias INTEGER NOT NULL DEFAULT 15,
    criado_em TEXT NOT NULL,
    editado_em TEXT,
    criado_por INTEGER NOT NULL REFERENCES usuarios (id)
);

CREATE TABLE IF NOT EXISTS itens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    orcamento_id INTEGER NOT NULL REFERENCES orcamentos (id) ON DELETE CASCADE,
    descricao TEXT NOT NULL,
    quantidade INTEGER NOT NULL DEFAULT 1,
    preco_centavos INTEGER NOT NULL DEFAULT 0,
    ordem INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pdf_enviados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    orcamento_id INTEGER NOT NULL REFERENCES orcamentos (id) ON DELETE CASCADE,
    enviado_em TEXT NOT NULL,
    arquivo BLOB NOT NULL
);

CREATE TABLE IF NOT EXISTS configuracoes (
    chave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orcamentos_busca
    ON orcamentos (cliente_nome, telefone, cidade, veiculo);

CREATE INDEX IF NOT EXISTS idx_itens_orcamento
    ON itens (orcamento_id);

CREATE INDEX IF NOT EXISTS idx_pdf_enviados_orcamento
    ON pdf_enviados (orcamento_id);
