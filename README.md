# Sistema de Orçamentos — Magela Diesel

Fases concluídas: estrutura/banco/login (1), formulário de orçamento (2), geração do PDF (3), WhatsApp/impressão (4).

## Rodando localmente

1. Crie um ambiente virtual e instale as dependências:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
```

2. Copie `.env.example` para `.env` e preencha (`SECRET_KEY`, e os usuários em
   `USUARIO_1`/`SENHA_1`, `USUARIO_2`/`SENHA_2`...). O `.env` nunca entra no
   git (`.gitignore`); em produção, defina essas mesmas variáveis direto na
   configuração do servidor em vez de usar o arquivo.

```bash
cp .env.example .env
```

3. Crie os usuários definidos no `.env` (lê `USUARIO_1`/`SENHA_1` etc. e
   salva cada senha com hash no banco — nunca em texto puro):

```bash
python criar_usuario.py
```

   Pra criar ou trocar a senha de só um usuário na hora, sem usar o `.env`:

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
- `orcamentos.py` — lista (com busca), novo/editar/salvar/excluir, geração do PDF, marcar como enviado (grava cópia em `pdf_enviados`).
- `dinheiro.py` — conversão centavos ↔ string formatada.
- `pdf.py` — monta o PDF do orçamento igual ao modelo de papel (cabeçalho, logos, tabela, regra de ajuste de fonte e paginação).
- `csrf.py` — geração/validação de token CSRF.
- `criar_usuario.py` — script de linha de comando para criar/atualizar usuários (sem tela pública de cadastro); sem argumento, lê `USUARIO_N`/`SENHA_N` do `.env`.
- `templates/`, `static/` — HTML, CSS, JS e imagens/fontes.
- `static/fonts/` — fontes Bitstream Vera (licença livre, embutidas localmente; `bitstream-vera-license.txt`).
- `instance/orcamentos.db` — banco SQLite (fora do controle de versão).

## O que falta (próximas fases)

- Fase 5: backup, configurações e guia de deploy no PythonAnywhere.

## WhatsApp e impressão (fase 4)

- "Enviar por WhatsApp" usa a Web Share API (`navigator.share` com o arquivo
  PDF) — funciona em Android/Chrome com HTTPS e toque do usuário. Em
  navegadores sem suporte a compartilhar arquivo (como desktop), baixa o PDF
  e orienta a anexar manualmente no WhatsApp.
- Cada envio (compartilhado com sucesso ou baixado no fallback) grava uma
  cópia do PDF em `pdf_enviados` com data/hora; o detalhe mostra "Enviado ao
  cliente em..." e um link "Ver PDF enviado" pra essa cópia congelada
  (não o PDF gerado na hora, que pode já ter mudado se o orçamento foi
  editado depois).
- "Editado em ..." só aparece se a edição foi **depois** do último envio —
  editar antes de enviar não mostra nada, porque não há nada que o cliente
  já tenha recebido pra ficar desatualizado.
- **Ainda não testado em celular Android real** — só no navegador desktop
  (onde cai no fallback de download). Antes de considerar pronto, testar o
  compartilhamento de verdade num Android/Chrome com HTTPS.
