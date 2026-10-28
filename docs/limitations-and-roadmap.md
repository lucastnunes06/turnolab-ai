# Limitações e evolução

## Limitações atuais

Dados e custos sintéticos; receitas pequenas e mix fixo nas features. Snapshots de
estoque são estados independentes. Fila fluida sem desistência, tipos de pedido,
turnos ou segurança alimentar. Aumento de estoque é hipótese de simulação; não
faz compra. Promoção usa coeficiente hipotético sem identificação causal.

Intervalos com cobertura operacional abaixo do nominal. Calibração temporal não
satisfaz automaticamente exchangeability. Teste final já consultado: qualquer
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
MLflow tem adaptador, mas pacote/servidor não foram exercitados. Docker e GitHub
Actions foram preparados; execução só deve ser declarada após verificação.

## Próximos experimentos, em ordem

1. Novo período de teste e intervalos separados por abertura/pico; avaliar drift
   de resíduo e custo de subcobertura por restaurante.
2. Estoque contínuo com entregas e mix variáveis; separar risco de entrega e demanda.
3. Corpus maior e conjunto de RAG cego; comparação lexical vs encoder versionado.
4. Julgamento humano de justificativas e decisões, sem atribuir cálculos à LLM.
5. Auth real, idempotência, migração para PostgreSQL e logs com retenção.
6. Validar MLflow, containers, CI remota, navegador e gravação de 90 segundos.
   O HTTP/TCP local foi validado em 28/10/2026; a navegação do Chromium segue bloqueada pela política do ambiente.
7. Migrar a UI para React/TypeScript quando houver dependências, preservando os
   contratos e fluxos já existentes, sem reescrever os números no frontend.

Os IDs de treino v1 são geridos manualmente. `--retrain` substitui seus arquivos;
para preservar reexecução de decisões antigas, arquive banco, código, registry e
artefatos antes de retreinar. O rollback do registry alterna versões existentes,
mas não reconstrói um arquivo que já foi sobrescrito. Versionamento imutável de
todo novo treino é uma evolução necessária para operação prolongada.
