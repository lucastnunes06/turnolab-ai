# Auditoria técnica independente — TurnoLab AI

**Data da auditoria:** 28/10/2026  
**Fonte:** pacote `turnolab-ai (1).zip` enviado pelo usuário.  
**Estado final:** **parcialmente validado**, com melhoria comprovada em HTTP real e reprodução dos dados. **Não** há evidência de entrega integral, publicação ou deploy.

## O que foi executado

| Critério | Evidência | Resultado |
|---|---|---|
| Bootstrap local | `python scripts/bootstrap.py` | **Aprovado** |
| Testes Python | 49 testes `unittest` | **49/49 aprovados** |
| Testes frontend | 13 testes Node (`utils` e componentes) | **13/13 aprovados** |
| Formatação, compilação, build, guardrails | `scripts/check.py` | **Aprovados** |
| API HTTP/TCP real | Uvicorn em localhost; `/health`, `/ready`, API, docs e `/` | **Aprovada**: 9 rotas HTTP 200; recurso protegido retorna 401 sem token |
| Carga ASGI | 80 requisições, concorrência cooperativa 4 | **Aprovada** no escopo ASGI: zero erros; não é benchmark de rede |
| Dados independentes | `python scripts/reproduce_data.py` | **Aprovados**: 6 CSVs, schemas e SHA-256 iguais |
| Modelos pré-treinados do ZIP | Comparação SHA-256 dos artefatos originais e desta cópia | **Íntegros**; não houve alteração dos modelos |
| Re-treinamento integral limpo | `scripts/reproduce.py` | **Não reconfirmado**: execução excedeu limite de tempo; o resultado histórico do ZIP foi preservado |
| Browser Playwright | Chromium iniciou, mas política bloqueou `Page.goto` | **Bloqueado**: `ERR_BLOCKED_BY_ADMINISTRATOR` |
| Captura / GIF | Depende de browser navegado com êxito | **Não gerados**; nenhuma imagem simulada foi adicionada |
| MLflow real | `scripts/mlflow_check.py` | **Bloqueado**: pacote ausente e índice pip inacessível por DNS |
| Docker | CLI / daemon | **Bloqueado**: CLI não instalada |
| GitHub Actions remoto | Repositório de destino | **Não realizado**: TurnoLab não está entre os repositórios autorizados |
| LLM externo | Groq/Gemini | **Não avaliado ao vivo**; contratos são testes com mocks |

## Correções feitas nesta revisão

1. **Bootstrap antes da verificação completa:** `scripts/release_check.py` prepara banco, dados e artefatos necessários antes dos testes. O verificador para com evidência explícita quando o bootstrap falha.
2. **Falha de pré-requisito compreensível:** `scripts/check.py` orienta a executar o bootstrap, em vez de gerar dezenas de falhas por ausência dos CSVs.
3. **Diagnóstico correto de navegador:** `scripts/browser_check.py` grava `reports/browser.json` quando o Chromium é bloqueado pela política do ambiente; o status é `blocked`, não falha funcional presumida.
4. **Reprodução de dados independente:** novo `scripts/reproduce_data.py` refaz os seis CSVs e confere os hashes, sem alegar novo treinamento.
5. **Relatórios e documentação atualizados:** status de HTTP real, navegador, MLflow, Docker e CI remota separados.

## Riscos e ressalvas técnicas

- **Alta — Deploy público:** os tokens embutidos são credenciais de *demo*. A aplicação não deve ser publicada na internet como sistema autenticado real sem identidade, autorização e política de segredos adequadas.
- **Média — Confiabilidade:** a cobertura nominal de 90% dos intervalos cai para aproximadamente 82,4% em horários de funcionamento nos resultados de referência. Uma previsão deve exibir essa incerteza e ser recalibrada com novo conjunto separado.
- **Média — Restrição operacional:** a análise de referência aponta 2,25% de violações da regra de até duas pessoas adicionais. O simulador não deve ser descrito como otimizador de políticas totalmente conforme.
- **Média — Generalização:** todos os resultados são obtidos com dados sintéticos e modelos locais; não demonstram impacto em restaurantes reais, ganho financeiro ou validade externa.
- **Baixa — Avaliação da IA:** há testes de RAG e contratos de provedores, mas não benchmark cego amplo nem avaliação real de Groq/Gemini.
- **Ambiente:** a auditoria usou Python 3.13.5; a CI declarada usa Python 3.12. Um workflow remoto bem-sucedido permanece necessário para confirmar a matriz de dependências da CI.

## Executar e completar fora deste ambiente

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/bootstrap.py
python scripts/check.py
python scripts/reproduce_data.py
python scripts/release_check.py
```

Para completar requisitos ainda bloqueados, utilizar uma máquina com navegador autorizado, Chromium Playwright, Docker/daemon disponíveis e acesso a um índice de pacotes para MLflow. Executar as verificações documentadas em `docs/final-verification.md`, manter os relatórios brutos e só então alterar seus status para `passed`.

**GitHub Actions:** publicar em um repositório TurnoLab explicitamente autorizado, observar um workflow real com conclusão `success` e conferir que o SHA da execução corresponde ao commit do projeto. Não utilizar um run de outro repositório como evidência.

## Evidências internas

- `reports/checks.json` — comandos de testes e saídas.
- `reports/release.json` — última execução completa do verificador de liberação.
- `reports/browser.json` — erro observável do navegador.
- `reports/data_reproduction.json` — regeneração independente de dados.
- `reports/audit-2026-10-28.json` — resumo desta auditoria e hashes.
- `reports/load.json` — carga via ASGI.
- `docs/acceptance.md` — critérios aceitos e pendências.

**Transparência de autoria:** parte substancial do código e desta revisão teve assistência de IA. Para entrevistas de estágio, o candidato deve executar, entender e conseguir modificar as partes que apresentar como evidência técnica individual.
