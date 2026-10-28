import { escapeHTML as e, number as n, percent as pct, currency as brl, timeLabel, pathFrom, clamp } from './utils.js';
const paths = {
  grid: 'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z',
  chart: 'M3 3v18h18M7 14l4-5 4 3 6-8',
  flask: 'M9 3h6M10 3v7L4 20h16L14 10V3M8 14h8',
  spark: 'm12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3zM20 3v4M18 5h4',
  box: 'm3 7 9-4 9 4v11l-9 4-9-4V7zm0 0 9 4 9-4M12 11v11M7 5l10 4',
  pulse: 'M2 12h4l3-8 5 16 3-8h5',
  check: 'm5 12 4 4L19 6',
  checks: 'm3 12 4 4L17 6M12 16l9-10',
  clock: 'M12 8v5l3 2M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0z',
  arrow: 'M5 12h14m-5-5 5 5-5 5',
  chevron: 'm9 5 7 7-7 7',
  down: 'm6 9 6 6 6-6',
  calendar: 'M4 5h16v16H4zM8 3v4M16 3v4M4 10h16',
  restaurant: 'M4 21V9h16v12M2 9l2-6h16l2 6M8 21v-6h4v6M3 9c2 3 4 0 4 0s2 3 5 0c2 3 5 0 5 0s2 3 4 0',
  bell: 'M5 16h14l-2-3V8a5 5 0 0 0-10 0v5l-2 3zm5 4h4',
  settings: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM9 3h6l1 3 3 1 2 5-2 5-3 1-1 3H9l-1-3-3-1-2-5 2-5 3-1 1-3z',
  help: 'M9 8a3 3 0 0 1 6 1c0 2-3 2-3 5M12 17h.01M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0z',
  shield: 'm12 2 8 3v7c0 5-8 10-8 10S4 17 4 12V5l8-3zm-4 10 3 3 5-6',
  layers: 'm12 3 10 5-10 5L2 8l10-5zM2 12l10 5 10-5M2 16l10 5 10-5',
  document: 'M5 3h10l4 4v14H5V3zm10 0v5h4M8 12h8M8 16h6',
  link: 'M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-2 2M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l2-2',
  search: 'M20 20l-5-5M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0z',
  trend: 'm3 16 6-6 4 4 8-10M15 4h6v6',
  users: 'M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM2 21v-3a7 7 0 0 1 14 0v3M16 4a4 4 0 0 1 0 7M19 14a6 6 0 0 1 3 5v2',
  warning: 'm12 3 10 18H2L12 3zm0 5v6M12 17h.01',
  terminal: 'm5 6 6 6-6 6M13 18h7',
  refresh: 'M20 7v5h-5M4 17v-5h5M6 7a7 7 0 0 1 13-1l1 6M18 17a7 7 0 0 1-13 1l-1-6',
  download: 'M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5',
  send: 'm3 3 19 9-19 9 3-9-3-9zm3 9h16',
  arrowUp: 'm7 17 10-10M7 7h10v10',
  menu: 'M3 6h18M3 12h18M3 18h18',
  x: 'm6 6 12 12M6 18 18 6',
  activity: 'M5 4h14v16H5zM9 8h6M9 12h6M9 16h4',
  rocket: 'M5 14 3 21l7-2M9 15 4 10l6-2 4-5h7v7l-5 4-2 6-5-5zM15 7h.01'
};
const icon = (name, cls = '') => `<svg class="icon ${cls}" viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[name] || paths.chart}"/></svg>`;
const navs = [['dashboard', 'grid', 'Visão geral'], ['demand', 'chart', 'Demand Intelligence'], ['scenarios', 'flask', 'Scenario Lab'], ['copilot', 'spark', 'AI Copilot'], ['inventory', 'box', 'Inventory Intelligence'], ['models', 'pulse', 'Model Observatory'], ['actions', 'checks', 'Action Center'], ['experiments', 'layers', 'Experiments']];
const titles = {
  dashboard: 'Sua operação, um passo à frente.',
  demand: 'Antecipe a demanda. Entenda os limites.',
  scenarios: 'Boas decisões começam com um teste.',
  copilot: 'Pergunte. Investigue. Decida.',
  inventory: 'O próximo gargalo pode estar no estoque.',
  models: 'Confiança se mede, não se presume.',
  actions: 'A inteligência sugere. Você decide.',
  experiments: 'O que realmente melhora uma decisão?',
  settings: 'Seu ambiente de demonstração'
};
const subtitles = {
  dashboard: 'Demanda, capacidade e decisões conectadas em um só lugar.',
  demand: 'Previsões rastreáveis, intervalos calibrados e erros que merecem atenção.',
  scenarios: 'Compare hipóteses operacionais antes de propor uma mudança.',
  copilot: 'Um copiloto fundamentado em ferramentas, políticas e evidências.',
  inventory: 'Consumo esperado, entregas e risco — ingrediente por ingrediente.',
  models: 'Modelos, baselines e sinais de degradação, com resultados observados.',
  actions: 'Propostas pendentes e um histórico verificável de cada decisão.',
  experiments: 'Ablações controladas em cenários sintéticos. Sem favorecer a IA.',
  settings: 'Autenticação demonstrativa, sem conexão com operações reais.'
};
const state = {
  page: location.hash.slice(1) || 'dashboard',
  rid: 1,
  restaurants: [],
  data: null,
  models: null,
  experiments: null,
  monitoring: null,
  actions: null,
  audit: null,
  simulation: null,
  messages: [],
  loading: true,
  error: null,
  chatBusy: false,
  menu: false
};
let toastTimer;
function toast(text) {
  const node = document.querySelector('#toast');
  node.textContent = text;
  node.classList.add('visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => node.classList.remove('visible'), 4000);
}
async function api(path, options = {}) {
  const token = sessionStorage.getItem('turnolab-token') || 'turnolab-demo';
  const r = await fetch('/api' + path, {
    ...options,
    headers: {
      Authorization: 'Bearer ' + token,
      'Content-Type': 'application/json',
      ...(options.headers || {})
    }
  });
  let body;
  try {
    body = await r.json();
  } catch {
    throw Error('A API retornou uma resposta inválida.');
  }
  if (!r.ok) throw Error(typeof body.detail === 'string' ? body.detail : `Falha na API (${r.status}). Confira os dados e tente novamente.`);
  return body;
}
const post = (path, body) => api(path, {
  method: 'POST',
  body: JSON.stringify(body)
});
const scope = suffix => `/restaurants/${state.rid}/${suffix}`;
const badge = (text, color = '', ic = '') => `<span class="badge ${color}">${ic ? icon(ic) : ''}${e(text)}</span>`;
const button = (text, action, primary = false, ic = 'arrow', extra = '') => `<button class="btn ${primary ? 'primary' : ''} ${extra}" data-action="${e(action)}">${icon(ic)}${e(text)}</button>`;
const footer = () => `<footer class="main-footer"><span>TurnoLab AI · Laboratório experimental com dados sintéticos. Sem afiliação com o iFood.</span><span>${icon('shield', 'inline-icon')} <b>Evidências antes de decisões.</b></span></footer>`;
const dateLine = () => `<div class="date-row">${icon('calendar')}<span>Sábado, 29 de agosto de 2026</span><span class="separator"></span><span>Replay às 18:00 UTC</span><span class="data-label">${icon('refresh')} Dados reproduzíveis · seed 42</span></div>`;
const info = (text, warning = false) => `<div class="info-banner ${warning ? 'warning' : ''}">${icon(warning ? 'warning' : 'shield')}<div>${text}</div></div>`;
function shell(content) {
  const nav = navs.map(([key, ic, title], i) => `${i === 5 ? '</div><div class="nav-section-label">ENGENHARIA</div><div class="nav-group">' : ''}<a href="#${key}" class="nav-item ${state.page === key ? 'active' : ''}" ${state.page === key ? 'aria-current="page"' : ''}>${icon(ic)}<span>${e(title)}</span>${key === 'actions' && state.actions?.items.filter(a => a.status === 'pending').length ? `<span class="nav-dot">${state.actions.items.filter(a => a.status === 'pending').length}</span>` : ''}</a>`).join('');
  return `<div class="menu-backdrop ${state.menu ? 'open' : ''}" data-action="menu"></div><aside class="sidebar ${state.menu ? 'open' : ''}"><a class="brand" href="#dashboard"><span class="brand-mark">t<span>↗</span></span><span>turnolab<small>AI</small></span></a><div class="nav-section-label">WORKSPACE</div><nav class="nav-group" aria-label="Navegação principal">${nav}</nav><div class="sidebar-bottom"><div class="lab-note"><strong>${icon('flask')} Um laboratório, decisões reais.</strong>Simule possibilidades.<br>Questione previsões.<br>Decida com evidências.</div><a href="#settings" class="nav-item">${icon('settings')}Configurações</a><button class="nav-item" data-action="help">${icon('help')}Sobre o laboratório${icon('arrowUp')}</button><div class="profile"><div class="avatar">OP</div><div class="profile-text"><strong>Operador do laboratório</strong><span class="muted">Workspace de demonstração</span></div></div></div></aside>
 <header class="topbar"><div class="breadcrumb"><button class="mobile-menu" data-action="menu" aria-label="Abrir menu">${icon('menu')}</button>${icon('restaurant')}<span>Workspace</span>${icon('chevron')}<span class="current">${e(navs.find(x => x[0] === state.page)?.[2] || 'Configurações')}</span></div><div class="top-right"><span class="replay-tag"><i class="status-dot"></i> Ambiente de demonstração</span><button class="icon-button" data-action="alerts" aria-label="Ver riscos operacionais">${icon('bell')}<i class="notification-dot"></i></button><div class="avatar small-hide" style="background: #edf1ee">OP</div></div></header>
 <main class="main" id="content" tabindex="-1"><div class="page-head"><div><div class="eyebrow">OPERATIONAL INTELLIGENCE / ${e(state.page === 'dashboard' ? 'OVERVIEW' : state.page.toUpperCase())}</div><h1>${e(titles[state.page] || titles.dashboard)}</h1><p class="page-subtitle">${e(subtitles[state.page] || subtitles.dashboard)}</p></div><div class="head-tools"><div class="select-wrap">${icon('restaurant')}<select id="restaurant-select" aria-label="Restaurante fictício">${state.restaurants.map(r => `<option value="${r.id}" ${r.id === state.rid ? 'selected' : ''}>${e(r.name)}</option>`).join('')}</select></div>${button('Exportar evidências', 'export', false, 'download', 'export')}</div></div>${content}${footer()}</main>`;
}
const loading = () => `<div class="loading-grid">${Array.from({
  length: 4
}, () => '<div class="skeleton"></div>').join('')}</div><div class="skeleton loading-main" role="status" aria-label="Carregando dados reais da API"></div>`;
function render() {
  let content;
  if (state.error) content = `<div class="error-box" role="alert"><h2>Não foi possível carregar o laboratório.</h2><p>${e(state.error)}</p>${button('Tentar novamente', 'retry', true, 'refresh')}${button('Configurar token', 'settings', false, 'settings')}</div>`;else if (state.loading) content = loading();else content = ({
    dashboard,
    demand: demandPage,
    scenarios: scenarioPage,
    copilot: copilotPage,
    inventory: inventoryPage,
    models: modelsPage,
    actions: actionsPage,
    experiments: experimentsPage,
    settings: settingsPage
  }[state.page] || dashboard)();
  document.querySelector('#app').innerHTML = shell(`<div class="page-content">${content}</div>`);
}
function sparkline(values, color = '#65a88a') {
  const points = values.slice(-15);
  const max = Math.max(1, ...points),
    min = Math.min(...points);
  const coords = points.map((v, i) => [i * 72 / Math.max(points.length - 1, 1), 28 - (v - min) / (max - min || 1) * 22]);
  return `<svg class="kpi-spark" viewBox="0 0 75 32" aria-hidden="true"><path d="${pathFrom(coords)}" fill="none" stroke="${color}" stroke-width="1.6"/></svg>`;
}
function kpi(label, value, unit, foot, ic, color = '', spark = []) {
  return `<section class="card kpi ${color}"><div class="kpi-top">${e(label)}<span class="kpi-icon">${icon(ic)}</span></div><div class="kpi-value">${e(value)}${unit ? `<small>${e(unit)}</small>` : ''}</div><div class="kpi-footer">${foot}</div>${spark.length ? sparkline(spark, color === 'purple' ? '#a791ce' : color === 'orange' ? '#d4b382' : '#70b19b') : ''}</section>`;
}
function demandChart(large = false) {
  const d = state.data;
  const observed = d.history.filter(r => Number(r.timestamp.slice(11, 13)) >= 9 && r.timestamp.slice(0, 10) === d.as_of.slice(0, 10));
  const forecasts = d.forecast.forecasts;
  const all = [...observed.map(r => r.orders), ...forecasts.map(f => f.upper)];
  const cap = Math.min(d.restaurant.kitchen_capacity, d.forecast.current.staff * 12);
  const max = Math.ceil(Math.max(...all, cap, 40) / 20) * 20;
  const W = 900,
    H = large ? 340 : 290,
    left = 43,
    right = 22,
    top = 36,
    bottom = 36;
  const originHour = 18;
  const x = h => left + (h - 9) / 11 * (W - left - right);
  const y = v => top + (1 - v / max) * (H - top - bottom);
  const time = s => Number(s.slice(11, 13)) + Number(s.slice(14, 16)) / 60;
  const pts = observed.map(r => [x(time(r.timestamp)), y(r.orders)]);
  const last = observed.at(-1) || {
    timestamp: d.as_of,
    orders: 0
  };
  const fp = [[x(18), y(last.orders)], ...forecasts.map(f => [x(time(f.target)), y(f.point)])];
  const band = [[x(18), y(last.orders)], ...forecasts.map(f => [x(time(f.target)), y(f.upper)]), ...forecasts.toReversed().map(f => [x(time(f.target)), y(f.lower)]), [x(18), y(last.orders)]];
  return `<div class="chart-area"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Histórico real do dataset sintético, previsão e intervalo conformal para os próximos 30 e 60 minutos"><defs><linearGradient id="area-gradient" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#70b99b" stop-opacity=".19"/><stop offset="1" stop-color="#70b99b" stop-opacity=".015"/></linearGradient></defs><rect x="${x(originHour)}" y="${top - 18}" width="${x(20) - x(originHour)}" height="${H - bottom - top + 18}" rx="5" fill="#f4faf6"/><text x="${x(18) + 12}" y="${top - 5}" fill="#8bb39e" font-size="8" letter-spacing="1.2">PREVISÃO</text>${[0, .25, .5, .75, 1].map(v => `<line class="chart-grid" x1="${left}" x2="${W - right}" y1="${y(v * max)}" y2="${y(v * max)}"/><text class="chart-axis" x="${left - 12}" y="${y(v * max) + 3}" text-anchor="end">${n(v * max)}</text>`).join('')}<text class="chart-axis" x="${left}" y="14">PEDIDOS / 30 MIN</text><path d="${pathFrom(pts)} L${pts.at(-1)?.[0] || left},${H - bottom} L${left},${H - bottom} Z" fill="url(#area-gradient)"/><line x1="${left}" x2="${W - right}" y1="${y(cap)}" y2="${y(cap)}" stroke="#d7b17d" stroke-width="1" stroke-dasharray="4 5"/><text x="${left + 7}" y="${y(cap) - 7}" fill="#c9ad84" font-size="8">CAPACIDADE · ${n(cap)}</text><path d="${pathFrom(band)} Z" fill="#d8eee2" opacity=".8"/><path d="${pathFrom(pts)}" fill="none" stroke="#3a9a7b" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/><path d="${pathFrom(fp)}" fill="none" stroke="#3a9a7b" stroke-width="2" stroke-dasharray="5 5"/>${observed.map(r => `<circle cx="${x(time(r.timestamp))}" cy="${y(r.orders)}" r="2" fill="#fff" stroke="#3a9a7b" stroke-width="1.3"><title>${e(timeLabel(r.timestamp))}: ${r.orders} pedidos</title></circle>`).join('')}${forecasts.map(f => `<circle cx="${x(time(f.target))}" cy="${y(f.point)}" r="4" fill="#3a9a7b" stroke="#fff" stroke-width="2"><title>${e(timeLabel(f.target))}: ${n(f.point, 1)} [${n(f.lower, 1)} – ${n(f.upper, 1)}]</title></circle>`).join('')}<line x1="${x(18)}" x2="${x(18)}" y1="${top}" y2="${H - bottom}" stroke="#b6cebf" stroke-dasharray="3 5"/>${[10, 12, 14, 16, 18, 20].map(h => `<text class="chart-axis" x="${x(h)}" y="${H - 12}" text-anchor="middle">${String(h).padStart(2, '0')}:00</text>`).join('')}</svg></div>`;
}
const chartLegend = () => `<div class="chart-legend"><span><i class="legend-mark"></i>Histórico</span><span><i class="legend-mark forecast"></i>Previsão</span><span><i class="legend-mark band"></i>Intervalo 90%</span></div>`;
function stockTable(compact = false) {
  return `<div class="table-wrap"><table><thead><tr><th>Ingrediente</th><th>Disponível</th>${compact ? '' : '<th>Consumo previsto</th><th>Reposição</th>'}<th>Risco estimado</th><th>Status</th></tr></thead><tbody>${state.data.inventory.items.map((s, i) => `<tr><td><div class="ingredient"><span class="ingredient-swatch">${['F', 'A', 'V', 'P'][i]}</span><strong>${e(s.name)}</strong></div></td><td>${n(s.on_hand, 1)} <span class="muted">${e(s.unit)}</span></td>${compact ? '' : `<td>${n(s.forecast_consumption, 1)} ${e(s.unit)}</td><td>${s.lead_minutes} min</td>`}<td><span class="bad">${pct(s.probability, 0)}</span><div class="mini-progress"><span style="width:${s.probability * 100}%"></span></div></td><td>${badge(s.critical ? 'Atenção' : 'Monitorado', s.critical ? 'amber' : '', '')}</td></tr>`).join('')}</tbody></table></div>`;
}
function dashboard() {
  const d = state.data,
    m = d.metrics,
    f = d.forecast.forecasts[0],
    stock = d.inventory.items;
  return `${dateLine()}<div class="kpi-grid">${kpi('Pedidos observados hoje', n(m.orders_today), '', `<b>${m.cancellations_today} cancelamentos</b> <span>· até 18:00</span>`, 'box', '', d.history.map(x => x.orders))}${kpi('Demanda nos próximos 60 min', n(m.demand_60_minutes), 'pedidos', `<b>Previsão do modelo</b> <span>· 2 intervalos</span>`, 'spark', 'purple', d.forecast.forecasts.map(x => x.point))}${kpi('Capacidade prevista em uso', pct(m.capacity_utilization), '', `<span>${d.forecast.current.staff} pessoas</span> <span>· próximo intervalo</span>`, 'pulse', 'orange', d.history.map(x => x.capacity))}${kpi('Ingredientes em atenção', `${m.critical_ingredients} <span class="muted">/ ${stock.length}</span>`, '', `<b>Revisar reposição</b> <span>· modelo de risco</span>`, 'warning', 'red').replace(e(`${m.critical_ingredients} <span class="muted">/ ${stock.length}</span>`), `${m.critical_ingredients}<small>/ ${stock.length}</small>`)}</div>
 <div class="dashboard-middle"><section class="card"><div class="card-heading"><div><h2>Um olhar para o próximo turno</h2><p>Demanda observada e previsão · intervalos de 30 minutos</p></div>${chartLegend()}</div>${demandChart()}<div class="chart-bottom"><span>${icon('clock', 'inline-icon')} Origem da previsão: 18:00 · ${e(f.model_version)}</span><a href="#demand" class="good">Explorar demanda ${icon('arrow', 'inline-icon')}</a></div></section>
 <aside class="risk-panel card"><div class="risk-top"><span class="risk-icon">${icon('warning')}</span><span>RADAR OPERACIONAL</span></div><h2>${m.critical_ingredients ? 'O estoque pede atenção.' : 'Um turno para acompanhar.'}</h2><p>${m.critical_ingredients ? `${m.critical_ingredients} ingredientes ultrapassaram o limiar de risco. Reforçar a equipe pode não resolver o gargalo.` : 'Compare capacidade e incerteza antes de alterar a operação.'}</p><div class="risk-rule"></div><div class="risk-line"><span>Próximo intervalo</span><strong>${n(f.point, 0)} pedidos previstos</strong></div><div class="risk-line"><span>Faixa de previsão</span><strong>${n(f.lower, 0)}–${n(f.upper, 0)} pedidos</strong></div><button class="btn" data-action="go-scenarios">Explorar um cenário ${icon('arrow')}</button></aside></div>
 <div class="dashboard-bottom"><section class="card table-card"><div class="card-heading"><div><h2>Antes que falte</h2><p>Ingredientes monitorados · dados do restaurante selecionado</p></div><a href="#inventory" class="small good">Ver estoque ${icon('arrow', 'inline-icon')}</a></div>${stockTable(true)}</section><section class="card copilot-teaser"><div class="copilot-title"><span class="ai-symbol">${icon('spark')}</span><div><h2>Uma segunda leitura da operação</h2><small>AI Copilot · evidências conectadas</small></div>${badge('Offline', 'neutral')}</div><p>Há mais demanda a caminho. Mas contratar outra pessoa é a melhor decisão?<br>Compare cenários e descubra o que sustenta cada recomendação.</p><div class="section-gap"><span class="evidence-pill">${icon('chart')}Previsão</span><span class="evidence-pill">${icon('document')}Políticas</span><span class="evidence-pill">${icon('flask')}Simulação</span></div><button class="prompt-button" data-action="ask-shortcut" data-question="O que acontece se eu adicionar uma pessoa à equipe?">O que acontece com uma pessoa a mais? ${icon('arrow')}</button></section></div>
 <div class="pipeline"><span class="pipeline-label">Cada decisão tem um caminho.</span>${[['box', 'Dados validados'], ['chart', 'Previsão + incerteza'], ['flask', 'Simulação'], ['spark', 'Recomendação'], ['shield', 'Sua aprovação']].map(([i, l], idx) => `${idx ? '<span class="pipeline-arrow">→</span>' : ''}<span class="pipeline-step">${icon(i)}${l}</span>`).join('')}</div>`;
}
function demandPage() {
  const f = state.data.forecast.forecasts;
  const imp = state.models?.demand.feature_importance['30'] || [];
  const labels = {
    seasonal_day: 'Mesmo horário · dia anterior',
    seasonal_week: 'Sazonalidade semanal',
    lag_0: 'Último intervalo',
    lag_1: 'Intervalo anterior',
    lag_2: 'Lag de 60 minutos',
    rolling_4: 'Média das últimas 2h',
    rolling_12: 'Média das últimas 6h',
    rolling_48: 'Média das últimas 24h',
    hour_cos: 'Ciclo de horário',
    hour_sin: 'Ciclo de horário',
    promotion_known: 'Promoção anunciada',
    restaurant_id: 'Restaurante',
    capacity: 'Capacidade',
    staff: 'Equipe disponível'
  };
  return `${dateLine()}<section class="card section-gap"><div class="card-heading"><div><h2>O histórico encontra a previsão</h2><p>Os dados futuros observados ficam fora da consulta de inferência.</p></div>${chartLegend()}</div>${demandChart(true)}<div class="chart-bottom"><span>Intervalo conformal · calibração cronológica · cobertura nominal de 90%</span>${badge('Modelo treinado', '', 'check')}</div></section><div class="model-hero"><section class="card table-card"><div class="card-heading"><div><h2>Previsões para os próximos intervalos</h2><p>Contagens por meia hora; o horizonte de 60 min não é uma soma.</p></div></div><div class="table-wrap"><table><thead><tr><th>Horizonte</th><th>Previsão</th><th>Intervalo</th><th>Cobertura aberta¹</th></tr></thead><tbody>${f.map(x => `<tr><td><strong>${x.horizon_minutes} min</strong></td><td>${n(x.point, 1)}</td><td>${n(x.lower, 1)}–${n(x.upper, 1)}</td><td class="bad">${pct(x.empirical_coverage.open_coverage, 1)}</td></tr>`).join('')}</tbody></table></div><div class="body-padding small muted">¹ Cobertura empírica em horários de funcionamento no teste sintético. O agregado, que inclui horários fechados, é maior.</div></section><section class="card"><div class="card-heading"><div><h2>O que ajuda o modelo a prever</h2><p>Importância por permutação · validação · não é causalidade</p></div></div><div class="body-padding">${imp.slice(0, 6).map(x => `<div class="importance-row"><span>${e(labels[x.feature] || x.feature)}</span><div class="importance-track"><span style="width:${clamp(x.mae_increase / Math.max(imp[0]?.mae_increase || 1, .001) * 100, 0, 100)}%"></span></div><span>${n(x.mae_increase, 2)}</span></div>`).join('')}</div></section></div>${info('<strong>Incerteza exige contexto.</strong> Os intervalos têm cobertura inferior a 90% durante a operação. O modelo pode subestimar eventos atípicos; use o limite superior como teste de estresse, sem tratá-lo como garantia.', true)}<div class="pipeline"><span class="pipeline-label">Rastreabilidade</span><span class="pipeline-step mono">${e(f[0].model_version)}</span><span class="pipeline-step">Treino até 24/07 · calibração até 11/08</span><span class="pipeline-step">Origem: ${e(state.data.as_of)}</span></div>`;
}
function slider(id, label, value, min, max, step = 1, unit = '') {
  return `<div class="field"><label for="${id}">${e(label)}<output for="${id}" id="${id}-value">${n(value, step < 1 ? 1 : 0)}${e(unit)}</output></label><input id="${id}" name="${id}" type="range" min="${min}" max="${max}" step="${step}" value="${value}" data-unit="${e(unit)}"><div class="range-labels"><span>${min}${e(unit)}</span><span>${max}${e(unit)}</span></div></div>`;
}
function scenarioPage() {
  const d = state.data;
  const a = state.simulation?.input_alternative;
  const c = state.simulation?.changes || {};
  return `${dateLine()}<div class="split-panel"><form class="card controls-card" id="scenario-form"><div class="flex-row"><h2>Desenhe uma alternativa</h2>${badge('Hipóteses', 'purple')}</div><p>O cenário atual vem do replay e dos modelos.</p>${slider('staff', 'Pessoas na equipe', a?.staff || d.forecast.current.staff + 1, 1, 12)}${slider('kitchen_capacity', 'Capacidade física · pedidos/30 min', Math.round(a?.kitchen_capacity || d.restaurant.kitchen_capacity), 20, 140)}${slider('demand_multiplier', 'Multiplicador da demanda', c.demand_multiplier ?? 1, .5, 2, .1, '×')}${slider('stock_multiplier', 'Multiplicador do estoque', c.stock_multiplier ?? 1, 0, 3, .1, '×')}${slider('promotion', 'Promoção adicional', c.promotion ?? 0, 0, .6, .1)}<details><summary>Reposição e custos hipotéticos</summary><div class="field"><label for="replenishment_orders">Reposição · pedidos equivalentes</label><input type="number" id="replenishment_orders" name="replenishment_orders" value="${c.replenishment_orders ?? 0}" min="0" max="10000"><p class="field-hint">Equivalência pelo ingrediente limitante; não altera o estoque real.</p></div><div class="field"><label for="replenishment_after">Prazo · intervalos de 30 min</label><input type="number" name="replenishment_after" id="replenishment_after" value="${c.replenishment_after ?? 2}" min="1" max="24"></div><div class="field"><label for="wage_per_hour">Custo por pessoa/hora · R$</label><input type="number" name="wage_per_hour" id="wage_per_hour" value="${c.wage_per_hour ?? 24}" min="0" max="1000"></div><div class="field"><label for="backlog_cost">Atraso por pedido/intervalo · R$</label><input type="number" name="backlog_cost" id="backlog_cost" value="${c.backlog_cost ?? 8}" min="0" max="1000"></div><div class="field"><label for="stockout_cost">Estoque insuficiente · R$</label><input type="number" name="stockout_cost" id="stockout_cost" value="${c.stockout_cost ?? 15}" min="0" max="1000"></div></details><button class="btn primary" type="submit">${icon('flask')}Comparar cenários</button><p class="field-hint supported">${icon('shield')}Cálculos determinísticos. Sem LLM.</p></form><div>${state.simulation ? comparisonResult() : `<div class="card empty-state"><div class="empty-icon">${icon('flask')}</div><h2>Uma decisão. Mais possibilidades.</h2><p>Altere as hipóteses ao lado para comparar backlog, capacidade e custo. Os resultados serão calculados pela API.</p><div class="pill-row">${badge('Cenário atual')}${badge('Alternativa', 'purple')}</div></div>${info('Aumentar a equipe pode não reduzir a fila quando faltam ingredientes ou capacidade física.')}`}</div></div>`;
}
function comparisonResult() {
  const s = state.simulation;
  const max = Math.max(s.current.backlog, s.alternative.backlog, 1);
  return `<section class="card"><div class="comparison-head"><div><h2>Atual vs. alternativa</h2><small>Horizonte de 60 minutos · ${e(s.forecast_model)}</small></div>${badge('Simulado', '', 'check')}</div><div class="comparison-grid">${[['Cenário atual', s.current, ''], ['Sua alternativa', s.alternative, 'alt']].map(([label, r, cls]) => `<div class="comparison-column ${cls}">${badge(label, cls ? '' : 'neutral')}<div class="result-stat"><label>Backlog ao final</label><strong>${n(r.backlog, 1)}</strong><small>pedidos</small><div class="result-bar"><span style="width:${r.backlog / max * 100}%"></span></div></div><div class="result-stat"><label>Pedidos processados</label><strong>${n(r.processed, 1)}</strong></div><div class="result-stat"><label>Capacidade / 30 min</label><strong>${n(r.capacity_per_interval)}</strong></div><div class="result-stat"><label>Custo operacional hipotético</label><strong>${brl(r.total_cost)}</strong></div>${badge(r.stock_insufficient ? 'Estoque limita o cenário' : 'Estoque suficiente', r.stock_insufficient ? 'amber' : '')}</div>`).join('')}</div><div class="comparison-summary"><p>Impacto na fila<br><strong>${s.delta.backlog < 0 ? '−' : '+'}${n(Math.abs(s.delta.backlog), 1)} pedidos</strong></p><p>Variação de custo<br><strong>${s.delta.cost < 0 ? '−' : '+'}${brl(Math.abs(s.delta.cost))}</strong></p>${button('Criar proposta', 'propose', true, 'checks')}</div></section><section class="card sensitivity"><h3>${icon('pulse')}E se a demanda mudar?</h3><p class="tiny muted spacer-top">Sensibilidade da alternativa às hipóteses de demanda.</p><table><thead><tr><th>Demanda</th><th>Backlog</th><th>Custo hipotético</th></tr></thead><tbody>${s.sensitivity.map(r => `<tr><td>${pct(r.demand_multiplier)}</td><td>${n(r.backlog, 1)}</td><td>${brl(r.total_cost)}</td></tr>`).join('')}</tbody></table></section>${info(`A simulação ${e(s.id.slice(0, 8))} foi registrada com entradas, versão e resultados. Aprovar uma proposta registra uma decisão; não modifica estoque ou equipe.`)}`;
}
function inventoryPage() {
  return `${dateLine()}<div class="inventory-grid">${state.data.inventory.items.map((s, i) => `<section class="card stock-card"><div class="flex-row"><span class="ingredient-swatch">${['F', 'A', 'V', 'P'][i]}</span>${badge(s.critical ? 'Atenção' : 'Monitorado', s.critical ? 'amber' : '')}</div><h3>${e(s.name)}</h3><span class="tiny muted">Disponível no snapshot operacional</span><div class="stock-amount">${n(s.on_hand, 1)} <small>${e(s.unit)}</small></div><div class="stock-details"><span>Reserva de segurança</span><span>${n(s.safety_stock, 1)} ${e(s.unit)}</span></div><div class="stock-details"><span>Reposição prevista</span><span>${s.lead_minutes} min</span></div><div class="risk-meter"><span style="width:${s.probability * 100}%"></span></div><div class="risk-label"><span>Probabilidade de nível crítico</span><strong>${pct(s.probability)}</strong></div></section>`).join('')}</div><section class="card table-card"><div class="card-heading"><div><h2>Consumo, prazo e risco</h2><p>Previsor de demanda congelado antes do treino do classificador · inventory-v1</p></div>${badge('Classificador calibrado', 'purple')}</div>${stockTable()}</section>${info('O consumo usa receitas e mix esperado de produtos. A classificação considera risco antes da reposição; atrasos e mudanças de mix são fontes de erro. Quantidade disponível não é atualizada pela LLM.')}<section class="card body-padding"><h2>Uma regra ou um modelo?</h2><p class="small muted spacer-top">Comparação no mesmo teste cronológico de snapshots sintéticos. Custos dos erros: falso negativo R$ 60; falso positivo R$ 12.</p><div class="table-wrap spacer-top"><table><thead><tr><th>Estratégia</th><th>Precision</th><th>Recall</th><th>F1</th><th>PR-AUC</th><th>Brier ↓</th></tr></thead><tbody>${Object.entries(state.models?.inventory.models || {}).map(([k, v]) => `<tr class="${k === 'classifier' ? 'table-selected' : ''}"><td><strong>${e({
    rule: 'Regra determinística',
    classifier: 'Classificador',
    hybrid: 'Híbrida'
  }[k])}</strong></td><td>${pct(v.precision, 1)}</td><td>${pct(v.recall, 1)}</td><td>${n(v.f1, 3)}</td><td>${n(v.pr_auc, 3)}</td><td>${n(v.brier, 3)}</td></tr>`).join('')}</tbody></table></div></section>`;
}
function modelsPage() {
  const d = state.models?.demand;
  if (!d) return info('Relatório de ML indisponível. Execute o treinamento.');
  const champion = d.models.filter(x => x.selected);
  const monitoring = state.monitoring;
  return `${dateLine()}<div class="model-hero section-gap">${champion.map(c => `<section class="card model-box"><div class="model-title"><div><div class="eyebrow">DEMAND · ${c.horizon_minutes} MIN</div><h2>Gradient Boosting</h2></div>${badge('Champion', '', 'check')}</div><div class="metric-row"><div><label>MAE · pedidos</label><strong>${n(c.mae, 2)}</strong></div><div><label>RMSE · pedidos</label><strong>${n(c.rmse, 2)}</strong></div><div><label>WAPE</label><strong>${pct(c.wape, 1)}</strong></div></div><p>Teste cronológico isolado · ${n(c.n)} intervalos · ${e(c.model)}</p></section>`).join('')}</div><section class="card table-card section-gap"><div class="card-heading"><div><h2>O baseline também merece uma chance</h2><p>Mesmo conjunto e protocolo para todos os modelos · horizonte de 30 minutos</p></div>${badge('Menor MAE é melhor', 'neutral')}</div><div class="table-wrap"><table><thead><tr><th>Modelo</th><th>MAE validação</th><th>MAE teste</th><th>RMSE</th><th>WAPE</th><th>Status</th></tr></thead><tbody>${d.models.filter(c => c.horizon_minutes === 30).map(c => `<tr class="${c.selected ? 'table-selected' : ''}"><td><strong>${e({
    last: 'Último intervalo',
    moving_average: 'Média móvel · 2h',
    seasonal: 'Sazonal · horário/dia',
    ridge: 'Regressão Ridge',
    random_forest: 'Random Forest',
    gradient_boosting_15: 'Gradient Boosting · 15 folhas',
    gradient_boosting_31: 'Gradient Boosting · 31 folhas'
  }[c.model])}</strong></td><td>${n(c.validation_mae, 2)}</td><td>${n(c.mae, 2)}</td><td>${n(c.rmse, 2)}</td><td>${pct(c.wape, 1)}</td><td>${badge(c.selected ? 'Champion' : 'Comparado', c.selected ? '' : 'neutral')}</td></tr>`).join('')}</tbody></table></div></section><div class="model-hero"><section class="card body-padding"><h2>Monitorar a distribuição</h2><p class="small muted spacer-top">PSI · referência de treino vs. 7 dias recentes · restaurante selecionado</p><div class="spacer-top">${monitoring?.drift.features.map(x => `<div class="importance-row"><span>${e(x.feature)}</span><div class="importance-track"><span style="width:${clamp(x.psi / .3 * 100, 1, 100)}%"></span></div><span>${n(x.psi, 3)}</span></div>`).join('') || '<p class="muted">Carregando monitoramento…</p>'}</div><span class="tiny muted">Alerta heurístico em PSI &gt; 0,2; não prova mudança de conceito.</span></section><section class="card body-padding"><h2>Calibração não é uma garantia</h2><div class="metric-row spacer-top"><div><label>Cobertura nominal</label><strong>90%</strong></div><div><label>Empírica · aberto</label><strong class="bad">${pct(d.coverage['30'].open_coverage, 1)}</strong></div><div><label>Empírica · agregado</label><strong>${pct(d.coverage['30'].empirical, 1)}</strong></div></div><p class="small muted spacer-top">Horários fechados com demanda zero aumentam a cobertura agregada. Há um alerta de desempenho aberto; uma nova calibração precisa de outro período de avaliação.</p></section></div>${info(`Ledger local de experimentos disponível. MLflow: ${d.mlflow_available ? 'integração executada' : 'adaptador preparado, pacote indisponível neste ambiente; não executado'}. Versão selecionada por MAE de validação, com checksum e caminho de rollback.`)}<section class="card body-padding"><h2>Telemetria observada</h2><div class="metric-row spacer-top"><div><label>Requisições do processo</label><strong>${n(monitoring?.api.requests || 0)}</strong></div><div><label>Latência média · ms</label><strong>${n(monitoring?.api.mean_ms || 0, 1)}</strong></div><div><label>Inferências agregadas</label><strong>${n(monitoring?.inference.count || 0)}</strong></div><div><label>Abstenções do copiloto</label><strong>${n(monitoring?.copilot.abstentions || 0)}</strong></div></div><p class="tiny muted spacer-top">Métricas da execução local e do restaurante selecionado. A latência da API inclui uma janela do processo.</p></section>`;
}
function copilotPage() {
  const d = state.data;
  return `${dateLine()}<div class="chat-layout"><section class="card chat-card"><div class="chat-top"><div class="copilot-title"><span class="ai-symbol">${icon('spark')}</span><div><h2>TurnoLab Copilot</h2><small>Ferramentas tipadas · respostas fundamentadas</small></div></div>${badge('Templates offline', 'neutral', 'shield')}</div><div class="chat-log" id="chat-log">${state.messages.length ? state.messages.map(chatMessage).join('') : `<div class="chat-welcome"><span class="ai-symbol">${icon('spark')}</span><h2>O que vale investigar neste turno?</h2><p>Consulte a operação, teste uma hipótese ou abra a política que fundamenta uma recomendação.</p><div class="suggestions">${['Por que a demanda prevista está alta?', 'Quais ingredientes estão em risco?', 'O que acontece se eu adicionar uma pessoa à equipe?', 'Qual é a política de reposição de estoque?'].map(q => `<button data-action="ask" data-question="${e(q)}">${e(q)}</button>`).join('')}</div></div>`}${state.chatBusy ? `<div class="message-label">${icon('refresh')}Consultando ferramentas e documentos…</div>` : ''}</div><div class="chat-input"><form id="chat-form"><input name="question" aria-label="Pergunta ao copiloto" maxlength="1500" minlength="2" placeholder="Pergunte sobre demanda, equipe ou estoque…" required autocomplete="off" ${state.chatBusy ? 'disabled' : ''}><button type="submit" aria-label="Enviar pergunta" ${state.chatBusy ? 'disabled' : ''}>${icon('send')}</button></form><p>Modo offline usa templates e dados. Não é uma LLM local. Nenhuma ação é aprovada pelo agente.</p></div></section><aside class="card context-card"><h3>O contexto desta conversa</h3><div class="context-section"><div class="context-label">RESTAURANTE</div><div class="context-value">${e(d.restaurant.name)}</div><p>${e(d.restaurant.cuisine)} · ${e(d.restaurant.city)}</p></div><div class="context-section"><div class="context-label">PREVISÃO · PRÓXIMOS 30 MIN</div><div class="context-value">${n(d.forecast.forecasts[0].point, 1)} pedidos</div><p>Faixa ${n(d.forecast.forecasts[0].lower, 1)}–${n(d.forecast.forecasts[0].upper, 1)} · nominal 90%</p></div><div class="context-section"><div class="context-label">MODELO E ORIGEM</div><div class="context-value mono small">demand-v1</div><p>29/08/2026 · 18:00 UTC<br>Replay com dados sintéticos</p></div><div class="context-section"><div class="context-label">FONTES OPERACIONAIS</div>${['replenishment', 'peaks', 'capacity', 'governance'].map((id, i) => `<button class="citation" data-action="document" data-doc="${id}">${icon('document')}${['Reposição', 'Picos de pedidos', 'Capacidade', 'Governança'][i]}</button>`).join('')}</div><div class="context-section"><div class="context-label">CONTROLE HUMANO</div><p>O copiloto lê, simula e cria propostas pendentes. Aprovar é uma decisão sua.</p></div></aside></div>`;
}
function chatMessage(message) {
  if (message.role === 'user') return `<div class="chat-message user">${e(message.text)}</div>`;
  const r = message.result;
  if (message.error) return `<div class="info-banner warning" role="alert">${e(message.error)}</div>`;
  return `<div class="chat-message assistant"><div class="message-label">${icon('spark')}TurnoLab Copilot ${badge(r.blocked ? 'Solicitação bloqueada' : r.abstained ? 'Evidência insuficiente' : 'Fundamentado', r.blocked ? 'amber' : '', '')}${badge(r.generative ? 'Provedor externo' : 'Template offline', 'neutral')}</div><p>${e(r.answer)}</p>${r.facts?.length ? `<div class="fact-grid">${r.facts.map(f => `<div class="fact"><label>${e(f.label)}</label><strong>${typeof f.value === 'number' ? n(f.value, 1) : e(f.value)}</strong><small>${e(f.unit)}${f.interval ? ` · [${n(f.interval[0], 1)}, ${n(f.interval[1], 1)}]` : ''}</small><small>Fonte: ${e(f.source)}</small></div>`).join('')}</div>` : ''}${r.generative ? `<p>${e(r.interpretation)}</p>` : ''}<div class="citations">${r.citations?.map((c, i) => `<button class="citation" data-action="document" data-doc="${e(c.document_id)}">${icon('document')}[${i + 1}] ${e(c.title)}</button>`).join('') || ''}</div>${r.tools?.length ? `<details class="trace"><summary>${r.tools.length} ferramentas validadas · ${n(r.latency_ms, 0)} ms · abrir rastreabilidade</summary><ul>${r.tools.map(t => `<li><span class="mono">${e(t.tool)}</span> · ${n(t.latency_ms, 1)} ms · restaurante ${t.restaurant_id}</li>`).join('')}</ul><div>Prompt coordinator-v1 · ${e(r.architecture_note || '')}</div></details>` : ''}${r.proposal ? `<p class="supported">${icon('checks')}Proposta ${e(r.proposal.id.slice(0, 8))} criada como pendente. <a class="record-link" href="#actions">Abrir Action Center</a></p>` : ''}${r.warnings?.length ? `<p class="supported">${icon('warning')}A cobertura durante o funcionamento é inferior ao nível nominal.</p>` : ''}</div>`;
}
function actionsPage() {
  const items = state.actions?.items || [],
    audits = state.audit?.items || [];
  return `${dateLine()}<div class="kpi-grid">${kpi('Aguardando sua revisão', n(items.filter(a => a.status === 'pending').length), '', '<span>Propostas pendentes</span>', 'clock', 'orange')}${kpi('Aprovadas', n(items.filter(a => a.status === 'approved').length), '', '<span>Decisões registradas</span>', 'checks')}${kpi('Rejeitadas', n(items.filter(a => a.status === 'rejected').length), '', '<span>Hipóteses descartadas</span>', 'x', 'purple')}${kpi('Eventos recentes', n(audits.length), '', '<span>Últimos registros de auditoria</span>', 'shield')}</div><div class="flex-row section-gap"><h2>Propostas da operação</h2>${button('Atualizar', 'refresh-actions', false, 'refresh')}</div>${items.length ? items.map(a => `<section class="card action-card"><span class="ai-symbol">${icon(a.status === 'pending' ? 'flask' : 'checks')}</span><div class="action-main">${badge({
    pending: 'Aguardando revisão',
    approved: 'Aprovada',
    rejected: 'Rejeitada'
  }[a.status], {
    pending: 'amber',
    approved: '',
    rejected: 'neutral'
  }[a.status])}<h3>${e(a.title)}</h3><p>Proposta ${e(a.id.slice(0, 8))} · origem: ${e(a.created_by)} · ${e(a.created_at)}<br>Simulação ${e(a.simulation_id.slice(0, 8))}${a.decided_by ? ' · decisão: ' + e(a.decided_by) : ''}</p></div><div class="action-buttons"><button class="btn" data-action="view-simulation" data-id="${e(a.simulation_id)}">Ver cenário</button>${a.status === 'pending' ? `<button class="btn danger" data-action="decide" data-id="${e(a.id)}" data-decision="rejected">Rejeitar</button><button class="btn primary" data-action="decide" data-id="${e(a.id)}" data-decision="approved">${icon('check')}Aprovar</button>` : ''}</div></section>`).join('') : `<div class="card empty-state section-gap"><div class="empty-icon">${icon('checks')}</div><h2>As próximas decisões começam no laboratório.</h2><p>Compare um cenário e crie uma proposta para revisar os resultados antes de aprovar.</p><div class="spacer-top">${button('Abrir Scenario Lab', 'go-scenarios', true, 'flask')}</div></div>`}${info('Aprovação demonstrativa: registra status e responsável, sem alterar estoque, contratar equipe ou acionar serviços externos.')}<section class="card"><div class="card-heading section-gap"><div><h2>Um histórico para reconstruir decisões</h2><p>Entradas, versões e responsáveis conectados por identificadores</p></div>${badge('Append-only', 'neutral', 'shield')}</div>${audits.length ? audits.map(a => `<div class="audit-item"><span class="audit-node">${icon(a.event.includes('approved') ? 'check' : a.event.includes('rejected') ? 'x' : 'flask')}</span><div><strong>${e({
    'simulation.created': 'Simulação registrada',
    'proposal.created': 'Proposta criada',
    'proposal.approved': 'Proposta aprovada',
    'proposal.rejected': 'Proposta rejeitada'
  }[a.event] || a.event)}</strong><p>${e(a.actor)} · <span class="mono">${e(a.entity_id.slice(0, 8))}</span></p></div><span class="audit-time">${e(a.created_at)}</span></div>`).join('') : '<p class="body-padding small muted">Nenhum evento registrado para este restaurante.</p>'}</section>`;
}
function experimentsPage() {
  const r = state.experiments?.operational;
  const rag = state.experiments?.rag;
  const agents = state.experiments?.agents;
  return `${dateLine()}<section class="experiment-hypothesis"><div class="eyebrow">A PERGUNTA DO EXPERIMENTO</div><h2>Previsão, simulação e conhecimento ajudam a decidir melhor do que regras fixas?</h2><p>Mesmos cenários, mesma função de custo. RAG e copiloto não recebem crédito pelos cálculos do simulador.</p></section>${r?.strategies ? `<section class="card table-card section-gap"><div class="card-heading"><div><h2>Decisões sob teste</h2><p>${r.n_scenarios} cenários isolados de teste · custos hipotéticos · fluid-v1</p></div>${badge('Avaliação executada', '', 'check')}</div><div class="table-wrap"><table><thead><tr><th>Estratégia</th><th>Backlog médio ↓</th><th>Custo médio ↓</th><th>Suporte documental</th><th>Conformidade de política</th></tr></thead><tbody>${r.strategies.map(x => `<tr><td><strong>${e(x.label)}</strong></td><td>${n(x.mean_backlog, 1)}</td><td>${brl(x.mean_cost)}</td><td>${pct(x.document_support, 0)}</td><td>${pct(x.policy_compliance, 0)}</td></tr>`).join('')}</tbody></table></div><p class="chart-note spacer-top">${e(r.conclusion)}</p></section>` : info('O relatório operacional ainda não foi gerado. Execute python -m ml.experiments; os resultados aparecerão aqui.')}<div class="model-hero"><section class="card table-card"><div class="card-heading"><div><h2>Recuperação de conhecimento</h2><p>Avaliação de desenvolvimento · 19 perguntas respondíveis + 4 negativas</p></div></div><div class="table-wrap"><table><thead><tr><th>Recuperador</th><th>Hit@3</th><th>Precisão ref.</th><th>Abstenção</th></tr></thead><tbody>${['lexical', 'lsa', 'hybrid'].filter(k => rag?.[k]).map(k => `<tr class="${k === 'lexical' ? 'table-selected' : ''}"><td>${e({
    lexical: 'TF-IDF lexical',
    lsa: 'Projeção LSA',
    hybrid: 'Híbrido word/char'
  }[k])}</td><td>${pct(rag[k].hit_rate_at_3, 1)}</td><td>${pct(rag[k].reference_relevance_precision, 1)}</td><td>${pct(rag[k].correct_abstention)}</td></tr>`).join('')}</tbody></table></div><p class="chart-note spacer-top">A recuperação lexical foi mantida: precisão maior neste conjunto pequeno. LSA não é um modelo de embeddings pré-treinado.</p></section><section class="card body-padding"><h2>Papéis separados ou tool calling simples?</h2><p class="small muted spacer-top">Analysis, Knowledge e Coordinator são papéis determinísticos em um processo. A explicação não usa agentes autônomos.</p>${agents?.simple ? `<div class="metric-row spacer-top"><div><label>Tool calling · mediana</label><strong>${n(agents.simple.median_ms, 1)}<small class="tiny muted"> ms</small></strong></div><div><label>Papéis · mediana</label><strong>${n(agents.roles.median_ms, 1)}<small class="tiny muted"> ms</small></strong></div></div><p class="small muted spacer-top">${e(agents.conclusion)}</p>` : '<p class="small muted spacer-top">Comparação de orquestração ainda não executada.</p>'}</section></div>${info('Validade externa limitada: gerador, simulador e políticas foram escritos para este laboratório. As métricas não estimam impacto em restaurantes reais.', true)}`;
}
function settingsPage() {
  return `<section class="card body-padding settings-panel"><h2>Token da sessão</h2><p class="small muted spacer-top">Autenticação demonstrativa aplicada no backend. As contas não representam pessoas reais.</p><form id="token-form"><label for="token" class="small muted">Bearer token</label><input id="token" type="password" name="token" autocomplete="off" placeholder="Token da demonstração" required><button class="btn primary" type="submit">${icon('shield')}Usar token nesta sessão</button></form><p class="token-hint spacer-top">Conta de demonstração: <code>turnolab-demo</code><br>Conta restrita ao restaurante 2: <code>turnolab-other</code><br>O token é mantido apenas na sessão do navegador. Estes valores públicos são exclusivos do ambiente de portfólio.</p></section>${info('Este ambiente não possui credenciais de provedores externos. O copiloto funciona com templates e recuperação documental local.')}`;
}
async function loadInitial() {
  state.loading = true;
  state.error = null;
  render();
  try {
    const list = await api('/restaurants');
    state.restaurants = list.items;
    if (!list.items.some(r => r.id === state.rid)) state.rid = list.items[0].id;
    await loadData();
  } catch (err) {
    state.error = err.message;
  }
  state.loading = false;
  render();
}
async function loadData() {
  const results = await Promise.allSettled([api(scope('overview')), api('/models'), api('/experiments')]);
  if (results[0].status === 'rejected') throw results[0].reason;
  state.data = results[0].value;
  for (let i = 1; i < results.length; i++) {
    if (results[i].status === 'fulfilled') state[i === 1 ? 'models' : 'experiments'] = results[i].value;else toast(results[i].reason.message);
  }
  if (state.page === 'models') state.monitoring = await api(scope('monitoring'));
  if (state.page === 'actions') await loadActions();
}
async function loadActions() {
  const results = await Promise.allSettled([api(scope('actions') + '?limit=100'), api(scope('audit'))]);
  for (let i = 0; i < results.length; i++) {
    if (results[i].status === 'fulfilled') state[i === 0 ? 'actions' : 'audit'] = results[i].value;else throw results[i].reason;
  }
}
async function navigate(page) {
  if (page === 'content') {
    document.querySelector('#content')?.focus();
    return;
  }
  state.page = navs.some(x => x[0] === page) || page === 'settings' ? page : 'dashboard';
  state.menu = false;
  state.error = null;
  if (!state.data) {
    await loadInitial();
    return;
  }
  render();
  try {
    if (state.page === 'models') {
      state.monitoring = await api(scope('monitoring'));
      render();
    }
    if (state.page === 'actions') {
      await loadActions();
      render();
    }
  } catch (err) {
    toast(err.message);
  }
  window.scrollTo({
    top: 0,
    behavior: 'instant'
  });
}
async function sendQuestion(text) {
  if (state.chatBusy || !text.trim()) return;
  state.page = 'copilot';
  if (location.hash !== '#copilot') history.replaceState(null, '', '#copilot');
  state.messages.push({
    role: 'user',
    text
  });
  state.chatBusy = true;
  render();
  try {
    const result = await post(scope('copilot'), {
      message: text,
      architecture: 'simple'
    });
    state.messages.push({
      role: 'assistant',
      result
    });
  } catch (err) {
    state.messages.push({
      role: 'assistant',
      error: err.message
    });
  }
  state.chatBusy = false;
  render();
  const log = document.querySelector('#chat-log');
  if (log) log.scrollTop = log.scrollHeight;
  document.querySelector('#chat-form input')?.focus();
}
async function openDocument(id) {
  const doc = await api('/documents/' + encodeURIComponent(id));
  document.querySelector('#document-content').innerHTML = `<div class="eyebrow">CORPUS FICTÍCIO · DOCUMENTO OPERACIONAL</div><h2>${e(doc.title)}</h2>${badge('Referência verificável', '', 'document')}<pre>${e(doc.content)}</pre><code>SHA-256 · ${e(doc.sha256)}</code>`;
  document.querySelector('#document-dialog').showModal();
}
function exportEvidence() {
  const evidence = {
    restaurant: state.data.restaurant,
    forecast: state.data.forecast,
    inventory: state.data.inventory,
    simulation: state.simulation,
    as_of: state.data.as_of,
    notice: 'Synthetic data. No iFood affiliation.'
  };
  const blob = new Blob([JSON.stringify(evidence, null, 2)], {
    type: 'application/json'
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `turnolab-evidence-${state.rid}.json`;
  a.click();
  URL.revokeObjectURL(url);
  toast('Evidências exportadas com versão e origem.');
}
document.addEventListener('click', async event => {
  const close = event.target.closest('.dialog-close');
  if (close) {
    document.querySelector('#document-dialog').close();
    return;
  }
  const target = event.target.closest('[data-action]');
  if (!target) return;
  const action = target.dataset.action;
  try {
    if (action === 'menu') {
      state.menu = !state.menu;
      render();
    } else if (action === 'retry') await loadInitial();else if (action === 'settings') location.hash = 'settings';else if (action === 'go-scenarios') location.hash = 'scenarios';else if (action === 'alerts') location.hash = 'inventory';else if (action === 'help') await openDocument('governance');else if (action === 'export') exportEvidence();else if (action === 'ask-shortcut' || action === 'ask') await sendQuestion(target.dataset.question);else if (action === 'document') await openDocument(target.dataset.doc);else if (action === 'refresh-actions') {
      await loadActions();
      render();
    } else if (action === 'propose') {
      target.disabled = true;
      const proposal = await post(scope('actions'), {
        simulation_id: state.simulation.id
      });
      toast('Proposta ' + proposal.id.slice(0, 8) + ' criada. Aguardando revisão humana.');
      location.hash = 'actions';
    } else if (action === 'decide') {
      target.disabled = true;
      await post(scope('actions') + '/' + target.dataset.id + '/decision', {
        status: target.dataset.decision
      });
      await loadActions();
      render();
      toast(target.dataset.decision === 'approved' ? 'Aprovação registrada na auditoria.' : 'Rejeição registrada na auditoria.');
    } else if (action === 'view-simulation') {
      const list = await api(scope('simulations') + '?limit=100');
      const found = list.items.find(s => s.id === target.dataset.id);
      if (!found) throw Error('Simulação fora da janela atual. Consulte a API pelo histórico.');
      state.simulation = found.results;
      location.hash = 'scenarios';
    }
  } catch (err) {
    target.disabled = false;
    toast(err.message);
  }
});
document.addEventListener('change', async event => {
  if (event.target.id === 'restaurant-select') {
    state.rid = Number(event.target.value);
    state.loading = true;
    state.simulation = null;
    state.messages = [];
    state.actions = null;
    state.audit = null;
    render();
    try {
      await loadData();
    } catch (err) {
      state.error = err.message;
    }
    state.loading = false;
    render();
  }
});
document.addEventListener('input', event => {
  if (event.target.type === 'range') {
    const input = event.target;
    const output = document.getElementById(input.id + '-value');
    if (output) output.textContent = n(Number(input.value), Number(input.step) < 1 ? 1 : 0) + (input.dataset.unit || '');
  }
});
document.addEventListener('submit', async event => {
  if (event.target.id === 'chat-form') {
    event.preventDefault();
    await sendQuestion(new FormData(event.target).get('question'));
  } else if (event.target.id === 'scenario-form') {
    event.preventDefault();
    const btn = event.target.querySelector('button[type=submit]');
    btn.disabled = true;
    btn.innerHTML = icon('refresh') + 'Calculando…';
    const values = Object.fromEntries([...new FormData(event.target).entries()].map(([k, v]) => [k, Number(v)]));
    try {
      state.simulation = await post(scope('simulations'), values);
      render();
      toast('Comparação calculada e registrada.');
    } catch (err) {
      btn.disabled = false;
      btn.textContent = 'Comparar cenários';
      toast(err.message);
    }
  } else if (event.target.id === 'token-form') {
    event.preventDefault();
    sessionStorage.setItem('turnolab-token', new FormData(event.target).get('token'));
    state.data = null;
    state.actions = null;
    state.messages = [];
    state.simulation = null;
    state.page = 'dashboard';
    history.replaceState(null, '', '#dashboard');
    await loadInitial();
  }
});
window.addEventListener('hashchange', () => navigate(location.hash.slice(1)));
loadInitial();
