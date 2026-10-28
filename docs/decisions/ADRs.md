# Decisões arquiteturais

## ADR 001 — monólito modular

**Decisão:** módulos Python separados para dados, previsão, estoque, simulação e
assistência; uma API e um banco. As fronteiras são verificadas por testes e
contratos, sem serviços artificiais. Facilita rastrear uma recomendação de ponta a
ponta e executar tudo em CPU. Microserviços não resolvem um problema observado aqui.

## ADR 002 — SQLite e migrations SQL

**Decisão:** biblioteca padrão `sqlite3`, FKs, parâmetros e migrations versionadas.
SQLAlchemy/Alembic/PostgreSQL eram preferências, mas não estavam disponíveis no
ambiente e a instalação ficou bloqueada por permissões de rede. A alternativa
funciona com menos dependências. A migração para PostgreSQL e Alembic está pendente;
o repositório não se apresenta como compatível com PostgreSQL.

## ADR 003 — previsão tabular direta

**Decisão:** modelos separados para +30 e +60 minutos; HistGradientBoosting compete
com quatro baselines e Random Forest. Dados são pequenos e tabulares; nenhuma GPU,
rede neural ou modelo sequencial seria justificável antes de superar esses baselines.
A validação escolhe 31 folhas nos dois horizontes. O teste não é usado na promoção.

## ADR 004 — conformal estratificado por pico

**Decisão:** quantil finito-amostral do resíduo absoluto em período posterior à
validação, separado por pico/não pico. É simples e auditável, mas o grupo fora do
pico mistura horários abertos e fechados. Isso prejudica a cobertura durante a
operação. O achado fica visível; não se recalibra no teste para melhorar o número.
Próximo experimento: grupo aberto/fechado/pico e validação em novo período.

## ADR 005 — lexical antes de embeddings remotos

**Decisão:** TF-IDF lexical é o default do copiloto. LSA e word/char híbrido foram
avaliados; não melhoraram precisão das referências neste pequeno conjunto. LSA é
uma projeção do corpus, não um embedding semântico pré-treinado. Um encoder externo
fica pendente, com ablação e novo conjunto de avaliação antes de ser adotado.

## ADR 006 — ferramentas controladas, explicação opcional

**Decisão:** roteamento determinístico de intenções e allowlist Pydantic. O adaptador
externo só recebe evidências e devolve explicação sem números novos. Não executa
ferramentas. O modo offline usa templates, trechos documentais e dados reais da API.
A arquitetura reduz superfície de risco e continua demonstrável sem chave.

## ADR 007 — interface local sem downloads

**Decisão:** JavaScript ESM, CSS próprio, SVG e contratos TypeScript declarativos
(`contracts.d.ts`). Os pacotes React/Vite/Tailwind não estavam instalados e não houve
acesso autorizado aos downloads. A interface tem oito telas conectadas à API;
**não é implementada em React nem compilada com TypeScript**. Migração futura deve
preservar contratos e testes de fluxo. A preferência de stack não justifica impedir
uma aplicação utilizável com os recursos disponíveis.

## ADR 008 — tracking com degradação explícita

**Decisão:** ledger SQLite é obrigatório; `mlflow-skinny` é integração opcional em
`ml/tracking.py`. Sem pacote instalado, o relatório declara `mlflow_available=false`.
Não se afirma execução de MLflow. Parâmetros, métricas, versões, CSVs e artefatos
continuam auditáveis. O adaptador precisa ser exercitado ao liberar a instalação.
