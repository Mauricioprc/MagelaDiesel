# Sistema de Orçamentos — Magela Diesel

Fase 1: estrutura, banco, login, criação de usuário por script, lista e busca.

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
- `main.py` — tela Início e tela Lista (com busca).
- `csrf.py` — geração/validação de token CSRF.
- `criar_usuario.py` — script de linha de comando para criar/atualizar usuários (sem tela pública de cadastro).
- `templates/`, `static/` — HTML e CSS/imagens.
- `instance/orcamentos.db` — banco SQLite (fora do controle de versão).

## O que falta (próximas fases)

- Fase 2: formulário de novo/editar orçamento (máscara de dinheiro, bomba, autocomplete, rascunho).
- Fase 3: geração do PDF.
- Fase 4: WhatsApp, impressão, cópia do PDF enviado.
- Fase 5: backup, configurações e guia de deploy no PythonAnywhere.
