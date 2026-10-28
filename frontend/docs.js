import { escapeHTML as e } from './utils.js';
const select = document.getElementById('api-endpoint'),
  response = document.getElementById('api-response');
let endpoints = [];
function defaults() {
  const selected = endpoints[Number(select.value)];
  document.getElementById('api-path').value = selected.path.replaceAll('{rid}', '1');
  let body = {};
  if (selected.path.endsWith('/simulations')) body = {
    staff: 4,
    kitchen_capacity: 60
  };
  if (selected.path.endsWith('/copilot')) body = {
    message: 'Qual a política de reposição de estoque?'
  };
  if (selected.path.endsWith('/decision')) body = {
    status: 'rejected'
  };
  document.getElementById('api-body').value = JSON.stringify(body, null, 2);
}
try {
  const spec = await (await fetch('/openapi.json')).json();
  endpoints = Object.entries(spec.paths).flatMap(([path, methods]) => Object.entries(methods).map(([method, definition]) => ({
    path,
    method: method.toUpperCase(),
    ...definition
  })));
  select.innerHTML = endpoints.map((ep, i) => `<option value="${i}">${e(ep.method)} ${e(ep.path)}</option>`).join('');
  document.getElementById('api-endpoints').innerHTML = `<table><thead><tr><th>Método</th><th>Caminho</th><th>Descrição</th></tr></thead><tbody>${endpoints.map(ep => `<tr><td>${e(ep.method)}</td><td class="mono">${e(ep.path)}</td><td>${e(ep.summary || '')}</td></tr>`).join('')}</tbody></table>`;
  defaults();
} catch (err) {
  response.textContent = 'Não foi possível carregar OpenAPI: ' + err.message;
}
select.addEventListener('change', defaults);
document.getElementById('api-form').addEventListener('submit', async event => {
  event.preventDefault();
  const input = new FormData(event.target),
    ep = endpoints[Number(input.get('endpoint'))];
  const path = String(input.get('path'));
  if (!path.startsWith('/api/') && !['/health', '/ready'].includes(path)) {
    response.textContent = 'Somente endpoints desta API são permitidos.';
    return;
  }
  try {
    const headers = {
      Authorization: 'Bearer ' + input.get('token'),
      'Content-Type': 'application/json'
    };
    const options = {
      method: ep.method,
      headers
    };
    if (ep.method === 'POST') options.body = JSON.stringify(JSON.parse(input.get('body')));
    const r = await fetch(path, options);
    response.textContent = `HTTP ${r.status} · request ${r.headers.get('X-Request-ID')}\n\n` + JSON.stringify(await r.json(), null, 2);
  } catch (err) {
    response.textContent = err.message;
  }
});
