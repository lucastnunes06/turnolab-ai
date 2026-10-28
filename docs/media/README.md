# Capturas da interface

Nenhuma screenshot, GIF ou vídeo foi aprovado neste ambiente: Chromium iniciou,
mas a navegação foi bloqueada por `ERR_BLOCKED_BY_ADMINISTRATOR`. Os gráficos em `reports/`
são resultados experimentais e não são apresentados como screenshots.

Em ambiente com Chromium permitido, execute:

```bash
python scripts/browser_check.py
python scripts/capture_demo.py
```

O primeiro script grava dashboard, demanda, simulação, ações, copiloto, citações,
estoque, modelos e tela móvel a partir da API real. O segundo grava aproximadamente
90 segundos de uso em `demo.gif`. Confira `reports/browser.json` e `reports/demo.json`
após a execução; não assumir sucesso apenas pela existência de um arquivo de imagem.
