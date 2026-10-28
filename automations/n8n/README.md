# Integração opcional (não executada neste ambiente)

Importe `operational-alert.json` no n8n. Configure `TURNOLAB_API_URL` para a origem
acessível pela instância n8n e crie uma credencial Header Auth com
`Authorization: Bearer <token-da-demo>`. Associe-a ao nó HTTP Request. Configure
outra credencial Header Auth para o webhook; use um segredo próprio. Não coloque
segredos no JSON exportado. O workflow é importado inativo.

O agendamento consulta `POST /api/restaurants/1/evaluate`. A API calcula riscos,
registra o alerta e devolve o evento. O nó final preserva o evento no histórico de
execução do n8n. O webhook autenticado permite receber o mesmo contrato por um job
externo autorizado. Nenhuma mensagem é enviada a pessoas ou serviços terceiros.

Na plataforma, `GET /api/restaurants/1/alerts` retorna o histórico. O núcleo não
faz chamadas ao n8n e funciona sem ele. A integração e o formato de importação
precisam ser conferidos na versão de n8n que você usar; não há execução verificada
nem promessa de entrega exactly-once. Em uma evolução, usar outbox + idempotência.
