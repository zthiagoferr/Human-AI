# Guia do Professor — Humano ou IA?

## 1. Para que serve

“Humano ou IA?” é uma atividade de **letramento digital e leitura crítica**. O aluno lê 22 citações e decide se cada uma foi escrita por um humano ou gerada por IA. O objetivo não é “acertar o detector”, mas observar **marcas de escrita**, argumentar com evidências do texto e refletir sobre autoria, estilo e uso responsável de IA.

A atividade foi desenhada para uma aula de 50–60 minutos, mas pode ser adaptada.

## 2. Objetivos de aprendizagem

Ao final, o aluno deve ser capaz de:

- identificar traços de estilo, voz e intenção em um texto curto;
- reconhecer fórmulas recorrentes em textos gerados por IA;
- evitar conclusões binárias do tipo “isso é IA porque parece robótico”;
- usar evidências textuais para justificar uma interpretação;
- discutir autoria, crédito e uso ético de IA na escola;
- compreender que marcadores estilísticos são **indícios probabilísticos**, não provas.

## 3. Antes da aula

1. Instale e rode o back-end e o front-end (ver `README.md`).
2. Configure o Firebase do projeto ativo `human-ai-5c442`:
   - habilite **Email/Password**;
   - cadastre o **Web App** e preencha `frontend/src/environments/firebase.config.ts` com a configuração pública;
   - adicione `localhost` e o domínio de produção aos **domínios autorizados**;
   - gere uma nova chave de service account/ADC do projeto `human-ai-5c442` e exporte `GOOGLE_APPLICATION_CREDENTIALS` (nunca versionar).
3. Revogue a chave antiga de service account, se ainda existir.
4. Crie/verifique a conta do professor no Firebase e coloque o e-mail em `HUMANAI_PROFESSOR_EMAILS` (o claim `email_verified` precisa ser `true`).
5. Configure `HUMANAI_FIREBASE_PROJECT_ID=human-ai-5c442`.
6. Faça backup de `backend/humanai.db`, `-wal` e `-shm` antes da primeira execução em banco existente.
7. Verifique se as 22 cartas estão preenchidas e validadas:
   ```bash
   cd backend
   python scripts/validar_cartas.py
   ```
8. Faça uma partida de teste com uma conta de demonstração.
9. Teste cadastro, login, logout e recuperação de senha.
10. Confira se o ranking abre e atualiza.
11. Prepare os dispositivos: um por aluno ou um por dupla.
12. Tenha o gabarito impresso ou aberto em uma tela separada, nunca projetada.
13. Leia previamente as análises das cartas para conduzir o debate.

## 4. Onde fica o gabarito

O gabarito **não** é exibido ao aluno antes do fim da partida. Existem duas cópias de referência:

1. **No back-end:** `backend/app/data/cartas_gabarito.json`, nos campos `origem` e `analise` de cada carta. Esse arquivo é lido apenas pelo servidor e não é servido por nenhuma rota. A pasta `backend/` é material do professor: não a distribua aos alunos nem a publique.
2. **No PDF de origem:** a página de **“Gabarito Separado”** ao final de `Jogo Humano ou IA - 22 Cartas e Gabarito Separado (1).pdf`.

Este guia **não reproduz a lista de quais cartas são humanas ou de IA**, para evitar vazamento acidental. A distribuição é de **11 cartas humanas e 11 cartas de IA**. Para conferir caso a caso, use o JSON no back-end ou a página de gabarito do PDF.

> **Cuidado:** o PDF contém o gabarito. Não o coloque em `frontend/public`, não o projete e não o envie aos alunos. Após a atividade, o aluno vê a análise de cada carta na tela de resultado — isso é intencional e faz parte do aprendizado. O que não pode acontecer é o acesso antes da finalização.

### 4.1 Contas antigas (migração)

O projeto **não** vincula automaticamente contas antigas por e-mail. Isso evita que alguém tome o histórico de um aluno apenas criando uma conta Firebase com o e-mail dele.

Processo:
1. O aluno cria/loga com a nova conta Firebase.
2. Você gera um código para a conta legada:
   - pela API autenticada como professor (`POST /api/professor/legado/{id}/codigo`); ou
   - pela ferramenta local:
     ```bash
     cd backend
     source .venv/bin/activate
     python scripts/gerar_codigo_vinculo.py --usuario ana.lima
     ```
3. Entregue o código **individualmente** ao aluno. Não projete, não publique no chat da turma.
4. O aluno acessa `/vincular-legado`, entra com a nova conta e digita o código.
5. Se a conta nova ainda não tiver partidas, o vínculo é feito e o histórico legado é preservado.
6. Se a conta nova já tiver partidas, o sistema recusa (`CONTA_JA_POSSUI_PARTIDAS`). Oriente o aluno a falar com você; não mescle partidas automaticamente.
7. O código é de uso único, expira em 24 h por padrão e não deve ser compartilhado.

## 5. Roteiro de aula — 60 minutos

### 0–5 min — Abertura

Pergunte:

- “Quem já teve dúvida se um texto foi escrito por uma pessoa ou por uma IA?”
- “O que faria você desconfiar de um texto?”
- “É possível ter certeza só pelo estilo?”

Explique que o jogo não é uma prova de “detecção”, mas um exercício de leitura.

### 5–10 min — Combinados

- Um dispositivo por aluno ou dupla.
- Ler a citação inteira antes de responder.
- Não pesquisar a frase na internet durante a partida.
- O ranking é um jogo; não é medida de inteligência.
- O tempo é critério de desempate, mas a precisão vale mais.

### 10–30 min — Partida

- Login/cadastro com e-mail e senha (Firebase).
- 22 cartas, uma por vez.
- Em duplas, o aluno deve **dizer em voz alta uma razão** antes de escolher.
- Ao final, cada aluno lê sua correção em silêncio por 2–3 minutos.

### 30–40 min — Leitura da correção

Peça que escolham **duas cartas**:

- uma em que acertaram e têm certeza do porquê;
- uma em que erraram ou ficaram em dúvida.

Para cada uma, localizar no texto:

- uma palavra ou expressão que sustenta a interpretação;
- uma escolha de ritmo, pontuação ou imagem;
- uma fórmula que parece genérica.

### 40–55 min — Debate coletivo

Perguntas:

- “Que detalhe só um humano escreveria?”
- “Que frase parece cumprir a função de concluir um texto, sem acrescentar ideia?”
- “Há ironia? Como você percebeu?”
- “O texto arrisca uma metáfora original ou repete uma fórmula?”
- “O que mudaria na sua leitura se soubesse a origem?”
- “Por que acertar não prova que você ‘detecta IA’?”

Conduza para a ideia de **indício**, não de prova.

### 55–60 min — Fechamento

Exit ticket (uma frase):

- “Uma marca de escrita humana que eu consigo explicar é…”
- “Uma marca de escrita de IA que eu consigo explicar é…”
- “Uma coisa que eu ainda não consigo decidir só pelo texto é…”

## 6. Justificativa pedagógica

### 6.1 Traços humanos

Textos humanos, especialmente literários e autorais, tendem a apresentar:

- **Paradoxo:** convivem com contradições sem resolvê-las.
- **Ironia:** dizem o contrário do que parecem dizer; exigem inferência.
- **Vulnerabilidade:** assumem medo, dúvida, desejo, fracasso.
- **Metáforas originais:** imagens inesperadas, não apenas decorativas.
- **Especificidade:** detalhes concretos, nomes, objetos, cenas.
- **Ritmo irregular:** frases curtas e longas alternadas; pausas; rupturas.
- **Ambiguidade produtiva:** deixam pontas soltas.
- **Humor e autoironia:** brincam com o próprio discurso.
- **Referências culturais situadas:** alusões que exigem repertório.
- **Imperfeição:** repetições, correções, coloquialismos, marcas de oralidade.
- **Risco:** uma opinião forte, uma imagem estranha, uma conclusão que não agrada a todos.

### 6.2 Marcadores de IA

Textos gerados por IA, com frequência, apresentam:

- **Conectivos de conclusão genéricos:** “Em suma”, “Em resumo”, “Portanto”.
- **Fórmulas de importância:** “É fundamental destacar”, “É importante notar”, “Vale ressaltar que”.
- **Aberturas de contexto amplo:** “No mundo acelerado de hoje”, “Em um cenário cada vez mais…”, “Na era digital”.
- **Clichês corporativos:** “jornada”, “transformador”, “robusto”, “sinergia”, “alavancar”, “otimizar”, “solução inovadora”.
- **Simetria excessiva:** parágrafos do mesmo tamanho; listas de três; estrutura “não apenas… mas também”.
- **Otimismo genérico:** conclusão que promete benefícios sem custos.
- **Excesso de hedge:** “pode”, “talvez”, “de certa forma”, sem assumir posição.
- **Falta de detalhe concreto:** nenhuma cena, nome, objeto ou experiência situada.
- **Conclusão que repete a introdução:** o texto “fecha” sem avançar.

### 6.3 O essencial: indício, não prova

É preciso evitar dois erros:

1. **Essencialismo:** “todo texto humano é vulnerável; toda IA é genérica”. Há humanos que escrevem de forma corporativa e IAs que imitam ironia e vulnerabilidade.
2. **Detectivismo:** transformar a aula em caça às bruxas ou em treinamento de “detector de IA”. Detectores automáticos são pouco confiáveis e podem produzir falsos positivos.

O jogo ensina **leitura atenta, comparação e argumentação**. A pergunta produtiva não é “qual é a verdadeira origem?”, mas “que evidências textuais sustentam minha hipótese e quais a enfraquecem?”.

### 6.4 Autoria e ética

A atividade abre espaço para discutir:

- quando o uso de IA é apoio e quando é substituição do próprio trabalho;
- crédito e transparência;
- direitos autorais dos textos-fonte;
- preconceito e generalização;
- o valor do erro e da imperfeição na escrita;
- por que “parecer humano” não é o mesmo que “ser humano”.

## 7. Como usar o resultado

A tela de resultado mostra, para cada carta:

- a resposta do aluno;
- a resposta correta;
- se acertou;
- a análise da carta, vinda do gabarito.

Sugestões:

- Peça que o aluno sublinhe, na análise, uma expressão que ele **não** havia percebido.
- Compare duas cartas de origens diferentes e peça um critério comum.
- Escolha uma carta em que a turma divergiu e faça votação argumentada.
- Peça uma reescrita de uma carta de IA em estilo humano — e vice-versa — discutindo o que mudou.

## 8. Ranking: como apresentar

- O ranking ordena por **acertos**, depois **menor tempo**, depois **nome**.
- Uma tentativa melhor substitui a anterior; tentativas piores não pioram a posição.
- O tempo é apenas desempate; não é medida de inteligência, leitura ou valor.
- Alunos com necessidades de acessibilidade podem precisar de mais tempo. Considere avaliar apenas acertos ou formar duplas.
- Evite expor alunos com baixo desempenho. O ranking é uma ferramenta de jogo, não de constrangimento.
- Se a escola exigir privacidade, use nomes de exibição ou apelidos combinados.

## 9. Avaliação

Rubrica sugerida (4 níveis):

| Critério | 4 | 3 | 2 | 1 |
|---|---|---|---|---|
| Uso de evidência textual | Cita e explica marcas específicas | Cita marcas, explica parcialmente | Cita genericamente | Não cita o texto |
| Reconhecimento de incerteza | Distingue indício de prova | Menciona dúvida | Pouca dúvida | Trata hipótese como certeza |
| Argumentação | Compara, contra-argumenta, reconsidera | Argumenta com apoio | Opinião sem apoio | Sem argumento |
| Reflexão ética | Relaciona autoria, crédito e uso de IA | Menciona um aspecto | Superficial | Ausente |
| Participação | Escuta e contribui | Participa | Participa pouco | Não participa |

## 10. Adaptações

- **Sem dispositivos:** imprima apenas as páginas das cartas (nunca a página de gabarito); use cartões físicos e votação por levantar a mão.
- **Uma tela para a turma:** projete uma carta por vez; a turma vota; o professor registra.
- **Duplas:** um lê em voz alta, o outro argumenta; alternam.
- **Acessibilidade:** permita mais tempo, leitura em voz alta, contraste alto e fonte ampliada pelo navegador.
- **Aula curta:** use 10 cartas selecionadas e discuta o processo, não a pontuação.
- **Aula dupla:** inclua uma produção textual em que o aluno imite deliberadamente o estilo de IA e depois o subverta.

## 11. Problemas comuns

| Situação | Orientação |
|---|---|
| Aluno não consegue entrar | Confira e-mail/senha; o cadastro é autorregistro. Se a conta for antiga, gere código e oriente `/vincular-legado`. |
| Aluno não recebe e-mail de recuperação | Verifique spam; confirme o e-mail; o Firebase só envia para contas existentes. |
| “Este e-mail já está cadastrado” | Use login ou recuperação de senha; não crie duplicata. |
| Professor recebe 403 | Confirme `HUMANAI_PROFESSOR_EMAILS`, `email_verified=true` e reinicie o backend. |
| `AUTENTICACAO_INDISPONIVEL` | Verifique `GOOGLE_APPLICATION_CREDENTIALS`/ADC e `HUMANAI_FIREBASE_PROJECT_ID`. |
| “Já existe partida em andamento” | O jogo retoma automaticamente; se quiser recomeçar, use “Desistir da partida” |
| Ranking não atualiza | Aguarde até 5 s; verifique conexão; recarregue a tela |
| Resultado não abre | A partida pode não ter sido finalizada; volte ao jogo |
| Aluno viu a análise antes | Verifique se não há outra aba com resultado; o gabarito só é liberado após o envio |
| Turma sem internet | Rode tudo localmente; o front fala com `localhost:8000` e o Firebase precisa de rede |
| Nomes no ranking | Combine apelidos ou nomes de exibição previamente |

## 12. Perguntas frequentes

**O jogo prova se um texto foi escrito por IA?**  
Não. Ele exercita leitura e argumentação. Marcadores são indícios, não provas.

**Posso usar o ranking como nota?**  
Não é recomendado. O tempo e a competição podem distorcer o objetivo. Se necessário, avalie a justificativa escrita, não a posição.

**O aluno vê o gabarito?**  
Após finalizar, sim: ele vê a correção e a análise. Antes, não. O arquivo bruto do gabarito permanece no back-end.

**Posso reutilizar as cartas em outra turma?**  
Sim, mas esteja ciente de que respostas circulam. Para reuso, considere variar a ordem ou criar novas cartas.

**E se um aluno travou o tempo?**  
A duração é registrada no servidor; pausas contam. Ele pode desistir e começar de novo.

**Como falo de IA sem reforçar estereótipos?**  
Explore exemplos ambíguos, peça evidências e mostre que humanos também usam clichês. O foco é a leitura, não a essência.

## 13. Checklist rápido

- [ ] Back-end e front-end rodando.
- [ ] Firebase configurado (Email/Password, Web App, domínios autorizados).
- [ ] Credencial Admin nova/ADC configurada e chave antiga revogada.
- [ ] `HUMANAI_PROFESSOR_EMAILS` configurado e e-mail verificado.
- [ ] Backup do banco feito antes da migração.
- [ ] 22 cartas validadas.
- [ ] Conta de teste funcionando (cadastro/login/reset).
- [ ] Contas antigas vinculadas ou códigos preparados.
- [ ] Gabarito impresso/aberto em tela privada.
- [ ] Ranking testado.
- [ ] Regras de tempo e desempate explicadas.
- [ ] Plano B sem dispositivos.
- [ ] Conversa sobre ética e privacidade preparada.
