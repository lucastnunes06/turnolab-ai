# Empacotamento e deploy local (sem publicação externa)

```bash
docker compose up --build
```

A aplicação fica em http://127.0.0.1:8000. O bootstrap ocorre no container e volumes
preservam dados, modelos e relatórios. Primeira execução treina modelos em CPU;
aguarde `/ready`. `docker compose down` mantém volumes. Remover volumes apaga
propostas e dados: faça backup se quiser preservar a auditoria.

O Dockerfile usa usuário sem privilégios; Compose remove capabilities e limita
bind à interface local. A imagem base usa tag Python 3.12 slim; fixar digest e
lock transitivo seria necessário para supply chain mais estrita. A lista de
dependências diretas está pinada; ainda não é um lock transitivo por hash.

Em ambiente gerenciado com CA do proxy, configure o secret de build `proxy_ca`
com o bundle confiável do ambiente, sem copiá-lo para a imagem. Para build direto:

```bash
docker build -f backend/Dockerfile --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt -t turnolab-ai .
```

Isso preserva verificação TLS. Não remova o proxy nem use `--insecure`. Runtime
com LLM externa também precisa de trust/CA conforme o ambiente; o default é offline.

**Estado:** arquivos de Docker/Compose preparados. Não declarar build ou teste de
container aprovado sem uma execução registrada. PostgreSQL, hospedagem pública,
OIDC, secrets manager e automação de deploy não estão implementados.

O workflow GitHub Actions executa bootstrap, checks, lint, auditoria de pacotes e
Playwright em runner limpo. Está preparado, mas não foi disparado remotamente;
não há repositório remoto criado ou publicado. Publicar código/modelo requer
instrução e credenciais apropriadas do usuário.
