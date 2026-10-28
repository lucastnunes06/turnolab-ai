# Execução local

Requisitos: Python 3.12 (verificado; dependências pedem >=3.11), Node 24 para checks
do frontend e cerca de 100 MB livres além das bibliotecas. Não precisa de GPU,
credenciais de LLM, PostgreSQL ou n8n.

```bash
cd turnolab-ai
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python scripts/bootstrap.py
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Abra **http://127.0.0.1:8000**. OpenAPI: **http://127.0.0.1:8000/docs**. Health não
exige token; endpoints `/api` usam Bearer. A UI inicia com `turnolab-demo` (20
restaurantes), e Configurações permite `turnolab-other` (somente restaurante 2).
Tokens são de demonstração. Não há uma tela de cadastro ou login real.

O relógio padrão é replay de 29/08/2026 18:00 UTC. Não é a data atual. `DEMO_AS_OF`
pode mudar para uma meia hora dentro do dataset com histórico suficiente e duas
previsões suportadas. A UI exibe a data fixa do roteiro; personalizar o relógio
exige atualizar os rótulos de UI antes de apresentar outro dia.

O bootstrap é idempotente para dados e modelos existentes; não apaga ações. Os
relatórios de avaliação são recalculados. `--retrain` substitui artefatos locais e
retorna ao champion de referência; faça backup do registro antes de experimentos.
Reinicie a API após treinar para invalidar caches de modelos/relatórios.

```bash
python scripts/check.py
python scripts/reproduce_data.py
python scripts/load_check.py
python -m ml.registry list
python -m ml.registry promote demand-rf-v1   # recusa: pior MAE de validação
python -m ml.registry rollback demand-v1
```

Com o pacote Playwright instalado e Chromium disponível:

```bash
python scripts/browser_check.py
```

Por padrão usa `/usr/bin/chromium`; defina `CHROMIUM_EXECUTABLE=''` para o browser
instalado pelo Playwright. O script intercepta transporte HTTP e encaminha para
**a API real e o SQLite** usando ASGI em memória. Nenhuma resposta de API é
fabricada. Esse teste não mede rede/TCP. Em um host normal, o servidor Uvicorn pode
ser exercitado manualmente ou por um teste HTTP adicional.

`.env.example` é uma referência, não é lido automaticamente. Exporte as variáveis
no shell ou use `uvicorn --env-file .env` após instalar python-dotenv. Nunca publique
chaves. `LLM_PROVIDER=offline` é default; groq/gemini usam `LLM_API_KEY` e opcional
`LLM_MODEL`. Adaptação externa implementada, sem chamada real verificada.

## Ambiente desta entrega

A execução numérica, API em ASGI, testes e build estático foram exercitados. Esta auditoria executou Uvicorn em TCP/HTTP real com sucesso. Chromium conseguiu
iniciar, mas a política deste ambiente bloqueou a navegação (`ERR_BLOCKED_BY_ADMINISTRATOR`).
Docker, MLflow e CI remota permanecem sem execução comprovada neste ambiente.
Consulte `reports/release.json` para a separação entre aprovado e bloqueado. Consulte `acceptance.md`.
