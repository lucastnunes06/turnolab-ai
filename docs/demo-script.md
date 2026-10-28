# Demonstração de 90 segundos

Estado: roteiro e script Playwright implementados. Sem captura real aprovada,
não há vídeo/GIF a apresentar como demonstração gravada. Os passos abaixo são
executáveis na aplicação local depois de `bootstrap.py` e Uvicorn.

| Tempo | Ação na interface | O que explicar |
|---|---|---|
| 0–8s | Abrir Visão geral, selecionar Casa do Grão | Dados sintéticos, replay em 29/08/2026; sem afiliação com iFood |
| 8–17s | Abrir Demand Intelligence | Dois horizontes, faixa conformal e cobertura aberta abaixo do nominal |
| 17–25s | Abrir Inventory Intelligence | Risco é classificador calibrado, consumo vem de receitas |
| 25–43s | Scenario Lab: mais uma pessoa, capacidade 100, estoque fator 2 | Comparação matemática; equipe sozinha pode não vencer falta de ingredientes |
| 43–51s | Comparar cenários e abrir sensibilidade | Inputs, custo hipotético, backlog e ID persistidos |
| 51–66s | AI Copilot: perguntar por que reforçar equipe | Ferramentas validadas, fatos separados de interpretação, sem LLM local |
| 66–73s | Abrir uma referência documental | Política fictícia e checksum, citação rastreável |
| 73–83s | Criar proposta no simulador e aprovar/rejeitar no Action Center | Agente não aprova; status e ator entram na auditoria; sem operação real |
| 83–90s | Model Observatory | Baselines, erro, incerteza e PSI; números medidos, limites explícitos |

Captura: `scripts/browser_check.py` percorre o fluxo com Playwright e escreve
screenshots apenas depois de renderizar a interface real com a API real. Usa ponte
ASGI para funcionar sem servidor TCP. Se Chromium não iniciar, conserva o log da
falha e não produz imagens de uma interface inventada.

Uma gravação final pode usar o mesmo fluxo em host com browser e codificador
liberados. Não substituir telas faltantes por montagem, animação ou mock de dados.

Gravação automatizada de 90s: `python scripts/capture_demo.py`. Requer Pillow e
Chromium permitido. Cada frame é uma captura real; o script só escreve o GIF depois
de percorrer consultas, simulação, citação, proposta, rejeição e avaliação de modelo.
Não executado no sandbox que bloqueou o Chromium.
