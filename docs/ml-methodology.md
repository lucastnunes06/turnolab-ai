# Metodologia de ML

## Demanda

- Treino: alvos anteriores ao dia 54; os primeiros 14 dias servem de aquecimento.
- Validação: origens nos dias 54–64, alvos antes do dia 65.
- Calibração: origens nos dias 65–71, alvos antes do dia 72.
- Teste: origens a partir do dia 72, com alvos observáveis até o fim do dataset.

Os períodos são purgados pelo timestamp do alvo. Normalização de Ridge é ajustada
no treino dentro do pipeline. Nenhuma feature tem ajuste supervisionado global.
Modelos congelam após o treino; a validação seleciona o candidato e a configuração.
Após a seleção, todos os candidatos são avaliados no teste para comparação
transparente, sem substituir o champion pelo menor resultado do teste.

Baselines: último intervalo, média móvel de quatro intervalos, média semanal do
mesmo horário/dia e Ridge. ML: Random Forest de 40 árvores e Gradient Boosting
com 15 ou 31 folhas. A seleção usa MAE, previamente definido. WAPE devolve null
quando a soma absoluta dos alvos é zero; não se adiciona um denominador artificial.
RMSE mostra sensibilidade a erros grandes. Há métricas por restaurante, horário,
pico e resíduos nos CSVs/figuras em `reports/`.

Todos recebem a informação de abertura do alvo. A abertura é determinística neste
gerador; fechamento inesperado seria um caso fora dessa hipótese. Essa regra
melhora todos os candidatos de modo simétrico.

Walk-forward usa janelas expansivas com cortes 40/47/54 e sete dias posteriores,
configuração fixada de antemão, sem acessar o teste final. Não é uma nova seleção de
hiperparâmetros pelo teste.

Intervalos v2: resíduos absolutos de calibração **somente em horários abertos**, grupos pico/não pico, quantil
`ceil((n+1)*(1-alpha))/n`, arredondado para cima, alpha 0,1. Limite inferior truncado
em zero; horários fechados têm previsão/intervalo zero. A validade conformal depende
de hipóteses de estabilidade que séries com drift não satisfazem automaticamente.

A versão v1 misturava zeros de fechamento na calibração não pico. A v2 retira esses zeros; no teste sintético original a cobertura aberta foi 90,68% (30 min) e 90,48% (60 min), contra 82,38% e 82,30%. Duas sementes sintéticas adicionais mostraram melhora, mas não constituem validação externa. A largura dos intervalos cresceu. Veja `reports/independent_coverage_study.json` e `docs/ROADMAP_PROGRESS_2026-10-28.md`.

## Risco de estoque

Um previsor auxiliar de demanda é treinado **somente em dias <30**. Suas previsões
fora da amostra alimentam os snapshots dos dias >=30. O classificador não recebe
previsões de um modelo treinado no futuro desses snapshots.

Treino do classificador: 30–57; validação de folhas: 58–64; Platt scaling: 65–68;
limiar por custo: 69–71; teste: >=72. Features: estoque, entrega prevista, lead,
reserva, consumo por receita, demanda prevista, média recente e horário. O rótulo
usa consumo futuro e entrega simulada exclusivamente como variável alvo.

A regra compara consumo esperado + reserva contra estoque + entrega. O classificador
HistGradientBoosting e a estratégia híbrida usam o mesmo teste. Custo de FN=60 e
FP=12 é hipótese, não custo observado. Relatórios incluem Precision/Recall/F1,
PR-AUC, Brier, bins de calibração e matrizes de confusão.

## Registro e manutenção

`ml/tracking.py` grava experimentos em SQLite e envia ao MLflow se instalado.
`artifacts/registry.json` contém champion, challenger real e hashes. O comando
`python -m ml.registry promote ID` exige melhoria de MAE de validação, contrato
igual, hash correto e calibração suficiente. Rollback só aceita versões já
promovidas. A implementação é testada em registries temporários.

O challenger Random Forest é mantido sem promoção: não supera o champion em
validação. A inferência agrega contagens e latência. PSI compara treino e sete dias
recentes por restaurante, com limiar heurístico 0,2. Cobertura insuficiente gera
alerta. Não existe auto-retreino ou promoção autônoma. Reavaliação é explícita por
`bootstrap.py --retrain` e deve receber um novo holdout para novas decisões.
