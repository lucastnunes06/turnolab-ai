# Evidências verificadas no GitHub Actions — 28/10/2026

O TurnoLab foi publicado em [lucastnunes06/turnolab-ai](https://github.com/lucastnunes06/turnolab-ai).
Esta página distingue verificações executadas de recursos que continuam pendentes.

## Testes, análise estática e navegador

Na [execução aprovada do workflow principal](https://github.com/lucastnunes06/turnolab-ai/actions/runs/40726044887), em Linux (GitHub Actions):

- O bootstrap regenerou os modelos e os dados sem depender de binários versionados.
- O verificador executou **49 testes Python e 13 testes Node/frontend**, além do build estático.
- Foram aprovados o lint, Bandit e pip-audit com as dependências fixadas.
- O Playwright abriu Chromium e navegou pelas telas com o backend FastAPI e SQLite reais.
- O teste percorreu cenário, proposta, aprovação, copiloto, citações, estoque e observatório.
- A largura de **390 px** passou após correção do overflow horizontal. O primeiro run reprovou essa verificação, e a falha foi corrigida antes da aprovação.
- O workflow armazenou as evidências de navegação como artefato; as capturas desktop do dashboard, cenários e copiloto estão no repositório.

O transporte navegador ↔ API foi interceptado e encaminhado para **ASGITransport**. Isso exercita a aplicação real, mas **não** é um teste de latência de rede entre navegador e serviço.

## Docker Compose e rastreamento com MLflow

Na [execução de verificação estendida](https://github.com/lucastnunes06/turnolab-ai/actions/runs/40726836196):

- **Docker:** imagem construída, serviço iniciado com bootstrap, endpoints `/ready` e `/health` acessados via HTTP no host.
- **MLflow 3.5.1:** SDK executado; métricas de avaliação previamente calculadas e artefatos de modelos treinados foram registrados num tracking store local e consultados por `MlflowClient`.
- O artefato `mlflow-evidence` do workflow contém `reports/mlflow.json` com `live_tracking_executed: true`, versão `3.5.1` e seis caminhos de artefatos.

A primeira tentativa estendida falhou por incompatibilidade de versões com SQLAlchemy 2.1.
A configuração foi corrigida restringindo a versão do SQLAlchemy a `>=2.0.40,<2.1`.
O sucesso posterior não apaga a falha inicial do histórico.

## Estado dos artefatos publicados

Os arquivos `.joblib`, logs locais e CSVs muito extensos de previsões por evento
não foram colocados no repositório. O bootstrap cria esses arquivos novamente.
Dados brutos reais, identificadores pessoais e segredos não integram esta demonstração.

## Limites que permanecem

- GIF de aproximadamente **91 segundos**: **produzido e publicado** em `docs/media/demo.gif` a partir da execução real com Chromium/ASGI. [Workflow](https://github.com/lucastnunes06/turnolab-ai/actions/runs/40727621782) e `reports/demo.json`. Um vídeo MP4 editado separado não foi produzido.
- Provedores externos de LLM: implementados como adaptadores, sem validação com credenciais externas.
- Hugging Face: Model Card e exportador preparados, sem publicação externa efetivada.
- n8n: workflow exportado, sem execução integrada verificada.
- Dados e custos: sintéticos, não uma medida de impacto no mundo real.
- Deploy público, autenticação de produção, carga em produção e segurança completa: não comprovados.

As execuções remotas evidenciam o comportamento sob os cenários testados, não uma
garantia de aptidão clínica, comercial ou operacional.
