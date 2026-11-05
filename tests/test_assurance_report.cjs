const assert = require('node:assert/strict');
const fs = require('node:fs');
const { JSDOM, VirtualConsole } = require('jsdom');
const errors = [];
const virtualConsole = new VirtualConsole();
virtualConsole.on('jsdomError', error => errors.push(error.message));
let printed = false, downloaded = false;
const dom = new JSDOM(fs.readFileSync('security/evidence/readiness.html', 'utf8'), {
  runScripts: 'dangerously', virtualConsole,
  beforeParse(window) {
    window.HTMLDialogElement.prototype.showModal = function () { this.open = true; };
    window.HTMLDialogElement.prototype.close = function () { this.open = false; };
    window.URL.createObjectURL = () => 'blob:test-artifact';
    window.URL.revokeObjectURL = () => {};
    window.HTMLAnchorElement.prototype.click = function () { downloaded = Boolean(this.download); };
    window.print = () => { printed = true; };
  },
});
const { document: d, Event } = dom.window;
const data = JSON.parse(d.getElementById('assurance-data').textContent);
const byId = id => d.getElementById(id);
assert.equal(d.querySelectorAll('.assessment').length, data.assessments.length);
assert.equal(d.querySelectorAll('.artifact').length, data.artifacts.length);
assert.match(byId('release-detail').textContent, /acceptance remain pending/);
byId('category').value = 'HTTP probes';
byId('category').dispatchEvent(new Event('change'));
const httpFindings = data.findings.filter(f => f.category === 'HTTP probes');
assert.equal(d.querySelectorAll('#finding-rows tr').length, Math.min(8, httpFindings.length));
byId('search').value = 'a-finding-that-does-not-exist-43712';
byId('search').dispatchEvent(new Event('input'));
assert.equal(byId('finding-page').textContent, '0 matching findings');
assert.ok(byId('next').disabled);
byId('search').value = '';
byId('category').value = '';
byId('category').dispatchEvent(new Event('change'));
if (data.findings.length > 8) {
  byId('next').click();
  assert.match(byId('finding-page').textContent, /^9[–-]/);
  byId('previous').click();
  assert.match(byId('finding-page').textContent, /^1[–-]/);
}
d.querySelector('.artifact').click();
assert.equal(byId('artifact-dialog').open, true);
assert.ok(byId('dialog-hash').textContent.match(/^[a-f0-9]{64}$/));
byId('download-artifact').click();
assert.ok(downloaded);
byId('close-dialog').click();
assert.equal(byId('artifact-dialog').open, false);
downloaded = false;
byId('export').click();
assert.ok(downloaded);
byId('print').click();
assert.ok(printed);
assert.deepEqual(errors, []);
dom.window.close();
console.log('Assurance report: filters, pagination, evidence dialog, downloads, and print passed.');
