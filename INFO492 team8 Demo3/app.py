"""Team 8 Demo #3: one RFI exchanged between subcontractor, GC and design team, each with its own agent.

    python3 app.py            then open http://127.0.0.1:8766
    python3 app.py --watch-every 60   also publish the next addendum automatically every 60 seconds

Local only. State lives in runtime/ (never uploaded). See README.md for the demo users and PINs.
"""
import argparse
import csv
import hmac
import io
import json
import os
import secrets
import statistics
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import agents
from core import ROOT, settings
from protocol import (AGENTS, OPEN_STATUSES, ROLES, AuditLog, Denied, actor_of, can, can_view, envelope,
                      next_status, now_iso, require)

RUNTIME = Path(os.getenv('DEMO3_RUNTIME', str(ROOT / 'runtime')))
STATE_FILE = RUNTIME / 'state.json'
AUDIT = AuditLog(RUNTIME / 'audit.jsonl')
STUDY_FILE = RUNTIME / 'study.csv'
LOCK = threading.RLock()
SESSIONS = {}
USERS = {u['id']: u for u in json.loads((ROOT / 'data' / 'users.json').read_text(encoding='utf-8'))['users']}
CTX = {'index': agents.load('drawing_index.json'), 'revisions': agents.load('revisions.json')}
CASES = {c['case_id']: c for c in agents.load('rough_rfis.json')}
START_ADDENDUM = int(os.getenv('DEMO_START_ADDENDUM', '1'))


# --------------------------------------------------------------------------- state
def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding='utf-8'))
    return {'rfis': {}, 'next_no': 1, 'issued_through': START_ADDENDUM, 'alerts': [], 'seen': [], 'escalated': []}


def save_state(st):
    RUNTIME.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix('.tmp')
    tmp.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding='utf-8')
    os.replace(tmp, STATE_FILE)


def ctx(st):
    return dict(CTX, issued_through=st['issued_through'])


def log(msg_type, rfi_id, user=None, agent=None, to_party=None, body=None):
    return AUDIT.append(envelope(msg_type, rfi_id, actor_of(user, agent), to_party, body or {}))


def escalate(st):
    """Escalation rule: an open RFI within 5 days of its response date is escalated to the PM once."""
    for e in agents.due_soon(list(st['rfis'].values())):
        if e['rfi_id'] not in st['escalated']:
            st['escalated'].append(e['rfi_id'])
            log('escalation', e['rfi_id'], agent='watch_agent', to_party='gc',
                body={'to_role': 'project_manager', 'reason': f"Response needed by {e['needed_by']} ({e['days_left']} days).", **e})


def publish_next(st):
    """The continuous loop's step: a new addendum is issued; the watch agent re-checks every open RFI."""
    if st['issued_through'] >= 6:
        return {'addendum': None, 'alerts': [], 'message': 'All six addenda are already issued.'}
    n = st['issued_through'] + 1
    st['issued_through'] = n
    seen = set(st['seen'])
    new = agents.watch_agent(list(st['rfis'].values()), n, ctx(st), seen)
    st['seen'] = sorted(seen)
    for a in new:
        a['status'] = 'open'
        st['alerts'].append(a)
        log('revision_alert', a['rfi_id'], agent='watch_agent', to_party='gc', body=a)
    escalate(st)
    return {'addendum': n, 'alerts': new, 'message': f'Addendum {n} issued: {len(new)} new alert(s).'}


# --------------------------------------------------------------------------- RFI helpers
def summary(r):
    f = r.get('final') or {}
    return {'id': r['id'], 'status': r['status'], 'title': f.get('title') or (r.get('draft') or {}).get('title') or r['rough']['message'][:60],
            'created_by': USERS[r['created_by']]['name'], 'company': USERS[r['created_by']]['company'],
            'needed_by': f.get('needed_by', ''), 'returns': r.get('returns', 0), 'case_id': r.get('case_id'),
            'drawing_set': r['drawing_set']}


def get_rfi(st, rid, user):
    r = st['rfis'].get(rid)
    if not r or not can_view(user, r): raise Denied('RFI not found or not visible to your role.')
    return r


def create_rfi(st, user, body):
    require(user, 'create')
    case = CASES.get(body.get('case_id') or '')
    message = (case['message'] if case else str(body.get('message', ''))).strip()
    sheets = case['sheets_as_written'] if case else str(body.get('sheets_as_written', '')).strip()
    if not message: raise ValueError('Write what you found on site first.')
    if len(message) > 3000: raise ValueError('Message is too long (3,000 characters maximum).')
    want = case['drawing_set'] if case else int(body.get('drawing_set') or st['issued_through'])
    drawing_set = max(0, min(want, st['issued_through']))   # nobody can hold a set newer than today's latest addendum
    rid = f"RFI-{st['next_no']:03d}"; st['next_no'] += 1
    r = {'id': rid, 'case_id': case['case_id'] if case else None, 'created_by': user['id'], 'status': 'rough',
         'drawing_set': drawing_set, 'rough': {'message': message, 'sheets_as_written': sheets},
         'site_notes': case['site_notes'] if case else None, 'draft': None, 'final': None, 'check': None,
         'returns': 0, 'created_at': now_iso()}
    st['rfis'][rid] = r
    log('rfi_created', rid, user, to_party='sub', body={'rough': r['rough'], 'drawing_set': drawing_set})
    return r


def act(st, user, rid, action, body):
    r = get_rfi(st, rid, user)
    if action == 'draft':
        require(user, 'request_draft')
        if r['created_by'] != user['id']: raise Denied('Only the foreman who wrote this RFI can draft it.')
        use_ai = body.get('use_ai', True)
        fn = agents.draft_agent if use_ai else agents.code_draft
        msg = r['rough']['message'] if r['status'] != 'returned' else (r['final'] or {}).get('question', r['rough']['message'])
        r['draft'] = fn(msg, r['rough']['sheets_as_written'], r['drawing_set'], ctx(st))
        r['status'] = next_status('request_draft', r['status'])
        log('draft_suggestion', rid, agent='draft_agent', to_party='sub', body={'to_role': 'foreman', 'draft': r['draft']})
    elif action == 'approve':
        require(user, 'approve_draft')
        if r['created_by'] != user['id']: raise Denied('Only the foreman who wrote this RFI can approve it.')
        fields = {k: str(body.get(k, '')).strip()[:2000] for k in ('title', 'question', 'location', 'needed_by', 'impact', 'references', 'trade')}
        if not fields['question']: raise ValueError('The question cannot be empty.')
        suggestion = r.get('draft') or {}
        edited = [k for k in ('title', 'question') if suggestion.get(k) and suggestion.get(k) != fields[k]]
        r['final'] = fields
        r['status'] = next_status('approve_draft', r['status'])
        r['submitted_at'] = now_iso()
        log('draft_approved', rid, user, to_party='gc', body={'final': fields, 'used_agent_draft': bool(suggestion),
                                                               'edited_agent_text': edited})
    elif action == 'check':
        require(user, 'run_check')
        if not r.get('final'): raise ValueError('Nothing submitted to check yet.')
        r['check'] = agents.check_agent(r['final'], r['drawing_set'], ctx(st), use_ai=body.get('use_ai', True))
        log('check_result', rid, agent='check_agent', to_party='gc', body={'to_role': user['role'], 'check': r['check']})
    elif action in ('return', 'answer', 'forward'):
        require(user, action)
        note = str(body.get('note', '')).strip()[:2000]
        if action in ('return', 'answer') and not note:
            raise ValueError('Write what the subcontractor should add or fix.' if action == 'return' else 'Write the GC answer.')
        secs = body.get('review_seconds')
        if isinstance(secs, (int, float)) and 0 < secs < 7200 and 'gc_review_seconds' not in r:
            r['gc_review_seconds'] = round(secs, 1)
        if action == 'forward' and (r.get('check') or {}).get('needs_pm_cost_review') and user['role'] != 'project_manager':
            next_status('forward', r['status'])          # checks the move is allowed
            r['status'] = 'cost_review'
            log('cost_review_requested', rid, user, to_party='gc', body={'to_role': 'project_manager', 'note': note,
                                                                        'reason': r['check']['cost_flag']})
        else:
            r['status'] = next_status(action, r['status'])
            if action == 'return': r['returns'] = r.get('returns', 0) + 1
            if action == 'answer': r['response'] = {'text': note, 'by': user['name'], 'party': 'gc', 'at': now_iso()}
            log({'return': 'returned_to_sub', 'answer': 'gc_answer', 'forward': 'forwarded_to_design'}[action], rid, user,
                to_party={'return': 'sub', 'answer': 'sub', 'forward': 'design'}[action], body={'note': note})
    elif action == 'ack_cost':
        require(user, 'ack_cost')
        r['status'] = next_status('ack_cost', r['status'])
        log('cost_acknowledged', rid, user, to_party='design', body={'note': str(body.get('note', ''))[:1000]})
    elif action == 'respond':
        require(user, 'respond')
        text = str(body.get('answer', '')).strip()[:4000]
        if not text: raise ValueError('Write the design team response.')
        r['status'] = next_status('respond', r['status'])
        r['response'] = {'text': text, 'by': user['name'], 'party': 'design', 'at': now_iso()}
        log('design_response', rid, user, to_party='gc', body={'answer': text})
    else:
        raise ValueError('Unknown action.')
    escalate(st)
    return r


# --------------------------------------------------------------------------- control panel and export
def panel(st):
    rfis = list(st['rfis'].values())
    recs = AUDIT.records()
    by_status = {}
    for r in rfis: by_status[r['status']] = by_status.get(r['status'], 0) + 1
    drafts = [x['body']['draft'] for x in recs if x['type'] == 'draft_suggestion']
    approvals = [x['body'] for x in recs if x['type'] == 'draft_approved']
    checks = [x['body']['check'] for x in recs if x['type'] == 'check_result']
    secs = [r['gc_review_seconds'] for r in rfis if r.get('gc_review_seconds')]
    alerts = st['alerts']
    eval_file = ROOT / 'results' / 'demo3' / 'summary.json'
    return {
        'issued_through': st['issued_through'], 'rfis': len(rfis), 'by_status': by_status,
        'round_trips': {'returns': sum(r.get('returns', 0) for r in rfis), 'rfis_returned': sum(1 for r in rfis if r.get('returns'))},
        'draft_agent': {'suggestions': len(drafts), 'questions_asked': sum(len(d.get('questions_for_sub', [])) for d in drafts),
                        'guard_blocked_invented_values': sum(len(d.get('guard_blocked', [])) for d in drafts),
                        'approved_with_agent_draft': sum(1 for a in approvals if a.get('used_agent_draft')),
                        'agent_text_edited_by_foreman': sum(1 for a in approvals if a.get('edited_agent_text'))},
        'check_agent': {'checks': len(checks), 'recommended_return': sum(1 for c in checks if c.get('recommendation') == 'return_to_sub'),
                        'findings_code': sum(1 for c in checks for f in c.get('findings', []) if f['source'] == 'code'),
                        'findings_ai': sum(1 for c in checks for f in c.get('findings', []) if f['source'] == 'AI')},
        'watch_agent': {'alerts': len(alerts), 'open': sum(1 for a in alerts if a['status'] == 'open'),
                        'marked_useful': sum(1 for a in alerts if a['status'] == 'useful'),
                        'marked_wrong': sum(1 for a in alerts if a['status'] == 'wrong'),
                        'escalations': len(st['escalated'])},
        'gc_first_review_seconds': {'n': len(secs), 'median': statistics.median(secs) if secs else None},
        'ai_calls': agents.ai_calls(), 'audit': AUDIT.verify(),
        'offline_eval': json.loads(eval_file.read_text(encoding='utf-8')) if eval_file.exists() else None,
        'study': study_results(),
    }


def rfi_log_csv(st):
    """Procore-style RFI log export (sandbox: a file you can import, never a live write to another system)."""
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(['Number', 'Subject', 'Status', 'Received From', 'Responsible Contractor', 'Due Date', 'Drawing Number',
                'Location', 'Question', 'Cost/Schedule Impact', 'Answer', 'Answered By', 'Times Returned'])
    for r in sorted(st['rfis'].values(), key=lambda x: x['id']):
        f = r.get('final') or {}; resp = r.get('response') or {}; u = USERS[r['created_by']]
        w.writerow([r['id'], f.get('title', ''), r['status'], u['name'], u['company'], f.get('needed_by', ''), f.get('references', ''),
                    f.get('location', ''), f.get('question') or r['rough']['message'], f.get('impact', ''), resp.get('text', ''),
                    resp.get('by', ''), r.get('returns', 0)])
    return out.getvalue()


# --------------------------------------------------------------------------- timed review study
def study_items():
    f = ROOT / 'results' / 'demo3' / 'study_items.json'
    if f.exists(): return json.loads(f.read_text(encoding='utf-8'))
    return {'source': 'not built yet', 'items': []}


def study_order(reviewer):
    """Counterbalanced: odd reviewers see the first half raw and the second half agent-drafted; even reviewers the opposite."""
    items = study_items()['items']
    half = len(items) // 2
    out = []
    for i, it in enumerate(items):
        raw_first = (reviewer % 2 == 1)
        cond = ('raw' if i < half else 'agent') if raw_first else ('agent' if i < half else 'raw')
        out.append({'item_id': it['case_id'], 'condition': cond, 'rfi': it[cond]})
    return out


def study_record(body):
    row = {'at': now_iso(), 'reviewer': int(body['reviewer']), 'item_id': str(body['item_id'])[:10],
           'condition': body['condition'] if body.get('condition') in ('raw', 'agent') else 'unknown',
           'seconds': round(float(body['seconds']), 1), 'decision': body.get('decision') if body.get('decision') in ('send_on', 'go_back') else 'unknown',
           'reason': str(body.get('reason', ''))[:300]}
    RUNTIME.mkdir(parents=True, exist_ok=True)
    new = not STUDY_FILE.exists()
    with open(STUDY_FILE, 'a', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        if new: w.writeheader()
        w.writerow(row)
    return row


def study_results():
    if not STUDY_FILE.exists(): return None
    with open(STUDY_FILE, encoding='utf-8') as f: rows = list(csv.DictReader(f))
    out = {'reviewers': len({r['reviewer'] for r in rows}), 'records': len(rows)}
    for c in ('raw', 'agent'):
        rs = [r for r in rows if r['condition'] == c]
        out[c] = {'n': len(rs), 'median_seconds': statistics.median(float(r['seconds']) for r in rs) if rs else None,
                  'go_back': sum(1 for r in rs if r['decision'] == 'go_back')}
    return out


# --------------------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    server_version = 'Team8Demo3/1.0'

    def log_message(self, *a): pass

    def user(self):
        cookie = self.headers.get('Cookie', '')
        token = next((c.split('=', 1)[1] for c in cookie.split('; ') if c.startswith('d3session=')), None)
        return SESSIONS.get(token)

    def send(self, code, obj=None, ctype='application/json', raw=None, headers=None):
        data = raw if raw is not None else json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', ctype + ('; charset=utf-8' if ctype.startswith(('text', 'application/json')) else ''))
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        for k, v in (headers or {}).items(): self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        n = int(self.headers.get('Content-Length') or 0)
        if n > 200_000: raise ValueError('Request too large.')
        return json.loads(self.rfile.read(n) or b'{}')

    def do_GET(self):
        url = urlparse(self.path); p = url.path
        static = {'/': 'index.html', '/study': 'study.html', '/app.js': 'app.js', '/study.js': 'study.js', '/style.css': 'style.css'}
        if p in static:
            f = ROOT / 'static' / static[p]
            ctype = {'html': 'text/html', 'js': 'text/javascript', 'css': 'text/css'}[f.suffix[1:]]
            return self.send(200, raw=f.read_bytes(), ctype=ctype)
        try:
            with LOCK:
                st = load_state(); u = self.user()
                if p == '/api/meta':
                    cfg = settings()
                    return self.send(200, {'users': [{k: x[k] for k in ('id', 'name', 'role', 'company')} for x in USERS.values()],
                                           'roles': {k: {'party': v['party'], 'title': v['title'], 'can': sorted(v['can'])} for k, v in ROLES.items()},
                                           'agents': {k: dict(v, may_send=sorted(v['may_send'])) for k, v in AGENTS.items()},
                                           'me': u and {**{k: u[k] for k in ('id', 'name', 'role', 'company')}, 'can': sorted(ROLES[u['role']]['can'])},
                                           'issued_through': st['issued_through'], 'today': agents.DEMO_TODAY.isoformat(),
                                           'ai': {'connected': bool(cfg.get('key')), 'model': cfg.get('model')},
                                           'cases': [{'case_id': c['case_id'], 'title': c['source']['title'], 'drawing_set': c['drawing_set']} for c in CASES.values()]})
                if p.startswith('/api/study/items'):
                    reviewer = int(parse_qs(url.query).get('reviewer', ['1'])[0])
                    return self.send(200, {'source': study_items()['source'], 'items': study_order(reviewer)})
                if not u: return self.send(401, {'error': 'Sign in first.'})
                if p == '/api/rfis':
                    return self.send(200, [summary(r) for r in sorted(st['rfis'].values(), key=lambda x: x['id']) if can_view(u, r)])
                if p.startswith('/api/rfis/'):
                    r = get_rfi(st, p.split('/')[3], u)
                    view = dict(r)
                    if u['role'] == 'architect': view.pop('site_notes', None)
                    view['created_by_name'] = USERS[r['created_by']]['name']
                    return self.send(200, {'rfi': view, 'audit': AUDIT.records(r['id']),
                                           'alerts': [a for a in st['alerts'] if a['rfi_id'] == r['id']]})
                if p == '/api/alerts':
                    require(u, 'handle_alert'); return self.send(200, st['alerts'])
                if p == '/api/triage':
                    require(u, 'run_triage')
                    q = agents.triage_agent([r for r in st['rfis'].values() if r['status'] == 'forwarded'])
                    done = set(st.setdefault('triaged', []))
                    for x in q:
                        if x['rfi_id'] not in done:       # record each RFI's first triage note once
                            log('triage_note', x['rfi_id'], agent='triage_agent', to_party='design', body=x)
                            st['triaged'].append(x['rfi_id'])
                    save_state(st)
                    return self.send(200, q)
                if p == '/api/panel':
                    require(u, 'metrics'); return self.send(200, panel(st))
                if p == '/api/escalations':
                    require(u, 'metrics')
                    return self.send(200, [x for x in AUDIT.records() if x['type'] == 'escalation'])
                if p == '/api/export/rfi_log.csv':
                    require(u, 'export')
                    return self.send(200, raw=rfi_log_csv(st).encode(), ctype='text/csv',
                                     headers={'Content-Disposition': 'attachment; filename="rfi_log.csv"'})
                if p == '/api/export/study.csv':
                    require(u, 'metrics')
                    return self.send(200, raw=STUDY_FILE.read_bytes() if STUDY_FILE.exists() else b'', ctype='text/csv',
                                     headers={'Content-Disposition': 'attachment; filename="study.csv"'})
            return self.send(404, {'error': 'Not found.'})
        except Denied as e:
            return self.send(403, {'error': str(e)})
        except (ValueError, KeyError) as e:
            return self.send(400, {'error': str(e)})

    def do_POST(self):
        p = urlparse(self.path).path
        try:
            body = self.body()
            with LOCK:
                st = load_state(); u = self.user()
                if p == '/api/login':
                    cand = USERS.get(body.get('user_id'))
                    if not cand or not hmac.compare_digest(str(body.get('pin', '')), cand['pin']):
                        return self.send(401, {'error': 'Wrong user or PIN.'})
                    token = secrets.token_urlsafe(24); SESSIONS[token] = cand
                    log('session', None, cand, body={'event': 'sign_in'})
                    return self.send(200, {'ok': True}, headers={'Set-Cookie': f'd3session={token}; HttpOnly; SameSite=Strict; Path=/'})
                if p == '/api/logout':
                    return self.send(200, {'ok': True}, headers={'Set-Cookie': 'd3session=; Max-Age=0; Path=/'})
                if p == '/api/study/record':
                    return self.send(200, study_record(body))
                if not u: return self.send(401, {'error': 'Sign in first.'})
                if p == '/api/rfis':
                    r = create_rfi(st, u, body); save_state(st); return self.send(200, summary(r))
                if p.startswith('/api/rfis/'):
                    _, _, _, rid, action = p.split('/')
                    r = act(st, u, rid, action, body); save_state(st); return self.send(200, {'rfi': r})
                if p == '/api/watch/next':
                    require(u, 'run_watcher'); out = publish_next(st); save_state(st); return self.send(200, out)
                if p == '/api/watch/reset':
                    require(u, 'run_watcher')
                    n = int(body.get('issued_through', 1))
                    if not 0 <= n <= 6: raise ValueError('Addendum must be 0-6.')
                    st['issued_through'] = n; st['seen'] = [a for a in st['seen'] if int(a.split('|')[2]) <= n]
                    save_state(st); return self.send(200, {'issued_through': n})
                if p.startswith('/api/alerts/'):
                    require(u, 'handle_alert')
                    key = p.split('/', 3)[3].replace('%7C', '|')
                    a = next((x for x in st['alerts'] if x['key'] == key), None)
                    if not a: raise ValueError('Alert not found.')
                    verdict = body.get('verdict')
                    if verdict not in ('useful', 'wrong'): raise ValueError('Mark the alert useful or wrong.')
                    a['status'] = verdict; a['handled_by'] = u['name']
                    log('alert_handled', a['rfi_id'], u, to_party='gc', body={'key': key, 'verdict': verdict})
                    save_state(st); return self.send(200, a)
                if p == '/api/reset':
                    require(u, 'run_watcher')
                    for f in (STATE_FILE, AUDIT.path): f.unlink(missing_ok=True)
                    return self.send(200, {'ok': True})
            return self.send(404, {'error': 'Not found.'})
        except Denied as e:
            return self.send(403, {'error': str(e)})
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
            return self.send(400, {'error': str(e) or 'Bad request.'})


def watch_loop(every):
    while True:
        time.sleep(every)
        with LOCK:
            st = load_state()
            if st['issued_through'] < 6:
                publish_next(st); save_state(st)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8766)
    ap.add_argument('--watch-every', type=int, default=0, help='seconds between automatic addendum releases (0 = manual)')
    a = ap.parse_args()
    if a.watch_every: threading.Thread(target=watch_loop, args=(a.watch_every,), daemon=True).start()
    srv = ThreadingHTTPServer(('127.0.0.1', a.port), Handler)
    print(f'Team 8 Demo #3 running at http://127.0.0.1:{a.port}  (study page: /study).  Ctrl+C to stop.')
    try: srv.serve_forever()
    except KeyboardInterrupt: print('\nStopped.')


if __name__ == '__main__':
    main()
