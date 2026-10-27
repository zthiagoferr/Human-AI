# Humano ou IA?

Jogo educacional de letramento digital em que o aluno lê 22 citações e decide se cada uma foi escrita por um humano ou gerada por IA. Ao final, recebe a correção completa com a análise pedagógica de cada carta e vê sua posição no ranking da turma.

> **Demonstração educacional.** O acesso é feito pelo Firebase Authentication (e-mail e senha). Uso real exige HTTPS, limitação de tentativas/quotas, política de privacidade e revisão de segurança. Leia a seção **Segurança** antes de publicar.
>
> **Publicação atual:** a interface Angular está publicada em `https://zthiagoferr.github.io/Human-AI/` como **prévia**. O backend FastAPI está **preparado para produção no Railway/PostgreSQL**, mas ainda **não foi implantado**; por isso, login completo, partida, resultado e ranking não funcionam nesse endereço. Nenhum resultado é simulado.

## O que o jogo faz

1. O aluno cria uma conta ou entra com **e-mail e senha** pelo Firebase Authentication.
2. Recebe exatamente **22 cartas**, uma por vez, na ordem #01 a #22.
3. Para cada carta, escolhe **Humano** ou **IA**.
4. Ao finalizar as 22 respostas, vê:
   - total de acertos;
   - total de erros;
   - percentual;
   - duração da partida;
   - correção item a item, com a resposta do aluno, a resposta correta e a análise da carta.
5. O ranking da turma é atualizado e pode ser consultado sem recarregar a página.
6. O ranking ordena por acertos, depois por menor tempo e, por fim, por nome (A→Z).

O fluxo é linear: **login → jogo → resultado → ranking**. Não há menu de navegação; apenas botões contextuais em cada tela.

## Equipe

### Divisão de responsabilidades

O **Human-AI** é um projeto acadêmico desenvolvido em grupo, resultado da colaboração entre quatro integrantes. Cada membro assumiu responsabilidades específicas, contribuindo com suas habilidades e conhecimentos para o planejamento, desenvolvimento e implantação da aplicação.

#### Integrantes e suas contribuições

| Integrante | Função | Responsabilidades |
|---|---|---|
| **Thiago Ferreira de Oliveira** | Desenvolvedor Full Stack e responsável pelo Deploy | Desenvolvimento do frontend e backend, integração dos componentes da aplicação e implantação do sistema em produção. |
| **Gabriel Balbino Malaquias** | Engenharia de Prompts e Ideação | Elaboração e aprimoramento dos prompts utilizados no projeto, desenvolvimento de ideias e contribuição para a definição do conceito da aplicação. |
| **Gabrielle Preis** | Design e Identidade Visual | Criação da identidade visual, desenvolvimento da logo e contribuição para o design da interface da aplicação. |
| **Elcio Silveira Mello** | Banco de Dados e Autenticação | Responsável pela estruturação e gerenciamento do banco de dados, além da implementação e configuração da autenticação utilizando Firebase Authentication. |

### Desenvolvimento Colaborativo

O desenvolvimento do Human-AI foi realizado de maneira colaborativa, com a divisão de tarefas entre os integrantes da equipe.

As contribuições individuais foram fundamentais para a construção de uma aplicação que integra desenvolvimento web, inteligência artificial, identidade visual, persistência de dados e autenticação de usuários.

**O Human-AI representa o esforço coletivo de toda a equipe**, valorizando as responsabilidades e contribuições de cada integrante para a realização do projeto.

## Stack

- **Front-end:** Angular 20, componentes standalone, signals, rotas, `HttpClient`, formulários reativos e SCSS.
- **Back-end:** Python 3.12+, FastAPI, Uvicorn, SQLAlchemy 2.0; SQLite em desenvolvimento/testes e PostgreSQL em produção.
- **Autenticação:** Firebase Authentication (e-mail/senha) no frontend; `firebase-admin` valida ID Tokens no backend.
- **Banco:** SQLite local; PostgreSQL persistente no Railway em produção. A identidade local é vinculada por `firebase_uid`. Hashes de senha antigos permanecem inertes.
- **Gabarito:** JSON exclusivo do back-end, nunca servido ao front-end antes da finalização.
- **PDF:** extração com `pypdf` e/ou `pdftotext`; transcrição manual fiel para o JSON.

## Publicação no GitHub Pages

A interface Angular é publicada em **`https://zthiagoferr.github.io/Human-AI/`** pelo workflow `.github/workflows/deploy-pages.yml`, no mesmo repositório do back-end.

- **Status:** prévia da interface. A API FastAPI **não** está publicada. O `environment.prod.ts` mantém `apiUrl: ''` para que o app avise a indisponibilidade e não simule partidas, resultados ou ranking.
- **Deploy:** push em `main` ou execução manual do workflow (`workflow_dispatch`). O artefato publicado contém **somente** `frontend/dist/humano-ou-ia/browser` (HTML, JS, CSS e logo); não inclui `backend/`, JSON de gabarito, `.env`, banco nem credencial.
- **Rotas:** `baseHref` de produção é `/Human-AI/` e o roteador usa `withHashLocation()`. As URLs públicas têm `#`, por exemplo `https://zthiagoferr.github.io/Human-AI/#/login`. Isso faz reload e deep link funcionarem sem reescrita no GitHub Pages.
- **Ativação:** em **Settings → Pages → Build and deployment → Source**, selecione **GitHub Actions**.
- **Firebase:** adicione `zthiagoferr.github.io` em **Authentication → Settings → Authorized domains** e mantenha `localhost` para o desenvolvimento.
- **Quando a API existir:** publique-a em HTTPS, preencha `environment.prod.ts` com a URL real, inclua a origem `https://zthiagoferr.github.io` em `HUMANAI_CORS_ORIGINS` e faça novo deploy.

## Produção do backend no Railway + PostgreSQL

**Status:** o código está preparado, mas o serviço Railway e o PostgreSQL **ainda não foram criados**. O frontend continua em modo de prévia (`apiUrl: ''`) até a URL real da API existir.

- **Imagem:** `backend/Dockerfile` com `python:3.13-slim`, `psycopg[binary]` e `uvicorn` em `0.0.0.0:${PORT:-8080}`.
- **Configuração Railway:** `backend/railway.json` com healthcheck em `/api/health`, restart em falha e uma réplica. O **Root Directory** do serviço deve ser `backend`.
- **Banco:** serviço PostgreSQL do Railway; o app usa `DATABASE_URL` (precedência) e recusa SQLite quando `HUMANAI_ENV=production`.
- **Credencial Firebase Admin:** `HUMANAI_FIREBASE_CREDENTIALS_JSON` (JSON inline, secret) ou `GOOGLE_APPLICATION_CREDENTIALS`/ADC localmente. Nunca versionar.
- **CORS de produção:** `HUMANAI_CORS_ORIGINS=https://zthiagoferr.github.io` (sem barra final).
- **Docs:** `HUMANAI_DOCS_ENABLED=false` em produção.
- **Dados locais:** o script `backend/scripts/migrar_sqlite_para_postgres.py` copia o SQLite local para o PostgreSQL de forma não destrutiva, preservando IDs e ajustando sequences. O SQLite original nunca é apagado.

Variáveis mínimas no Railway:

```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
HUMANAI_ENV=production
HUMANAI_FIREBASE_PROJECT_ID=human-ai-5c442
HUMANAI_CORS_ORIGINS=https://zthiagoferr.github.io
HUMANAI_DOCS_ENABLED=false
HUMANAI_FIREBASE_CREDENTIALS_JSON=<json secreto da service account>
```

Migração local, usando a URL **pública** do PostgreSQL e sem imprimir o valor:

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
read -r -s -p "DATABASE_PUBLIC_URL: " DATABASE_URL; echo
export DATABASE_URL
python scripts/migrar_sqlite_para_postgres.py            # dry-run (padrão, somente leitura)
python scripts/migrar_sqlite_para_postgres.py --executar # grava no destino
unset DATABASE_URL
```

Não há automação de criação de serviços/deploy neste repositório; isso é uma etapa manual do responsável pelo Railway.

## Estrutura do repositório

```text
.
├── README.md
├── ARQUITETURA.md
├── DOCUMENTACAO_TECNICA.md
├── GUIA_DO_PROFESSOR.md
├── backend/
│   ├── app/
│   ├── scripts/
│   ├── tests/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── railway.json
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── .github/
│   └── workflows/
│       └── deploy-pages.yml
└── imagens/
    └── Logo HumanAI_ Conexão entre Humano e IA.png
```

## Requisitos

- Python **3.12+** (recomendado para wheels do `firebase-admin`; Python 3.14 também foi validado neste projeto)
- Node.js **20.19+** ou **22.12+**
- npm **10+**
- Projeto Firebase com **Email/Password** habilitado e um **Web App** cadastrado
- `poppler-utils` (opcional, para `pdftotext`)
- Navegador moderno (Chrome, Firefox, Edge ou Safari recente)

## Configuração do Firebase (antes de executar)

1. No Console do Firebase, abra **Authentication → Sign-in method** e habilite **Email/Password**.
2. Em **Authentication → Settings → Authorized domains**, inclua `localhost` e, para a publicação atual, `zthiagoferr.github.io` (somente o host, sem caminho).
3. Em **Project settings → Your apps**, cadastre um **Web App** do projeto `human-ai-5c442` e copie a configuração **pública** (`apiKey`, `authDomain`, `projectId`, `storageBucket`, `messagingSenderId`, `appId`, `measurementId`) para `frontend/src/environments/firebase.config.ts`.
4. Gere uma **nova chave de service account do projeto `human-ai-5c442`** ou use Application Default Credentials. Guarde a chave **fora do repositório** e exporte:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/caminho/fora-do-repo/nova-chave-human-ai-5c442.json
   ```
   No Railway, prefira `HUMANAI_FIREBASE_CREDENTIALS_JSON` com o JSON inline em uma variável secreta.
5. Copie `backend/.env.example` para `backend/.env` e ajuste `HUMANAI_FIREBASE_PROJECT_ID=human-ai-5c442` e, se houver professor, `HUMANAI_PROFESSOR_EMAILS`.
6. Nunca coloque a chave Admin no frontend, no Git ou em `firebase.config.ts`.

## Como executar

### 1. Back-end

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
export GOOGLE_APPLICATION_CREDENTIALS=/caminho/fora-do-repo/nova-chave-human-ai-5c442.json
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

O servidor estará em `http://localhost:8000`. A documentação interativa (ambiente de desenvolvimento) fica em `http://localhost:8000/docs`.

Na inicialização, o backend aplica a migração idempotente que adiciona `firebase_uid` e a tabela `codigos_vinculo`. Faça backup de `backend/humanai.db` antes da primeira execução em um banco existente. O script `python scripts/migrar_firebase.py` executa a mesma migração e compara contagens.

O back-end **não inicia** se `backend/app/data/cartas_gabarito.json` estiver incompleto ou divergente do gabarito oficial. Isso é intencional.

### 2. Front-end

Em outro terminal:

```bash
cd frontend
npm install
npm start
```

A aplicação abre em `http://localhost:4200`.

### 3. Uso

1. Abra `http://localhost:4200`.
2. Clique em **Criar conta** e cadastre-se com nome, e-mail e senha.
3. Responda as 22 cartas.
4. Veja o resultado e o ranking.
5. Use **Jogar novamente** para uma nova tentativa ou **Sair** para encerrar.
6. Em caso de senha esquecida, use **Esqueci minha senha** na tela de login.
7. Alunos de contas antigas devem receber um código do professor e acessar `/vincular-legado` **antes de jogar**.

## Configuração

Copie `backend/.env.example` para `backend/.env` e ajuste se necessário.

| Variável | Padrão | Descrição |
|---|---|---|
| `HUMANAI_ENV` | `dev` | `dev` ou `prod` |
| `HUMANAI_DATABASE_URL` | `sqlite:///./humanai.db` | Banco SQLite |
| `HUMANAI_CORS_ORIGINS` | `http://localhost:4200,http://127.0.0.1:4200` | Origens separadas por vírgula |
| `HUMANAI_RANKING_MAX_LIMIT` | `500` | Limite máximo do ranking |
| `HUMANAI_CARTAS_PATH` | `app/data/cartas_gabarito.json` | Caminho do gabarito |
| `HUMANAI_DOCS_ENABLED` | `true` | Habilita `/docs` e `/openapi.json` |
| `HUMANAI_FIREBASE_PROJECT_ID` | — | ID do projeto Firebase; obrigatório em produção |
| `HUMANAI_PROFESSOR_EMAILS` | vazio | E-mails de professor, separados por vírgula; exigem `email_verified=true` |
| `HUMANAI_FIREBASE_CHECK_REVOKED` | `false` | Consulta de revogação por request (mais lento) |
| `HUMANAI_VINCULO_TTL_HOURS` | `24` | Validade do código de vínculo de conta antiga |

A credencial Admin **não** é configurada por variável `HUMANAI_*`: use `GOOGLE_APPLICATION_CREDENTIALS` ou ADC no ambiente do processo.

O front-end usa `frontend/src/environments/firebase.config.ts` para a configuração pública e `frontend/src/environments/environment.ts`:


```ts
// firebase.config.ts (somente valores públicos do Web App)
export const firebaseConfig = {
  apiKey: 'AIzaSyDnVBy9IZ9aUkm_esuF3nx6dR1t0eXOcYA',
  authDomain: 'human-ai-5c442.firebaseapp.com',
  projectId: 'human-ai-5c442',
  storageBucket: 'human-ai-5c442.firebasestorage.app',
  messagingSenderId: '351099808084',
  appId: '1:351099808084:web:d9b2780aa1de5e4de0c0c1',
  measurementId: 'G-RD56LHCC9F'
};

// environment.ts (desenvolvimento)
export const environment = {
  producao: false,
  apiUrl: 'http://localhost:8000/api',
  rankingPollMs: 5000,
  rankingLimite: 500,
  firebase: firebaseConfig
};

// environment.prod.ts (produção no GitHub Pages)
export const environment = {
  producao: true,
  // A API pública ainda não foi publicada. Mantenha vazio.
  // Quando existir, use uma URL HTTPS real.
  apiUrl: '',
  rankingPollMs: 5000,
  rankingLimite: 500,
  firebase: firebaseConfig
};
```

O `environment.prod.ts` é aplicado pelo `fileReplacements` da configuração `production`. Com `apiUrl` vazio, o app exibe a nota de indisponibilidade no login e falha as chamadas de API com mensagem em português; não há resultados simulados.

## Cartas e gabarito

O arquivo `backend/app/data/cartas_gabarito.json` contém as 22 cartas e o gabarito (origem e análise). Ele é lido apenas pelo back-end. **Nunca copie esse arquivo, o PDF ou a pasta `backend/` para `frontend/public`.**

Para conferir a transcrição:

```bash
cd backend
python scripts/validar_cartas.py
```

O script verifica:

- 22 cartas, IDs `#01` a `#22`;
- 11 humanas e 11 de IA;
- campos obrigatórios preenchidos;
- correspondência com a lista oficial mantida no back-end.

### Extração do PDF

O PDF de origem é:

```text
Jogo Humano ou IA - 22 Cartas e Gabarito Separado (1).pdf
```

Extração sugerida:

```bash
cd backend
python scripts/extrair_pdf.py "../Jogo Humano ou IA - 22 Cartas e Gabarito Separado (1).pdf" > /tmp/humanai_cartas.txt
```

Alternativa com layout mais fiel (se `poppler-utils` estiver instalado):

```bash
pdftotext -layout -enc UTF-8 \
  "../Jogo Humano ou IA - 22 Cartas e Gabarito Separado (1).pdf" \
  /tmp/humanai_cartas_layout.txt
```

Depois:

1. Transcreva manualmente as 22 citações, categorias, temas e análises para o JSON.
2. Preserve acentos, aspas, travessões e pontuação.
3. Não parafraseie, não resuma e não corrija o estilo.
4. Rode `python scripts/validar_cartas.py`.
5. Apague os arquivos temporários de `/tmp` ao terminar: eles contêm o gabarito.

## Testes

Back-end:

```bash
cd backend
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

O driver PostgreSQL é `psycopg[binary]` (já em `requirements.txt`). Para rodar o smoke opcional em PostgreSQL real, defina `HUMANAI_TEST_POSTGRES_URL` e use um banco/schema descartável. Sem a variável, o teste é ignorado.

Front-end:

```bash
cd frontend
CHROME_BIN=/usr/bin/chromium npm test -- --watch=false --browsers=ChromeHeadless
```

O workflow de Pages roda os mesmos testes com ChromeHeadless (`38` testes) antes do build.

Em máquinas sem `/usr/bin/chromium`, ajuste `CHROME_BIN` para o binário do Chrome/Chromium.

Build de produção do front:

```bash
cd frontend
npm run build
```

A saída fica em `frontend/dist/humano-ou-ia/browser/index.html` e deve conter `<base href="/Human-AI/">`. O workflow publica apenas essa pasta. Para conferir localmente:

```bash
grep -n '<base href=' frontend/dist/humano-ou-ia/browser/index.html
```

## Segurança

Esta é uma **demonstração**. Antes de qualquer uso real:

- sirva tudo por **HTTPS** (o Firebase Authentication exige contexto seguro);
- configure **quotas e proteção contra abuso** no Firebase/Identity Platform e rate limiting no backend;
- mantenha a **API key pública** restrita por domínio/HTTP referrer no Google Cloud Console; ao publicar no Pages, inclua `https://zthiagoferr.github.io/*` e teste o login;
- **GitHub Pages:** adicione `zthiagoferr.github.io` aos domínios autorizados do Firebase; o artefato publicado deve conter somente `frontend/dist/humano-ou-ia/browser`;
- **Railway:** `DATABASE_URL` contém senha e `HUMANAI_FIREBASE_CREDENTIALS_JSON` contém a chave Admin; ambos devem ser secrets no Railway e nunca aparecer em logs, build, Dockerfile ou Git;
- **SQLite em produção:** recusado por `HUMANAI_ENV=production`; use PostgreSQL persistente;
- **Repositório público:** o código do backend e o JSON de cartas ficam visíveis no GitHub por decisão do projeto. Isso não envia o gabarito pelo app, mas permite leitura direta do arquivo no repositório; avalie separar o backend em repositório privado antes de uso real com alunos;
- **CORS futuro:** quando a API for publicada, use apenas a origem `https://zthiagoferr.github.io` (sem caminho e sem barra final) em `HUMANAI_CORS_ORIGINS`;
- aplique **CSP** e evite qualquer `innerHTML`: o SDK persiste a sessão no navegador;
- o logout é local (`signOut`); ID Tokens já emitidos podem valer até cerca de 1 hora. Use `HUMANAI_FIREBASE_CHECK_REVOKED=true` se precisar consultar revogação a cada request;
- desabilite cadastro aberto ou use convite/SSO se necessário;
- desabilite `/docs` e `/openapi.json` em produção;
- não exponha a pasta `backend/` nem o JSON de gabarito;
- defina política de privacidade e base legal para exibir nomes no ranking (LGPD);
- faça revisão de segurança e backups do banco.

**Credencial legada — projeto antigo `humanai-68a2d`:** o arquivo `humanai-68a2d-firebase-adminsdk-fbsvc-dbe02c3c0d.json` na raiz pertence ao projeto antigo e **não** deve ser usado pelo projeto ativo `human-ai-5c442`. Trate-o como comprometido; revogue a chave no Google Cloud Console, gere uma nova chave/ADC para `human-ai-5c442` fora do repositório e nunca coloque credencial Admin no frontend.

## Solução de problemas

| Problema | Causa provável | Solução |
|---|---|---|
| `CORS policy` no navegador | Origem diferente de `localhost:4200` | Ajuste `HUMANAI_CORS_ORIGINS` e reinicie o back-end |
| Back-end não inicia | JSON de cartas incompleto/inválido | Rode `python scripts/validar_cartas.py` e corrija |
| `AUTENTICACAO_INDISPONIVEL` | Credencial Admin ausente/inválida | Exporte `GOOGLE_APPLICATION_CREDENTIALS` ou configure `HUMANAI_FIREBASE_CREDENTIALS_JSON`/ADC; reinicie |
| Backend em produção recusa iniciar | `HUMANAI_ENV=production` com SQLite ou sem `DATABASE_URL` | Crie PostgreSQL no Railway e configure `DATABASE_URL`; SQLite é apenas dev/teste |
| `/api/health` retorna 503 | Banco indisponível no health check | Verifique o serviço PostgreSQL, `DATABASE_URL` e logs do Railway |
| `psycopg` não instala | Wheel incompatível ou dependência ausente | Use `psycopg[binary]>=3.2,<4.0`; a imagem usa Python 3.13 com wheel manylinux |
| Migração abortada | Duplicidade/órfão/limite de campo no SQLite | Corrija a origem ou use uma cópia consistente; nenhuma alteração é feita no SQLite |
| `railway logs` com credencial | Variável impressa por engano | Nunca rode `railway variables` em log compartilhado; rotacione o segredo |
| `auth/invalid-api-key` ou configuração incompleta | `firebase.config.ts` vazio/incorreto | Copie a configuração pública do Web App no Console |
| `auth/unauthorized-domain` | Domínio não autorizado | Adicione `zthiagoferr.github.io` (e mantenha `localhost`) em Authentication → Settings → Authorized domains |
| “API do jogo não está configurada” no Pages | `environment.prod.ts` com `apiUrl: ''` | Esperado enquanto a API não for publicada; para ativar, preencha a URL HTTPS e faça novo deploy |
| Página branca ou 404 ao abrir uma rota | URL sem `#` ou `baseHref` incorreto | Use `https://zthiagoferr.github.io/Human-AI/#/rota`; confira `<base href="/Human-AI/">` no build |
| `CORS policy` no Pages | API sem a origem do Pages | Inclua `https://zthiagoferr.github.io` em `HUMANAI_CORS_ORIGINS` e reinicie a API |
| `auth/operation-not-allowed` | Provedor Email/Password desabilitado | Habilite em Authentication → Sign-in method |
| Aluno de conta antiga não entra | Conta legada sem vínculo | Gere código de vínculo e oriente `/vincular-legado` antes de jogar |
| `database is locked` | Múltiplos workers ou escrita concorrente | Use `--workers 1`; mantenha WAL; feche conexões |
| Ranking vazio | Nenhuma partida concluída | Finalize uma partida |
| Acentos errados no PDF | Encoding | Use `-enc UTF-8` e salve o JSON em UTF-8 |
| Porta ocupada | Outro processo | `uvicorn ... --port 8001` e ajuste `apiUrl` |
| Token expirado | Expiração do ID Token | O SDK renova automaticamente; se persistir, entre novamente |

## Licença e uso

Projeto educacional, sem fins comerciais. O PDF, as citações e as análises pertencem aos seus respectivos autores/organizadores. Verifique a licença antes de redistribuir.
