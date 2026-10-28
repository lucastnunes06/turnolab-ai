export const escapeHTML = v => String(v ?? '').replace(/[&<>"']/g, c => ({
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;'
})[c]);
export const number = (v, d = 0) => Number(v ?? 0).toLocaleString('pt-BR', {
  maximumFractionDigits: d,
  minimumFractionDigits: d
});
export const percent = (v, d = 0) => number(Number(v) * 100, d) + '%';
export const currency = v => Number(v ?? 0).toLocaleString('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  maximumFractionDigits: 0
});
export const timeLabel = s => String(s).slice(11, 16);
export const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
export const finite = x => typeof x === 'number' && Number.isFinite(x);
export const pathFrom = points => points.map((p, i) => (i ? 'L' : 'M') + p.map(x => Number(x).toFixed(2)).join(',')).join(' ');
