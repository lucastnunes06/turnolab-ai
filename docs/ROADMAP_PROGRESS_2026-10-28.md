# Evolução do roadmap — confiabilidade dos experimentos

Atualização de 28/10/2026. Os resultados são exclusivamente **sintéticos**, não indicadores de impacto operacional real.

## 1. Limite de equipe no otimizador

O experimento anterior permitia 0–3 pessoas adicionais, embora a política fictícia permitisse no máximo duas. A execução v2 limita o conjunto de decisões a 0–2 pessoas (com ou sem reposição), inclusive para o oracle. São seis ações admissíveis. Novos testes impedem a regressão.

| Medida | Antes (v1) | Depois (v2) |
| --- | ---: | ---: |
| Violações em 400 cenários × 5 estratégias | 2,25% | **0%** |
| Custo médio do simulador (hipotético) | R$ 302,34 | **R$ 303,31** |
| Backlog médio do simulador | 11,75 | **11,92** |

O aumento de custo é esperado ao remover escolhas proibidas. A interface de simulação manual continua exploratória e informa quando o cenário excede a regra. Agora a API também **recusa criar propostas** a partir de cenários com mais de duas pessoas adicionais (HTTP 422), preservando a simulação sem permitir a proposta fora da política. Essa regra foi coberta por teste de integração.

Verificar em [protocolo](experiments/protocol.md), [scripts](../ml/experiments.py) e [relatório](../reports/experiments.json).

## 2. Cobertura de previsão nos horários abertos

Na versão anterior, horários de restaurante fechado contribuíam com muitos resíduos zero para o grupo não pico e estreitavam os intervalos durante o expediente. A v2 calibra separadamente pico e não pico usando **somente linhas abertas do período de calibração**. O estimador pontual não mudou.

| Amostra sintética | Horizonte | Antes: cobertura aberta | V2: cobertura aberta |
| --- | --- | ---: | ---: |
| Teste original | 30 min | 82,38% | **90,68%** |
| Teste original | 60 min | 82,30% | **90,48%** |
| Outra seed (20261029) | 30 min | 80,56% | **88,73%** |
| Outra seed (20261029) | 60 min | 80,86% | **89,21%** |
| Outra seed (20261030) | 30 min | 81,79% | **90,13%** |
| Outra seed (20261030) | 60 min | 81,59% | **89,88%** |

**Custo da melhora:** nos conjuntos independentes de seed, a largura média aberta passou de ~18,5 para ~22 pedidos. Uma previsão mais conservadora pode ser preferível a intervalos estreitos que não refletem incerteza suficiente.

Os novos conjuntos **não foram usados para calibrar quantis**, mas compartilham o gerador sintético. O teste original já havia revelado o problema; seus resultados v2 são exploratórios, não um novo holdout intacto. Não há garantia de 90% de cobertura em dados reais nem diante de drift.

Execute depois do bootstrap:

```bash
python scripts/independent_coverage_study.py
```

Resultados: [estudo de seeds](../reports/independent_coverage_study.json) e [avaliação principal](../reports/demand.json).

## 3. Registro de modelos após retreinamento

A rotina de treinamento antes substituía o registro de modelos e podia esquecer um *challenger* já treinado. Agora preserva apenas versões anteriores cujo artefato ainda existe e passa por verificação SHA-256. O bootstrap detecta uma entrada de challenger ausente. Testes locais verificaram a preservação do registro.

## 4. Verificações

Na revisão local:

- **56 testes Python**, **13 testes frontend**, lint de estrutura, compilação e build passaram.
- Retreinamento de demanda e bootstrap sem `--retrain` foram executados.
- Experimento de 400 cenários × cinco estratégias foi regenerado e validado: zero violações.
- A CI remota deve ser verificada separadamente na aba Actions; nenhum resultado remoto é presumido.

## 5. O que continua pendente

Não seria honesto afirmar que o roadmap inteiro está encerrado. Permanecem:

- Dados externos e validação fora do gerador sintético.
- Estoque contínuo (os snapshots atuais não modelam uma operação encadeada real).
- Avaliação cega e humana do RAG, com corpus maior.
- Autenticação, permissões e infraestrutura adequadas para produção.
- Integrações externas de LLM, publicação Hugging Face e execução n8n ponta a ponta.

Essas limitações exigem dados, credenciais, implantação ou um redesenho de experimentos; não podem ser eliminadas apenas alterando documentação.
