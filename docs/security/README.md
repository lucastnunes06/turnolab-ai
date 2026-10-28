# Threat model e controles

Ativos: dados por restaurante, tokens de demonstração, artefatos de modelo,
propostas e integridade da auditoria. Ameaças: usuário tentando trocar tenant,
texto do usuário/documento tentando virar instrução, saída externa fora do
contrato, alucinação numérica e aprovação pelo próprio agente.

| Ameaça | Controle implementado | Limite conhecido |
|---|---|---|
| Acesso a outro restaurante | Token → Principal → `authorize`; broker revalida escopo | Tokens públicos de demo; sem OIDC/RBAC real |
| SQL/command injection | SQL com parâmetros; ferramentas sem shell/SQL livre | Migrations e artefatos são código local confiável |
| Prompt injection | Roteamento fechado; bloqueio lexical; chunks suspeitos em quarentena | Regex não cobre todos os ataques semânticos |
| Instrução em documento | Texto tratado como evidência, nunca dispatch de ferramenta | Revisão de corpus ainda necessária |
| Alucinação numérica | Números renderizados de fatos estruturados; prosa externa com dígitos é rejeitada | Frases qualitativas externas ainda podem estar erradas |
| Schema malformado | Pydantic `extra=forbid`, limites de tamanho e faixas | Sem prova formal dos contratos |
| Exfiltração de chave | Chave só no servidor; endpoints externos fixos; logs não imprimem prompts/segredos | Um segredo fornecido no próprio texto do usuário pode ser persistido |
| Ação não autorizada | Agente cria apenas pending; sem ferramenta de aprovação | Conta humana demo é ampla para demonstrar o fluxo |
| Dupla decisão | UPDATE com `status=pending` e rowcount; segunda decisão retorna 409 | Sem idempotency key para criação de propostas |
| Auditoria alterada | Triggers impedem UPDATE/DELETE da aplicação | Administrador do arquivo pode alterar banco |
| XSS | Escape de texto antes de HTML; CSP sem scripts inline; fontes locais | Estilos inline permitidos para barras; sem auditoria especializada |
| Modelo adulterado | SHA-256 do modelo de demanda e registro local | Pickle/joblib não deve receber arquivos não confiáveis; sem assinatura |

O adaptador Groq/Gemini tem timeout por tentativa, duas tentativas no máximo e
limite externo total. Falha de rede/schema/citação volta ao template offline.
Nenhum adaptador externo foi exercitado com credenciais neste ambiente.

A suíte testa autenticação, tenant, tentativa de ferramenta arbitrária, campos
extras, aprovação por agente, duplicidade de decisão, documentos maliciosos,
perguntas sem suporte e fallback de provedor. O guardrail AST impede eval/exec/shell
na aplicação. Isso não substitui pentest nem varredura de vulnerabilidades de
pacotes. CVE audit/containers/CI remota são explicitamente pendentes até execução.

Não exponha estes tokens na internet. Para uso real: OIDC, escopo mínimo, rate
limit, TLS, gestão de segredos, retenção/remoção de conversas, artefatos assinados,
review de corpus e monitoramento de abuso. O projeto não manipula dados pessoais
reais e não se declara adequado à operação de restaurantes reais.
