# Limitações e evolução

## Limitações atuais

Dados e custos sintéticos; receitas pequenas e mix fixo nas features. Snapshots de
estoque são estados independentes. Fila fluida sem desistência, tipos de pedido,
turnos ou segurança alimentar. Aumento de estoque é hipótese de simulação; não
faz compra. Promoção usa coeficiente hipotético sem identificação causal.

A calibração v2 exclui zeros estruturais de fechamento e melhora a cobertura operacional sintética, mas não garante 90% sob drift: nas duas novas sementes, a cobertura aberta variou de aproximadamente 88,7% a 90,1%. Calibração temporal não satisfaz automaticamente exchangeability. Teste final já consultado: qualquer
melhoria de calibração/modelo deve ser avaliada em um período novo, não no mesmo
holdout. No treinamento, a política de abertura é conhecida e simplificada.

RAG avaliado em conjunto de desenvolvimento pequeno, com um documento ouro por
pergunta. Não há encoder semântico pré-treinado, avaliação humana ou LLM externa
executada. Roteamento de intenção e bloqueios lexicais têm lacunas conhecidas.
Papéis não são agentes autônomos e não melhoraram decisões por si só.

Tokens públicos de demo; auditoria não é inviolável contra administrador; joblib
não é formato seguro para entrada não confiável. Chamadas CPU bloqueiam o event
loop. Dependências diretas pinadas, sem lock transitivo por hash. Não há operação
em produção, testes de PostgreSQL nem credenciais externas.

React/Vite/Tailwind e SQLAlchemy/Alembic ficaram fora da implementação devido à
indisponibilidade de pacotes. A alternativa entregue usa JS/CSS nativos e sqlite3.
MLflow local, Docker Compose e testes de navegador foram validados em runners do GitHub Actions, conforme `docs/CI_EVIDENCE_2026-10-28.md`. Isso não equivale a implantação pública ou operação de produção. Integrações LLM externas, n8n e Hugging Face permanecem sem validação completa.

## Próximos experimentos, em ordem

1. Novo período de teste e intervalos separados por abertura/pico; avaliar drift
   de resíduo e custo de subcobertura por restaurante.
2. Estoque contínuo com entregas e mix variáveis; separar risco de entrega e demanda.
3. Corpus maior e conjunto de RAG cego; comparação lexical vs encoder versionado.
4. Julgamento humano de justificativas e decisões, sem atribuir cálculos à LLM.
5. Auth real, idempotência, migração para PostgreSQL e logs com retenção.
6. Manter navegador, Compose e MLflow validados em CI; validar infraestrutura e autenticação reais antes de uma possível hospedagem pública.
7. Migrar a UI para React/TypeScript quando houver dependências, preservando os
   contratos e fluxos já existentes, sem reescrever os números no frontend.

Os IDs de treino v1 são geridos manualmente. `--retrain` substitui seus arquivos;
para preservar reexecução de decisões antigas, arquive banco, código, registry e
artefatos antes de retreinar. O rollback do registry alterna versões existentes,
mas não reconstrói um arquivo que já foi sobrescrito. Versionamento imutável de
todo novo treino é uma evolução necessária para operação prolongada.
