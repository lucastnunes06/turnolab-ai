# Prévia interativa (GitHub Pages)

O arquivo [index.html](preview/index.html) é uma **prévia estática responsiva**. Seus controles apresentam resultados publicados dos 400 cenários sintéticos, sem executar a API, treinar modelos ou chamar LLM. As capturas e o GIF vêm da aplicação real, testada com Chromium.

## Ativar Pages

1. Abra [Settings → Pages](https://github.com/lucastnunes06/turnolab-ai/settings/pages).
2. Em **Build and deployment → Source**, selecione **GitHub Actions**.
3. Em [Actions](https://github.com/lucastnunes06/turnolab-ai/actions), abra **Publish static portfolio preview to GitHub Pages (manual)** e clique em **Run workflow**.
4. Após o workflow ser concluído com sucesso, verifique o link `https://lucastnunes06.github.io/turnolab-ai/` em celular e desktop.

O URL não deve ser anunciado como publicado antes de sua verificação. O workflow monta um artefato mínimo apenas com HTML, imagens, CSV agregado e documentação, sem disponibilizar banco SQLite, arquivos de ambiente ou segredos.

Também é possível baixar/abrir `docs/preview/index.html` localmente a partir do clone do projeto.

Referência oficial: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
