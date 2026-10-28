# Matriz para a candidatura

Fonte oficial consultada em 28/10/2026: [Programa de Estágio — GenAI](https://job-boards.greenhouse.io/ifoodcarreiras/jobs/8901054002).
A vaga descreve software integrado a IA e construção/operacionalização de modelos
com ênfase em LLMs. A lista abaixo traduz isso em evidências do projeto; métodos
específicos não são atribuídos como requisitos oficiais. O projeto não comprova
experiência individual do candidato sem reprodução, revisão e compreensão.

## Núcleo de AI Engineering

| Competência | Evidência no projeto | Arquivo ou demonstração | Como explicar na entrevista |
|---|---|---|---|
| Software integrado a IA | API com inferência e interface consumindo endpoints | `backend/app/main.py`, `frontend/app.js` | Seguir uma requisição de previsão até features, modelo e resposta |
| ML prático | Dois problemas treinados em CPU | `ml/train.py`, `ml/stock.py` | Justificar baselines, features e escolha do modelo |
| Integração de LLMs | Adaptadores opcionais + fallback offline | `ai/providers.py` | Distinguir implementação de adaptador de chamada externa realmente validada |
| Treinamento e avaliação | Comparação temporal com sete candidatos | `reports/demand.json`, `demand_comparison.csv` | Explicar por que a seleção usa validação e não o teste |
| Operacionalização de pipelines | Bootstrap dados → treino → avaliação → registro | `scripts/bootstrap.py`, `ml/tracking.py` | Executar do zero e localizar os artefatos; MLflow ainda depende de instalação |
| Integração entre modelo, API e app | Oito telas e contratos reais | `frontend/contracts.d.ts`, endpoints OpenAPI | Mostrar que alterar restaurante troca dados e permissões |
| Experimentação e pesquisa | 400 cenários, ablação e intervalos bootstrap | `ml/experiments.py`, `docs/experiments/` | Distinguir contribuição numérica de suporte documental |
| Experimento até aplicação utilizável | Previsão → simulação → proposta → revisão | Scenario Lab e Action Center | Reconstruir entradas, versão, resultado e decisão pelo ID |
| Uso consciente de IA | Números fora da LLM, evidências e abstenção | `ai/coordinator.py`, testes adversariais | Demonstrar uma pergunta sem suporte e uma tentativa de ação indevida |
| Portfólio verificável | Código local, relatórios, artigo e Model Card | `README.md`, `docs/article/`, `artifacts/huggingface/` | Não alegar publicação em GitHub/HF antes de publicar com autorização |

## Diferenciais adicionais e trilha AI Builder

| Competência | Evidência no projeto | Arquivo ou demonstração | Como explicar na entrevista |
|---|---|---|---|
| Prompt engineering | Prompt versionado e saída restrita | `ai/prompts/coordinator-v1.txt` | Explicar o que o schema valida e o que não prova |
| RAG (decisão técnica adicional) | TF-IDF, LSA/híbrido, citações abríveis | `ai/rag.py`, `reports/rag.json` | Explicar a falha inicial de abstenção e o viés do conjunto de desenvolvimento |
| Agentes/orquestração | Ferramentas tipadas e ablação simple/roles | `ai/tools.py`, `reports/agents.json` | Admitir que papéis não trouxeram vantagem demonstrada |
| Automação | Workflow n8n opcional exportável | `automations/n8n/` | Integração preparada; execução do workflow ainda não verificada |
| API e dashboard | FastAPI e interface com dados do backend | `/docs`, `frontend/` | Justificar um monólito e mostrar estados de erro |
| Observabilidade e segurança (adicionais) | Latência, PSI, escopo por tenant e auditoria | endpoint monitoring, `backend/tests/` | Explicar os limites de uma demonstração local |

GitHub, modelos publicados em Hugging Face, pesquisa e artigos aparecem como
exemplos de portfólio na descrição da trilha. Este repositório local prepara
artefatos, mas não comprova publicação, Kaggle, usuários, economia de horas reais
ou operação em produção. Elegibilidade acadêmica e disponibilidade são informações
do candidato, não inferíveis do código.
