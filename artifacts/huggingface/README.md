---
language:
- pt
license: mit
library_name: sklearn
tags:
- tabular-regression
- time-series-forecasting
- synthetic-data
- conformal-prediction
---
# TurnoLab Demand v1

**Estado:** artefato local treinado, preparado para possível publicação.
Nenhum modelo foi publicado e nenhum URL do Hugging Face foi criado.

## Uso e contexto

Dois HistGradientBoostingRegressor para contagens em intervalos de 30 minutos,
previstos em horizontes +30 e +60. Demonstração de engenharia e aprendizado com
restaurantes fictícios. Não usar para dimensionar operações reais ou segurança
alimentar. Sem afiliação com iFood ou uso de seus dados.

## Dados e proveniência

Gerador `ml/data.py`, seed 42, 20 restaurantes, 90 dias, 86.400 linhas agregadas.
Licença MIT. Sem consumidores, dados pessoais ou dataset privado. Picos diários,
fins de semana, promoções, ruído Gamma-Poisson, choques e drift são artificiais.
Snapshots de estoque pertencem ao segundo problema; não são alvo destes modelos.

## Treinamento

Features causais descritas em `docs/data-and-features.md`. Comparação com último
intervalo, média móvel, sazonal, Ridge e Random Forest. Treino/validação/calibração/
teste cronológicos, com purge do alvo. MAE de validação seleciona 31 folhas,
120 iterações, learning rate 0,08 e l2=5, random_state=42. Treino termina antes do
dia 54. Não houve fine-tuning de LLM.

## Métricas observadas no teste sintético

| Horizonte | MAE | RMSE | WAPE | n |
|---|---:|---:|---:|---:|
| 30 min | 2,8861 | 5,9810 | 29,64% | 17.260 |
| 60 min | 2,9253 | 6,0508 | 30,01% | 17.240 |

Intervalos conformais nominais de 90%: cobertura agregada 90,08% / 90,02%; em
funcionamento, 82,38% / 82,30%. Os zeros em horários fechados inflam o agregado.
Não há garantia de cobertura condicional nem estabilidade sob drift. Intervalos
marginais dos horizontes não dão cobertura conjunta à soma das previsões.

## Inferência

A pasta exportada contém `model.joblib`, manifesto SHA-256, `predict.py`, exemplo
de features do replay e dependências. Execute `python predict.py`. O exemplo usa
um intervalo de pico e não implementa o pipeline de features de dados brutos;
para inferência geral, use a API do projeto. Nunca carregue pickle/joblib enviado
por fonte não confiável. Hash detecta corrupção contra o manifesto local, não
substitui assinatura e cadeia de confiança.

## Versões e limites

Python 3.12.14, scikit-learn 1.8.0, NumPy 2.3.5, pandas 2.2.3, joblib 1.5.3.
Não se promete compatibilidade de serialização entre versões. O ambiente usou CPU.
Demand-v1 é a versão local, com challenger RF não promovido por validação.

Desempenho não implica impacto real, generalização para restaurantes novos,
acurácia causal ou adequação a decisão automática. Dados longos, externos,
intervenções reais e validação humana seriam necessários para outra finalidade.
Assistência de IA foi usada no código e documentação; o candidato deve revisar e
reproduzir antes de apresentar o projeto como evidência de compreensão pessoal.
