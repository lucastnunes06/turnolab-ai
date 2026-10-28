# Arquitetura: um monólito com fronteiras explícitas

O usuário seleciona um restaurante e recebe um snapshot de replay. O frontend
consulta FastAPI; a API aplica autorização e chama módulos numéricos e de
conhecimento. SQLite guarda dados e decisões. Artefatos locais contêm modelos
congelados. Nenhuma LLM gera a previsão, resolve a fila ou aprova a proposta.

```mermaid
flowchart LR
  U[Operador humano] --> UI[Interface web]
  UI --> API[FastAPI: autenticação e escopo]
  API --> DB[(SQLite: dados e auditoria)]
  API --> ML[Previsão + risco calibrado]
  ML --> A[Artefatos com checksum]
  API --> SIM[Simulador fluido determinístico]
  API --> C[Coordinator: ferramentas tipadas]
  C --> AN[Analysis: consultas e simulação]
  C --> K[Knowledge: TF-IDF]
  K --> D[Políticas fictícias versionadas]
  C -. opcional .-> L[Adaptador Groq/Gemini]
  C --> P[Proposta pendente]
  P --> U
  U --> R[Aprovar/rejeitar na API]
  R --> DB
```

## Limites e contratos

- `ml/data.py`: gerador, validação e ingestão. Fatos sintéticos, sem dados pessoais.
- `ml/features.py`: origem e alvo separados. Toda observação tem tempo <= origem.
- `ml/train.py` e `ml/stock.py`: escolha por validação, calibração posterior e teste.
- `simulator/engine.py`: regras de conservação; Pydantic rejeita entradas inválidas.
- `ai/tools.py`: allowlist e autorização a cada chamada. Não há SQL, shell ou HTTP
  livre. O modo externo não escolhe ferramentas: explica evidências selecionadas.
- `backend/app/services.py`: transações de simulação, proposta e decisão humana.
- `frontend/`: aplicação sem dependências de runtime, com SVG e JavaScript nativo.

Os papéis Analysis/Knowledge/Coordinator são funções dentro do mesmo processo.
Não se afirma haver três agentes autônomos. A comparação com tool calling simples
é uma ablação nula: mesmos fatos, orquestração equivalente.

## Modelo relacional

```mermaid
erDiagram
  restaurants ||--o{ order_events : observa
  restaurants ||--o{ inventory_snapshots : possui
  ingredients ||--o{ inventory_snapshots : identifica
  products ||--o{ recipes : usa
  ingredients ||--o{ recipes : compoe
  restaurants ||--o{ promotion_calendar : agenda
  restaurants ||--o{ demand_forecasts : recebe
  model_versions ||--o{ demand_forecasts : produz
  restaurants ||--o{ simulation_runs : simula
  model_versions ||--o{ simulation_runs : fundamenta
  simulation_runs ||--o{ action_proposals : origina
  restaurants ||--o{ agent_conversations : consulta
  restaurants ||--o{ audit_logs : audita
  restaurants ||--o{ inference_aggregates : monitora
  restaurants ||--o{ operational_alerts : registra
```

`experiment_runs` é o ledger técnico independente de tenants. `schema_versions`
registra migrations. IDs, quantidades não negativas, status de proposta e
unicidade de snapshots/origens têm constraints. A auditoria impede UPDATE/DELETE
por triggers. Isso não é um log criptograficamente inviolável: quem controla o
arquivo SQLite pode alterar o banco fora da aplicação.

Migrations são SQL confiável do repositório, executadas em transação por versão.
O SQL de consultas usa parâmetros. Os nomes de tabelas na ingestão vêm de uma
allowlist de código, nunca de texto do usuário ou de uma LLM.

## Operação local

Um processo atende a demonstração. A API usa rotas assíncronas, mas inferência e
SQLite são síncronos no event loop; não há promessa de throughput de produção.
O teste de carga ASGI mede essa configuração e exclui custo de rede. Evoluir para
workers e fila de inferência exige medir concorrência e limites do banco.

Não há implantação em produção, autenticação corporativa, mensageria distribuída,
estoque transacional real ou execução de ações em sistemas de restaurantes.
