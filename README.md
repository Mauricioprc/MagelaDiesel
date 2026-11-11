# Sistema de Orçamentos — Magela Diesel

Fases concluídas: estrutura/banco/login (1), formulário de orçamento (2), geração do PDF (3).

## Rodando localmente

1. Crie um ambiente virtual e instale as dependências:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
```

2. Defina as variáveis de ambiente (veja `.env.example`). No PowerShell:

```powershell
$env:SECRET_KEY = "uma-chave-aleatoria-qualquer-para-teste"
$env:SESSION_COOKIE_SECURE = "0"
```

3. Crie um usuário:

```bash
python criar_usuario.py maria
```

4. Rode o servidor:

```bash
python -m flask --app app run
```

Acesse `http://127.0.0.1:5000/`.

## Testes automatizados

```bash
pip install -r requirements-dev.txt
pytest
```

## Estrutura

- `app.py` — cria a aplicação Flask (`create_app`).
- `config.py` — configuração lida de variáveis de ambiente.
- `db.py` — conexão SQLite e inicialização do schema (`schema.sql`).
- `auth.py` — login, logout, limite de tentativas, decorator `login_required`.
- `main.py` — tela Início.
- `orcamentos.py` — lista (com busca), novo/editar/salvar/excluir, geração do PDF.
- `dinheiro.py` — conversão centavos ↔ string formatada.
- `pdf.py` — monta o PDF do orçamento igual ao modelo de papel (cabeçalho, logos, tabela, regra de ajuste de fonte e paginação).
- `csrf.py` — geração/validação de token CSRF.
- `criar_usuario.py` — script de linha de comando para criar/atualizar usuários (sem tela pública de cadastro).
- `templates/`, `static/` — HTML, CSS, JS e imagens/fontes.
- `static/fonts/` — fontes Bitstream Vera (licença livre, embutidas localmente; `bitstream-vera-license.txt`).
- `instance/orcamentos.db` — banco SQLite (fora do controle de versão).

## O que falta (próximas fases)

- Fase 4: enviar por WhatsApp (Web Share API), cópia do PDF enviado (`pdf_enviados`), "editado em" só depois do envio.
- Fase 5: backup, configurações e guia de deploy no PythonAnywhere.
