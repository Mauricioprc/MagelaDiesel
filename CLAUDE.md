# Sistema de Orçamentos — MD Magela Diesel

## Contexto
Oficina diesel (Boa Esperança - MG) que trabalha só com **bomba injetora e bico injetor de tratores**. Hoje os orçamentos são feitos num modelo Word/papel. Sem computador, precisam fazer **pelo celular (Android, Chrome)**. O sistema gera o orçamento **igual ao modelo de papel**, em PDF (imprimir e mandar por WhatsApp), e guarda tudo num lugar só com busca.

- Usuários: 2–3 funcionários, nível técnico intermediário. **Todos têm a mesma permissão** (todos podem editar e excluir).
- Quem mantém o sistema: Maurício (desenvolvedor). Responda ao Maurício em português, direto, sem enrolar. Aponte riscos e decisões ruins em vez de concordar por padrão.
- **Escopo: somente orçamento.** Nada de ordem de serviço, estoque, financeiro, número de orçamento, importação de dados. Se achar que falta algo, pergunte antes; não adicione.

## Stack (decidida, não trocar sem avisar)
- Python 3 + **Flask** + **SQLite** (um arquivo só).
- **reportlab** para o PDF (A4, gerado no servidor).
- Front: HTML + CSS + JS puro, **mobile-first**. Sem framework pesado.
- Hospedagem: **PythonAnywhere plano grátis** (Beginner). Restrições do plano grátis que você DEVE respeitar:
  - 1 web app, 512 MB de disco, sem SSH, **sem tarefas agendadas**, sem domínio próprio.
  - Acesso à internet de saída só para sites da lista permitida → **não dependa de APIs externas, CDNs de fonte ou serviços de terceiros em runtime.** Tudo local (fontes, ícones, JS em /static).
  - Deploy via Bash console + aba Web (WSGI). Entregue instruções passo a passo de deploy.

## Segurança (obrigatório)
- Login por usuário e senha; senhas com hash (`werkzeug.security`), nunca em texto puro.
- Sessão com cookie `HttpOnly`, `Secure`, `SameSite=Lax`, expiração razoável.
- Proteção **CSRF** em todos os formulários/POST (ex.: Flask-WTF ou token próprio).
- Limite de tentativas de login (bloqueio temporário por usuário/IP).
- `SECRET_KEY` fora do código (variável de ambiente / arquivo fora do repositório). `.gitignore` cobrindo banco, segredos e backups.
- Todas as consultas SQL **parametrizadas**. Escape de saída nos templates.
- Todas as rotas (exceto login) exigem autenticação.
- Banco (`.db`) fora da pasta `static`, nunca servido publicamente.
- Cadastro de usuários: sem tela pública. Criar por script/CLI (`python criar_usuario.py`).
- Confirme que o site responde só por **HTTPS** (necessário para o compartilhamento no WhatsApp).

## Backup (ponto crítico — plano grátis não tem tarefa agendada)
- Tela/rota protegida **"Baixar backup"** que gera e baixa uma cópia consistente do banco (usar `sqlite3` backup API, não copiar o arquivo aberto).
- Mostrar na tela inicial/configurações a **data do último backup baixado** e um aviso discreto se passar de 7 dias.
- Documentar no README a rotina: Maurício baixa o backup toda semana e guarda fora do PythonAnywhere.
- Cópias dos PDFs enviados ficam no banco/disco (ver abaixo); considerar incluí-las no backup.

## Dados
Tabelas mínimas (ajuste nomes se preciso, mantenha simples):
- `usuarios` (id, nome_usuario, senha_hash)
- `orcamentos` (id, cliente_nome, telefone, cidade, veiculo, data, bomba_incluida, bomba_preco_centavos, validade_dias, criado_em, editado_em, criado_por)
- `itens` (id, orcamento_id, descricao, quantidade, preco_centavos, ordem)
- `pdf_enviados` (id, orcamento_id, enviado_em, arquivo/blob) — cópia do PDF no momento do envio
- `configuracoes` (chave, valor) — preço padrão da bomba, validade padrão (15 dias)
- **Valores em centavos (inteiro).** Nunca float para dinheiro.
- **Sem número de orçamento.** Não buscar por id.
- Sem importação inicial: a lista de descrições começa **vazia** e aprende com o uso.

## Telas (mobile-first, 390px de largura de referência)
1. **Entrar:** logo, "MD Magela Diesel", Usuário, Senha, botão Entrar.
2. **Início:** dois quadrados grandes: **"Fazer orçamento"** e **"Ver orçamentos antigos"**. Botão Sair.
3. **Orçamentos antigos:** busca única (nome, telefone, cidade, veículo), cards com Nome · Veículo · Cidade · Data · Total. Toque abre o detalhe.
4. **Novo/Editar orçamento:**
   - Campos: Nome, Telefone, Cidade, Veículo, Data (padrão hoje).
   - **Linha padrão da bomba:** "Desmontar, montar e regular bomba injetora na bancada de teste", qtd 1, **R$ 1.100,00**, com **chave para remover**. Preço padrão editável numa pequena tela de configurações.
   - Demais itens começam **em branco**, adicionados pelo usuário de forma rápida (botão "+ Item"). Autocomplete com descrições já usadas e **sugestão do último preço**.
   - **Rascunho salvo automaticamente** (mostrar "Rascunho salvo").
   - **Barra fixa embaixo:** TOTAL sempre visível + botão Salvar.
   - **Máscara de dinheiro estilo centavos (da direita para a esquerda):** só dígitos; digitar `19100` mostra `191,00`; colar `191.00` vira `191,00`; `110000` vira `1.100,00`. Quantidade: só dígitos. O usuário vê a formatação enquanto digita.
5. **Orçamento salvo (detalhe):** dados do cliente, itens, subtotal, TOTAL, mostrando "Enviado ao cliente em dd/mm/aa, às hh:mm" + "Ver PDF enviado" quando houver. Botões: **Enviar por WhatsApp**, **Imprimir ou baixar PDF**, **Editar**, **Excluir** (com confirmação). Mostrar "editado em ..." quando editado depois do envio.
6. **Configurações (simples):** preço padrão da bomba, validade padrão, Baixar backup.

## PDF (idêntico ao modelo de papel)
- A4. Cabeçalho compacto com logos (CAT, Delphi, New Holland, Bosch, Case IH e logo MD), nome "MD Magela Diesel", endereço e telefone:
  - **Av. Joaquim Três Pontas, n° 430, Bairro Santa Terezinha, Boa Esperança - MG, 37170-000 — Tel.: (35) 3851-2837**
  - Manter as **cores** do modelo original (usar os PNGs fornecidos em `static/img/`, sem redistorcer).
- Título **"ORÇAMENTO"** à direita da linha do NOME. Campos: Nome, Telefone, Cidade, Veículo, Data.
- Tabela: Qtd · Descrição · Valor. Linhas em branco pautadas **só preenchem o espaço que sobrar** (como no papel).
- **SUBTOTAL** (dos itens, antes da linha da bomba, conforme modelo) e **TOTAL** final.
- Abaixo da última linha da tabela: **"Garantia de 90 dias por Defeito de Fábrica"** (fixo em todos).
- Rodapé: à esquerda, em **cinza claro**, "Orçamento válido por 15 dias" (padrão 15, ajustável nas configurações); à direita "Obrigado! Volte Sempre!".
- **Regra de ajuste automático para caber na página:**
  1. Tamanho normal: fonte 15px / linha 26px (~23 itens por página).
  2. Se não couber, **reduz** gradualmente até o mínimo: fonte ~10pt / linha 22px (~29 itens).
  3. Se ainda não couber, volta ao tamanho normal e **continua na página 2** com o cabeçalho da tabela repetido e "Pág. 1/2".
  4. Total, garantia e agradecimento aparecem **só na última página**.
  5. Descrições longas quebram linha e contam a altura real.
- Dados do cliente e itens com acentos corretos (usar fonte TTF com suporte a português, embutida localmente).

## WhatsApp e impressão
- **Web Share API** (`navigator.share` com arquivo PDF) no Android/Chrome. Exige HTTPS e toque do usuário.
- **Fallback:** se não suportar, baixar o PDF e orientar a anexar manualmente no WhatsApp.
- Ao enviar/compartilhar: **guardar uma cópia do PDF** (`pdf_enviados`) com data/hora.
- Imprimir/baixar: abrir o PDF para o usuário imprimir.
- **Deve ser testado nos celulares reais da oficina** — não considerar pronto sem isso.

## Regra de aprovação por fase (obrigatória)
- Trabalhe **uma fase por vez**, somente quando o Maurício pedir (ex.: "faça a fase 1"). Nunca construa tudo de uma vez.
- Ao terminar uma fase, **PARE**: resuma o que foi feito, o que não foi testado e os riscos. Depois **espere a aprovação explícita** do Maurício.
- **Não comece a próxima fase** sem ele aprovar a atual. Silêncio não é aprovação.
- Se ele pedir ajustes, corrija dentro da mesma fase e peça aprovação de novo.

## Ordem de trabalho (fases; pare e mostre ao final de cada uma)
1. Estrutura, banco, login, criar usuário por script, lista e busca.
2. Formulário rápido (máscara, bomba padrão, autocomplete, rascunho, barra fixa) + salvar/editar/excluir.
3. PDF idêntico ao papel, com regra de ajuste e múltiplas páginas. Gerar PDFs de teste com 5, 23, 29 e 40 itens e conferir visualmente.
4. WhatsApp/impressão, cópia do PDF enviado, "editado em".
5. Backup, configurações, README e **guia de deploy no PythonAnywhere** passo a passo.

## Como trabalhar
- Código simples e legível; o Maurício vai manter. Comentários curtos onde não for óbvio.
- Se uma decisão não estiver neste arquivo, **pergunte** em vez de inventar.
- Não adicione funcionalidades fora do escopo.
- Teste o que construir (máscara de dinheiro, cálculo de totais, paginação do PDF) com testes automatizados simples.
- Ao terminar cada fase, diga o que foi feito, o que **não** foi testado e quais riscos restam.

## Pendências a confirmar antes de produção (não assumir)
- Regra atual de **renovação/expiração** do app no plano grátis do PythonAnywhere (a política mudou em jan/2026) e se o HTTPS do subdomínio está ativo.
- Texto de condições de garantia além da linha de 90 dias (não definido; deixar sem).
- Uso de logos de marcas de terceiros no cabeçalho: decisão do dono da oficina.
