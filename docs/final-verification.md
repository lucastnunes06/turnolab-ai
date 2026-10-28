# Verificação de liberação

Execute, a partir da raiz do projeto:

```bash
python scripts/release_check.py
```

O comando **primeiro executa o bootstrap** caso o pacote ainda não tenha sido inicializado; em seguida, executa os checks locais, serve HTTP real com Uvicorn, percorre a
interface com Playwright, captura a demonstração quando o navegador passa, verifica
o SDK MLflow local e testa uma imagem Docker em um container descartável. O
resultado é `reports/release.json`; código de saída **2** indica requisito bloqueado
ou incompleto. A presença do script não significa que essas etapas passaram.

O verificador não instala pacotes, não publica código, não altera repositórios
remotos e não envia notificações. O teste de Docker remove somente seu próprio
container descartável. Tokens/credenciais do processo não são impressos.

Em uma máquina autorizada, prepare as dependências e o Chromium antes:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pip install mlflow-skinny==3.9.0 sqlalchemy==2.0.46 playwright==1.62.0 pillow==12.3.0
python -m playwright install chromium
CHROMIUM_EXECUTABLE='' python scripts/release_check.py
```

Docker precisa estar disponível. O teste usa o socket local explícito, sem
selecionar um daemon remoto configurado no shell. Em ambiente gerenciado, o
Dockerfile aceita a CA confiável pelo secret `proxy_ca` e preserva TLS.

A CI remota requer um repositório de destino e autorização explícita para publicar
o código. Não foi criado um repositório ou um histórico fictício para preencher
esse requisito. O workflow local passa pelos checks existentes; ele não é
apresentado como execução de GitHub Actions.

## Adaptadores de LLM

`backend/tests/test_provider_contracts.py` verifica Groq e Gemini com
`httpx.MockTransport`: contrato HTTP, sucesso estruturado, schema extra, citações
inválidas, números novos, retries, timeout e destino de requisição. São testes de
integração com um transporte determinístico de teste; **não houve chamada aos
provedores reais nem medição da qualidade de uma LLM externa**. A demonstração
continua útil sem chave, com ferramentas e templates explicitamente rotulados.

## Resultado desta auditoria (28/10/2026)

O bootstrap, os 49 testes Python, os 13 testes frontend, o build e a API servida
via **HTTP/TCP real** passaram. Foram consultadas nove rotas em loopback;
os endpoints protegidos exigiram autenticação. `reports/release.json` registra
status, comandos e tempos.

O Chromium abriu, porém a política bloqueou a navegação (inclusive localhost).
A evidência está em `reports/browser.json`; não houve captura/GIF verdadeira.
MLflow está sem pacote instalado e o `pip` não conseguiu acessar o índice via DNS.
Docker CLI não está instalada. CI remota depende de publicação e permissão de um
repositório específico, que não foi criado/publicado nesta auditoria.

`python scripts/reproduce_data.py` gera novamente os seis CSVs sintéticos e
compara seus hashes ao baseline, sem treinar modelos. A reprodução integral do
treinamento necessita execução separada (com tempo e CPU suficientes).

A existência de um workflow, Dockerfile ou script de browser não substitui
evidência de execução. O projeto continua **parcialmente validado**, sem resultados fabricados.

Para conferir uma execução real de GitHub Actions já autorizada, use
`--github-run-url https://github.com/OWNER/REPO/actions/runs/RUN_ID`. O verificador
exige um commit local real, fontes sem alterações e o mesmo SHA no workflow com
conclusão success. O parâmetro não publica código nem dispara uma execução.
