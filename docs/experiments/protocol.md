# Experimento de decisões e ablações

Pergunta: previsão, simulação e conhecimento melhoram decisões frente a regras
fixas em cenários fictícios? O protocolo está em `ml/experiments.py`; seed
20261028, diferente da geração de dados. As regras foram escritas sem consultar
os resultados amostrados do teste operacional.

Amostram-se 400 origens de teste (dias >=72, 16h–21h). Para cada origem, previsão
dos dois intervalos é informação de decisão; pedidos observados são usados só na
avaliação. Capacidade, equipe, estoque, backlog inicial, lead e custos são sorteados
com seed fixa e ficam disponíveis ao decisor. Não são operações reais.

1. Regras fixas: reforço de uma pessoa após 18h.
2. Regra + previsão: limiar de demanda por produtividade, até duas pessoas extras;
   reposição de 60 pedidos equivalentes quando faltará estoque e lead é um passo.
3. Previsão + simulador: enumera 0–2 pessoas extras e reposição 0/60; minimiza custo
   previsto de fila, estoque, mão de obra e custo de mobilização/compra.
4. + RAG: **mesma decisão numérica**; agrega referência recuperada da política.
5. + copiloto: **mesma decisão numérica**; representa a camada de explicação offline.

Um assert garante que RAG não muda os custos da estratégia com simulador. A
presença de referência é medida separadamente. Esse desenho isola contribuição
documental, mas não mede se um humano entende ou decide melhor. Não houve avaliação
com usuários nem LLM externa. A latência de solver é compartilhada nos registros;
não deve ser usada como latência total das cinco arquiteturas. A comparação de
orquestração é medida separadamente em `reports/agents.json`.

O custo inclui R$ 8 hipotéticos de mobilização por pessoa extra e custo de compra
simulado. A função de custo do app não inclui essas taxas extras; elas são extensão
**apenas do experimento**. Ambas as fórmulas estão em código e esta distinção evita
comparar diretamente custos de telas com médias experimentais.

Regret compara custo realizado com um oracle que conhece os dois alvos futuros e
usa o mesmo espaço de ações. É um limite dentro do simulador, não um ótimo real.
São reportados backlog, custo, regret, conformidade com limite de duas pessoas e
referência documental. A regra fictícia de até duas pessoas extras agora é aplicada no espaço de ações, tanto pelo otimizador quanto pelo oracle. A execução corrigida (v2) apresenta 100% de conformidade nos 2.000 registros; a execução v1 permanece no histórico.

Intervalos bootstrap pareados de 95% usam 1.000 reamostragens de cenários para o
custo contra regras fixas. Eles ignoram correlação entre restaurantes/horários.
Seu alcance é descritivo nesta simulação, não inferência de impacto real.

Ameaças: gerador e simulador compartilham pressupostos; produtividade fixa e fila
fluida; função de custo escolhida pelo projeto; demanda correlacionada; pouca
variabilidade de receitas; amostra de conhecimento pequena; ausência de humano
na avaliação de explicação. Sensibilidade interativa usa demanda 0,8/1,0/1,2; o
relatório adicional varia penalidade de fila (0,5/1/2) e demanda (0,8/1/1,2), mantendo ações congeladas. Produtividade continua fixa; variar esse parâmetro é trabalho futuro.
