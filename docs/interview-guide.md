# Roteiro de entrevista: estudar, reproduzir e só então assumir autoria

As respostas abaixo descrevem o artefato. Não são experiências pessoais prontas
para decorar. O candidato deve reproduzir os comandos, revisar o código e explicar
mudanças próprias antes de usar frases como “implementei” ou “aprendi”. O código
foi desenvolvido com assistência de IA neste workspace.

**Por que esse problema?** A demanda só vira uma decisão útil quando comparada a
capacidade, estoque, custo e incerteza. A demonstração permite seguir essa cadeia.
Exercício: mostrar um cenário em que mais equipe não aumenta a produção.

**Por que ML em vez de regras?** O projeto não assume que ML vence. Último intervalo,
médias, sazonal e Ridge competem no mesmo teste; Gradient Boosting reduziu o erro
neste gerador. Isso não prova que um restaurante real precisaria do mesmo modelo.

**Como evitou vazamento?** Origens e alvos explícitos, lags causais, calendário de
promoção conhecido previamente, scaler só no treino e purge por alvo. O estoque usa
um previsor congelado antes das origens de treino do classificador. Exercício:
rodar o teste que altera pedidos futuros e explicar por que as features não mudam.

**Qual baseline foi mais difícil de superar?** Entre os baselines simples, Ridge
teve menor MAE de validação que último intervalo, média e sazonal. Random Forest
foi um challenger muito próximo. Consultar o CSV, incluindo erros por segmento,
antes de responder em números.

**Como escolheu o modelo final?** Menor MAE em validação, com os mesmos períodos e
features. A escolha de 31 folhas foi feita antes de medir teste. Calibração tem
período próprio. Não trocar champion após olhar qual ficou melhor no teste.

**Como avaliou o RAG?** Um conjunto pequeno com documento ouro por pergunta,
Hit/Recall@3, precisão de referências, negativas e latência. Os resultados são de
desenvolvimento: foram usados para corrigir abstenção. Não houve avaliação humana
cega nem medida de entailment de uma LLM externa.

**Por que usar agentes?** Os papéis organizam a implementação; a ablação não
mostrou vantagem de três agentes autônomos, que nem foram implementados. A UI usa
tool calling determinístico simples. Mais autonomia só se justificaria com ganho
medido e controles equivalentes.

**O que acontece quando a LLM falha?** Timeout, tentativas limitadas e validação
levam a um template offline com ferramentas e documentos. O rótulo informa o modo.
O teste simula chave ausente. Chamada externa com chave ainda precisa ser validada.

**Como sabe que a recomendação é confiável?** Não se promete confiança absoluta.
A pessoa pode abrir previsão, versão, limites, inputs da simulação e política.
Aprovação é humana. Cobertura em funcionamento está abaixo do nominal, e hipóteses
podem falhar. Demonstrar um erro é parte da resposta.

**Qual foi o maior problema técnico encontrado?** Dois achados documentados: zeros
em horários fechados mascararam cobertura inferior durante operação, e palavras
funcionais geraram falsas referências em perguntas sem suporte. O candidato só deve
chamar isso de experiência pessoal depois de reproduzir e investigar esses casos.

**O que faria diferente?** Novo holdout para calibração segmentada, labels de estoque
com dinâmica contínua, avaliação cega de justificativas e grupos de bootstrap por
restaurante. A escolha entre melhorar modelo ou dados deve vir de erros observados.

**O que mudaria com dados reais?** Contratos de disponibilidade em cada timestamp,
licença e base legal, retenção, privacidade, eventos atrasados, revisões de estoque,
sazonalidade longa, observação de intervenções e validação fora de restaurante.
Custos e produtividade precisariam ser medidos. Nenhuma métrica sintética serve
como garantia operacional.

**Qual parte compreende pessoalmente?** Preencher após revisão: quais funções leu,
quais testes executou, qual bug diagnosticou, que mudança fez sem copiar e como a
validou. Uma boa prova é adicionar um terceiro horizonte sem vazamento e justificar
um novo corte temporal. Não atribuir ao candidato todo o código gerado por IA.

Checklist de estudo: executar bootstrap; explicar um lag; recalcular uma métrica
à mão; seguir uma proposta na auditoria; encontrar a pior cobertura por restaurante;
reproduzir uma negativa de RAG; alterar um custo e prever o efeito antes de clicar.
