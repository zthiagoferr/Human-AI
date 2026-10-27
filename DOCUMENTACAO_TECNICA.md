# Documentação Técnica — Humano ou IA?

## 1. Visão geral

- **Front-end:** Angular 20 em `http://localhost:4200` (dev) e em `https://zthiagoferr.github.io/Human-AI/` (prévia no GitHub Pages).
- **Back-end:** FastAPI/Uvicorn em `http://localhost:8000`; preparado para Railway, mas a API pública ainda **não** foi implantada.
- **Base da API:** `http://localhost:8000/api` em desenvolvimento; `environment.prod.ts` usa `apiUrl: ''` até a API pública existir.
- **Banco:** SQLite `backend/humanai.db` em desenvolvimento/testes; PostgreSQL persistente no Railway em produção.
- **Formato:** JSON camelCase; datas ISO 8601 UTC.
- **Autenticação:** Firebase Authentication (e-mail/senha) no frontend; `Authorization: Bearer <ID Token>` na API.
- **Identidade local:** `usuarios.firebase_uid` (único); o banco relacional guarda partidas/ranking.
- **Hospedagem:** o GitHub Pages publica somente o build estático do Angular; o FastAPI não é executado no Pages.

## 2. Autenticação

### 2.1 Cadastro e login

- O cadastro e o login são feitos no **Firebase Authentication** (e-mail/senha).
- O frontend nunca envia senha ao backend.
- Após autenticar, o frontend chama `POST /api/auth/sessao` (cadastro) ou `GET /api/auth/me` (login/restauração) com o ID Token.
- O backend valida o token e recupera ou cria o usuário local vinculado ao `uid`.
- Senhas antigas (Argon2id) permanecem inertes em `usuarios.senha_hash` e não são migradas nem verificadas.

### 2.2 ID Token

- JWT emitido pelo Firebase; renovado automaticamente pelo SDK (`getIdToken()`).
- O backend usa `firebase_admin.auth.verify_id_token()`: assinatura, expiração, `aud` e `iss`.
- O projeto esperado é `HUMANAI_FIREBASE_PROJECT_ID`; tokens de outro projeto são rejeitados.
- **Projeto ativo:** `human-ai-5c442`. O valor de `HUMANAI_FIREBASE_PROJECT_ID` deve ser exatamente esse; tokens do projeto antigo ou de qualquer outro projeto falham na validação de `aud`/`iss`.
- O token não é armazenado no banco nem em `sessionStorage` próprio.
- Logout é `signOut()` no cliente; tokens já emitidos podem valer até cerca de 1 h.
- **Papel:** calculado no backend por `HUMANAI_PROFESSOR_EMAILS` + `email_verified === true`.

### 2.3 Headers

```http
Authorization: Bearer <ID Token Firebase>
Content-Type: application/json
Accept: application/json
```

## 3. Erros

```json
{
  "erro": {
    "codigo": "DADOS_INVALIDOS",
    "mensagem": "Um ou mais campos são inválidos.",
    "detalhes": [{ "campo": "senha", "mensagem": "..." }]
  }
}
```

| HTTP | Código |
|---|---|
| 400 | `CODIGO_INVALIDO` |
| 401 | `NAO_AUTENTICADO` |
| 401 | `TOKEN_INVALIDO` |
| 401 | `TOKEN_EXPIRADO` |
| 401 | `TOKEN_REVOGADO` |
| 403 | `ACESSO_NEGADO` |
| 404 | `PARTIDA_NAO_ENCONTRADA` |
| 404 | `ROTA_NAO_ENCONTRADA` |
| 404 | `USUARIO_NAO_ENCONTRADO` |
| 405 | `METODO_NAO_PERMITIDO` |
| 409 | `CONFLITO_USUARIO` |
| 409 | `USUARIO_JA_VINCULADO` |
| 409 | `CONTA_JA_POSSUI_PARTIDAS` |
| 409 | `PARTIDA_EM_ANDAMENTO` |
| 409 | `PARTIDA_NAO_ESTA_EM_ANDAMENTO` |
| 409 | `PARTIDA_NAO_CONCLUIDA` |
| 410 | `AUTENTICACAO_MIGRADA` |
| 422 | `DADOS_INVALIDOS` |
| 422 | `RESPOSTAS_INCOMPLETAS` |
| 422 | `RESPOSTA_DUPLICADA` |
| 422 | `CARTA_FORA_DA_PARTIDA` |
| 4xx/5xx | `ERRO_HTTP` |
| 500 | `ERRO_INTERNO` |
| 503 | `AUTENTICACAO_INDISPONIVEL` |

Não incluir tokens, senhas, hashes ou credenciais nos detalhes/logs de validação.

## 4. Endpoints

### 4.1 `POST /api/auth/registro`

**Auth:** pública, mas **desativada**. Retorna **410** `AUTENTICACAO_MIGRADA`. O cadastro é feito no Firebase.

### 4.2 `POST /api/auth/login`

**Auth:** pública, mas **desativada**. Retorna **410** `AUTENTICACAO_MIGRADA`. O login é feito no Firebase.

### 4.3 `POST /api/auth/logout`

**Auth:** não é necessário. Retorna **410** `AUTENTICACAO_MIGRADA`. O frontend usa `signOut()` do Firebase.

### 4.4 `GET /api/auth/me`

**Auth:** Bearer (ID Token Firebase). Recupera ou auto-provisiona o usuário local.

```json
{
  "usuario": { "id": 1, "nome": "Maria Clara de Souza", "usuario": "maria.souza" },
  "papel": "aluno"
}
```

**Erros:** 401 `NAO_AUTENTICADO`/`TOKEN_INVALIDO`/`TOKEN_EXPIRADO`/`TOKEN_REVOGADO`; 503 `AUTENTICACAO_INDISPONIVEL`.

### 4.5 `POST /api/auth/sessao`

**Auth:** Bearer. Body opcional `{ "nome": "Maria Clara de Souza" }`. Idempotente; cria o usuário local se ainda não existir. Usado no cadastro para gravar o nome de exibição.

**200:** mesmo payload de `/auth/me`. **Erros:** 401/503/422.

### 4.6 `POST /api/auth/vincular-legado`

**Auth:** Bearer. Body `{ "codigo": "XXXXX-XXXXX" }`. Vincula a conta Firebase atual a um usuário legado sem `firebase_uid`.

**200:** `{ "usuario": {...}, "papel": "aluno" }`.

**Erros:** 400 `CODIGO_INVALIDO`; 409 `USUARIO_JA_VINCULADO`; 409 `CONTA_JA_POSSUI_PARTIDAS`.

### 4.7 `GET /api/professor/legado/pendentes`

**Auth:** Bearer + papel professor. Query `limite` (1–100, padrão 50) e `offset`.

```json
{
  "total": 1,
  "limite": 50,
  "offset": 0,
  "itens": [
    { "id": 3, "nome": "Ana Lima", "usuario": "ana.lima", "criadoEm": "2026-03-01T12:00:00+00:00" }
  ]
}
```

### 4.8 `POST /api/professor/legado/{usuarioId}/codigo`

**Auth:** Bearer + papel professor. Gera código de uso único e TTL configurável.

```json
{
  "codigo": "A1B2C-3D4E5",
  "expiraEm": "2026-10-24T18:00:00+00:00",
  "usuario": { "id": 3, "nome": "Ana Lima", "usuario": "ana.lima" }
}
```

**Erros:** 403 `ACESSO_NEGADO`; 404 `USUARIO_NAO_ENCONTRADO`; 409 `USUARIO_JA_VINCULADO`.

### 4.9 `GET /api/partidas/atual`

**Auth:** Bearer.

Sem partida:

```json
{ "partida": null }
```

Com partida:

```json
{
  "partida": {
    "id": 12,
    "iniciadaEm": "2026-10-23T14:02:11.482000+00:00",
    "totalPerguntas": 22,
    "cartas": [
      {
        "id": "01",
        "numero": 1,
        "citacao": "Texto integral da carta #01, transcrito fielmente do PDF.",
        "categoria": "Categoria temática da carta #01",
        "tema": "Tema da carta #01"
      }
    ]
  }
}
```

A resposta real tem 22 cartas. Cada carta tem **somente** `id`, `numero`, `citacao`, `categoria`, `tema`.

### 4.10 `POST /api/partidas`

**Auth:** Bearer. **201** `{ "partida": { ... } }`.  
**409** se já houver partida ativa:

```json
{
  "erro": {
    "codigo": "PARTIDA_EM_ANDAMENTO",
    "mensagem": "Já existe uma partida em andamento.",
    "detalhes": { "partidaId": 12 }
  }
}
```

### 4.11 `POST /api/partidas/{partidaId}/abandonar`

**Auth:** Bearer, dono. **204**. Idempotente se já abandonada; 409 se concluída; 404 se de outro aluno.

### 4.12 `POST /api/partidas/{partidaId}/respostas`

**Auth:** Bearer, dono.

```json
{
  "respostas": [
    { "cartaId": "01", "escolha": "exemplo" },
    { "cartaId": "02", "escolha": "exemplo" }
  ]
}
```

> **Nota:** `"escolha": "exemplo"` é um placeholder documental e não representa o gabarito. No contrato real, o campo aceita apenas `"humano"` ou `"ia"`.

Deve conter exatamente 22 itens, uma vez por carta da partida.

**200:**

```json
{
  "partidaId": 12,
  "totalPerguntas": 22,
  "acertos": 15,
  "erros": 7,
  "percentual": 68.2,
  "duracaoMs": 382145,
  "iniciadaEm": "2026-10-23T14:02:11.482000+00:00",
  "concluidaEm": "2026-10-23T14:08:33.627000+00:00",
  "correcao": [
    {
      "numero": 1,
      "cartaId": "01",
      "citacao": "Texto integral da carta #01, transcrito fielmente do PDF.",
      "categoria": "Categoria temática da carta #01",
      "tema": "Tema da carta #01",
      "escolhaAluno": "exemplo",
      "respostaCorreta": "exemplo",
      "acertou": true,
      "analise": "Análise integral da carta #01, transcrita do gabarito do PDF."
    }
  ]
}
```

> **Nota:** os valores `"exemplo"` são placeholders documentais para não reproduzir o gabarito. No contrato real, `escolhaAluno` e `respostaCorreta` são `"humano"` ou `"ia"`. Os demais campos do exemplo são ilustrativos e não representam a carta #01 real.

`correcao` tem 22 itens na ordem das cartas. Idempotente: se já concluída, retorna o resultado existente.

**Erros:** 422 `RESPOSTAS_INCOMPLETAS`, `RESPOSTA_DUPLICADA`, `CARTA_FORA_DA_PARTIDA`; 409; 404; 401.

### 4.13 `GET /api/partidas/{partidaId}/resultado`

**Auth:** Bearer, dono. **200** mesmo payload. **409** `PARTIDA_NAO_CONCLUIDA`; **404** para outro aluno/inexistente.

### 4.14 `GET /api/ranking?limite=500&offset=0`

**Auth:** Bearer. `limite` 1–500 (padrão 100); `offset` ≥ 0.

```json
{
  "atualizadoEm": "2026-10-23T14:09:02.114000+00:00",
  "totalParticipantes": 237,
  "limite": 500,
  "offset": 0,
  "itens": [
    {
      "posicao": 1,
      "usuarioId": 42,
      "nome": "Ana Beatriz Ferreira",
      "acertos": 22,
      "erros": 0,
      "duracaoMs": 214300,
      "concluidaEm": "2026-10-23T14:01:11.000000+00:00"
    }
  ],
  "meuResultado": {
    "posicao": 18,
    "usuarioId": 7,
    "nome": "Maria Clara de Souza",
    "acertos": 19,
    "erros": 3,
    "duracaoMs": 322000,
    "concluidaEm": "2026-10-23T14:08:33.627000+00:00"
  }
}
```

`meuResultado` é `null` sem partida concluída.

### 4.15 `GET /api/health`

```json
{ "status": "ok", "versao": "1.0.0", "cartasCarregadas": 22 }
```

## 5. Modelo de dados

### 5.1 DDL

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;

CREATE TABLE usuarios (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT NOT NULL,
    nome_ordenacao  TEXT NOT NULL,
    usuario         TEXT NOT NULL COLLATE NOCASE,
    senha_hash      TEXT NOT NULL,          -- legado inerte ou '!firebase'
    criado_em       TEXT NOT NULL,
    firebase_uid    TEXT
);

CREATE UNIQUE INDEX ux_usuarios_usuario ON usuarios(usuario COLLATE NOCASE);
CREATE INDEX ix_usuarios_nome_ordenacao ON usuarios(nome_ordenacao);
CREATE UNIQUE INDEX ux_usuarios_firebase_uid
    ON usuarios(firebase_uid) WHERE firebase_uid IS NOT NULL;

CREATE TABLE codigos_vinculo (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    codigo_hash     TEXT NOT NULL,
    criado_em       TEXT NOT NULL,
    expira_em       TEXT NOT NULL,
    usado_em        TEXT,
    revogado_em     TEXT,
    criado_por_uid  TEXT NOT NULL
);

CREATE UNIQUE INDEX ux_codigos_vinculo_hash ON codigos_vinculo(codigo_hash);
CREATE INDEX ix_codigos_vinculo_usuario ON codigos_vinculo(usuario_id);
CREATE INDEX ix_codigos_vinculo_expira ON codigos_vinculo(expira_em);
```

> Bancos existentes podem manter a tabela `sessoes` fisicamente. Ela é **legado inerte**: nenhuma rota/modelo a utiliza e a migração não a apaga.

CREATE TABLE partidas (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id       INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    status           TEXT NOT NULL DEFAULT 'em_andamento'
                     CHECK (status IN ('em_andamento', 'concluida', 'abandonada')),
    total_perguntas  INTEGER NOT NULL DEFAULT 22 CHECK (total_perguntas = 22),
    iniciada_em      TEXT NOT NULL,
    concluida_em     TEXT,
    duracao_ms       INTEGER CHECK (duracao_ms IS NULL OR duracao_ms >= 0),
    acertos          INTEGER CHECK (acertos IS NULL OR acertos BETWEEN 0 AND 22),
    erros            INTEGER CHECK (erros IS NULL OR erros BETWEEN 0 AND 22),
    CHECK (
        (status = 'concluida'
         AND concluida_em IS NOT NULL
         AND duracao_ms IS NOT NULL
         AND acertos IS NOT NULL
         AND erros IS NOT NULL
         AND acertos + erros = total_perguntas)
        OR
        (status <> 'concluida'
         AND concluida_em IS NULL
         AND duracao_ms IS NULL
         AND acertos IS NULL
         AND erros IS NULL)
    )
);

CREATE UNIQUE INDEX ux_partidas_ativa
    ON partidas(usuario_id)
    WHERE status = 'em_andamento';

CREATE INDEX ix_partidas_usuario ON partidas(usuario_id);
CREATE INDEX ix_partidas_concluidas
    ON partidas(usuario_id, acertos DESC, duracao_ms ASC, concluida_em ASC)
    WHERE status = 'concluida';

CREATE TABLE partida_cartas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    partida_id  INTEGER NOT NULL REFERENCES partidas(id) ON DELETE CASCADE,
    carta_id    TEXT NOT NULL CHECK (length(carta_id) = 2),
    posicao     INTEGER NOT NULL CHECK (posicao BETWEEN 1 AND 22),
    UNIQUE (partida_id, posicao),
    UNIQUE (partida_id, carta_id)
);

CREATE INDEX ix_partida_cartas_partida ON partida_cartas(partida_id, posicao);

CREATE TABLE respostas (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    partida_id    INTEGER NOT NULL REFERENCES partidas(id) ON DELETE CASCADE,
    carta_id      TEXT NOT NULL CHECK (length(carta_id) = 2),
    escolha       TEXT NOT NULL CHECK (escolha IN ('humano', 'ia')),
    correta       INTEGER NOT NULL CHECK (correta IN (0, 1)),
    respondida_em TEXT NOT NULL,
    UNIQUE (partida_id, carta_id)
);

CREATE INDEX ix_respostas_partida ON respostas(partida_id);
```

### 5.2 View de ranking

```sql
DROP VIEW IF EXISTS vw_ranking;

CREATE VIEW vw_ranking AS
WITH melhores AS (
    SELECT
        p.id AS partida_id,
        p.usuario_id,
        p.acertos,
        p.erros,
        p.duracao_ms,
        p.concluida_em,
        ROW_NUMBER() OVER (
            PARTITION BY p.usuario_id
            ORDER BY p.acertos DESC, p.duracao_ms ASC, p.concluida_em ASC, p.id ASC
        ) AS rn
    FROM partidas p
    WHERE p.status = 'concluida'
)
SELECT
    ROW_NUMBER() OVER (
        ORDER BY m.acertos DESC, m.duracao_ms ASC, u.nome_ordenacao ASC, u.id ASC
    ) AS posicao,
    u.id AS usuario_id,
    u.nome AS nome,
    m.partida_id AS partida_id,
    m.acertos AS acertos,
    m.erros AS erros,
    m.duracao_ms AS duracao_ms,
    m.concluida_em AS concluida_em
FROM melhores m
JOIN usuarios u ON u.id = m.usuario_id
WHERE m.rn = 1;
```

### 5.3 Índices

- `ux_partidas_ativa`: garante uma única partida em andamento.
- `ix_partidas_concluidas`: acelera a melhor partida por aluno.
- `ix_usuarios_nome_ordenacao`: acelera o desempate alfabético.
- `ux_usuarios_firebase_uid`: unicidade da identidade Firebase, permitindo vários legados com `NULL`.
- `ux_codigos_vinculo_hash`: busca segura do código sem armazenar texto puro.
- `ix_respostas_partida`: correção e idempotência.
- `ix_partida_cartas_partida`: leitura ordenada das 22 cartas.
- `sessoes`: tabela legada inerte em bancos antigos; não é usada.

## 6. Arquivo de cartas

### 6.1 Formato

```json
{
  "versao": 1,
  "fonte": "Jogo Humano ou IA - 22 Cartas e Gabarito Separado (1).pdf",
  "cartas": [
    {
      "id": "01",
      "numero": 1,
      "citacao": "Texto integral da citação #01, fiel ao PDF.",
      "categoria": "Categoria temática da carta #01",
      "tema": "Tema da carta #01",
      "origem": "exemplo",
      "analise": "Análise integral da carta #01, fiel ao gabarito do PDF."
    }
  ]
}
```

> **Nota:** `"origem": "exemplo"` é placeholder documental; não representa a origem real da carta #01. No arquivo real, os valores são `"humano"` ou `"ia"`.

### 6.2 Validação

- Exatamente 22 cartas; IDs `"01"`–`"22"`.
- `numero == int(id)`.
- `origem` `"humano"` ou `"ia"`.
- 11 humanas e 11 de IA.
- `citacao`, `categoria`, `tema`, `analise` não vazios.
- Sem HTML; texto puro.
- UTF-8, sem BOM.
- Lista oficial de IDs por origem mantida apenas em `backend/app/domain/cartas.py`; o startup falha se divergir.

### 6.3 Extração

```bash
cd backend
python scripts/extrair_pdf.py "../Jogo Humano ou IA - 22 Cartas e Gabarito Separado (1).pdf" > /tmp/cartas.txt

# alternativa
pdftotext -layout -enc UTF-8 "../Jogo Humano ou IA - 22 Cartas e Gabarito Separado (1).pdf" /tmp/cartas_layout.txt

python scripts/validar_cartas.py
```

Transcrever manualmente, preservando pontuação, acentos, aspas e travessões. Não parafrasear. Apagar os temporários ao final.

## 7. Pontuação e ranking

- 1 ponto por acerto; máximo 22; sem penalidade.
- `erros = 22 - acertos`; `percentual = round(acertos / 22 * 100, 1)`.
- Ranking: acertos ↓, `duracao_ms` ↑, `nome_ordenacao` ↑, `usuario_id` ↑.
- `nome_ordenacao`: NFKD, remoção de marcas combinantes, espaços colapsados, `casefold()`.
- Uma linha por aluno, usando a melhor partida concluída.
- Partidas abandonadas não entram.
- Posições únicas com `ROW_NUMBER()`.

## 8. Tempo

- `iniciada_em`: no `POST /partidas` ou no início da partida retomada.
- `concluida_em`: no processamento de `POST /respostas`.
- `duracao_ms`: calculado no servidor, nunca aceito do cliente.
- Justificativa: relógio/DevTools do cliente não são confiáveis; o tempo é critério de desempate.
- O tempo inclui leitura e pausas. Para recomeçar, use “Desistir” (partida abandonada).

## 9. CORS

```text
Origens: http://localhost:4200, http://127.0.0.1:4200
Métodos: GET, POST, OPTIONS
Headers: Authorization, Content-Type, Accept
Credenciais: false
Max-Age: 600
```

Configurável por `HUMANAI_CORS_ORIGINS` (vírgula). Em desenvolvimento:
`http://localhost:4200,http://127.0.0.1:4200`.
Em produção:
`https://zthiagoferr.github.io` (sem barra final).
Não usar `*`; `allow_credentials=False`.

## 10. Front-end

### 10.1 Rotas

| Rota | Guard | Tela |
|---|---|---|
| `/login` | `guestGuard` | Login (e-mail/senha) |
| `/registrar` | `guestGuard` | Registro (nome/e-mail/senha) |
| `/recuperar-senha` | `guestGuard` | Recuperação de senha |
| `/jogo` | `authGuard` | Jogo |
| `/resultado/:partidaId` | `authGuard` | Resultado |
| `/ranking` | `authGuard` | Ranking |
| `/vincular-legado` | `authGuard` | Vínculo de conta antiga |
| `''` | — | Redireciona para `/login` |
| `**` | — | Redireciona para `''` |

No GitHub Pages, as URLs públicas incluem hash (`/#/login`, `/#/jogo`, `/#/resultado/12`, `/#/ranking`). O `baseHref` de produção é `/Human-AI/`; o desenvolvimento continua em `/`.

### 10.2 Serviços

- `AuthService`: inicialização, cadastro, login, logout, recuperação, vínculo e sincronização local.
- `FirebaseAuthGateway`: wrapper testável do SDK (persistência, observer, ID Token, operações de auth).
- `PartidaService`: partida atual, início, abandono, envio, resultado, cache.
- `RankingService`: carregamento, polling, revisão.
- `SessaoStore`: signals de usuário/papel/autenticado/pronto.
- `SessaoStorage`: limpeza do token legado e das respostas parciais.
- `authInterceptor`: ID Token via SDK + tratamento de 401; não atua quando `apiUrl` está vazio.
- `apiIndisponivelInterceptor`: bloqueia `/auth`, `/partidas` e `/ranking` quando a API não está configurada, retornando `ApiIndisponivelError` em PT-BR sem chamada de rede.

### 10.3 Formulários reativos

- Login: e-mail e senha obrigatórios.
- Registro: nome, e-mail, senha e confirmação; validador de igualdade.
- Recuperação: e-mail.
- Vínculo: código do professor.
- Jogo: `FormArray` com 22 grupos `{ cartaId, escolha }`; `escolha` obrigatória.

### 10.4 Ranking sem reload

- Após o envio, `notificarConclusao()` invalida o cache.
- Resultado consulta `GET /ranking?limite=1` para a posição.
- Ranking faz polling de 5 s com `timer` + `exhaustMap`.
- Em erro, mantém a lista anterior e tenta de novo.
- Sem `location.reload()`.

### 10.5 Build, ambientes e publicação

- `angular.json` → `configurations.production.baseHref: "/Human-AI/"`; `development` continua com `/`.
- `fileReplacements` troca `environment.ts` por `environment.prod.ts` no build de produção.
- `environment.prod.ts` usa `apiUrl: ''` enquanto a API pública não existe. Com isso, `apiIndisponivelInterceptor` bloqueia `/auth`, `/partidas` e `/ranking`, e `AuthService` falha antes do Firebase.
- O roteador usa `withHashLocation()`: URLs públicas com `#` e reload/deep link sem reescrita SPA.
- Workflow `.github/workflows/deploy-pages.yml`:
  - gatilhos `push` em `main` e `workflow_dispatch`;
  - permissões `contents: read`, `pages: write`, `id-token: write`;
  - `concurrency: pages`, sem cancelar deploy em andamento;
  - build com Node 22, `npm ci`, testes ChromeHeadless e `npm run build`;
  - verificação de `<base href="/Human-AI/">` e de arquivos proibidos/credenciais/URL local;
  - upload de `frontend/dist/humano-ou-ia/browser` via `actions/upload-pages-artifact`;
  - deploy com `actions/configure-pages` e `actions/deploy-pages` no environment `github-pages`.
- O artefato não inclui `backend/`, JSON de cartas, `.env`, banco, PDF ou credencial.
- Ativação manual: Settings → Pages → Source: GitHub Actions.
- Firebase: adicionar `zthiagoferr.github.io` em Authentication → Settings → Authorized domains.

## 11. Segurança — leia antes de publicar

Esta é uma **demonstração**. Em uso real:

1. **HTTPS** obrigatório.
2. **Quotas/rate limiting** no Firebase e no backend para login, reset e respostas.
3. **Sessão:** gerenciada pelo Firebase SDK (persistência local); aplicar CSP e evitar XSS.
4. **Logout:** local; tokens já emitidos podem valer até ~1 h. Avaliar `HUMANAI_FIREBASE_CHECK_REVOKED=true`.
5. **Cadastro aberto** permite contas falsas; usar convite/SSO ou aprovação.
6. **Gabarito:** manter `backend/` privado; não versionar PDF; não servir `app/data`.
7. **LGPD:** ranking com nomes exige base legal, consentimento e política de privacidade.
8. **Docs:** desabilitar `/docs` e `/openapi.json` em produção.
9. **Credencial Admin:** a chave antiga deve ser revogada; a nova fica fora do repositório. Nunca no frontend. Em produção, preferir `HUMANAI_FIREBASE_CREDENTIALS_JSON` como secret.
10. **API key pública:** restringir por domínio/HTTP referrer no Google Cloud Console; incluir `https://zthiagoferr.github.io/*`.
11. **GitHub Pages:** adicionar `zthiagoferr.github.io` aos Authorized domains; publicar somente o build do frontend.
12. **Repositório público:** o código do backend e o JSON de cartas são visíveis por decisão do projeto; o app não os serve, mas o arquivo pode ser lido no GitHub. Rever antes de uso real.
13. **CORS futuro:** incluir `https://zthiagoferr.github.io` em `HUMANAI_CORS_ORIGINS`; API deve ser HTTPS.
14. **Railway/PostgreSQL:** `DATABASE_URL` e `HUMANAI_FIREBASE_CREDENTIALS_JSON` são secrets; não logar URL, senha, caminho ou JSON.
15. **SQLite em produção:** recusado por `HUMANAI_ENV=production`; usar PostgreSQL persistente.

## 12. Testes

### Back-end

```bash
cd backend
pytest -q
```

Cobrir:

- 22 cartas, 11/11, IDs oficiais, campos.
- Firebase: token ausente/inválido/expirado/revogado/outro projeto; auto-provisionamento; papéis.
- Rotas legadas 410; vínculo por código e uso único.
- Início de partida, 22 cartas, ausência de `origem`/`analise`.
- Uma partida ativa, retomada, abandono.
- 22 respostas exatas, duplicata, carta inválida.
- Pontuação e duração do servidor.
- Idempotência do envio.
- Ranking com 220 usuários, empates, melhor tentativa, posição própria.
- Migração não destrutiva e preservação de dados/ranking.
- Segurança: CORS, 401/403/410, sem vazamento antes do fim.
- Produção: normalização de `DATABASE_URL`, precedência, fail-fast de SQLite, `producao` com `production`, modelo sem `NOCASE` no PG, índice `lower(usuario)`, health 503, credencial Firebase JSON e smoke opcional em PostgreSQL (`HUMANAI_TEST_POSTGRES_URL`).

### Front-end

```bash
cd frontend
CHROME_BIN=/usr/bin/chromium npm test -- --watch=false --browsers=ChromeHeadless
```

Cobrir guards, gateway fake, persistência simulada, interceptor, formulários, polling e renderização. O CI de Pages roda os 38 testes com ChromeHeadless antes do build.

Build de produção:

```bash
cd frontend
npm run build
grep -n '<base href=' dist/humano-ou-ia/browser/index.html
# esperado: <base href="/Human-AI/">
```

## 13. Operação

- Rodar o back-end a partir de `backend/`.
- `uvicorn app.main:app --reload --port 8000`.
- Em dev, SQLite; em produção, PostgreSQL (Railway).
- Migração automática no startup: `firebase_uid`, índice único e `codigos_vinculo`; idempotente; no PG cria índice `lower(usuario)` e view com `CREATE OR REPLACE`.
- Rodar `python scripts/migrar_firebase.py` para aplicar/verificar e comparar contagens (SQLite local).
- Migração SQLite → PostgreSQL: `python scripts/migrar_sqlite_para_postgres.py --dry-run` e depois `--executar`; preserva IDs, ajusta sequences e não altera o SQLite.
- Gerar código de vínculo: `python scripts/gerar_codigo_vinculo.py --usuario ana.lima`.
- Resetar banco SQLite (apenas desenvolvimento): parar servidor e apagar `humanai.db` (e `-wal`/`-shm`). Nunca em produção sem backup.
- Logs sem tokens, senhas, credenciais, URL do banco ou corpos sensíveis.
- Backup: SQLite com servidor parado; PostgreSQL com `pg_dump`/snapshot do Railway, guardado fora do repositório.
- Credencial Admin: `HUMANAI_FIREBASE_CREDENTIALS_JSON` (secret), `GOOGLE_APPLICATION_CREDENTIALS` ou ADC; nunca versionar.
- Deploy do frontend: push em `main` ou `gh workflow run deploy-pages.yml`; monitorar com `gh run list`/`gh run view`.
- Deploy do backend: serviço Railway com Root Directory `backend`, Dockerfile, PostgreSQL e domínio; ainda não realizado.
- GitHub Pages: ativar em Settings → Pages → Source: GitHub Actions antes do primeiro deploy.
- Rollback: novo commit com correção e novo deploy; nunca force push.

## 14. Produção — Railway + PostgreSQL

### 14.1 Variáveis

```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
HUMANAI_ENV=production
HUMANAI_FIREBASE_PROJECT_ID=human-ai-5c442
HUMANAI_CORS_ORIGINS=https://zthiagoferr.github.io
HUMANAI_DOCS_ENABLED=false
HUMANAI_FIREBASE_CREDENTIALS_JSON=<json secreto>
```

Opcionais: `HUMANAI_PROFESSOR_EMAILS`, `HUMANAI_FIREBASE_CHECK_REVOKED`, `HUMANAI_VINCULO_TTL_HOURS`, `HUMANAI_RANKING_MAX_LIMIT`.

- `DATABASE_URL` tem precedência sobre `HUMANAI_DATABASE_URL`.
- `postgres://`/`postgresql://` são normalizados para `postgresql+psycopg://`.
- `?ssl=require` é convertido para `?sslmode=require` se não houver `sslmode`.
- `HUMANAI_ENV=production` recusa SQLite.
- `PORT` é injetada pelo Railway; o container usa `${PORT:-8080}`.
- `HUMANAI_FIREBASE_CREDENTIALS_JSON` deve ser secret e validado contra `project_id=human-ai-5c442`.

### 14.2 Imagem e Railway

- `backend/Dockerfile`: `python:3.13-slim`, `psycopg[binary]`, Uvicorn em `0.0.0.0:${PORT:-8080}`, usuário não-root.
- `backend/.dockerignore`: exclui `.venv`, `.env`, bancos, testes, scripts e JSON de credencial; mantém `app/data/cartas_gabarito.json`.
- `backend/railway.json`: healthcheck `/api/health`, restart em falha, uma réplica.
- Serviço Railway: root directory `backend`, builder Dockerfile, PostgreSQL anexado, domínio público.

### 14.3 Saúde e erros

- `/api/health` executa `SELECT 1`; 200 confirma banco; 503 genérico se indisponível.
- `SQLAlchemyError` não tratado retorna 503 genérico e loga apenas o tipo.
- Startup com banco inválido falha com mensagem genérica, sem URL/senha.
- Logs não incluem token, claims, credencial ou URL do banco.

### 14.4 Migração de dados

- Script `scripts/migrar_sqlite_para_postgres.py`.
- Dry-run padrão; `--executar` para escrita.
- Fonte SQLite em `mode=ro`; destino PostgreSQL.
- Aborta se o destino tiver dados, se houver órfãos/duplicidades/campos longos ou schema incompatível.
- Preserva IDs; ajusta sequences com `setval`.
- Nunca apaga/trunca tabelas e nunca modifica o SQLite.
