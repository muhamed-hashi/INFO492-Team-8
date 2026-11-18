// Team 8 Demo 4 — RFI Exchange front end. One URL, role-based sign-in, Demo 3 RFI flow plus Demo 4 close-out.
// Plain JS, no build step. Every view renders into #main (or #view inside it) from the JSON API in app.py.

// ------------------------------------------------------------------ helpers
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const pill = (text, tone = '') => `<span class="pill ${tone ? 'tone-' + tone : ''}">${esc(text)}</span>`;
const empty = (html) => `<div class="empty"><p>${html}</p></div>`;

async function api(path, body) {
  const res = await fetch(path, body === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  const data = res.headers.get('Content-Type')?.includes('json') ? await res.json() : await res.text();
  if (!res.ok) throw new Error(data.error || 'Request failed');
  return data;
}

function toast(msg, bad) {
  const t = document.createElement('div');
  t.className = 'toast' + (bad ? ' bad' : '');
  t.textContent = msg;
  $('#toasts').appendChild(t);
  setTimeout(() => t.remove(), 4200);
}

// Runs an async action with the button disabled; errors become a red toast.
async function run(fn, btn) {
  const label = btn?.textContent;
  if (btn) { btn.disabled = true; btn.textContent = 'Working…'; }
  try { return await fn(); } catch (e) { toast(e.message, true); } finally { if (btn?.isConnected) { btn.disabled = false; btn.textContent = label; } }
}
const onClick = (sel, fn) => $$(sel).forEach((b) => b.onclick = () => run(() => fn(b), b));

// ------------------------------------------------------------------ state + vocabulary
let META = null, ME = null, TAB = null, OPEN = null, OPENED_AT = null;
let SIGNIN_PARTY = null, CO_OPEN = null, CO_FILTER = 'attention', LANDED = false;

const PARTIES = {
  sub: { label: 'Subcontractor', hint: 'Draft a site question before it goes to the GC', roles: ['foreman'] },
  gc: { label: 'General contractor', hint: 'Review RFIs, revision alerts and RFI close-out', roles: ['site_manager', 'project_manager'] },
  design: { label: 'Design team', hint: 'Answer forwarded RFIs and close-out questions', roles: ['architect'] },
};
const FIELDS = { title: 'Title', question: 'Question', location: 'Location', needed_by: 'Needed by', impact: 'Impact', references: 'Sheets' };

const STATUS = {
  rough: ['Rough note', ''], drafted: ['Draft suggested', 'violet'], submitted: ['Submitted to GC', 'info'],
  returned: ['Returned to sub', 'warn'], cost_review: ['Waiting for PM (cost/scope)', 'warn'], forwarded: ['With architect', 'info'],
  answered: ['Answered by architect', 'ok'], answered_by_gc: ['Answered by GC', 'ok'],
};
const CO_STATUS = {
  answered: ['Answered, not closed', ''], closed: ['Closed', 'ok'], kept_open: ['Kept open (IFC)', 'info'],
  asked_architect: ['Asked architect', 'violet'], architect_replied: ['Architect replied', 'violet'],
};
const CO_REC = { ok_to_close: ['OK to close', 'ok'], keep_open: ['Keep open', 'info'], hold: ['Hold', 'bad'], check: ['Check', 'warn'] };
const CHECK_REC = { return_to_sub: 'Return to sub', gc_can_answer: 'GC can answer', forward_to_design: 'Forward to architect' };
const CO_DECISION = { close: 'closed the RFI', keep_open: 'kept it open (carry to IFC set)', ask_architect: 'asked the architect' };

const fromMap = (map) => (k, prefix = '') => { const [label, tone] = map[k] || [k, '']; return pill(prefix + label, tone); };
const badge = fromMap(STATUS);
const coBadge = fromMap(CO_STATUS);
const rec = (r, who) => r ? fromMap(CO_REC)(r, who ? who + ': ' : '') : '';

const can = (a) => ME?.can.includes(a);
const roleTitle = (r) => META.roles[r]?.title || r;
const usersForParty = (party) => META.users.filter((u) => PARTIES[party].roles.includes(u.role));

function auditTrail(audit) {
  return `<details class="audit"><summary>Audit trail (${audit.length})</summary><ol>${audit.map((m) =>
    `<li><code>${esc(m.at.slice(11, 19))}</code> <b>${esc(m.type)}</b> — ${m.from.kind === 'agent' ? 'agent ' + esc(m.from.id) : esc(m.from.name)}</li>`).join('')}</ol></details>`;
}

// ------------------------------------------------------------------ shell
async function boot() {
  META = await api('/api/meta'); ME = META.me;
  const ai = META.ai;
  $('#status-line').innerHTML = `<span>Drawings through <b>Addendum ${META.issued_through}</b></span>
    <span><span class="ai-dot ${ai.connected ? 'on' : 'off'}"></span>${ai.connected ? 'AI ready' : 'AI off'}${ai.budget ? ` · ${ai.budget.n}/${ai.budget.limit}` : ''}</span>`;
  if (!ME) return LANDED ? signIn() : landing();

  $('#who').innerHTML = `<span class="party p-${META.roles[ME.role].party}">${esc(roleTitle(ME.role))}</span><span class="who-name">${esc(ME.name)}</span>
    <button class="link" type="button" id="help">Help</button><button class="link" type="button" id="out">Sign out</button>`;
  $('#out').onclick = async () => { await api('/api/logout', {}); location.reload(); };
  $('#help').onclick = () => toast('Agents only suggest and cite their evidence. You make every decision.');

  const tabs = ME.role === 'foreman' ? [['list', 'My RFIs'], ['new', 'New RFI']]
    : ME.role === 'architect' ? [['queue', 'Queue'], ['list', 'RFIs'], ['closeout', 'Close-out questions']]
    : [['list', 'Inbox'], ['alerts', 'Alerts'], ['closeout', 'Close-out'], ...(can('metrics') ? [['panel', 'Metrics']] : [])];
  if (!tabs.some(([k]) => k === TAB)) TAB = tabs[0][0];
  $('#main').innerHTML = `<nav class="tabs" role="tablist">${tabs.map(([k, l]) =>
    `<button type="button" role="tab" data-tab="${k}" class="${k === TAB ? 'on' : ''}" aria-selected="${k === TAB}">${l}</button>`).join('')}</nav><section id="view"></section>`;
  $$('[data-tab]').forEach((b) => b.onclick = () => { TAB = b.dataset.tab; OPEN = null; boot(); });
  ({ list: listView, new: newView, alerts: alertsView, panel: panelView, queue: queueView, closeout: closeoutView })[TAB]();
}

function landing() {
  $('#who').innerHTML = '';
  const steps = [
    ['Subcontractor', 'Draft', 'A rough message from site becomes a clear RFI. The draft agent asks for what is missing (room, date, impact) and never fills it in itself.'],
    ['General contractor', 'Check', 'The check agent looks up every sheet against the latest addenda and recommends answer, forward or return.'],
    ['Design team', 'Answer', 'The architect answers forwarded RFIs; the triage agent orders the queue by urgency.'],
    ['General contractor', 'Close out', 'Before an answered RFI is closed, the close-out agent checks that every drawing the answer promised was actually issued.'],
  ];
  $('#main').innerHTML = `<section class="landing">
    <div class="hero">
      <div class="eyebrow">Team 8 · INFO 492 · Demo 4</div>
      <h1>RFI Exchange</h1>
      <p class="lead">One RFI, three parties, one agent each. The agents read, check and cite their evidence; at every step a person decides.</p>
      <button type="button" class="primary" id="enter">Sign in by role →</button>
    </div>
    <div class="flow">${steps.map(([who, what, txt], i) => `<div class="card"><span class="num">${i + 1}</span>
      <small class="muted">${who}</small><h3>${what}</h3><p>${txt}</p></div>`).join('')}</div>
    <div class="card"><h3>Built on real project documents</h3>
      <p>RFIs, answers and drawing lists from the Dett Elementary School Annex and Renovations (Public Building Commission of Chicago, Addenda 1–6, 2023): 108 answered RFIs and 412 issued drawings. Shaped by an assistant PM at a St. Louis general contractor, who tested Demo #3.</p>
      <p class="muted small"><a href="https://github.com/muhamed-hashi/INFO492-Team-8" target="_blank" rel="noopener">GitHub</a> · <a href="https://muhamed-hashi.github.io/INFO492-Team-8/" target="_blank" rel="noopener">Team site</a></p></div>
  </section>`;
  $('#enter').onclick = () => { LANDED = true; signIn(); };
}

function signIn() {
  $('#who').innerHTML = '';
  if (!SIGNIN_PARTY) {
    $('#main').innerHTML = `<section class="card narrow signin">
      <button type="button" class="link" id="home">← Home</button>
      <h2>Sign in</h2><p class="muted">One link for everyone. Pick your side of the project.</p>
      <div class="party-pick">${Object.entries(PARTIES).map(([k, p]) => `<button type="button" class="party-card" data-party="${k}">
        <span class="party p-${k}">${esc(p.label)}</span><div><span class="hint">${esc(p.hint)}</span></div></button>`).join('')}</div>
    </section>`;
    $('#home').onclick = () => { LANDED = false; landing(); };
    $$('[data-party]').forEach((b) => b.onclick = () => { SIGNIN_PARTY = b.dataset.party; signIn(); });
    return;
  }
  const users = usersForParty(SIGNIN_PARTY);
  $('#main').innerHTML = `<section class="card narrow signin">
    <button type="button" class="link" id="back">← Change role</button>
    <h2>Sign in as ${esc(PARTIES[SIGNIN_PARTY].label.toLowerCase())}</h2>
    <div class="users">${users.map((u, i) => `<label class="user"><input type="radio" name="u" value="${u.id}" ${i ? '' : 'checked'}>
      <span><b>${esc(u.name)}</b><br><small>${esc(roleTitle(u.role))} · ${esc(u.company)}</small></span></label>`).join('')}</div>
    <form class="row" id="pin-form"><input id="pin" type="password" inputmode="numeric" placeholder="Demo PIN" maxlength="8" autocomplete="off" aria-label="Demo PIN">
      <button type="submit" id="go" class="primary">Sign in</button></form>
    <p class="muted pin-hint" id="pin-hint"></p>
    <details><summary>What do the agents do?</summary><ul class="small">${Object.entries(META.agents).map(([k, a]) =>
      `<li><b>${esc(k)}</b>: ${esc(a.does)}</li>`).join('')}</ul></details>
  </section>`;
  $('#back').onclick = () => { SIGNIN_PARTY = null; signIn(); };
  const showPin = () => {
    const u = $('input[name=u]:checked');
    $('#pin-hint').textContent = u && META.demo_pins?.[u.value] ? `Demo PIN for this user: ${META.demo_pins[u.value]}` : 'Pick a user to see the demo PIN.';
  };
  $$('input[name=u]').forEach((i) => i.onchange = showPin);
  showPin();
  $('#pin').focus();
  $('#pin-form').onsubmit = (e) => {
    e.preventDefault();
    run(async () => {
      const u = $('input[name=u]:checked'); if (!u) throw new Error('Pick a user.');
      await api('/api/login', { user_id: u.value, pin: $('#pin').value });
      SIGNIN_PARTY = null; TAB = null; boot();
    }, $('#go'));
  };
}

// ------------------------------------------------------------------ RFI list + detail
async function listView() {
  const rows = await api('/api/rfis');
  const none = ME.role === 'foreman' ? 'No RFIs yet. Open <b>New RFI</b> to start one.' : 'Inbox empty.';
  $('#view').innerHTML = `<div class="split"><div class="list">${rows.map((r) => `<button type="button" class="item ${OPEN === r.id ? 'on' : ''}" data-id="${r.id}">
      <span class="item-top">${esc(r.id)} ${badge(r.status)}</span><b>${esc(r.title)}</b>
      <small>${esc(r.created_by)} · ${r.needed_by ? 'needed by ' + esc(r.needed_by) : 'no date'}</small></button>`).join('') || empty(none)}</div>
    <div id="detail">${empty('Select an RFI')}</div></div>`;
  $$('.item').forEach((b) => b.onclick = () => openRfi(b.dataset.id));
  if (OPEN) openRfi(OPEN);
}

async function openRfi(id) {
  if (OPEN !== id) OPENED_AT = performance.now();
  OPEN = id;
  $$('.item').forEach((b) => b.classList.toggle('on', b.dataset.id === id));
  const { rfi, audit, alerts } = await api('/api/rfis/' + id);
  const panel = ME.role === 'foreman' ? foremanPanel(rfi) : ME.role === 'architect' ? architectPanel(rfi) : gcPanel(rfi, alerts);
  $('#detail').innerHTML = `<div class="detail-head"><h2>${esc(rfi.id)} ${badge(rfi.status)}</h2>
    <p class="muted small">Drawing set: ${rfi.drawing_set ? 'Addendum ' + rfi.drawing_set : 'Bid set'}${rfi.case_id ? ' · scenario ' + esc(rfi.case_id) : ''}</p></div>
    ${panel}${auditTrail(audit)}`;
  wire(rfi);
}

function finalCard(r) {
  const f = r.final || {};
  return `<div class="card"><h3>RFI</h3><dl>${Object.entries(FIELDS).map(([k, l]) => `<dt>${l}</dt><dd>${esc(f[k]) || '—'}</dd>`).join('')}</dl>
    ${r.response ? `<div class="note ok" style="margin:14px 0 0"><b>Answer:</b> ${esc(r.response.text)}</div>` : ''}</div>`;
}

// Foreman: message → draft agent → approve & send.
function foremanPanel(r) {
  const d = r.draft, f = r.final || {}, editable = ['rough', 'drafted', 'returned'].includes(r.status);
  const step = !d && editable ? 1 : editable ? 2 : 3;
  let html = r.status === 'returned' ? '<div class="note warn">The GC returned this RFI. Update it and send again.</div>' : '';
  html += `<ol class="stepper" aria-label="Progress">${['Message', 'Draft agent', 'Send'].map((s, i) =>
    `<li class="${step > i ? 'on' : ''}">${i + 1} · ${s}</li>`).join('')}</ol>`;
  html += `<div class="card"><h3>From site</h3><p class="quote">${esc(r.rough.message)}</p><p class="muted small">Sheets: ${esc(r.rough.sheets_as_written || '—')}</p></div>`;
  if (editable) {
    html += `<div class="card"><button type="button" class="primary wide" data-act="draft-ai">Run draft agent</button>
      <details><summary>Checklist only (no AI)</summary><button type="button" data-act="draft-code">Run checklist</button></details></div>`;
  }
  if (d) {
    const src = (x) => x.source === 'message' ? '<span class="src ok">from message</span>' : '<span class="src miss">you fill in</span>';
    html += `<div class="card agent"><h3>Draft suggestion</h3>
      ${d.questions_for_sub.length ? `<div class="asks"><b>Answer these:</b><ul>${d.questions_for_sub.map((q) => `<li><b>${esc(FIELDS[q.field] || q.field)}</b> — ${esc(q.ask)}</li>`).join('')}</ul></div>` : '<p class="ok">No gaps flagged.</p>'}
      <ul class="facts">${['location', 'needed_by', 'impact'].map((k) => `<li>${src(d[k])}<b>${FIELDS[k]}:</b> ${esc(d[k].value)}</li>`).join('')}</ul>
      <ul class="refs">${(d.references?.lookup || []).map((x) => `<li class="r-${x.status}">${esc(x.message)}</li>`).join('') || '<li>No sheets found</li>'}</ul></div>`;
  }
  if (!editable) return html + finalCard(r);
  const v = (k) => esc(f[k] || (d ? (typeof d[k] === 'object' ? (d[k].value === '(stated in the message)' ? '' : d[k].value) : d[k]) : '') || '');
  const refs = esc(f.references || d?.references?.text || r.rough.sheets_as_written || '');
  return html + `<div class="card"><h3>RFI to send</h3>
    <label>Question<textarea id="f-question" rows="3">${esc(f.question || d?.question || r.rough.message)}</textarea></label>
    <div class="grid2"><label>Location<input id="f-location" value="${v('location')}"></label><label>Needed by<input id="f-needed_by" value="${v('needed_by')}" placeholder="YYYY-MM-DD"></label></div>
    <label>Impact<input id="f-impact" value="${v('impact')}"></label>
    <div class="grid2"><label>Sheets<input id="f-references" value="${refs}"></label><label>Title<input id="f-title" value="${v('title')}"></label></div>
    <input id="f-trade" type="hidden" value="${esc(f.trade || d?.trade || '')}">
    <button type="button" class="primary wide" data-act="approve">Approve & send to GC</button></div>`;
}

// GC: check agent → return / answer / forward (PM signs off on cost/scope).
function gcPanel(r, alerts) {
  let html = finalCard(r);
  if (!r.final) return html + '<p class="muted">Waiting for the foreman to submit.</p>';
  alerts.filter((a) => a.status === 'open').forEach((a) => html += `<div class="note warn"><b>watch_agent:</b> ${esc(a.message)}</div>`);
  const c = r.check;
  if (['submitted', 'cost_review'].includes(r.status)) {
    html += `<div class="card"><button type="button" class="primary wide" data-act="check-ai">Run check agent</button>
      <details><summary>Checklist only (no AI)</summary><button type="button" data-act="check-code">Run checklist</button></details>
      <span class="timer">Review time: <b id="timer">0</b>s</span></div>`;
  }
  if (c) {
    html += `<div class="card agent"><h3>Check result</h3><p><b>${esc(CHECK_REC[c.recommendation] || c.recommendation)}</b></p>
      <ul class="refs">${c.findings.map((x) => `<li>${esc(x.message)}</li>`).join('') || '<li>No issues</li>'}</ul></div>`;
    // After peer feedback: when the checklist and the AI disagree, say so instead of silently returning.
    const blocking = c.findings.filter((x) => x.blocking);
    if (c.recommendation === 'return_to_sub' && blocking.length && blocking.every((x) => x.source === 'AI')) {
      html += `<div class="note warn"><b>The agents disagree.</b> Every required field is filled in (the sub's draft and the checklist pass it), but the AI judged a field not specific enough.
        A return costs a full round trip with the sub (our stakeholder: often a day or two). Read the reason and decide; you can still forward or answer.</div>`;
    }
  }
  if (r.status === 'submitted' && (can('return') || can('forward'))) {
    html += `<div class="card"><h3>Your decision</h3>
      <label>Note<textarea id="note" rows="2" placeholder="Required to return or answer"></textarea></label>
      <div class="actions"><button type="button" data-act="return">Return to sub</button><button type="button" data-act="answer">Answer</button><button type="button" class="primary" data-act="forward">Forward to architect</button></div></div>`;
  }
  if (r.status === 'cost_review' && can('ack_cost')) html += `<div class="card"><button type="button" class="primary wide" data-act="ack_cost">PM sign-off → forward</button></div>`;
  return html;
}

function architectPanel(r) {
  let html = finalCard(r);
  if (r.status === 'forwarded') html += `<div class="card"><h3>Response</h3><label class="sr-only" for="answer">Response</label><textarea id="answer" rows="4"></textarea>
    <div class="row"><button type="button" class="primary wide" data-act="respond">Send answer</button></div></div>`;
  return html;
}

function wire(r) {
  const timer = $('#timer');
  if (timer) {
    const t = setInterval(() => { if (!timer.isConnected) return clearInterval(t); timer.textContent = Math.round((performance.now() - OPENED_AT) / 1000); }, 500);
  }
  onClick('[data-act]', async (b) => {
    const a = b.dataset.act, path = `/api/rfis/${r.id}/`;
    if (a === 'draft-ai' || a === 'draft-code') await api(path + 'draft', { use_ai: a === 'draft-ai' });
    if (a === 'check-ai' || a === 'check-code') await api(path + 'check', { use_ai: a === 'check-ai' });
    if (a === 'approve') await api(path + 'approve', Object.fromEntries([...Object.keys(FIELDS), 'trade'].map((k) => [k, $('#f-' + k).value])));
    if (['return', 'answer', 'forward'].includes(a)) await api(path + a, { note: $('#note').value, review_seconds: (performance.now() - OPENED_AT) / 1000 });
    if (a === 'ack_cost') await api(path + 'ack_cost', {});
    if (a === 'respond') await api(path + 'respond', { answer: $('#answer').value });
    toast('Saved.');
    OPEN = r.id;
    if (TAB === 'queue') { TAB = 'list'; return boot(); }
    listView();
  });
}

// ------------------------------------------------------------------ other tabs
async function queueView() {
  const q = await api('/api/triage');
  $('#view').innerHTML = `<div class="card narrow" style="margin-left:0"><h2>Queue</h2><p class="muted small">Ordered by the triage agent, most urgent first.</p>
    <ol class="queue">${q.map((x) => `<li><button type="button" class="link" data-id="${x.rfi_id}">${esc(x.rfi_id)}</button> — ${esc(x.title)}</li>`).join('') || '<li class="muted">Empty</li>'}</ol></div>`;
  $$('.queue [data-id]').forEach((b) => b.onclick = () => { TAB = 'list'; OPEN = b.dataset.id; boot(); });
}

function newView() {
  const sets = [...Array(META.issued_through + 1).keys()];
  $('#view').innerHTML = `<div class="card narrow" style="margin-left:0"><h2>New RFI</h2><p class="muted small">Write it like a text to the GC. The draft agent turns it into a clear RFI next.</p>
    <label>Test scenario<select id="case"><option value="">Write my own</option>
      ${META.cases.map((c) => `<option value="${c.case_id}">${c.case_id}: ${esc(c.title)}</option>`).join('')}</select></label>
    <div id="own"><label>Site message<textarea id="msg" rows="4" placeholder="e.g. Panel LP-2 on E-301 clashes with the duct in room 114, where do we move it?"></textarea></label>
      <div class="grid2"><label>Sheets<input id="sheets" placeholder="E-301"></label>
      <label>Drawing set<select id="set">${sets.map((n) => `<option value="${n}" ${n === META.issued_through ? 'selected' : ''}>${n ? 'Addendum ' + n : 'Bid set'}</option>`).join('')}</select></label></div></div>
    <button type="button" class="primary wide" id="create">Create RFI</button></div>`;
  $('#case').onchange = () => $('#own').hidden = !!$('#case').value;
  onClick('#create', async () => {
    const r = await api('/api/rfis', { case_id: $('#case').value, message: $('#msg').value, sheets_as_written: $('#sheets').value, drawing_set: +$('#set').value });
    TAB = 'list'; OPEN = r.id; boot();
  });
}

async function alertsView() {
  const al = await api('/api/alerts');
  $('#view').innerHTML = `<div class="card"><div class="row" style="justify-content:space-between;margin-top:0"><div><h2>Revision alerts</h2>
      <p class="muted small">The watch agent flags open RFIs whose sheets changed in a newer addendum.</p></div>
      ${can('run_watcher') ? '<button type="button" class="primary" id="next">Issue next addendum</button>' : ''}</div>
    <div class="table-wrap"><table><tr><th>RFI</th><th>Alert</th><th>Verdict</th></tr>${al.map((a) => `<tr><td><code>${esc(a.rfi_id)}</code></td><td>${esc(a.message)}</td>
      <td>${a.status === 'open' ? `<div class="actions"><button type="button" data-k="${esc(a.key)}" data-v="useful">Useful</button><button type="button" data-k="${esc(a.key)}" data-v="wrong">Wrong</button></div>`
        : pill(a.status, a.status === 'useful' ? 'ok' : 'bad')}</td></tr>`).join('') || '<tr><td colspan="3" class="muted">No alerts.</td></tr>'}</table></div></div>`;
  onClick('[data-k]', async (b) => { await api('/api/alerts/' + encodeURIComponent(b.dataset.k), { verdict: b.dataset.v }); alertsView(); });
  onClick('#next', async () => { toast((await api('/api/watch/next', {})).message); boot(); });
}

// ------------------------------------------------------------------ close-out (Demo 4)
const needsAttention = (x) => x.code !== 'ok_to_close' || (x.agent && x.agent !== 'ok_to_close') || ['asked_architect', 'architect_replied'].includes(x.status);
const CO_FILTERS = {
  attention: ['Needs a look', needsAttention],
  answered: ['Not closed yet', (x) => x.status !== 'closed'],
  closed: ['Closed', (x) => x.status === 'closed'],
  all: ['All', () => true],
};

async function closeoutView() {
  const all = await api('/api/closeout');
  const isArch = ME.role === 'architect';
  const rows = isArch ? all : all.filter(CO_FILTERS[CO_FILTER][1]);
  const intro = isArch ? 'Questions from the GC before they close an RFI you answered.'
    : `The project's real RFI log (Dett Annex, Addenda 1–6): ${all.length} answered RFIs. Before the PM closes one, the close-out agent checks that every drawing change the answer promised was actually issued.`;
  const chips = isArch ? '' : `<div class="chips">${Object.entries(CO_FILTERS).map(([k, [label, f]]) =>
    `<button type="button" class="chip ${CO_FILTER === k ? 'on' : ''}" data-f="${k}">${label} <span class="n">${all.filter(f).length}</span></button>`).join('')}</div>`;
  $('#view').innerHTML = `<p class="intro">${intro}</p>${chips}
    <div class="split"><div class="list">${rows.map((x) => `<button type="button" class="item ${CO_OPEN === x.id ? 'on' : ''}" data-co="${x.id}">
      <span class="item-top">${esc(x.id.replace('Dett-', ''))} ${coBadge(x.status)}</span>
      <b>${esc(x.question.slice(0, 90))}${x.question.length > 90 ? '…' : ''}</b>
      <small>${rec(x.code, 'Code')} ${rec(x.agent, 'Agent')}</small></button>`).join('') || empty('Nothing here.')}</div>
    <div id="codetail">${empty('Select an RFI')}</div></div>`;
  $$('[data-f]').forEach((b) => b.onclick = () => { CO_FILTER = b.dataset.f; closeoutView(); });
  $$('[data-co]').forEach((b) => b.onclick = () => openCloseout(b.dataset.co));
  if (CO_OPEN && rows.some((x) => x.id === CO_OPEN)) openCloseout(CO_OPEN);
}

function reasonsList(res) {
  const ev = Object.fromEntries((res.evidence || []).map((e) => [e.text, e]));
  return `<ul class="refs">${(res.reasons || []).map((t) => ev[t]
    ? `<li class="r-current">${esc(t)} <a href="${esc(ev[t].url)}" target="_blank" rel="noopener">Open PDF page ↗</a></li>`
    : `<li class="r-not_in_index">${esc(t)}</li>`).join('')}</ul>`;
}

async function openCloseout(id) {
  CO_OPEN = id;
  $$('[data-co]').forEach((b) => b.classList.toggle('on', b.dataset.co === id));
  const d = await api('/api/closeout/' + id);
  const parts = [`<div class="detail-head"><h2>${esc(d.id)} ${coBadge(d.status)}</h2>
    <p class="muted small">RFI ${esc(d.rfi_no)} · answered in Addendum ${d.addendum} · <a href="${esc(d.source_url)}" target="_blank" rel="noopener">source PDF, page ${esc(d.pdf_page || '')} ↗</a></p></div>
    <div class="card"><h3>Question <small>from a bidder</small></h3><p>${esc(d.question)}</p><h3 style="margin-top:14px">Architect's answer</h3><p class="quote">${esc(d.response)}</p></div>`];

  if (ME.role === 'architect') {
    parts.push(`<div class="card"><h3>GC's question before close-out</h3><p class="quote">${esc(d.query?.text || '')}</p>
      ${d.reply ? `<div class="note ok" style="margin:12px 0 0"><b>Your reply:</b> ${esc(d.reply.text)}</div>` : ''}
      ${d.status === 'asked_architect' ? `<label style="margin-top:12px">Reply<textarea id="co-reply" rows="3"></textarea></label><button type="button" class="primary" data-coact="reply">Send reply</button>` : ''}</div>`);
  } else {
    const c = d.code, a = d.agent;
    parts.push(`<div class="card"><h3>Code check <small>no AI: keywords + drawing-list lookup</small></h3><p>${rec(c.recommendation)}</p>${reasonsList(c)}</div>`);
    if (a) {
      parts.push(`<div class="card agent"><h3>Close-out agent <small>AI reads the answer · code verifies every sheet</small></h3>
        <p>${rec(a.recommendation)} <span class="muted small">The answer commits to: <b>${esc(a.commitment.replaceAll('_', ' '))}</b></span></p>
        <dl><dt>Revised sheets</dt><dd>${esc((a.revised_sheets || []).join(', ') || '—')}</dd>
            <dt>Only referred to</dt><dd>${esc((a.referenced_only || []).join(', ') || '—')}</dd></dl>
        ${reasonsList(a)}
        ${(a.guard || []).length ? `<div class="note warn" style="margin:12px 0 0"><b>Guard:</b> ${a.guard.map(esc).join(' ')}</div>` : ''}
        ${a.ai_reason ? `<p class="muted small" style="margin-top:10px">${esc(a.ai_reason)}</p>` : ''}</div>`);
    }
    if (can('closeout_review') && d.status !== 'closed') {
      parts.push(`<div class="card"><button type="button" class="primary wide" data-coact="agent">${a ? 'Run close-out agent again' : 'Run close-out agent'}</button></div>`);
    }
    if (d.reply) parts.push(`<div class="note ok"><b>Architect replied:</b> ${esc(d.reply.text)}</div>`);
    if (d.decision) {
      const x = d.decision;
      parts.push(`<div class="note ${x.override ? 'warn' : 'ok'}"><b>${esc(x.by)}</b> ${esc(CO_DECISION[x.decision])}${x.override ? " against the agent's advice" : ''}${x.note ? ' — “' + esc(x.note) + '”' : ''}</div>`);
    }
    if (can('close_rfi') && d.status !== 'closed') {
      parts.push(`<div class="card"><h3>Your decision <small>the agent only recommends</small></h3>
        <label>Note<textarea id="co-note" rows="2" placeholder="Required to close against the advice, or to ask the architect"></textarea></label>
        <div class="actions"><button type="button" data-codec="ask_architect">Ask architect</button><button type="button" data-codec="keep_open">Keep open</button><button type="button" class="primary" data-codec="close">Close RFI</button></div></div>`);
    } else if (!can('close_rfi')) parts.push('<p class="muted small">Only the project manager can close an RFI.</p>');
    parts.push(auditTrail(d.audit));
  }

  $('#codetail').innerHTML = parts.join('');
  onClick('[data-coact]', async (b) => {
    if (b.dataset.coact === 'agent') await api(`/api/closeout/${id}/agent`, {});
    if (b.dataset.coact === 'reply') await api(`/api/closeout/${id}/reply`, { answer: $('#co-reply').value });
    toast('Saved.'); closeoutView();
  });
  onClick('[data-codec]', async (b) => {
    await api(`/api/closeout/${id}/decide`, { decision: b.dataset.codec, note: $('#co-note').value });
    toast('Decision recorded.'); closeoutView();
  });
}

// ------------------------------------------------------------------ metrics (PM)
function coEvalTable(ev) {
  const pct = (x) => x && x[1] ? `${x[0]}/${x[1]} (${Math.round(100 * x[0] / x[1])}%)` : '—';
  const table = (title, entry) => {
    const m = Object.keys(entry).filter((k) => entry[k]?.right);
    const name = (k) => k === 'code_only' ? 'Code only' : k.replace('agent_run', 'Agent run ');
    const row = (t, f) => `<tr><td>${t}</td>${m.map((k) => `<td>${f(entry[k])}</td>`).join('')}</tr>`;
    return `<div class="table-wrap"><table><tr><th>${esc(title)}</th>${m.map((k) => `<th>${name(k)}</th>`).join('')}</tr>
      ${row('Right recommendation', (x) => pct(x.right))}
      ${row('Missed problems (closed too early)', (x) => pct(x.missed_problems))}
      ${row('False alarms', (x) => pct(x.false_alarms))}</table></div>`;
  };
  const r = ev.real_log || {};
  const parts = [];
  if (r.labeled) parts.push(table(`Real Dett RFIs vs. hand labels (${r.labeled} of ${r.rfis})`, r.vs_hand_labels));
  else if (r.rfis) parts.push(`<p class="muted">Real Dett log: ${r.rfis} RFIs, code stops ${r.rfis - (r.flags.code_only.ok_to_close || 0)}. Hand labels not in yet.</p>`);
  Object.entries(ev.other_sets || {}).forEach(([n, e]) => parts.push(table(`${n} (${e.cases} cases)`, e)));
  return parts.join('');
}

async function panelView() {
  const p = await api('/api/panel');
  const co = p.closeout, ev = p.offline_eval;
  const tile = (label, value, sub) => `<div class="tile"><span>${esc(label)}</span><b>${value ?? '—'}</b>${sub ? `<small>${esc(sub)}</small>` : ''}</div>`;
  $('#view').innerHTML = `<div class="card"><h2>Control panel</h2><p class="muted small">Live counts on this server.</p>
    <h3 style="margin-top:16px">RFI exchange</h3><div class="tiles">
      ${tile('RFIs', p.rfis)} ${tile('Returns to sub', p.round_trips.returns)} ${tile('AI calls today', p.ai_calls.n + ' / ' + p.ai_calls.limit)}
      ${tile('False-alarm marks', p.watch_agent.marked_wrong, p.watch_agent.alerts + ' alerts')}</div>
    <h3>Close-out <small>real Dett RFI log</small></h3><div class="tiles">
      ${tile('Answered RFIs', co.log_rfis)} ${tile('Flagged by code', co.code_flags)}
      ${tile('Agent checks', co.agent_checks, co.agent_flags + ' flagged')}
      ${tile('Closed', co.closed, co.overrides + ' against advice')} ${tile('Kept open / asked', co.kept_open + ' / ' + co.asked_architect)}</div>
    ${co.eval ? coEvalTable(co.eval) : '<p class="muted">Close-out evaluation not run yet (scripts/run_demo4_eval.py).</p>'}
    ${ev ? `<p class="muted small">Offline eval: ${esc(ev.conditions?.[2]?.needs_return_after ?? '')} still need return (draft agent)</p>` : ''}
    <div class="row" style="margin-top:18px"><button type="button" id="next">Issue next addendum</button>
      <a class="button" href="/api/export/rfi_log.csv">Export log (CSV)</a>
      <button type="button" id="wipe" class="danger">Reset demo</button></div></div>`;
  onClick('#next', async () => { toast((await api('/api/watch/next', {})).message); boot(); });
  onClick('#wipe', async () => { if (!confirm('Clear all RFIs on this server?')) return; await api('/api/reset', {}); location.reload(); });
}

boot().catch((e) => { $('#main').innerHTML = `<p class="pad">Could not load: ${esc(e.message)}</p>`; });
