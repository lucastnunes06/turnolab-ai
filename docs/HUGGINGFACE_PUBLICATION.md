# Publicação do modelo TurnoLab no Hugging Face

O repositório GitHub guarda **código, métricas e Model Card**. Os arquivos `.joblib` são regenerados localmente e não ficam versionados. O exportador prepara um pacote com avaliação sintética, manifesto SHA-256, inferência e avisos de segurança.

## O que já existe
- `scripts/bootstrap.py`: dados e treinamento reproduzíveis.
- `scripts/ui_fixture.py`: exemplo de features derivado da API real.
- `scripts/export_hf.py`: gera `artifacts/huggingface/model.joblib` e manifesto.
- `scripts/publish_hf.py`: valida hash e envia pacote para um repositório de modelo com autorização explícita.
- `.github/workflows/huggingface-publish.yml`: pipeline manual de treino, exportação, publicação e verificação no Hub.

## Publicar com segurança

1. Crie uma conta no [Hugging Face](https://huggingface.co/).
2. Crie um token de acesso **fine-grained** com permissão de escrita para seu namespace/modelo.
3. No GitHub, cadastre o token como **secret** `HF_TOKEN` no repositório; nunca cole o segredo em issue, conversa, README ou commit.
4. Abra **Actions → Publish synthetic model to Hugging Face (manual) → Run workflow**.
5. Digite o ID completo sob seu namespace, por exemplo `seu-usuario/turnolab-demand`, e a confirmação literal `publish`.
6. Aguarde a execução e confira o link e os arquivos remotos. Somente então inclua o URL público no currículo/README.

Alternativa local:
```bash
python scripts/bootstrap.py
python scripts/ui_fixture.py
python scripts/export_hf.py
python -m pip install 'huggingface_hub>=0.34,<2'
export HF_TOKEN='...'  # apenas sessão local
export HF_REPO_ID='seu-usuario/turnolab-demand'
export HF_PUBLISH_CONFIRM=publish
python scripts/publish_hf.py
```

**Limites:** o modelo foi treinado com dados sintéticos; não é uma previsão para estabelecimentos reais. O formato joblib/pickle só deve ser carregado de fonte confiável. Publicação não equivale a deploy, validação externa ou API de produção. A reprodução depende de Python/scikit-learn e versões documentadas.

Referência: https://huggingface.co/docs/huggingface_hub/main/guides/upload
