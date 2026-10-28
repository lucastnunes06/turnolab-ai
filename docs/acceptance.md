# Estado de aceitação — auditoria de 28/10/2026

Não há declaração de conclusão integral. Os resultados abaixo distinguem código
implementado, execução verificada e dependências que o ambiente não permitiu validar.

| Critério | Estado | Evidência / limite |
|---|---|---|
| Backend funcional | Verificado em ASGI e HTTP/TCP local | `reports/checks.json`, `reports/release.json` |
| Frontend funcional | Implementado; browser pendente | Oito telas, 13 testes Node/componentes; sem captura aprovada |
| Dados reproduzíveis | Verificado | `scripts/reproduce_data.py` regenerou 6 CSVs; hashes SHA-256 iguais (`reports/data_reproduction.json`) |
| Validação | Verificado | Ausentes, IDs, unidades, duplicatas, ordem, gaps e constraints |
| Modelos treinados | Verificado | Demand + estoque + challenger em `artifacts/` |
| Baselines | Verificado | 14 avaliações, sete candidatos/configurações × dois horizontes |
| Separação temporal | Verificado pelos testes e revisão | Purge, lags causais, previsor auxiliar congelado; não é prova formal universal |
| Avaliação registrada | Verificado | SQLite ledger, JSON/CSV e gráficos |
| Incerteza | Implementada e analisada | Subcobertura operacional explicitamente reportada |
| Simulador | Verificado | Conservação, limites e entrega por prazo |
| Copiloto integrado | Verificado via API | Templates úteis; adaptador externo não exercitado |
| RAG/citações | Verificado via API | Referências consultáveis; conjunto de desenvolvimento pequeno |
| Ferramentas | Verificado | Pydantic + allowlist + autorização por restaurante |
| Aprovação humana | Verificado via API | Pending → approved/rejected + auditoria; dupla decisão recusada |
| Segurança básica | Verificado no escopo dos testes | Sem pentest ou CVE audit concluído |
| Logs e métricas | Verificado | Request IDs, latência, inferência, fallback/abstenção, PSI |
| Pipeline MLOps local | Verificado parcialmente | Treino/registro/champion/challenger/rollback; **MLflow pendente** |
| Testes locais | Aprovados | 49 Python + 13 frontend; `reports/checks.json` |
| CI GitHub Actions | Preparada; execução remota pendente | Nenhum repositório publicado ou workflow remoto disparado |
| Execução local | Verificada via HTTP real | 9 rotas HTTP 200 (incluindo API/UI/OpenAPI); sem autenticação recebe 401 (`reports/release.json`) |
| Demo sem chave | Verificada na API | Modo offline não usa LLM local |
| README/arquitetura | Entregues | README, C4/ER simplificado, ADRs |
| Capturas reais/GIF/vídeo 90s | **Pendentes** | Chromium inicia, mas navegação recebe `ERR_BLOCKED_BY_ADMINISTRATOR`; não existem capturas aprovadas |
| Estudo experimental | Executado | 400 cenários, pares, bootstrap e sensibilidade |
| Artigo | Entregue | `docs/article/turnolab.md` |
| Model Card | Entregue | Pacote local + inferência executada; sem publicação HF |
| Docker/Compose | Preparados; execução pendente | CLI `docker` indisponível neste runtime; build/container não executados |
| n8n | Opcional, exportado; não executado | Workflow inativo e instruções de credenciais |
| Limitações | Entregues | `limitations-and-roadmap.md`, relatórios e alertas na UI |

## Adaptações de stack

O ambiente continha FastAPI, Pydantic, pandas, NumPy, scikit-learn, Matplotlib,
httpx e Playwright, mas não SQLAlchemy/Alembic/MLflow/pytest/React/Vite. Downloads
solicitados não foram autorizados/concluídos. Foram usados sqlite3, migrations SQL,
unittest e interface JS/CSS nativa. Testes não dependem de pytest. Contratos `.d.ts`
não equivalem a uma aplicação TypeScript compilada.

## Bloqueios observados

- `pip`: instalação opcional MLflow indisponível; tentativa encontrou falha DNS para o índice de pacotes.
- Uvicorn: HTTP real em loopback **aprovado**, inclusive frontend e endpoints protegidos.
- Chromium: processo inicializou, mas a política do navegador recusou navegação, até em localhost.
- Docker: a CLI não está instalada; não foi possível tentar o build.
- GitHub Actions: não existe repositório TurnoLab autorizado ao conector no momento desta auditoria.

São limites observados deste ambiente, não diagnóstico de falha na máquina do
usuário. Os scripts e os logs permitem repetir os testes em host autorizado.
Não foram fabricados screenshots, GIF, cobertura de testes, execução de CI ou
resultados de uma LLM externa para preencher essas lacunas.

`reports/reproduction.json` pertence à avaliação da versão recebida. A tentativa de
**reexecutar todo o treinamento nesta auditoria excedeu o tempo disponível**; por
isso não é usada como prova de nova execução integral. Nesta auditoria foi verificada
a reprodução independente dos dados e a identidade SHA-256 dos principais artefatos
e relatórios da versão original. Isso não comprova novo treinamento integral.

## Verificação final desta retomada

Foram acrescentados nove testes de contrato dos provedores externos e quatro testes de validação da evidência de CI. A suíte
agora tem 49 testes Python e 13 de frontend. O verificador de liberação foi executado novamente, registrando **bootstrap,
testes e HTTP/TCP aprovados** e **browser, MLflow, Docker e CI remota bloqueados** em
`reports/release.json`. O estado permanece incompleto; não há capturas reais
novas nem publicação externa nesta sessão.
