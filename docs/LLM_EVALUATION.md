# Avaliação reproduzível do copiloto e das LLMs externas

O núcleo do TurnoLab produz valores numéricos com modelos e simulação; o adaptador generativo **não** calcula esses valores. O benchmark abaixo usa **dez perguntas sintéticas** sobre cinco políticas fictícias e registra recuperação documental, IDs de citações, erros, tokens estimados e latência.

## Executar sem credenciais (baseline de templates)

```bash
python scripts/llm_benchmark.py --provider offline
```

A saída `reports/llm_benchmark_offline.json` identifica claramente `real_external_llm_executed: false`. Isso **não avalia uma LLM**; serve para conferir a estrutura do teste, a recuperação e o comportamento de fallback.

## Avaliar realmente Groq ou Gemini

Configure uma chave de API **somente no ambiente local**, nunca no código:

```bash
export LLM_API_KEY='SUA_CHAVE'
python scripts/llm_benchmark.py --provider groq --live
# ou: --provider gemini --live
```

Também é possível abrir **Actions → Optional live LLM evidence → Run workflow** após cadastrar um secret `LLM_API_KEY` no GitHub e configurar seu environment `llm-evaluation`.

O script usa o mesmo `ExternalProvider` da aplicação, com schema estruturado e allowlist de referências. Ele falha se o provedor não responder com resultados válidos. O relatório **não** grava a chave, o corpo integral das respostas nem conversas de usuários.

### O que o benchmark consegue medir

| Métrica | Interpretação |
| --- | --- |
| Retrieval Hit@3 | Documento ouro recuperado entre os três primeiros |
| Abstenção de recuperação | Perguntas fora do corpus sem trechos relevantes |
| Citation-ID allowlist | Nenhum identificador de documento fora das evidências |
| Citação do documento esperado | Proporção de casos respondíveis com ID correto |
| Latência e tokens | Valores observados na execução; sem alegar SLA/custo real |

**Limites:** dez perguntas manuais não equivalem a benchmark cego; IDs de citação válidos não garantem suporte semântico da explicação, e os documentos são fictícios. Uma etapa futura deve usar anotadores independentes, mais casos, políticas adversariais e avaliação de entailment. Nunca comparar offline templates com LLMs como se fossem modelos equivalentes.

## Segurança e rastreabilidade

- As evidências carregam a **pergunta original**, URLs de documentos e fatos estruturados.
- Números novos na explicação externa são rejeitados pelo schema/validador existente.
- IDs fora do conjunto recuperado são rejeitados.
- Falha de rede, timeout ou JSON inválido não executam ações.
- Ações requerem aprovação humana e permissões no backend.

**Status da integração:** SDK e contratos HTTP simulados já testados no CI. A execução de LLM real permanece pendente até um relatório `--live` aprovado e verificável; não declarar sucesso com base apenas no workflow ou no código.
