import { cpSync, mkdirSync } from 'node:fs';
mkdirSync('dist', {
  recursive: true
});
for (const f of ['index.html', 'app.js', 'utils.js', 'styles.css', 'assets', 'api-docs.html', 'docs.js']) cpSync(f, 'dist/' + f, {
  recursive: true
});
console.log('Static production bundle created in frontend/dist');
