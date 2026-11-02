// Team 8 Demo 3 front end. One page; what you see depends on the signed-in role.
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
let META = null, ME = null, TAB = null, OPEN = null, OPENED_AT = null;

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

async function boot() {
  META = await api('/api/meta'); ME = META.me;
  $('#clock').innerHTML = `Simulated project date <b>${META.today}</b> (Dett data is from 2023) · drawings issued through <b>Addendum ${META.issued_through}</b> · AI ${META.ai.connected ? '<b>connected</b>' : '<b class="warn">not connected</b>'}`;
  if (!ME) return signIn();
  $('#who').innerHTML = `<span class="party p-${META.roles[ME.role].party}">${esc(roleTitle(ME.role))}</span> ${esc(ME.name)} · ${esc(ME.company)} <button class="link" id="out">Sign out</button>`;
  $('#out').onclick = async () => { await api('/api/logout', {}); location.reload(); };
  const tabs = ME.role === 'foreman' ? [['list', 'My RFIs'], ['new', 'New RFI']]
    : ME.role === 'architect' ? [['queue', 'Triage queue'], ['list', 'All forwarded']]
    : [['list', 'Inbox'], ['alerts', 'Revision alerts'], ...(can('metrics') ? [['panel', 'Control panel']] : [])];
  TAB = TAB || tabs[0][0];
  $('#main').innerHTML = `<nav class="tabs">${tabs.map(([k, l]) => `<button data-tab="${k}" class="${k === TAB ? 'on' : ''}">${l}</button>`).join('')}</nav><section id="view"></section>`;
  document.querySelectorAll('[data-tab]').forEach((b) => b.onclick = () => { TAB = b.dataset.tab; OPEN = null; boot(); });
  ({ list: listView, new: newView, alerts: alertsView, panel: panelView, queue: queueView })[TAB]();
}

function signIn() {
  $('#who').innerHTML = '';
  $('#main').innerHTML = `<section class="card narrow"><h2>Sign in</h2>
    <p class="muted">Each person signs in with their role. What you can see and do depends on that role. Demo PINs are in the README.</p>
    <div class="users">${META.users.map((u) => `<label class="user"><input type="radio" name="u" value="${u.id}">
      <span><b>${esc(u.name)}</b><br><span class="party p-${META.roles[u.role].party}">${esc(roleTitle(u.role))}</span><br><small>${esc(u.company)}</small></span></label>`).join('')}</div>
    <div class="row"><input id="pin" type="password" inputmode="numeric" placeholder="PIN" maxlength="8"><button id="go" class="primary">Sign in</button></div>
    <details><summary>Who are the agents?</summary><ul>${Object.entries(META.agents).map(([k, a]) => `<li><b>${k}</b> (${esc(META.roles[a.acts_for].title)}): ${esc(a.does)}</li>`).join('')}</ul></details></section>`;
  $('#go').onclick = (e) => run(async () => {
    const u = document.querySelector('input[name=u]:checked'); if (!u) throw new Error('Pick a user.');
    await api('/api/login', { user_id: u.value, pin: $('#pin').value }); TAB = null; boot();
  }, e.target);
}

// ------------------------------------------------------------------ lists
async function listView() {
  const rows = await api('/api/rfis');
  $('#view').innerHTML = `<div class="split"><div class="list">${rows.length ? rows.map((r) => `<button class="item ${OPEN === r.id ? 'on' : ''}" data-id="${r.id}">
      <span>${esc(r.id)} ${badge(r.status)}</span><b>${esc(r.title)}</b><small>${esc(r.created_by)} · ${r.needed_by ? 'needed by ' + esc(r.needed_by) : 'no date'}${r.returns ? ' · returned ' + r.returns + '×' : ''}</small></button>`).join('')
    : '<p class="muted pad">Nothing here yet.' + (ME.role === 'foreman' ? ' Start with “New RFI”.' : '') + '</p>'}</div><div id="detail" class="detail"><p class="muted pad">Pick an RFI.</p></div></div>`;
  document.querySelectorAll('.item').forEach((b) => b.onclick = () => openRfi(b.dataset.id));
  if (OPEN) openRfi(OPEN);
}

async function openRfi(id) {
  if (OPEN !== id) OPENED_AT = performance.now();
  OPEN = id;
  document.querySelectorAll('.item').forEach((b) => b.classList.toggle('on', b.dataset.id === id));
  const { rfi, audit, alerts } = await api('/api/rfis/' + id);
  const parts = [`<h2>${esc(rfi.id)} ${badge(rfi.status)}</h2><p class="muted">Written from the <b>Addendum ${rfi.drawing_set}</b> drawing set by ${esc(rfi.created_by_name)}${rfi.case_id ? ' · test scenario ' + esc(rfi.case_id) : ''}</p>`];
  if (ME.role === 'foreman') parts.push(foremanPanel(rfi));
  else if (ME.role === 'architect') parts.push(architectPanel(rfi));
  else parts.push(gcPanel(rfi, alerts));
  parts.push(`<details class="audit"><summary>Audit trail (${audit.length} messages, hash-chained)</summary><ol>${audit.map((m) =>
    `<li><code>${esc(m.at.slice(11, 19))}</code> <b>${esc(m.type)}</b> from ${m.from.kind === 'agent' ? '🤖 ' + esc(m.from.id) : esc(m.from.name) + ' (' + esc(roleTitle(m.from.role)) + ')'}${m.to_party ? ' → ' + esc(m.to_party) : ''}${m.body?.note ? ': “' + esc(m.body.note) + '”' : ''}</li>`).join('')}</ol></details>`);
  $('#detail').innerHTML = parts.join('');
  wire(rfi);
}

// ------------------------------------------------------------------ foreman
function foremanPanel(r) {
  const d = r.draft, f = r.final || {}, editable = ['rough', 'drafted', 'returned'].includes(r.status);
  const ret = r.status === 'returned' ? `<div class="note warn">The GC returned this RFI. Fix what they asked for and send it again (see the audit trail for their note).</div>` : '';
  const notes = r.site_notes ? `<details><summary>Your site notes (scenario brief: what you would know on site)</summary><dl>${['location', 'needed_by', 'impact', 'references']
    .map((k) => `<dt>${k}</dt><dd>${esc(r.site_notes[k])}</dd>`).join('')}</dl></details>` : '';
  let html = `${ret}<div class="card"><h3>What you sent from site</h3><p class="quote">${esc(r.rough.message)}</p><p class="muted">Sheets as written: ${esc(r.rough.sheets_as_written || '—')}</p>${notes}</div>`;
  if (editable) html += `<div class="row"><button class="primary" data-act="draft-ai">Ask the draft agent (code + AI)</button><button data-act="draft-code">Checklist only (no AI)</button></div>`;
  if (d) {
    const src = (x) => x.source === 'message' ? `<span class="src ok">from your message</span>` : `<span class="src miss">missing — please add</span>`;
    html += `<div class="card agent"><h3>🤖 Draft agent suggestion <small>${esc(d.engine)}${d.model ? ' · ' + esc(d.model) : ''}</small></h3>
      ${d.questions_for_sub.length ? `<div class="asks"><b>The agent needs from you:</b><ul>${d.questions_for_sub.map((q) => `<li><b>${esc(q.field)}</b>: ${esc(q.ask)}</li>`).join('')}</ul></div>` : '<p class="ok">Nothing missing found.</p>'}
      <ul class="facts">${['location', 'needed_by', 'impact'].map((k) => `<li><b>${k}</b> ${src(d[k])} ${esc(d[k].value)}</li>`).join('')}</ul>
      <p><b>Sheets (looked up by code):</b></p><ul class="refs">${d.references.lookup.map((x) => `<li class="r-${x.status}">${esc(x.message)}</li>`).join('') || '<li class="r-not_in_index">No sheet number found.</li>'}</ul>
      ${d.guard_blocked?.length ? `<p class="muted">Guard removed ${d.guard_blocked.length} value(s) the AI filled in that your message does not say.</p>` : ''}
      ${d.changes?.length ? `<details><summary>What the agent changed</summary><ul>${d.changes.map((c) => `<li>${esc(c.what)} — ${esc(c.why)}</li>`).join('')}</ul></details>` : ''}</div>`;
  }
  if (editable) {
    const v = (k) => esc(f[k] || (d ? (typeof d[k] === 'object' ? (d[k].value === '(stated in the message)' ? '' : d[k].value) : d[k]) : '') || '');
    const refs = esc(f.references || d?.references?.text || r.rough.sheets_as_written || '');
    html += `<div class="card"><h3>Your RFI — edit, then approve</h3><p class="muted">The agent only suggests. Nothing goes to the GC until you approve it.</p>
      <label>Title<input id="f-title" value="${v('title')}"></label>
      <label>Question<textarea id="f-question" rows="4">${esc(f.question || d?.question || r.rough.message)}</textarea></label>
      <div class="grid2"><label>Location<input id="f-location" value="${v('location')}"></label><label>Response needed by<input id="f-needed_by" value="${v('needed_by')}" placeholder="YYYY-MM-DD"></label></div>
      <label>Impact if late<input id="f-impact" value="${v('impact')}"></label>
      <div class="grid2"><label>Drawing sheets<input id="f-references" value="${refs}"></label><label>Trade<input id="f-trade" value="${esc(f.trade || d?.trade || '')}"></label></div>
      <button class="primary" data-act="approve">Approve and send to GC</button></div>`;
  } else html += finalCard(r);
  return html;
}

function finalCard(r) {
  const f = r.final || {};
  return `<div class="card"><h3>Submitted RFI</h3><dl>${['title', 'question', 'location', 'needed_by', 'impact', 'references', 'trade']
    .map((k) => `<dt>${k.replace('_', ' ')}</dt><dd>${esc(f[k]) || '<span class="miss">—</span>'}</dd>`).join('')}</dl>
    ${r.response ? `<div class="note ok"><b>Answer from ${esc(r.response.by)} (${r.response.party === 'gc' ? 'GC' : 'architect'}):</b> ${esc(r.response.text)}</div>` : ''}</div>`;
}

// ------------------------------------------------------------------ GC
function gcPanel(r, alerts) {
  let html = finalCard(r);
  if (!r.final) return html + '<p class="muted">The foreman has not sent this RFI yet.</p>';
  alerts.filter((a) => a.status === 'open').forEach((a) => html += `<div class="note warn">🤖 watch_agent: ${esc(a.message)}</div>`);
  const c = r.check;
  if (['submitted', 'cost_review'].includes(r.status)) html += `<div class="row"><button class="primary" data-act="check-ai">Run check agent (code + AI)</button><button data-act="check-code">Checklist only (no AI)</button>
    <span class="muted">Review timer: <b id="timer">0</b> s</span></div>`;
  if (c) html += `<div class="card agent"><h3>🤖 Check agent <small>${esc(c.engine)}</small></h3>
    <p>Recommendation: <b>${esc({ return_to_sub: 'Return to the subcontractor', gc_can_answer: 'GC can answer', forward_to_design: 'Forward to the architect' }[c.recommendation])}</b></p>
    <ul class="refs">${c.findings.map((x) => `<li class="${x.blocking ? 'r-not_in_index' : 'r-revised_since_your_set'}"><span class="src">${esc(x.source)}</span> ${esc(x.message)}</li>`).join('') || '<li class="r-current">No problems found.</li>'}</ul>
    ${c.judgements ? `<p class="muted">AI on location: ${esc(c.judgements.location?.value)} — ${esc(c.judgements.location?.reason)}<br>AI on impact: ${esc(c.judgements.impact?.value)} — ${esc(c.judgements.impact?.reason)}</p>` : ''}
    ${c.route ? `<p class="muted">Route: ${esc(c.route.value)} — ${esc(c.route.reason)}</p>` : ''}
    ${c.cost_flag?.value === 'yes' ? `<p class="note warn">Possible cost/scope item: ${esc(c.cost_flag.reason)} Forwarding needs the PM's sign-off.</p>` : ''}</div>`;
  if (r.status === 'submitted' && (can('return') || can('forward'))) html += `<div class="card"><h3>Your decision</h3>
    <label>Note to the sub (required to return or answer)<textarea id="note" rows="2"></textarea></label>
    <div class="row"><button data-act="return">Return to sub</button><button data-act="answer">Answer as GC</button><button class="primary" data-act="forward">Forward to architect</button></div></div>`;
  if (r.status === 'cost_review' && can('ack_cost')) html += `<div class="card"><h3>PM sign-off</h3><p>The site manager wants to forward this RFI, and the check agent flagged a possible cost/scope change.</p>
    <button class="primary" data-act="ack_cost">I have read it — forward to architect</button></div>`;
  return html;
}

// ------------------------------------------------------------------ architect
function architectPanel(r) {
  let html = finalCard(r);
  if (r.status === 'forwarded') html += `<div class="card"><h3>Response</h3><p class="muted">Only you answer design questions. The triage agent orders your queue; it never drafts an answer.</p>
    <textarea id="answer" rows="4"></textarea><button class="primary" data-act="respond">Send response to GC</button></div>`;
  return html;
}
async function queueView() {
  const q = await api('/api/triage');
  $('#view').innerHTML = `<div class="card"><h2>🤖 Triage agent: your queue</h2><p class="muted">Ordered by days left and whether the impact says work is held. Code only.</p>
    <ol class="queue">${q.map((x) => `<li><button class="link" data-id="${x.rfi_id}">${esc(x.rfi_id)} ${esc(x.title)}</button><br><small>${x.why.map(esc).join(' · ')}</small></li>`).join('') || '<li class="muted">Nothing forwarded yet.</li>'}</ol></div><div id="detail" class="detail"></div>`;
  document.querySelectorAll('.queue [data-id]').forEach((b) => b.onclick = () => openRfi(b.dataset.id));
}

// ------------------------------------------------------------------ actions
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
    toast('Done.'); TAB === 'queue' ? (await queueView(), openRfi(r.id)) : listView();
  }, b));
}

// ------------------------------------------------------------------ new RFI (foreman)
function newView() {
  $('#view').innerHTML = `<div class="card narrow"><h2>New RFI from site</h2>
    <label>Start from a test scenario (simulated, from real Dett RFIs)<select id="case"><option value="">— write my own —</option>
      ${META.cases.map((c) => `<option value="${c.case_id}">${c.case_id}: ${esc(c.title)}</option>`).join('')}</select></label>
    <div id="own"><label>What did you find? (write it the way you would text it)<textarea id="msg" rows="4"></textarea></label>
      <div class="grid2"><label>Sheets you are looking at<input id="sheets" placeholder="e.g. E-301"></label>
      <label>Your drawing set<select id="set">${[...Array(META.issued_through + 1).keys()].map((n) => `<option value="${n}" ${n === META.issued_through ? 'selected' : ''}>${n ? 'Addendum ' + n : 'Bid set'}</option>`).join('')}</select></label></div></div>
    <button class="primary" id="create">Create</button></div>`;
  $('#case').onchange = () => $('#own').style.display = $('#case').value ? 'none' : '';
  $('#create').onclick = (e) => run(async () => {
    const r = await api('/api/rfis', { case_id: $('#case').value, message: $('#msg').value, sheets_as_written: $('#sheets').value, drawing_set: +$('#set').value });
    TAB = 'list'; OPEN = r.id; boot();
  }, e.target);
}

// ------------------------------------------------------------------ alerts and control panel (GC)
async function alertsView() {
  const al = await api('/api/alerts');
  $('#view').innerHTML = `<div class="card"><h2>🤖 Watch agent: revision alerts</h2>
    <p class="muted">When an addendum is issued, the watch agent checks every open RFI for sheets revised after the drawing set it was written from. It flags; you decide. Mark each alert so we can measure false alarms.</p>
    ${can('run_watcher') ? '<div class="row"><button class="primary" id="next">Issue next addendum</button></div>' : ''}
    <table><tr><th>RFI</th><th>Alert</th><th>Evidence</th><th></th></tr>${al.map((a) => `<tr><td>${esc(a.rfi_id)}</td><td>${esc(a.message)}</td><td><small>${esc(a.evidence)}</small></td>
      <td>${a.status === 'open' ? `<button data-k="${esc(a.key)}" data-v="useful">Useful</button><button data-k="${esc(a.key)}" data-v="wrong">Wrong</button>` : esc(a.status)}</td></tr>`).join('') || '<tr><td colspan="4" class="muted">No alerts yet.</td></tr>'}</table></div>`;
  document.querySelectorAll('[data-k]').forEach((b) => b.onclick = () => run(async () => { await api('/api/alerts/' + encodeURIComponent(b.dataset.k), { verdict: b.dataset.v }); alertsView(); }, b));
  if ($('#next')) $('#next').onclick = (e) => run(async () => { const o = await api('/api/watch/next', {}); toast(o.message); boot(); }, e.target);
}

async function panelView() {
  const p = await api('/api/panel');
  const tile = (label, value, sub) => `<div class="tile"><span>${esc(label)}</span><b>${value ?? '—'}</b>${sub ? `<small>${esc(sub)}</small>` : ''}</div>`;
  const ev = p.offline_eval, st = p.study;
  $('#view').innerHTML = `<div class="card"><h2>Control panel</h2><p class="muted">Live numbers from this session's audit trail, plus the offline evaluation and the timed review study.</p>
    <h3>Live system</h3><div class="tiles">
      ${tile('RFIs', p.rfis, Object.entries(p.by_status).map(([k, v]) => `${STATUS[k] || k}: ${v}`).join(' · '))}
      ${tile('Round trips (returns to sub)', p.round_trips.returns, p.round_trips.rfis_returned + ' RFIs returned')}
      ${tile('GC first-review time (median s)', p.gc_first_review_seconds.median?.toFixed?.(1), 'n = ' + p.gc_first_review_seconds.n)}
      ${tile('Draft agent questions asked', p.draft_agent.questions_asked, p.draft_agent.suggestions + ' drafts · ' + p.draft_agent.guard_blocked_invented_values + ' invented values blocked')}
      ${tile('Foreman edited agent text', p.draft_agent.agent_text_edited_by_foreman, 'of ' + p.draft_agent.approved_with_agent_draft + ' approved with a draft')}
      ${tile('Check agent: return recommended', p.check_agent.recommended_return, p.check_agent.checks + ' checks · findings code ' + p.check_agent.findings_code + ' / AI ' + p.check_agent.findings_ai)}
      ${tile('Revision alerts', p.watch_agent.alerts, `useful ${p.watch_agent.marked_useful} · wrong ${p.watch_agent.marked_wrong} · open ${p.watch_agent.open}`)}
      ${tile('Escalations to PM', p.watch_agent.escalations, 'RFIs within 5 days of their date')}
      ${tile('AI calls (guardrail)', p.ai_calls.n + ' / ' + p.ai_calls.limit)}
      ${tile('Audit chain', p.audit.ok ? 'intact' : 'BROKEN', p.audit.ok ? p.audit.records + ' records' : 'at record ' + p.audit.broken_at_record)}
    </div>
    <h3>Offline evaluation (12 rough RFIs, scripts/run_demo3_eval.py)</h3>
    ${ev ? `<table><tr><th>Method</th><th>Missing items caught</th><th>Asked for something already there</th><th>Reference problems caught</th><th>Invented facts in final RFI</th><th>Still needs a return after drafting</th></tr>
      ${ev.conditions.map((c) => `<tr><td>${esc(c.label)}</td><td>${esc(c.missing_caught)}</td><td>${esc(c.false_asks)}</td><td>${esc(c.ref_caught)}</td><td>${esc(c.invented)}</td><td>${esc(c.needs_return_after)}</td></tr>`).join('')}</table>
      <p class="muted">Run ${esc(ev.run_at)} · ${esc(ev.model)} · ${ev.runs} run(s). ${esc(ev.note || '')}</p>` : '<p class="muted">Not run yet: python3 scripts/run_demo3_eval.py</p>'}
    <h3>Timed review study (/study)</h3>
    ${st ? `<table><tr><th></th><th>Reviews</th><th>Median seconds</th><th>Would go back to the sub</th></tr>
      ${['raw', 'agent'].map((c) => `<tr><td>${c === 'raw' ? 'Rough message' : 'Agent-drafted, foreman-approved'}</td><td>${st[c].n}</td><td>${st[c].median_seconds ?? '—'}</td><td>${st[c].go_back}</td></tr>`).join('')}</table>
      <p class="muted">${st.reviewers} reviewer(s). <a href="/api/export/study.csv">Download study.csv</a></p>` : '<p class="muted">No study records yet. Open /study in another tab.</p>'}
    <h3>Project clock and data</h3><div class="row">
      <button id="next">Issue next addendum (watch agent runs)</button>
      <label class="inline">Reset clock to Addendum <select id="to">${[0, 1, 2, 3, 4, 5, 6].map((n) => `<option ${n === p.issued_through ? 'selected' : ''}>${n}</option>`).join('')}</select></label><button id="setclock">Set</button>
      <a class="button" href="/api/export/rfi_log.csv">Export RFI log (CSV, Procore-style)</a>
      <button id="wipe" class="danger">Reset demo data</button></div></div>`;
  $('#next').onclick = (e) => run(async () => { const o = await api('/api/watch/next', {}); toast(o.message); boot(); }, e.target);
  $('#setclock').onclick = (e) => run(async () => { await api('/api/watch/reset', { issued_through: +$('#to').value }); boot(); }, e.target);
  $('#wipe').onclick = (e) => run(async () => { if (!confirm('Delete all RFIs and the audit trail on this computer?')) return; await api('/api/reset', {}); location.reload(); }, e.target);
}

boot().catch((e) => { $('#main').innerHTML = `<p class="pad">Could not load: ${esc(e.message)}</p>`; });
