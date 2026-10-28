import test from 'node:test';
import assert from 'node:assert/strict';
import { escapeHTML, number, percent, pathFrom, clamp } from '../utils.js';
test('untrusted text is escaped before interpolation', () => {
  assert.equal(escapeHTML('<img src=x onerror="alert(1)">'), '&lt;img src=x onerror=&quot;alert(1)&quot;&gt;');
});
test('numbers and percentages follow the Portuguese locale', () => {
  assert.equal(number(1234.25, 1), '1.234,3');
  assert.equal(percent(.8237, 1), '82,4%');
});
test('chart coordinates remain finite and rounded', () => {
  assert.equal(pathFrom([[0, 10.3333], [20, 0]]), 'M0.00,10.33 L20.00,0.00');
  assert.equal(clamp(-10, 0, 100), 0);
});
