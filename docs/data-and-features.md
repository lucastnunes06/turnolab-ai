# Dados e features

## Proveniência

Todos os dados são sintéticos e gerados localmente por NumPy com seed 42. Nenhum
pedido, restaurante ou ingrediente deriva de dados internos do iFood. Nomes são
fictícios. Código, corpus e dados gerados podem ser usados sob MIT neste projeto.

O gerador cria 20 restaurantes, 90 dias desde 01/06/2026, intervalos de 30 minutos,
três produtos, quatro ingredientes e seis relações de receita. Existem 86.400
intervalos agregados e 86.240 snapshots de estoque. `order_events` agrega eventos
por meia hora; não guarda consumidores nem uma linha por pedido individual.

São inseridos ciclos de almoço/jantar, fim de semana, promoções planejadas,
variabilidade entre restaurantes, falta ocasional de equipe, choques diários,
eventos atípicos e mudança de comportamento a partir do dia 64. Amostragem
Gamma-Poisson gera superdispersão. Cancelamentos aumentam sob pressão de capacidade.
Os modelos não observam os choques latentes.

Snapshots de estoque são estados experimentais independentes em cada origem,
baseados em demanda passada e ruído; não simulam um ciclo contínuo real de compras.
Receitas e mix têm valores conhecidos, mas rótulos de risco incluem ruído de mix e
atraso de entrega. Não há segurança alimentar ou logística real representada.

## Ingestão e qualidade

`generate → validate → CSV+SHA256 → ingest`.

A validação detecta ausentes, duplicatas, tempos desalinhados, eventos fora de
ordem, lacunas, chaves estrangeiras inválidas, quantidades negativas/não finitas,
unidades divergentes, cancelamentos acima dos pedidos e restrições operacionais.
A carga recusa sobrescrever um banco povoado. Constraints atuam como segunda barreira.
A limpeza normaliza timestamps para ISO, ordena features por restaurante e preserva
as linhas problemáticas como erro, sem imputação silenciosa de fatos.

`reports/data_quality.json` registra volume e hashes de todos os CSVs. O hash de
demanda é reprodutível para as versões de dependências fixadas; versões futuras
podem alterar a serialização ou algoritmos.

## Contrato temporal

Na origem `t`, a quantidade de pedidos do intervalo `t` já foi observada. O alvo é
`t+1` ou `t+2`; cada alvo contém pedidos de uma meia hora. A interface soma as duas
previsões para o próximo período de 60 minutos, mas não atribui cobertura conjunta
a uma soma de limites marginais.

Features: ID do restaurante, seno/cosseno de hora e dia, indicador de fim de semana,
abertura, promoção planejada no alvo, lags 0/1/2/48, médias 4/12/48 intervalos,
mesmo horário no dia anterior, média dos dois horários semanais anteriores,
equipe e capacidade conhecidas na origem. Não há prep time futuro ou cancelamento
futuro entre as features.

`seasonal_day = orders.shift(48-h)` e `seasonal_week` usa `336-h` e `672-h`;
para h em {1,2}, todos os valores são anteriores à origem. As médias incluem o
intervalo atual já observado. Isso **não** serve para previsão antes do fechamento
do intervalo atual; mudar a semântica exigiria deslocar as features mais um passo.

A tabela `promotion_calendar` registra `known_at` um dia antes. A inferência lê
apenas esse calendário para o futuro, nunca as contagens futuras. O teste adversarial
substitui todos os pedidos após uma origem por 99.999 e verifica que as features
dessa origem não mudam. Esse teste complementa a revisão dos shifts, não prova
que toda integração futura estará livre de vazamento.
