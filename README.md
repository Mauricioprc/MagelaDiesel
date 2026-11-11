# Sistema de Orçamentos — Magela Diesel

Fases concluídas: estrutura/banco/login (1), formulário de orçamento (2), geração do PDF (3), WhatsApp/impressão (4), backup/configurações/deploy (5).

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
- `configuracoes.py` — tela de configurações (preço padrão da bomba, validade padrão) e rota de backup (`sqlite3` backup API).
- `templates/`, `static/` — HTML, CSS, JS e imagens/fontes.
- `static/fonts/` — fontes Bitstream Vera (licença livre, embutidas localmente; `bitstream-vera-license.txt`).
- `instance/orcamentos.db` — banco SQLite (fora do controle de versão).

## Configurações e backup (fase 5)

- Tela **Configurações** (ícone de engrenagem na Início): preço padrão da
  bomba e validade padrão do orçamento (em dias). Esses valores são lidos da
  tabela `configuracoes` e usados só em orçamentos **novos** — editar um
  orçamento existente não muda a validade já gravada nele.
- O rodapé do PDF ("Orçamento válido por N dias") usa a validade gravada em
  cada orçamento, não um texto fixo.
- Botão **Baixar backup** gera uma cópia do banco inteiro (`.db`) usando a
  API de backup do SQLite (`Connection.backup()` + `serialize()`), nunca
  copiando o arquivo aberto direto do disco — evita pegar o banco no meio de
  uma escrita.
- A tela de Configurações e a Início mostram a data do último backup
  baixado, com um aviso discreto se já fizer mais de 7 dias (ou se nunca foi
  baixado).
- **Importante — plano grátis do PythonAnywhere não tem tarefa agendada.**
  Isso significa que ninguém faz backup sozinho: **o Maurício precisa
  entrar no sistema e clicar em "Baixar backup" manualmente, toda semana**,
  e guardar o arquivo baixado fora do PythonAnywhere (no próprio
  computador, num drive, etc.). O aviso na tela ajuda a lembrar, mas não
  substitui esse hábito.

## Deploy no PythonAnywhere (plano grátis)

Passo a passo pra colocar o sistema no ar. Faça isso só quando o Maurício
pedir pra subir pra produção.

1. **Criar a conta** em pythonanywhere.com, plano **Beginner (grátis)**.

2. **Subir o código.** Na aba **Consoles**, abra um **Bash console** e
   clone o repositório (ou suba um `.zip` pela aba **Files** e extraia):

   ```bash
   git clone https://github.com/<usuario>/MagelaDiesel.git
   cd MagelaDiesel
   ```

3. **Criar o ambiente virtual e instalar as dependências:**

   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configurar as variáveis de ambiente.** Não suba o `.env` nem use o
   arquivo em produção. Na aba **Web**, seção **Environment variables**, do
   app criado no passo 5, adicione:

   - `SECRET_KEY` — uma chave aleatória longa (gere com
     `python -c "import secrets; print(secrets.token_hex(32))"`).
   - `SESSION_COOKIE_SECURE` — `1` (o padrão; só usar `0` em desenvolvimento
     local sem HTTPS).
   - `DATABASE_PATH` — opcional; por padrão fica em
     `<pasta do projeto>/instance/orcamentos.db`.

5. **Criar o Web App.** Na aba **Web**, clique em **Add a new web app** →
   escolha **Manual configuration** (não "Flask", pra usar o `app.py`
   existente) → Python 3.11.

6. **Apontar o virtualenv.** Em **Virtualenv**, informe o caminho completo,
   ex.: `/home/<usuario>/MagelaDiesel/venv`.

7. **Editar o arquivo WSGI** (link na própria aba Web, algo como
   `/var/www/<usuario>_pythonanywhere_com_wsgi.py`). Apague o conteúdo de
   exemplo e deixe só:

   ```python
   import sys
   path = "/home/<usuario>/MagelaDiesel"
   if path not in sys.path:
       sys.path.insert(0, path)

   from app import app as application
   ```

8. **Criar os usuários do sistema.** De volta ao Bash console, com o
   virtualenv ativado e as variáveis de ambiente definidas na sessão (ou um
   `.env` temporário só pra rodar o script uma vez):

   ```bash
   source venv/bin/activate
   python criar_usuario.py
   ```

9. **Static files.** Na aba Web, seção **Static files**, adicione:
   - URL `/static/` → Directory `/home/<usuario>/MagelaDiesel/static/`

10. **Recarregar o app** (botão verde **Reload** no topo da aba Web) e
    acessar `https://<usuario>.pythonanywhere.com`.

11. **Conferir HTTPS.** O domínio `*.pythonanywhere.com` do plano grátis já
    vem com HTTPS; confirme que o cadeado aparece no navegador — é
    obrigatório pro botão "Enviar por WhatsApp" (Web Share API) funcionar.

12. **Testar no celular de verdade.** Entrar pelo Android/Chrome, criar um
    orçamento de teste, mandar por WhatsApp e excluir o orçamento de teste
    depois.

### Limites do plano grátis a respeitar

- **Sem tarefa agendada** → backup é manual, toda semana (ver seção acima).
- **1 web app, 512 MB de disco** → de olho no tamanho do banco (os PDFs
  enviados ficam guardados nele).
- **Sem acesso à internet de saída** pra sites fora da lista permitida do
  PythonAnywhere → por isso tudo já é local (fontes em `static/fonts/`,
  sem CDN).
- **O app "dorme"/expira** se ninguém acessar por um tempo, no plano
  grátis — a regra exata mudou em jan/2026, então **confirme no painel do
  PythonAnywhere antes de prometer disponibilidade**; não documentamos um
  prazo aqui pra não assumir algo que pode estar desatualizado.

## O que falta (próximas fases)

Nenhuma fase pendente no escopo combinado no CLAUDE.md. Pendências que
dependem de decisão do Maurício/dono da oficina, não de código, estão na
seção de pendências do CLAUDE.md (uso de logos de terceiros, texto de
garantia além dos 90 dias, confirmação da política de expiração do
PythonAnywhere).

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
