# Humano ou IA?

Jogo educacional de letramento digital em que o aluno lê 22 citações e decide se cada uma foi escrita por um humano ou gerada por IA. Ao final, recebe a correção completa com a análise pedagógica de cada carta e vê sua posição no ranking da turma.

> **Demonstração educacional.** O acesso é feito pelo Firebase Authentication (e-mail e senha). Uso real exige HTTPS, limitação de tentativas/quotas, política de privacidade e revisão de segurança. Leia a seção **Segurança** antes de publicar.

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

## Stack

- **Front-end:** Angular 20, componentes standalone, signals, rotas, `HttpClient`, formulários reativos e SCSS.
- **Back-end:** Python 3.12+, FastAPI, Uvicorn, SQLAlchemy 2.0 e SQLite.
- **Autenticação:** Firebase Authentication (e-mail/senha) no frontend; `firebase-admin` valida ID Tokens no backend.
- **Banco:** SQLite; a identidade local é vinculada por `firebase_uid`. Hashes de senha antigos permanecem inertes.
- **Gabarito:** JSON exclusivo do back-end, nunca servido ao front-end antes da finalização.
- **PDF:** extração com `pypdf` e/ou `pdftotext`; transcrição manual fiel para o JSON.

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
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
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
2. Em **Authentication → Settings → Authorized domains**, inclua `localhost` e o domínio real de produção.
3. Em **Project settings → Your apps**, cadastre um **Web App** do projeto `human-ai-5c442` e copie a configuração **pública** (`apiKey`, `authDomain`, `projectId`, `storageBucket`, `messagingSenderId`, `appId`, `measurementId`) para `frontend/src/environments/firebase.config.ts`.
4. Gere uma **nova chave de service account do projeto `human-ai-5c442`** ou use Application Default Credentials. Guarde a chave **fora do repositório** e exporte:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/caminho/fora-do-repo/nova-chave-human-ai-5c442.json
   ```
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

// environment.ts
export const environment = {
  producao: false,
  apiUrl: 'http://localhost:8000/api',
  rankingPollMs: 5000,
  rankingLimite: 500,
  firebase: firebaseConfig
};
```

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

Front-end:

```bash
cd frontend
CHROME_BIN=/usr/bin/chromium npm test -- --watch=false --browsers=ChromeHeadless
```

Em máquinas sem `/usr/bin/chromium`, ajuste `CHROME_BIN` para o binário do Chrome/Chromium.

Build de produção do front:

```bash
cd frontend
npm run build
```

## Segurança

Esta é uma **demonstração**. Antes de qualquer uso real:

- sirva tudo por **HTTPS** (o Firebase Authentication exige contexto seguro);
- configure **quotas e proteção contra abuso** no Firebase/Identity Platform e rate limiting no backend;
- mantenha a **API key pública** restrita por domínio/HTTP referrer no Google Cloud Console;
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
| `AUTENTICACAO_INDISPONIVEL` | Credencial Admin ausente/inválida | Exporte `GOOGLE_APPLICATION_CREDENTIALS` ou configure ADC; reinicie |
| `auth/invalid-api-key` ou configuração incompleta | `firebase.config.ts` vazio/incorreto | Copie a configuração pública do Web App no Console |
| `auth/unauthorized-domain` | Domínio não autorizado | Adicione o domínio em Authentication → Settings → Authorized domains |
| `auth/operation-not-allowed` | Provedor Email/Password desabilitado | Habilite em Authentication → Sign-in method |
| Aluno de conta antiga não entra | Conta legada sem vínculo | Gere código de vínculo e oriente `/vincular-legado` antes de jogar |
| `database is locked` | Múltiplos workers ou escrita concorrente | Use `--workers 1`; mantenha WAL; feche conexões |
| Ranking vazio | Nenhuma partida concluída | Finalize uma partida |
| Acentos errados no PDF | Encoding | Use `-enc UTF-8` e salve o JSON em UTF-8 |
| Porta ocupada | Outro processo | `uvicorn ... --port 8001` e ajuste `apiUrl` |
| Token expirado | Expiração do ID Token | O SDK renova automaticamente; se persistir, entre novamente |

## Licença e uso

Projeto educacional, sem fins comerciais. O PDF, as citações e as análises pertencem aos seus respectivos autores/organizadores. Verifique a licença antes de redistribuir.
