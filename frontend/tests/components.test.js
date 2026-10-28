import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import * as utils from '../utils.js';
const fixture = JSON.parse(readFileSync(new URL('../../.data/ui_fixture.json', import.meta.url)));
const source = readFileSync(new URL('../app.js', import.meta.url), 'utf8').replace(/^import[\s\S]*?from\s+['"]\.\/utils\.js['"];?\n/, 'const {escapeHTML:e,number:n,percent:pct,currency:brl,timeLabel,pathFrom,clamp}=utils;\n').replace(/loadInitial\(\);\s*$/, '');
const document = {
  addEventListener() {},
  querySelector() {
    return {
      innerHTML: ''
    };
  }
};
const build = new Function('utils', 'document', 'location', 'sessionStorage', 'window', source + '\nreturn {state,views:{dashboard,demandPage,scenarioPage,copilotPage,inventoryPage,modelsPage,actionsPage,experimentsPage,settingsPage}};');
const app = build(utils, document, {
  hash: ''
}, {
  getItem() {
    return null;
  }
}, {
  addEventListener() {}
});
Object.assign(app.state, fixture, {
  restaurants: fixture.restaurants.items,
  loading: false
});
for (const [name, render] of Object.entries(app.views)) test('component renders ' + name + ' from measured API fixture', () => {
  const html = render();
  assert.equal(typeof html, 'string');
  assert.ok(html.length > 300);
  assert.ok(!html.includes('NaN'));
  assert.ok(!html.includes('undefined'));
});
test('backend-originated names are escaped in overview', () => {
  const name = app.state.data.restaurant.name;
  app.state.data.restaurant.name = '<img onerror="alert(1)">';
  const html = app.views.copilotPage();
  assert.ok(!html.includes('<img onerror'));
  assert.ok(html.includes('&lt;img'));
  app.state.data.restaurant.name = name;
});
