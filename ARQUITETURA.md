# Arquitetura — Humano ou IA?

## 1. Princípios

- **Fluxo linear:** login → jogo → resultado → ranking, sem menu de navegação.
- **Gabarito isolado:** o aluno só recebe origem e análise depois de finalizar as 22 respostas.
- **Servidor como autoridade:** tempo, pontuação e ranking são calculados no back-end.
- **Contratos explícitos:** DTOs públicos não contêm campos do gabarito; o JSON é camelCase.
- **Simplicidade operacional:** SQLite + Uvicorn em um único processo para a demonstração.
- **Design editorial:** papel, tinta e tipografia com serifa, sem dependência de fontes externas.
- **Evolução possível:** a separação em camadas permite trocar SQLite por PostgreSQL, polling por SSE e o provedor de identidade sem alterar partidas/ranking.

## 2. Estrutura de pastas

```text
Human-AI/
├── README.md
├── ARQUITETURA.md
├── DOCUMENTACAO_TECNICA.md
├── GUIA_DO_PROFESSOR.md
├── .gitignore
├── imagens/
│   └── Logo HumanAI_ Conexão entre Humano e IA.png
├── backend/
│   ├── .env.example
│   ├── .gitignore
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── security.py
│   │   ├── legacy_passwords.py
│   │   ├── firebase_auth.py
│   │   ├── migrations.py
│   │   ├── dependencies.py
│   │   ├── exceptions.py
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── professor.py
│   │   │   ├── partidas.py
│   │   │   ├── ranking.py
│   │   │   └── health.py
│   │   ├── services/
│   │   │   ├── usuario_service.py
│   │   │   ├── vinculo_service.py
│   │   │   ├── partida_service.py
│   │   │   └── ranking_service.py
│   │   ├── domain/
│   │   │   ├── cartas.py
│   │   │   └── normalizacao.py
│   │   └── data/
│   │       └── cartas_gabarito.json
│   ├── scripts/
│   │   ├── extrair_pdf.py
│   │   ├── validar_cartas.py
│   │   ├── migrar_firebase.py
│   │   └── gerar_codigo_vinculo.py
│   └── tests/
│       ├── conftest.py
│       ├── fakes.py
│       ├── test_auth.py
│       ├── test_firebase_auth.py
│       ├── test_professor.py
│       ├── test_vinculo.py
│       ├── test_migracao.py
│       ├── test_cartas.py
│       ├── test_partidas.py
│       ├── test_ranking.py
│       └── test_seguranca.py
└── frontend/
    ├── angular.json
    ├── package.json
    ├── tsconfig*.json
    ├── public/
    │   └── logo-humanai.png
    └── src/
        ├── index.html
        ├── main.ts
        ├── styles.scss
        ├── environments/
        └── app/
            ├── app.component.*
            ├── app.config.ts
            ├── app.routes.ts
            ├── core/
            │   ├── auth/
            │   ├── models/
            │   ├── services/
            │   └── utils/
            ├── features/
            │   ├── login/
            │   ├── registro/
            │   ├── jogo/
            │   ├── resultado/
            │   └── ranking/
            └── shared/
                ├── components/
                ├── pipes/
                └── styles/
```

## 3. Arquitetura do front-end

### 3.1 Componentes standalone

Angular 20 com `bootstrapApplication`, `provideRouter`, `provideHttpClient(withInterceptors([authInterceptor]))` e `provideAppInitializer`. O inicializador restaura a sessão do Firebase e sincroniza o perfil local via `/auth/me`. Não há `NgModule` de feature. O carregamento das telas é lazy por rota.

- `AppComponent`: shell mínimo, apenas `<router-outlet />` e o fundo de papel.
- `features/*`: telas.
- `shared/*`: marca, avisos, pipes e estilos.
- `core/*`: autenticação, modelos, serviços de API e utilitários.

### 3.2 Estado com signals

- `SessaoStore`: usuário local, papel, `autenticado` e `pronto`; sem token em storage próprio.
- `FirebaseAuthGateway`: wrapper testável do Firebase JS SDK (login, cadastro, logout, reset, ID Token).
- `PartidaService`: partida atual, cache do último resultado e respostas parciais.
- `RankingService`: dados, carregando, erro e contador de revisão.

Não há NgRx. O estado é pequeno e local; signals evitam complexidade e atualizam a UI sem reload.

### 3.3 Formulários reativos

- Login e registro usam `FormBuilder`, `Validators` e validadores customizados. Login é e-mail/senha; registro é nome/e-mail/senha.
- O jogo usa `FormArray` com exatamente 22 `FormGroup`s `{ cartaId, escolha }`.
- O botão de finalização só habilita com `form.valid`.
- Mensagens de erro são associadas aos campos e anunciadas com `aria-live`; erros do Firebase são traduzidos para PT-BR.

### 3.4 Fluxo linear e guards

- `authGuard`: exige usuário Firebase autenticado; senão redireciona para `/login`.
- `guestGuard`: se autenticado, redireciona para `/jogo`; senão permite login/registro/recuperação.
- Nenhuma rota ou componente contém menu de navegação.
- Ações contextuais: “Criar conta”, “Já tenho conta”, “Esqueci minha senha”, “Ver ranking”, “Jogar novamente”, “Sair”, “Desistir da partida”.

### 3.5 Ranking sem reload

- Após o envio, `RankingService.notificarConclusao()` invalida o cache.
- A tela de resultado consulta a posição do aluno.
- A tela de ranking faz polling de 5 s com `timer` + `exhaustMap`, atualizando signals.
- Nenhum `location.reload()`.

## 4. Arquitetura do back-end

### 4.1 Camadas

```text
HTTP (routers)
  → validação de schema (schemas.py)
  → regras de aplicação (services)
  → domínio de cartas (domain/cartas.py)
  → persistência (models.py + database.py)
```

- `routers/*`: rotas, status HTTP, dependências de autenticação.
- `services/*`: transações, regras de partida, ranking, autenticação.
- `domain/cartas.py`: carrega e valida o JSON; expõe DTO público e consulta interna de origem/análise.
- `schemas.py`: Pydantic v2, camelCase, response models que impedem vazamento.
- `exceptions.py`: erros padronizados.

### 4.2 Autenticação

- **Frontend:** Firebase Authentication (e-mail/senha) via Firebase JS SDK modular, sem AngularFire.
- **Persistência:** `browserLocalPersistence`; a sessão sobrevive a recarregamentos.
- **Token:** o interceptor pede `getIdToken()` ao SDK e envia `Authorization: Bearer <ID Token>`.
- **Backend:** `firebase-admin` inicializado por ADC/`GOOGLE_APPLICATION_CREDENTIALS`.
- **Projeto ativo:** `human-ai-5c442`. O backend valida `aud`/`iss` contra `HUMANAI_FIREBASE_PROJECT_ID`; tokens do projeto antigo são rejeitados.
- **Validação:** `verify_id_token()` verifica assinatura, expiração, `aud` e `iss`; há checagem explícita do projeto configurado.
- **Identidade:** `users.firebase_uid` é único; o `uid` é imutável. O usuário local é recuperado ou auto-provisionado.
- **Papel:** calculado por allowlist de e-mails verificados (`HUMANAI_PROFESSOR_EMAILS`), nunca aceito do cliente.
- **Legado:** não há auto-link por e-mail; contas antigas usam código temporário emitido pelo professor.
- **Erros:** token ausente/inválido/expirado → 401; sem papel de professor → 403; Firebase indisponível → 503; rotas antigas → 410.

### 4.3 Gabarito

- `backend/app/data/cartas_gabarito.json` (ou caminho em `HUMANAI_CARTAS_PATH`).
- Carregado no startup; se inválido, o processo não sobe.
- Nenhuma rota estática aponta para `app/data`.
- DTO público `CartaPublica` contém apenas `id`, `numero`, `citacao`, `categoria`, `tema`.
- `origem` e `analise` só aparecem no resultado final.

### 4.4 Banco e ranking

- SQLite com WAL, foreign keys e busy timeout.
- Uma partida ativa por aluno via índice único parcial.
- Ranking é uma view (`vw_ranking`) com `ROW_NUMBER()`, sem tabela materializada.
- Melhor partida por aluno; ordenação: acertos ↓, duração ↑, nome normalizado ↑, id ↑.

### 4.5 CORS

- Origens explícitas: `http://localhost:4200` e `http://127.0.0.1:4200`.
- Sem `*`; sem credenciais de cookie.
- Headers: `Authorization`, `Content-Type`, `Accept`.
- Métodos: `GET`, `POST`, `OPTIONS`.

## 5. Fluxo de dados

### 5.1 Login

```text
Angular → Firebase Auth (signInWithEmailAndPassword / createUserWithEmailAndPassword)
        ← usuário Firebase persistido no navegador
Angular → GET/POST /api/auth/me|sessao com Bearer ID Token
        ← usuário local + papel
Angular salva usuário/papel em signals; o token fica a cargo do SDK
```

### 5.2 Partida

```text
Angular → GET /api/partidas/atual
        ← partida ativa (22 cartas) ou null
se null:
Angular → POST /api/partidas
        ← 201 partida com 22 cartas públicas
```

### 5.3 Respostas

```text
Angular monta FormArray com 22 escolhas
Angular → POST /api/partidas/{id}/respostas
        ← acertos, erros, duração e correção com análise
Angular → GET /api/ranking?limite=1 (posição)
Angular navega para /resultado/{id}
```

### 5.4 Ranking

```text
RankingComponent → GET /api/ranking?limite=500
                 ← lista + meuResultado
timer(5s) repete sem reload
```

## 6. Decisões e justificativas

| Decisão | Alternativa | Por que |
|---|---|---|
| FastAPI | Flask | Validação tipada, OpenAPI, injeção de dependências e menos boilerplate para REST |
| SQLite | PostgreSQL | Zero configuração para demonstração; WAL e índices suportam 200+ alunos |
| SQLAlchemy 2.0 | SQL puro | Transações, modelos e legibilidade; DDL documentado separadamente |
| Firebase Authentication | Autenticação própria | Provedor maduro para senha, reset e ID Tokens; remove Argon2/sessões próprias |
| Firebase JS SDK modular | AngularFire | SDK agnóstico de framework; evita acoplamento de peer dependency com Angular 20 |
| SQLite mantido | Firestore | O jogo precisa de SQL transacional, view de ranking e migração simples; Firestore não substitui |
| Allowlist de professor | Coluna `papel` | Sem privilégio persistido/desatualizado; revogação por variável de ambiente |
| Código de vínculo | Auto-link por e-mail | Evita tomada de conta por quem registrar o e-mail antigo |
| JSON de cartas | Tabela de cartas | Mantém o gabarito em um único arquivo server-side e facilita auditoria |
| Tempo no servidor | Tempo no cliente | Impede manipulação de relógio/DevTools |
| Melhor tentativa | Última tentativa | Não pune prática; ranking educacional mais justo |
| Polling 5 s | WebSocket/SSE | Simples, robusto e suficiente para uma turma |
| Ordem fixa #01–#22 | Embaralhar | Preserva a numeração do PDF e a conferência; não há requisito de embaralhar |
| Sem Angular Material | Material | O design editorial exige controle total de tipografia, papel e filetes |
| Persistência local do Firebase | sessionStorage próprio | Sobrevive a recarregamentos; o SDK gerencia refresh e armazenamento |
| Uvicorn 1 worker | Vários workers | SQLite não é ideal para escrita concorrente multi-processo |

## 7. Segurança e limites

- **Gabarito:** nunca no front-end, nunca em `public/`, nunca em resposta pré-final.
- **Senhas:** gerenciadas pelo Firebase Authentication; o backend nunca as recebe.
- **Tokens:** ID Tokens verificados por assinatura, expiração, `aud` e `iss`; não são armazenados no banco.
- **Logout:** `signOut` no cliente; tokens já emitidos valem até ~1 h. `check_revoked` é opcional.
- **Enumeração:** login/reset genéricos; partida de outro usuário → 404.
- **Papel:** allowlist de e-mails verificados; verificação no backend.
- **Contas legadas:** código temporário emitido pelo professor; sem auto-link por e-mail.
- **SQL injection:** ORM e parâmetros.
- **XSS:** Angular escapa interpolações; não usar `innerHTML`; CSP; sessão do SDK no navegador.
- **CORS:** origens explícitas.
- **Rate limiting:** não implementado na demo; obrigatório em produção.
- **HTTPS:** obrigatório em produção.
- **LGPD:** ranking exibe nomes; obter consentimento/base legal e limitar acesso.
- **Credencial Firebase:** chave antiga comprometida; revogar e usar nova fora do repositório.

## 8. Desempenho com 200+ alunos

- Consulta de ranking com view + índices parciais; payload de 500 linhas é pequeno.
- Uma linha por aluno, não uma por tentativa.
- SQLite em WAL suporta leituras concorrentes; escritas são serializadas.
- Para escala maior: PostgreSQL, cache do ranking e SSE/WebSocket.

## 9. Testes

- **Cartas:** 22, 11/11, IDs, campos, lista oficial.
- **Auth:** auto-provisionamento, idempotência, token inválido/expirado/revogado, projeto divergente, papéis.
- **Partidas:** 22 cartas, ausência de gabarito, uma ativa, retomada, abandono, propriedade.
- **Respostas:** 22 exatas, duplicata, carta inválida, pontuação, idempotência, duração do servidor.
- **Ranking:** 220 usuários, ordenação, desempate, melhor tentativa, posição própria, paginação.
- **Vínculo:** códigos, expiração, uso único, shell com partidas, preservação do legado.
- **Migração:** coluna `firebase_uid`, índice único, idempotência, preservação de contagens e ranking.
- **Segurança:** CORS, 401/403/410, ausência de gabarito antes do fim.
- **Front:** guards, formulários, gateway fake, interceptor, persistência simulada, polling, renderização.

## 10. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Vazamento do gabarito | DTO público, response models, backend privado, sem static em `app/data` |
| PDF com gabarito no repositório | Não versionar o PDF; manter local; `.gitignore` |
| Credencial Firebase exposta | Revogar/rotacionar; não copiar; `.gitignore` |
| XSS e roubo de sessão | Não usar `innerHTML`; CSP; sessão gerenciada pelo SDK |
| Força bruta | Quotas do Firebase + rate limiting em produção |
| Credencial Admin comprometida | Revogar chave antiga; nova chave fora do repositório; `.gitignore` |
| Conta legada sem vínculo | Código emitido pelo professor; comunicação prévia |
| Aluno joga antes de vincular | Link retorna 409; orientar vínculo antes da primeira partida |
| SQLite lock | Um worker; WAL; busy timeout |
| Trapaça no tempo | Timestamps do servidor |
| Pressão por tempo | Explicar que o ranking não mede inteligência; adaptar avaliação |
| Nomes no ranking | Política de privacidade/LGPD; acesso autenticado |
| PDF mal transcrito | Validação + conferência manual + script |

## 11. Não objetivos

- Painel do professor dentro do app (os endpoints/CLI são operacionais).
- Múltiplas turmas/turmas privadas.
- Aplicativo mobile nativo.
- Detecção automática de IA.
- WebSocket/SSE em tempo real.
- Migrações Alembic.
- Mesclagem automática de partidas entre conta nova e legada.
