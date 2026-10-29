# Quando uma previsão vira uma decisão: cinco lições do TurnoLab AI

*Artigo técnico baseado em resultados reproduzíveis de uma simulação de restaurantes. Não há operações ou custos reais.*

Um restaurante está perto do horário de pico. A previsão indica uma fila crescente. Contratar uma pessoa extra parece uma solução lógica — até perceber que o gargalo pode ser a capacidade física da cozinha ou um ingrediente indisponível.

Foi a partir desse tipo de pergunta que surgiu o TurnoLab AI: um laboratório experimental que combina previsão, simulação e explicações com evidências. A parte mais interessante não foi construir um chatbot, mas descobrir **em quais etapas a IA realmente acrescenta valor**.

## 1. Um modelo complexo precisa vencer um baseline

A aplicação trabalha com 20 restaurantes e 90 dias fictícios: 86.400 intervalos, com picos, ruído, promoções programadas e mudanças de comportamento. Primeiro foram construídos baselines — último intervalo, média móvel, sazonalidade e Ridge — e depois comparados modelos tabulares.

O Gradient Boosting selecionado pela validação atingiu MAE **2,886** no horizonte de 30 minutos e **2,925** no de 60 minutos no teste sintético. A Random Forest ficou próxima. Uma diferença pequena não autoriza a conclusão de que um algoritmo é universalmente melhor.

O corte entre treino, validação, calibração e teste é cronológico. Features futuras indisponíveis no momento da previsão não podem aparecer no treinamento.

## 2. Uma métrica agregada pode esconder o problema principal

A primeira calibração dos intervalos nominais de 90% cobria apenas **82,38% das observações em horários de funcionamento**, embora a cobertura agregada parecesse melhor. Os muitos zeros durante os períodos fechados inflavam a média.

A revisão passou a calibrar os resíduos **somente nos horários abertos**, separando pico e não pico. No mesmo teste sintético original, a cobertura operacional passou a **90,68% em 30 minutos** e **90,48% em 60 minutos**. Essa verificação do conjunto já consultado é exploratória. Duas novas seeds sintéticas resultaram em cobertura entre **88,73% e 90,13%**, com intervalos mais largos.

A lição: uma previsão menos confiante pode ser mais útil que um intervalo estreito e enganoso.

## 3. A regra precisa existir no código, não apenas na documentação

O simulador compara custo hipotético, estoque, capacidade e backlog em 400 cenários. Na primeira versão, o otimizador podia escolher três pessoas extras, apesar de a política fictícia limitar reforços a duas.

O espaço de busca foi corrigido. Na reexecução, as **2.000 decisões avaliadas tiveram zero violações**. O custo médio simulado da estratégia com previsão passou de **R$ 302,34 para R$ 303,31**, e o backlog médio de **11,75 para 11,92**. A escolha anterior era aparentemente melhor porque permitia ações proibidas.

Restrições de negócio são parte do algoritmo, não um aviso opcional na interface.

## 4. RAG melhora explicação, não necessariamente o resultado operacional

Cinco documentos fictícios formam o corpus de procedimentos. O recuperador lexical oferece trechos com IDs verificáveis; uma pergunta sem suporte deve permitir abstenção.

No experimento de 400 cenários, regras fixas custaram em média **R$ 367,37**; regras com previsão, **R$ 329,67**; previsão com simulação e restrição de equipe, **R$ 303,31**. Acrescentar recuperação documental e copiloto offline **não alterou esses números** — a mesma decisão numérica foi usada, por desenho experimental.

Esse resultado é relevante: o texto pode melhorar a capacidade de entender e contestar uma decisão, sem ser o responsável pela melhora matemática.

## 5. LLMs precisam de limites e avaliação própria

O copiloto do projeto consulta ferramentas tipadas e políticas. Modelos externos são opcionais; não são necessários para executar a demo offline. Explicações generativas têm schema, citações permitidas, timeout e fallback. Nenhuma aprovação crítica acontece automaticamente.

O que ainda falta? Uma avaliação cega maior da qualidade das explicações e execuções reais verificadas contra provedores externos. Testar o contrato HTTP com mocks não é o mesmo que avaliar uma LLM em operação.

## O que eu levaria para uma nova versão

Evoluiria o estoque para estados contínuos de consumo e reposição, ampliaria a avaliação de RAG e investigaria modelos sob dados externos autorizados. Antes de pensar em escala, priorizaria monitoramento, restrições operacionais e qualidade dos dados.

O TurnoLab não comprova economia real e não pretende reproduzir a operação de uma empresa. Seu valor está em oferecer experimentos claros, testes e decisões que podem ser auditadas.

**Repositório:** https://github.com/lucastnunes06/turnolab-ai

**Evidências:** relatórios de avaliação, testes no GitHub Actions, Model Card e documentação de experimentos publicados no próprio repositório.
