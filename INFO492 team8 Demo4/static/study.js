// Timed review study: each reviewer sees every RFI once, half as the rough message and half agent-drafted
// (which half depends on whether the reviewer number is odd or even). Times and decisions go to runtime/study.csv.
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const FIELDS = { title: 'Title', question: 'Question', location: 'Location', needed_by: 'Needed by', impact: 'Impact', references: 'Sheets' };
let items = [], i = 0, reviewer = 0, t0 = 0;

function start() {
  $('#s').innerHTML = `<div class="card"><h2>Before you start</h2>
    <p>You are the GC's site manager. For each RFI, decide as quickly as you can: is it clear enough to send to the architect, or would you go back to the subcontractor first?</p>
    <p class="muted">The timer starts when the RFI appears and stops when you click a decision. Please don't pause in the middle of an RFI.</p>
    <form id="go-form"><label>Your reviewer number (ask the team)<input id="rev" type="number" min="1" max="99" required></label>
    <button class="primary" type="submit">Start</button></form></div>`;
  $('#go-form').onsubmit = async (e) => {
    e.preventDefault();
    reviewer = +$('#rev').value; if (!reviewer) return;
    const data = await (await fetch('/api/study/items?reviewer=' + reviewer)).json();
    items = data.items;
    if (!items.length) { $('#s').innerHTML = '<div class="card">No study items yet. The team needs to run scripts/run_demo3_eval.py first.</div>'; return; }
    i = 0; show();
  };
}

function show() {
  if (i >= items.length) { $('#s').innerHTML = '<div class="card"><h2>Thank you!</h2><p>All your reviews are saved.</p></div>'; return; }
  const it = items[i], r = it.rfi;
  const body = it.condition === 'raw'
    ? `<p class="quote big">${esc(r.message)}</p><p class="muted small">Sheets: ${esc(r.sheets || '—')}</p>`
    : `<dl class="big">${Object.entries(FIELDS).map(([k, l]) => `<dt>${l}</dt><dd>${esc(r[k]) || '—'}</dd>`).join('')}</dl>`;
  $('#s').innerHTML = `<p class="muted small">RFI ${i + 1} of ${items.length}</p>
    <div class="progress"><span style="width:${(100 * i) / items.length}%"></span></div>
    <div class="card">${body}</div>
    <label>Why? (optional)<input id="why"></label>
    <div class="actions"><button data-d="go_back">Go back to the sub first</button><button class="primary" data-d="send_on">Clear enough — send to architect</button></div>`;
  t0 = performance.now();
  document.querySelectorAll('[data-d]').forEach((b) => b.onclick = async () => {
    const seconds = (performance.now() - t0) / 1000;
    document.querySelectorAll('[data-d]').forEach((x) => x.disabled = true);
    await fetch('/api/study/record', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reviewer, item_id: it.item_id, condition: it.condition, seconds, decision: b.dataset.d, reason: $('#why').value }) });
    i++; show();
  });
}
start();
