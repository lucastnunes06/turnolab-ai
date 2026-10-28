# Um copiloto de IA deveria decidir por um restaurante? O que aprendi construindo o TurnoLab

*Relato técnico dos artefatos e experimentos executados neste workspace, com
assistência substancial de IA. O título é uma proposta editorial; antes de
publicar em primeira pessoa, o candidato deve reproduzir e compreender o projeto.
Não se atribuem a ele experiências profissionais ou implementação individual.*

Um restaurante espera um pico de pedidos. Adicionar uma pessoa parece uma decisão
plausível. Mas pode ser inútil se o gargalo estiver no forno, ou piorar o custo
se faltarem ingredientes. Esse pequeno exemplo definiu a pergunta do TurnoLab:
como transformar uma previsão em uma decisão que possa ser examinada?

A resposta construída não começa pelo chat. Começa pelo dado observado, passa por
uma previsão com incerteza, compara cenários e só então produz uma proposta. A
explicação de IA fica no fim dessa cadeia. Aprovar continua sendo uma decisão humana.

## Dados que dificultam, sem fingir que são reais

Foram gerados 20 restaurantes fictícios, 90 dias e 86.400 intervalos de meia hora.
O gerador inclui almoço, jantar, fins de semana e promoções anunciadas, mas também
ruído Gamma-Poisson, choques diários, eventos raros, falta de equipe e uma mudança
de comportamento. Não há pedidos de pessoas ou dados internos de uma empresa.

O cuidado principal foi não confundir reprodutibilidade com facilidade artificial.
Se a demanda fosse uma função limpa da hora, bastaria aprender a fórmula do
gerador. Os eventos latentes criam erros inevitáveis. Ainda assim, o experimento
continua limitado pelo mundo que o próprio projeto inventou.

O estoque tem outra simplificação: snapshots são estados experimentais gerados em
cada origem, não a trajetória contínua de um restaurante. Isso permite aprender
um classificador de risco, mas não provar uma política real de reposição.

## Um baseline antes da ferramenta favorita

Último intervalo, média móvel, sazonal e Ridge foram comparados a Random Forest e
Gradient Boosting. Os horizontes de 30 e 60 minutos usam a mesma família de features,
com modelos separados. A previsão de 60 minutos é a contagem da segunda meia hora;
a UI soma as duas previsões quando quer mostrar pedidos no próximo período de uma hora.

O corte é cronológico: treino, validação, calibração e teste. Uma linha sai do treino
se seu alvo atravessa a fronteira. Os lags usam apenas observações disponíveis na
origem. Uma promoção futura só entra porque o calendário registra que foi anunciada
um dia antes. Um teste altera todos os pedidos futuros e exige que as features da
origem permaneçam iguais.

Gradient Boosting de 31 folhas teve o menor MAE de validação nos dois horizontes.
No teste, o MAE foi 2,886 pedidos em +30 e 2,925 em +60. Random Forest ficou muito
próximo em +30, com 2,911. O resultado não justifica dizer que boosting é sempre
superior: a diferença é pequena e pertence a esse gerador e a esse período.

## O número agregado que parecia confortável

O resultado mais instrutivo foi a incerteza. Os intervalos conformais nominais de
90% tiveram cobertura agregada de 90,08% em +30. Parecia adequado. Durante o
funcionamento, porém, a cobertura caiu para 82,38%.

A causa está no protocolo: o grupo fora do pico mistura operação e horários
fechados. Prever zero quando o restaurante fecha é fácil e aumenta a cobertura
agregada, enquanto a calibração fica estreita para parte da operação. A UI mostra
as duas coberturas e um alerta. Depois de olhar o teste, mudar o agrupamento e
reavaliar no mesmo conjunto seria usar o teste para desenvolver o método.

O próximo experimento precisa de um novo período. Essa decisão deixa um modelo
imperfeito na demonstração, mas preserva uma conclusão honesta.

## Estoque: prever risco sem olhar o consumo futuro

O segundo problema estima se um ingrediente cairá abaixo da reserva antes da
reposição. A regra determinística compara consumo previsto e disponibilidade. O
classificador recebe estoque, entrega prevista, lead, receita e demanda estimada.

Há uma armadilha temporal: usar previsões de um modelo treinado no futuro para
ensinar o classificador. Para evitá-la, um previsor auxiliar foi congelado nos
primeiros 30 dias. O classificador só usa origens posteriores; calibração e
limiar também têm períodos separados.

No teste sintético, a regra teve recall 73,63%; o classificador, 92,95%, com
precision 76,24% e F1 0,838. Os custos de falso negativo e positivo são hipóteses
(R$ 60 e R$ 12), usadas para escolher limiar em período anterior ao teste. Eles
não são prejuízos medidos em restaurantes.

## Simulação é matemática, explicação é outra tarefa

O simulador é uma fila fluida. Em cada passo, chegam pedidos, capacidade limita
preparo, estoque limita conclusão e o restante vira backlog. Capacidade é o mínimo
entre cozinha e pessoas multiplicadas por produtividade. Entrega só entra depois
do prazo, nunca antes. Os testes verificam conservação, limites e casos em que
mais equipe não reduz fila.

Esse motor não usa LLM. Ele mantém inputs, resultados, versão e ID, permitindo
reconstruir a comparação. A hipótese de promoção usa um coeficiente explícito;
nenhuma tela trata esse coeficiente como causalidade observada.

## RAG que precisou aprender a ficar em silêncio

Cinco políticas fictícias formam o corpus local. Chunks por parágrafo recebem ID,
documento e referência abrível. Foram comparados TF-IDF lexical, projeção LSA e
mistura lexical com caracteres. Não houve download de um encoder pré-treinado.

Na primeira avaliação, perguntas sem suporte ainda recebiam referências por
palavras comuns. A remoção de palavras funcionais e uma exigência de suporte
lexical corrigiram essas quatro negativas. O relatório inicial foi preservado.

O lexical encontrou o documento ouro em 18 de 19 perguntas respondíveis e teve
precisão documental de 77,8%. Como o conjunto ajudou a corrigir a implementação,
é avaliação de desenvolvimento, não evidência imparcial de generalização. Abrir
uma fonte e verificar um trecho literal é útil, mas não equivale a provar que
toda explicação gerada estaria semanticamente correta.

## Por que não três agentes autônomos?

Analysis, Knowledge e Coordinator existem como papéis determinísticos. O broker
valida sete ferramentas e revalida escopo de restaurante em cada chamada. Não há
SQL livre, shell, rede arbitrária ou ferramenta de aprovação. Os dois modos de
orquestração produziram os mesmos fatos. A pequena diferença de latência não
sustenta uma vantagem de múltiplos agentes; a UI usa o caminho simples.

O provedor externo opcional recebe evidências já selecionadas. Precisa devolver
JSON válido, usar referências permitidas e não introduzir números na prosa.
Timeout ou schema inválido causam fallback. Sem credenciais, só o caminho offline
foi exercitado. Ele é chamado de template, não de LLM local.

## O experimento que separa contribuição de aparência

Em 400 origens de teste, regras fixas tiveram custo médio hipotético de R$ 367,37.
Uma regra com previsão chegou a R$ 329,67. Enumerar ações com previsão e simulador
chegou a R$ 302,34. O backlog médio passou de 13,98 para 11,75.

Adicionar RAG ou copiloto não alterou esses números: o desenho exige as mesmas
ações para isolar suporte documental. Isso impede atribuir ao texto um ganho
produzido pelo cálculo. O experimento também encontrou uma falha: o solver,
sem impor a política fictícia de duas pessoas extras, escolheu três em 2,25% dos
cenários. Recuperar uma política não significa aplicá-la como constraint.

Os intervalos bootstrap são pareados por cenário e não corrigem toda correlação
entre restaurantes e horários. O oracle compartilha o simulador, os custos são
escolhidos pelo projeto e não houve pessoas avaliando justificativas. O resultado
mostra uma possibilidade dentro desse laboratório, não efeito no mundo real.

## O que a entrega comprova — e o que falta

O repositório tem API, modelos treinados, simulador, RAG, propostas e auditoria.
Os checks locais incluem 49 testes Python e 13 de frontend, build estático e
guardrails. O teste de carga usa ASGI em memória, excluindo rede. O pacote de modelo
local executa uma inferência de exemplo.

A stack foi reduzida para o que o ambiente permitiu: SQLite e JS/CSS nativos. O
adaptador MLflow, Docker, CI remota e navegador precisam de verificações próprias;
não são apresentados como executados. Não houve publicação externa. Essas
limitações são parte do estado real, não uma lista disfarçada de funcionalidades.

Um copiloto deveria decidir sozinho? Este experimento não dá suporte a isso.
Ele mostra utilidade em organizar uma pergunta, trazer dados e facilitar a revisão
de hipóteses. A contribuição mais defensável é deixar a recomendação examinável,
inclusive quando o melhor próximo passo é recusar a sugestão ou admitir que faltam dados.
