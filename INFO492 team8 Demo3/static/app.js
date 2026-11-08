// Team 8 Demo 3 — one URL; role-based sign-in; mobile-first flows.
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
let META = null, ME = null, TAB = null, OPEN = null, OPENED_AT = null;
let SIGNIN_PARTY = null;

const PARTIES = {
  sub: { label: 'Subcontractor', hint: 'Draft a site question before it goes to the GC', roles: ['foreman'] },
  gc: { label: 'General contractor', hint: 'Review RFIs and revision alerts', roles: ['site_manager', 'project_manager'] },
  design: { label: 'Design team', hint: 'Answer forwarded RFIs', roles: ['architect'] },
};

async function api(path, body) {
  const res = await fetch(path, body === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  const data = res.headers.get('Content-Type')?.includes('json') ? await res.json() : await res.text();
  if (!res.ok) throw new Error(data.error || 'Request failed');
  return data;
}
function toast(msg, bad) {
  const t = document.createElement('div'); t.className = 'toast' + (bad ? ' bad' : ''); t.textContent = msg;
  document.body.appendChild(t); setTimeout(() => t.remove(), 4200);
}
async function run(fn, btn) {
  if (btn) { btn.disabled = true; btn.dataset.label = btn.textContent; btn.textContent = 'Working…'; }
  try { return await fn(); } catch (e) { toast(e.message, true); } finally { if (btn) { btn.disabled = false; btn.textContent = btn.dataset.label; } }
}
const can = (a) => ME && ME.can.includes(a);
const roleTitle = (r) => META.roles[r]?.title || r;
const STATUS = { rough: 'Rough note', drafted: 'Draft suggested', submitted: 'Submitted to GC', returned: 'Returned to sub',
  cost_review: 'Waiting for PM (cost/scope)', forwarded: 'With architect', answered: 'Answered by architect', answered_by_gc: 'Answered by GC' };
const badge = (s) => `<span class="status s-${s}">${esc(STATUS[s] || s)}</span>`;

function usersForParty(party) {
  return META.users.filter((u) => PARTIES[party].roles.includes(u.role));
}

async function boot() {
  META = await api('/api/meta'); ME = META.me;
  const aiDot = META.ai.connected ? 'on' : 'off';
  const budget = META.ai.budget ? ` · AI today ${META.ai.budget.n}/${META.ai.budget.limit}` : '';
  $('#clock').innerHTML = `Addendum <b>${META.issued_through}</b> · <span class="ai-dot ${aiDot}" title="Gemini"></span>${META.ai.connected ? ' AI ready' : ' AI off'}${budget}`;
  if (!ME) return signIn();
  $('#who').innerHTML = `<span class="party p-${META.roles[ME.role].party}">${esc(roleTitle(ME.role))}</span> ${esc(ME.name)}
    <button class="link" type="button" id="help">Help</button> <button class="link" type="button" id="out">Sign out</button>`;
  $('#out').onclick = async () => { await api('/api/logout', {}); location.reload(); };
  $('#help').onclick = () => toast('Demo PINs are on the sign-in screen. Agents suggest only — you decide.');
  const tabs = ME.role === 'foreman' ? [['list', 'My RFIs'], ['new', '+ New RFI']]
    : ME.role === 'architect' ? [['queue', 'Queue'], ['list', 'RFIs']]
    : [['list', 'Inbox'], ['alerts', 'Alerts'], ...(can('metrics') ? [['panel', 'Metrics']] : [])];
  TAB = TAB || tabs[0][0];
  $('#main').innerHTML = `<nav class="tabs">${tabs.map(([k, l]) => `<button type="button" data-tab="${k}" class="${k === TAB ? 'on' : ''}">${l}</button>`).join('')}</nav><section id="view"></section>`;
  document.querySelectorAll('[data-tab]').forEach((b) => b.onclick = () => { TAB = b.dataset.tab; OPEN = null; boot(); });
  ({ list: listView, new: newView, alerts: alertsView, panel: panelView, queue: queueView })[TAB]();
}

function signIn() {
  $('#who').innerHTML = '';
  const stepParty = !SIGNIN_PARTY;
  const partyUsers = SIGNIN_PARTY ? usersForParty(SIGNIN_PARTY) : [];
  $('#main').innerHTML = `<section class="card narrow signin">
    <h2>Sign in</h2>
    <p class="muted">One link for everyone. Pick your role, then use the demo PIN from the README.</p>
    ${stepParty ? `<div class="party-pick">${Object.entries(PARTIES).map(([k, p]) =>
      `<button type="button" class="party-card" data-party="${k}"><b>${esc(p.label)}</b><span>${esc(p.hint)}</span></button>`).join('')}</div>`
      : `<button type="button" class="link back" id="back">← Change role</button>
        <div class="users">${partyUsers.map((u) => `<label class="user"><input type="radio" name="u" value="${u.id}">
          <span><b>${esc(u.name)}</b><br><small>${esc(u.company)}</small></span></label>`).join('')}</div>
        <div class="row pin-row"><input id="pin" type="password" inputmode="numeric" placeholder="Demo PIN" maxlength="8" autocomplete="off">
        <button type="button" id="go" class="primary">Sign in</button></div>
        <p class="muted pin-hint" id="pin-hint"></p>
        <details class="help-drawer"><summary>What do the agents do?</summary><ul>${Object.entries(META.agents).map(([k, a]) =>
          `<li><b>${k}</b>: ${esc(a.does)}</li>`).join('')}</ul></details>`}
  </section>`;
  if (stepParty) {
    document.querySelectorAll('[data-party]').forEach((b) => b.onclick = () => { SIGNIN_PARTY = b.dataset.party; signIn(); });
    return;
  }
  $('#back').onclick = () => { SIGNIN_PARTY = null; signIn(); };
  const showPin = () => {
    const u = document.querySelector('input[name=u]:checked');
    $('#pin-hint').textContent = u && META.demo_pins?.[u.value] ? `Demo PIN for this user: ${META.demo_pins[u.value]}` : 'Pick a user to see the demo PIN.';
  };
  document.querySelectorAll('input[name=u]').forEach((i) => i.onchange = showPin);
  if (partyUsers[0]) { partyUsers[0].id; document.querySelector(`input[value="${partyUsers[0].id}"]`).checked = true; }
  showPin();
  $('#go').onclick = (e) => run(async () => {
    const u = document.querySelector('input[name=u]:checked'); if (!u) throw new Error('Pick a user.');
    await api('/api/login', { user_id: u.value, pin: $('#pin').value }); SIGNIN_PARTY = null; TAB = null; boot();
  }, e.target);
}

// ------------------------------------------------------------------ lists
async function listView() {
  const rows = await api('/api/rfis');
  $('#view').innerHTML = `<div class="split"><div class="list">${rows.length ? rows.map((r) => `<button type="button" class="item ${OPEN === r.id ? 'on' : ''}" data-id="${r.id}">
      <span>${esc(r.id)} ${badge(r.status)}</span><b>${esc(r.title)}</b><small>${esc(r.created_by)} · ${r.needed_by ? 'by ' + esc(r.needed_by) : 'no date'}</small></button>`).join('')
    : `<p class="muted pad">${ME.role === 'foreman' ? 'No RFIs yet. Tap <b>+ New RFI</b>.' : 'Inbox empty.'}</p>`}</div>
    <div id="detail" class="detail"><p class="muted pad">Select an RFI</p></div></div>`;
  document.querySelectorAll('.item').forEach((b) => b.onclick = () => openRfi(b.dataset.id));
  if (OPEN) openRfi(OPEN);
}

async function openRfi(id) {
  if (OPEN !== id) OPENED_AT = performance.now();
  OPEN = id;
  document.querySelectorAll('.item').forEach((b) => b.classList.toggle('on', b.dataset.id === id));
  const { rfi, audit, alerts } = await api('/api/rfis/' + id);
  const parts = [`<h2>${esc(rfi.id)} ${badge(rfi.status)}</h2><p class="muted">Drawing set: Addendum ${rfi.drawing_set}${rfi.case_id ? ' · scenario ' + esc(rfi.case_id) : ''}</p>`];
  if (ME.role === 'foreman') parts.push(foremanPanel(rfi));
  else if (ME.role === 'architect') parts.push(architectPanel(rfi));
  else parts.push(gcPanel(rfi, alerts));
  parts.push(`<details class="audit"><summary>Audit trail (${audit.length})</summary><ol>${audit.map((m) =>
    `<li><code>${esc(m.at.slice(11, 19))}</code> <b>${esc(m.type)}</b> — ${m.from.kind === 'agent' ? '🤖 ' + esc(m.from.id) : esc(m.from.name)}</li>`).join('')}</ol></details>`);
  $('#detail').innerHTML = parts.join('');
  wire(rfi);
}

// ------------------------------------------------------------------ foreman stepper
function foremanPanel(r) {
  const d = r.draft, f = r.final || {}, editable = ['rough', 'drafted', 'returned'].includes(r.status);
  const step = !d && editable ? 1 : editable ? 2 : 3;
  const ret = r.status === 'returned' ? `<div class="note warn">GC returned this RFI — update and send again.</div>` : '';
  let html = `${ret}<nav class="steps" aria-label="Progress"><span class="${step >= 1 ? 'on' : ''}">1 Message</span><span class="${step >= 2 ? 'on' : ''}">2 Agent</span><span class="${step >= 3 ? 'on' : ''}">3 Send</span></nav>`;
  html += `<div class="card"><h3>From site</h3><p class="quote">${esc(r.rough.message)}</p><p class="muted">Sheets: ${esc(r.rough.sheets_as_written || '—')}</p></div>`;
  if (editable) {
    html += `<div class="card step-panel"><div class="row actions-primary">
      <button type="button" class="primary wide" data-act="draft-ai">Run draft agent</button></div>
      <details><summary>Checklist only (no AI)</summary><button type="button" data-act="draft-code">Run checklist</button></details></div>`;
  }
  if (d) {
    const src = (x) => x.source === 'message' ? '<span class="src ok">from message</span>' : '<span class="src miss">you fill in</span>';
    html += `<div class="card agent"><h3>Draft suggestion</h3>
      ${d.questions_for_sub.length ? `<div class="asks"><b>Answer these:</b><ul>${d.questions_for_sub.map((q) => `<li><b>${esc(q.field)}</b> — ${esc(q.ask)}</li>`).join('')}</ul></div>` : '<p class="ok">No gaps flagged.</p>'}
      <ul class="facts">${['location', 'needed_by', 'impact'].map((k) => `<li><b>${k}</b> ${src(d[k])} ${esc(d[k].value)}</li>`).join('')}</ul>
      <ul class="refs">${(d.references?.lookup || []).map((x) => `<li class="r-${x.status}">${esc(x.message)}</li>`).join('') || '<li>No sheets found</li>'}</ul></div>`;
  }
  if (editable) {
    const v = (k) => esc(f[k] || (d ? (typeof d[k] === 'object' ? (d[k].value === '(stated in the message)' ? '' : d[k].value) : d[k]) : '') || '');
    const refs = esc(f.references || d?.references?.text || r.rough.sheets_as_written || '');
    html += `<div class="card"><h3>RFI to send</h3>
      <label>Question<textarea id="f-question" rows="3">${esc(f.question || d?.question || r.rough.message)}</textarea></label>
      <div class="grid2"><label>Location<input id="f-location" value="${v('location')}"></label><label>Needed by<input id="f-needed_by" value="${v('needed_by')}" placeholder="YYYY-MM-DD"></label></div>
      <label>Impact<input id="f-impact" value="${v('impact')}"></label>
      <div class="grid2"><label>Sheets<input id="f-references" value="${refs}"></label><label>Title<input id="f-title" value="${v('title')}"></label></div>
      <label class="sr-only">Trade<input id="f-trade" value="${esc(f.trade || d?.trade || '')}"></label>
      <button type="button" class="primary wide" data-act="approve">Approve & send to GC</button></div>`;
  } else html += finalCard(r);
  return html;
}

function finalCard(r) {
  const f = r.final || {};
  return `<div class="card"><h3>RFI</h3><dl>${['title', 'question', 'location', 'needed_by', 'impact', 'references']
    .map((k) => `<dt>${k.replace('_', ' ')}</dt><dd>${esc(f[k]) || '—'}</dd>`).join('')}</dl>
    ${r.response ? `<div class="note ok"><b>Answer:</b> ${esc(r.response.text)}</div>` : ''}</div>`;
}

// ------------------------------------------------------------------ GC
function gcPanel(r, alerts) {
  let html = finalCard(r);
  if (!r.final) return html + '<p class="muted">Waiting for the foreman to submit.</p>';
  alerts.filter((a) => a.status === 'open').forEach((a) => html += `<div class="note warn">watch_agent: ${esc(a.message)}</div>`);
  const c = r.check;
  if (['submitted', 'cost_review'].includes(r.status)) {
    html += `<div class="card gc-tools"><button type="button" class="primary wide" data-act="check-ai">Run check agent</button>
      <details><summary>Checklist only</summary><button type="button" data-act="check-code">Run checklist</button></details>
      <span class="muted">Review time: <b id="timer">0</b>s</span></div>`;
  }
  if (c) html += `<div class="card agent"><h3>Check result</h3>
    <p><b>${esc({ return_to_sub: 'Return to sub', gc_can_answer: 'GC can answer', forward_to_design: 'Forward to architect' }[c.recommendation])}</b></p>
    <ul class="refs">${c.findings.map((x) => `<li>${esc(x.message)}</li>`).join('') || '<li>No issues</li>'}</ul></div>`;
  if (r.status === 'submitted' && (can('return') || can('forward'))) {
    html += `<div class="card gc-decide" id="gc-decide"><h3>Your decision</h3>
      <label>Note<textarea id="note" rows="2" placeholder="Required to return or answer"></textarea></label>
      <div class="gc-actions"><button type="button" data-act="return">Return</button><button type="button" data-act="answer">Answer</button><button type="button" class="primary" data-act="forward">Forward</button></div></div>`;
  }
  if (r.status === 'cost_review' && can('ack_cost')) html += `<div class="card"><button type="button" class="primary wide" data-act="ack_cost">PM sign-off → forward</button></div>`;
  return html;
}

function architectPanel(r) {
  let html = finalCard(r);
  if (r.status === 'forwarded') html += `<div class="card"><h3>Response</h3><textarea id="answer" rows="4"></textarea>
    <button type="button" class="primary wide" data-act="respond">Send answer</button></div>`;
  return html;
}

async function queueView() {
  const q = await api('/api/triage');
  $('#view').innerHTML = `<div class="card"><h2>Queue</h2><ol class="queue">${q.map((x) => `<li><button type="button" class="link" data-id="${x.rfi_id}">${esc(x.rfi_id)}</button> — ${esc(x.title)}</li>`).join('') || '<li class="muted">Empty</li>'}</ol></div><div id="detail" class="detail"></div>`;
  document.querySelectorAll('.queue [data-id]').forEach((b) => b.onclick = () => { TAB = 'list'; OPEN = b.dataset.id; boot(); });
}

function wire(r) {
  const timer = $('#timer');
  if (timer) { const t = setInterval(() => { if (!document.body.contains(timer)) return clearInterval(t); timer.textContent = Math.round((performance.now() - OPENED_AT) / 1000); }, 500); }
  document.querySelectorAll('[data-act]').forEach((b) => b.onclick = () => run(async () => {
    const a = b.dataset.act, path = `/api/rfis/${r.id}/`;
    if (a === 'draft-ai' || a === 'draft-code') await api(path + 'draft', { use_ai: a === 'draft-ai' });
    if (a === 'check-ai' || a === 'check-code') await api(path + 'check', { use_ai: a === 'check-ai' });
    if (a === 'approve') await api(path + 'approve', Object.fromEntries(['title', 'question', 'location', 'needed_by', 'impact', 'references', 'trade'].map((k) => [k, $('#f-' + k).value])));
    if (['return', 'answer', 'forward'].includes(a)) await api(path + a, { note: $('#note').value, review_seconds: (performance.now() - OPENED_AT) / 1000 });
    if (a === 'ack_cost') await api(path + 'ack_cost', {});
    if (a === 'respond') await api(path + 'respond', { answer: $('#answer').value });
    toast('Saved.'); OPEN = r.id;
    if (TAB === 'queue') { await queueView(); return openRfi(r.id); }
    listView();
  }, b));
}

function newView() {
  $('#view').innerHTML = `<div class="card narrow"><h2>New RFI</h2>
    <label>Test scenario<select id="case"><option value="">Write my own</option>
      ${META.cases.map((c) => `<option value="${c.case_id}">${c.case_id}: ${esc(c.title)}</option>`).join('')}</select></label>
    <div id="own"><label>Site message<textarea id="msg" rows="4" placeholder="Like a text to the GC…"></textarea></label>
      <div class="grid2"><label>Sheets<input id="sheets" placeholder="E-301"></label>
      <label>Drawing set<select id="set">${[...Array(META.issued_through + 1).keys()].map((n) => `<option value="${n}" ${n === META.issued_through ? 'selected' : ''}>${n ? 'Addendum ' + n : 'Bid set'}</option>`).join('')}</select></label></div></div>
    <button type="button" class="primary wide" id="create">Create RFI</button></div>`;
  $('#case').onchange = () => $('#own').style.display = $('#case').value ? 'none' : '';
  $('#create').onclick = (e) => run(async () => {
    const r = await api('/api/rfis', { case_id: $('#case').value, message: $('#msg').value, sheets_as_written: $('#sheets').value, drawing_set: +$('#set').value });
    TAB = 'list'; OPEN = r.id; boot();
  }, e.target);
}

async function alertsView() {
  const al = await api('/api/alerts');
  $('#view').innerHTML = `<div class="card"><h2>Revision alerts</h2>
    ${can('run_watcher') ? '<button type="button" class="primary" id="next">Issue next addendum</button>' : ''}
    <table><tr><th>RFI</th><th>Alert</th><th></th></tr>${al.map((a) => `<tr><td>${esc(a.rfi_id)}</td><td>${esc(a.message)}</td>
      <td>${a.status === 'open' ? `<button type="button" data-k="${esc(a.key)}" data-v="useful">OK</button><button type="button" data-k="${esc(a.key)}" data-v="wrong">Wrong</button>` : esc(a.status)}</td></tr>`).join('') || '<tr><td colspan="3" class="muted">None</td></tr>'}</table></div>`;
  document.querySelectorAll('[data-k]').forEach((b) => b.onclick = () => run(async () => { await api('/api/alerts/' + encodeURIComponent(b.dataset.k), { verdict: b.dataset.v }); alertsView(); }, b));
  if ($('#next')) $('#next').onclick = (e) => run(async () => { const o = await api('/api/watch/next', {}); toast(o.message); boot(); }, e.target);
}

async function panelView() {
  const p = await api('/api/panel');
  const ev = p.offline_eval;
  const tile = (label, value, sub) => `<div class="tile"><span>${esc(label)}</span><b>${value ?? '—'}</b>${sub ? `<small>${esc(sub)}</small>` : ''}</div>`;
  $('#view').innerHTML = `<div class="card"><h2>Control panel</h2><div class="tiles">
      ${tile('RFIs', p.rfis)} ${tile('Returns', p.round_trips.returns)} ${tile('AI today', p.ai_calls.n + '/' + p.ai_calls.limit)}
      ${tile('False-alarm marks', p.watch_agent.marked_wrong, p.watch_agent.alerts + ' alerts')}
    </div>
    ${ev ? `<p class="muted">Offline eval: ${esc(ev.conditions?.[2]?.needs_return_after ?? '')} still need return (draft agent)</p>` : ''}
    <div class="row"><button type="button" id="next">Issue addendum</button>
      <a class="button" href="/api/export/rfi_log.csv">Export log</a>
      <button type="button" id="wipe" class="danger">Reset demo</button></div></div>`;
  $('#next').onclick = (e) => run(async () => { toast((await api('/api/watch/next', {})).message); boot(); }, e.target);
  $('#wipe').onclick = (e) => run(async () => { if (!confirm('Clear all RFIs on this server?')) return; await api('/api/reset', {}); location.reload(); }, e.target);
}

boot().catch((e) => { $('#main').innerHTML = `<p class="pad">Could not load: ${esc(e.message)}</p>`; });
