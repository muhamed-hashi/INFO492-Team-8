"""Demo #3 agents. Each agent works for one party and only suggests or flags (see protocol.py).

    draft_agent  (subcontractor) rough field message -> clearer RFI draft + questions for the foreman
    check_agent  (GC)            submitted RFI -> findings and a recommendation for the site manager
    triage_agent (design team)   forwarded RFIs -> queue ordered by deadline and impact (code only)
    watch_agent  (GC)            new addendum -> alerts for open RFIs citing a sheet revised since (code only)

Code does every lookup (sheet numbers, revisions, dates). The AI only reads and writes language, and a
guard removes any location, date or impact the AI filled in that the foreman's message does not contain.
"""
import hashlib
import json
import os
import re
from datetime import date, timedelta
from pathlib import Path

from core import ROOT, ai_reference_review, gemini_json, normalize_sheet, settings

SHEET_RE = re.compile(r'\b([A-Za-z]{1,3})-?(\d{3}[A-Za-z]?)\b')
NOT_SHEETS = {'RT', 'KN', 'AE', 'S4'}           # finish tags, keynotes etc. that look like sheet numbers
DEMO_TODAY = date.fromisoformat(os.getenv('DEMO_TODAY', '2023-09-15'))
MAX_AI_CALLS = int(os.getenv('MAX_AI_CALLS_PER_DAY', os.getenv('MAX_AI_CALLS', '300')))
_ai_calls = {'n': 0, 'day': None}
_budget_path = None
MONTHS = {m: i for i, m in enumerate(['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'], 1)}


def init_budget(path):
    """Persist daily AI usage across restarts (cloud demo)."""
    global _budget_path
    _budget_path = Path(path) if path else None
    _refresh_budget_day()


def _today():
    return date.today().isoformat()


def _refresh_budget_day():
    today = _today()
    if _ai_calls.get('day') == today:
        return
    if _budget_path and _budget_path.exists():
        try:
            data = json.loads(_budget_path.read_text(encoding='utf-8'))
            if data.get('day') == today:
                _ai_calls['n'] = int(data.get('n', 0))
                _ai_calls['day'] = today
                return
        except (OSError, ValueError, TypeError):
            pass
    _ai_calls['n'] = 0
    _ai_calls['day'] = today
    _persist_budget()


def _persist_budget():
    if not _budget_path:
        return
    _budget_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = _budget_path.with_suffix('.tmp')
    tmp.write_text(json.dumps({'day': _ai_calls['day'], 'n': _ai_calls['n']}), encoding='utf-8')
    os.replace(tmp, _budget_path)


def load(name):
    return json.loads((ROOT / 'data' / name).read_text(encoding='utf-8'))


def ai_calls():
    _refresh_budget_day()
    return {'n': _ai_calls['n'], 'day': _ai_calls['day'], 'limit': MAX_AI_CALLS}


def _ai(cfg, prompt_file, user, schema):
    """One budgeted Gemini call (daily cap, persisted when init_budget was set)."""
    _refresh_budget_day()
    if _ai_calls['n'] >= MAX_AI_CALLS:
        raise ValueError(
            f'This demo has used its daily AI limit ({MAX_AI_CALLS} calls). Try again tomorrow or use checklist-only.')
    if not cfg.get('key'):
        raise ValueError('AI is not connected. Run python3 setup_ai.py in this folder first.')
    if cfg.get('provider', 'gemini') != 'gemini':
        raise ValueError('Demo #3 agents use Gemini. Run python3 setup_ai.py.')
    prompt = (ROOT / 'prompts' / prompt_file).read_text(encoding='utf-8')
    _ai_calls['n'] += 1
    _persist_budget()
    out, raw = gemini_json(cfg, prompt, user, schema)
    if not isinstance(out, dict):
        raise ValueError('The AI returned an invalid object. No result was accepted.')
    meta = {'model': raw.get('modelVersion', cfg['model']), 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest()[:16],
            'tokens': raw.get('usageMetadata', {}).get('totalTokenCount')}
    return out, meta


# --------------------------------------------------------------------------- code: sheets, revisions, dates
def find_sheets(text):
    out = []
    for prefix, num in SHEET_RE.findall(text or ''):
        if prefix.upper() in NOT_SHEETS: continue
        s = f'{prefix.upper()}-{num.upper()}'
        if s not in out: out.append(s)
    return out


def revisions_after(sheet, drawing_set, issued_through, revisions):
    """Addenda issued after the writer's drawing set (and up to today's latest addendum) that revised this sheet."""
    return [a['addendum'] for a in revisions['addenda']
            if drawing_set < a['addendum'] <= issued_through and any(s['sheet'] == sheet for s in a['sheets'])]


def lookup(text, drawing_set, ctx):
    """Exact lookup of every recognisable sheet number. Never guesses."""
    index = ctx['index']; known = {normalize_sheet(k): k for k in index}
    rows = []
    for s in find_sheets(text):
        name = known.get(normalize_sheet(s))
        if not name:
            rows.append({'sheet': s, 'status': 'not_in_index', 'title': '', 'revised_in': [],
                         'message': f'{s} is not in the current drawing index. Please confirm the sheet number.'})
            continue
        rev = revisions_after(name, drawing_set, ctx['issued_through'], ctx['revisions'])
        title = index[name].get('title', '')
        if rev:
            rows.append({'sheet': name, 'status': 'revised_since_your_set', 'title': title, 'revised_in': rev,
                         'message': f'{name} was revised in Addendum {", ".join(map(str, rev))}, after the drawing set you are '
                                    f'using (Addendum {drawing_set}). Please confirm against the current revision.'})
        else:
            rows.append({'sheet': name, 'status': 'current', 'title': title, 'revised_in': [],
                         'message': f'{name} is in the current drawing index ({title or "no title recorded"}).'})
    return rows


def parse_date(text, today=None):
    """A specific calendar date in the text, as YYYY-MM-DD, or None. 'asap' or 'soon' is not a date."""
    today = today or DEMO_TODAY
    t = (text or '').lower()
    m = re.search(r'\b(20\d\d)-(\d\d)-(\d\d)\b', t)
    if m: return m.group(0)
    m = re.search(r'(?<![\d/-])(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?(?![\d/"\'])', t)   # 9/20, not 3-1/2"
    if m and 1 <= int(m.group(1)) <= 12 and 1 <= int(m.group(2)) <= 31:
        y = int(m.group(3)) if m.group(3) else None
        if y and y < 100: y += 2000
        return _date(y, int(m.group(1)), int(m.group(2)), today)
    m = re.search(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})\b', t)
    if m: return _date(None, MONTHS[m.group(1)], int(m.group(2)), today)
    return None


def _date(year, month, day, today):
    try:
        d = date(year or today.year, month, day)
    except ValueError:
        return None
    if year is None and d < today: d = date(today.year + 1, month, day)
    return d.isoformat()


def _norm(s):
    return ' '.join(re.sub(r'[^a-z0-9#/." -]', ' ', (s or '').lower()).split())


def supported(value, quote, message):
    """Guard against invented facts: the quote must be in the message, and every number in the value too."""
    if not value or not quote: return False
    if _norm(quote) not in _norm(message): return False
    msg_numbers = set(re.findall(r'\d+', message))
    return all(n in msg_numbers for n in re.findall(r'\d+', value))


# --------------------------------------------------------------------------- draft agent (subcontractor)
DRAFT_SCHEMA = {'type': 'object', 'additionalProperties': False,
    'required': ['title', 'question', 'trade', 'location', 'needed_by', 'impact', 'questions_for_sub', 'changes'],
    'properties': {
        'title': {'type': 'string'}, 'question': {'type': 'string'}, 'trade': {'type': 'string'},
        **{f: {'type': 'object', 'additionalProperties': False, 'required': ['found_in_message', 'quote', 'value'],
               'properties': {'found_in_message': {'type': 'boolean'}, 'quote': {'type': 'string'}, 'value': {'type': 'string'}}}
           for f in ('location', 'needed_by', 'impact')},
        'questions_for_sub': {'type': 'array', 'maxItems': 6, 'items': {'type': 'object', 'additionalProperties': False,
            'required': ['field', 'ask'], 'properties': {
                'field': {'type': 'string', 'enum': ['location', 'needed_by', 'impact', 'references', 'question']},
                'ask': {'type': 'string'}}}},
        'changes': {'type': 'array', 'maxItems': 6, 'items': {'type': 'object', 'additionalProperties': False,
            'required': ['what', 'why'], 'properties': {'what': {'type': 'string'}, 'why': {'type': 'string'}}}}}}

ASK = {'location': 'Where exactly is this? Give the building/wing, level and room number or gridline.',
       'needed_by': 'By what date do you need the answer before work is held up?',
       'impact': 'What happens to the work, schedule or cost if the answer comes late?',
       'references': 'Which drawing sheet(s) show this? Check the numbers against the current drawing set.',
       'question': 'What exactly do you need the GC or architect to confirm?'}
LOCATION_WORDS = re.compile(r'\b(room|rm|rooms|level|floor|hallway|corridor|office|wing|elev\w*|annex|gridline|grid|'
                            r'stair|roof|toilet|restroom|mdf|idf|pump room|elec room|electrical room)\b', re.I)
IMPACT_WORDS = re.compile(r'\b(hold|held|delay\w*|critical path|cant|can\'t|cannot|waiting|schedul\w*|order\w*|lead time|slip|cost)\b', re.I)


def code_draft(message, sheets_as_written, drawing_set, ctx):
    """The no-AI way: a checklist that only looks for keywords, dates and sheet numbers."""
    refs = lookup(message + ' ' + sheets_as_written, drawing_set, ctx)
    d = parse_date(message)
    fields = {'location': bool(LOCATION_WORDS.search(message)), 'needed_by': bool(d), 'impact': bool(IMPACT_WORDS.search(message))}
    asks = [{'field': f, 'ask': ASK[f]} for f, ok in fields.items() if not ok]
    if not refs or any(r['status'] != 'current' for r in refs):
        asks.append({'field': 'references', 'ask': ASK['references']})
    return {'engine': 'code', 'title': ' '.join(message.split()[:8]), 'question': message.strip(), 'trade': '',
            'location': {'value': '(stated in the message)' if fields['location'] else '', 'source': 'message' if fields['location'] else 'missing'},
            'needed_by': {'value': d or '', 'source': 'message' if d else 'missing'},
            'impact': {'value': '(stated in the message)' if fields['impact'] else '', 'source': 'message' if fields['impact'] else 'missing'},
            'references': {'text': ', '.join(r['sheet'] for r in refs) or sheets_as_written, 'lookup': refs},
            'questions_for_sub': asks, 'changes': [], 'guard_blocked': []}


def draft_agent(message, sheets_as_written, drawing_set, ctx, cfg=None):
    """Code + AI: code looks up sheets; the AI rewrites and asks; the guard drops anything not in the message."""
    cfg = cfg or settings()
    refs = lookup(message + ' ' + sheets_as_written, drawing_set, ctx)
    user = {'message': message, 'sheets_as_written': sheets_as_written, 'foreman_drawing_set': f'Addendum {drawing_set}',
            'code_lookup': [{k: r[k] for k in ('sheet', 'status', 'title', 'revised_in')} for r in refs]}
    out, meta = _ai(cfg, 'draft_agent.txt', user, DRAFT_SCHEMA)
    draft = {'engine': 'code+ai', **meta, 'title': str(out.get('title', ''))[:120], 'question': str(out.get('question', ''))[:2000],
             'trade': str(out.get('trade', ''))[:80], 'guard_blocked': []}
    asks = [q for q in out.get('questions_for_sub', []) if isinstance(q, dict) and q.get('field') in ASK and isinstance(q.get('ask'), str)]
    for f in ('location', 'needed_by', 'impact'):
        item = out.get(f) if isinstance(out.get(f), dict) else {}
        value, quote = str(item.get('value', '')).strip(), str(item.get('quote', '')).strip()
        ok = bool(item.get('found_in_message')) and supported(value, quote, message)
        if f == 'needed_by' and ok:
            value = parse_date(quote) or ''
            ok = bool(value)
        if item.get('found_in_message') and not ok:
            draft['guard_blocked'].append({'field': f, 'ai_value': value, 'reason': 'not supported by the words of the message'})
        draft[f] = {'value': value if ok else '', 'source': 'message' if ok else 'missing', 'quote': quote if ok else ''}
        if not ok and not any(q['field'] == f for q in asks):
            asks.append({'field': f, 'ask': ASK[f]})
    if (not refs or any(r['status'] != 'current' for r in refs)) and not any(q['field'] == 'references' for q in asks):
        asks.append({'field': 'references', 'ask': ASK['references']})
    draft['references'] = {'text': ', '.join(r['sheet'] for r in refs) or sheets_as_written, 'lookup': refs}
    draft['questions_for_sub'] = asks
    draft['changes'] = [c for c in out.get('changes', []) if isinstance(c, dict)][:6]
    return draft


# --------------------------------------------------------------------------- check agent (GC)
JUDGEMENT = {'type': 'object', 'additionalProperties': False, 'required': ['value', 'reason'], 'properties': {
    'value': {'type': 'string', 'enum': ['yes', 'no', 'unclear']}, 'reason': {'type': 'string'}}}
CHECK_SCHEMA = {'type': 'object', 'additionalProperties': False,
    'required': ['location_specific', 'impact_specific', 'route', 'possible_cost_or_scope', 'separate_questions'],
    'properties': {
        'location_specific': JUDGEMENT, 'impact_specific': JUDGEMENT,
        'route': {'type': 'object', 'additionalProperties': False, 'required': ['value', 'reason'], 'properties': {
            'value': {'type': 'string', 'enum': ['gc_can_answer', 'design_team', 'unclear']}, 'reason': {'type': 'string'}}},
        'possible_cost_or_scope': {'type': 'object', 'additionalProperties': False, 'required': ['value', 'reason'], 'properties': {
            'value': {'type': 'string', 'enum': ['yes', 'no']}, 'reason': {'type': 'string'}}},
        'separate_questions': {'type': 'integer'}}}
PLACEHOLDER = {'', 'tbd', 'n/a', 'na', 'unknown', 'asap', 'none', '-', 'see drawings'}


def code_check(rfi, drawing_set, ctx):
    """The GC checklist without AI: blanks, placeholders, a real date, sheet numbers and revisions."""
    findings = []
    for f, label in (('location', 'Location'), ('impact', 'Impact')):
        if (rfi.get(f) or '').strip().lower() in PLACEHOLDER:
            findings.append({'field': f, 'blocking': True, 'source': 'code', 'message': f'{label} is missing.'})
    if not parse_date(rfi.get('needed_by', '')):
        findings.append({'field': 'needed_by', 'blocking': True, 'source': 'code',
                         'message': f'No response-needed date ("{rfi.get("needed_by", "")}" is not a date).'})
    refs = lookup((rfi.get('references') or '') + ' ' + (rfi.get('question') or ''), drawing_set, ctx)
    if not refs:
        findings.append({'field': 'references', 'blocking': True, 'source': 'code', 'message': 'No drawing sheet number is cited.'})
    for r in refs:
        if r['status'] != 'current':
            findings.append({'field': 'references', 'blocking': True, 'source': 'code', 'message': r['message']})
    return findings, refs


def check_agent(rfi, drawing_set, ctx, cfg=None, use_ai=True):
    findings, refs = code_check(rfi, drawing_set, ctx)
    result = {'engine': 'code', 'references': refs, 'route': None, 'cost_flag': None}
    if use_ai:
        cfg = cfg or settings()
        out, meta = _ai(cfg, 'check_agent.txt', {'rfi': {k: rfi.get(k, '') for k in ('title', 'location', 'trade', 'question', 'needed_by', 'impact', 'references')}}, CHECK_SCHEMA)
        result.update(engine='code+ai', **meta)
        for f, key in (('location', 'location_specific'), ('impact', 'impact_specific')):
            j = out.get(key) or {}
            if j.get('value') == 'no' and not any(x['field'] == f for x in findings):
                findings.append({'field': f, 'blocking': True, 'source': 'AI', 'message': f'{f.title()} may not be specific enough: {j.get("reason", "")}'})
        if _ai_calls['n'] >= MAX_AI_CALLS: raise ValueError(f'AI call budget reached ({MAX_AI_CALLS}).')
        _ai_calls['n'] += 1
        rev = ai_reference_review({k: rfi.get(k, '') for k in ('title', 'location', 'trade', 'question', 'references')}, ctx['index'], cfg=cfg)
        for f in rev['findings']:
            findings.append({'field': 'references', 'blocking': False, 'source': 'AI', 'message': f['message']})
        result['judgements'] = {'location': out.get('location_specific'), 'impact': out.get('impact_specific')}
        result['route'] = out.get('route')
        result['cost_flag'] = out.get('possible_cost_or_scope')
        result['separate_questions'] = out.get('separate_questions')
    blocking = [f for f in findings if f['blocking']]
    if blocking:
        rec = 'return_to_sub'
    elif result['route'] and result['route'].get('value') == 'gc_can_answer':
        rec = 'gc_can_answer'
    else:
        rec = 'forward_to_design'
    result.update(findings=findings, recommendation=rec,
                  needs_pm_cost_review=bool(result['cost_flag'] and result['cost_flag'].get('value') == 'yes'))
    return result


# --------------------------------------------------------------------------- triage agent (design team), code only
def triage_agent(rfis, today=None):
    today = today or DEMO_TODAY
    queue = []
    for r in rfis:
        f = r.get('final') or {}
        d = parse_date(f.get('needed_by', ''), today)
        days = (date.fromisoformat(d) - today).days if d else None
        stops = bool(IMPACT_WORDS.search(f.get('impact', '')))
        score = (1000 - days if days is not None else 0) + (200 if stops else 0)
        why = [f'response needed in {days} days' if days is not None else 'no response date',
               'impact says work is held or delayed' if stops else 'no stated hold on the work']
        queue.append({'rfi_id': r['id'], 'title': f.get('title', ''), 'score': score, 'days_left': days, 'why': why})
    return sorted(queue, key=lambda x: -x['score'])


# --------------------------------------------------------------------------- watch agent (GC), code only
def watch_agent(rfis, addendum, ctx, seen):
    """Called when an addendum is published. Alerts once per (RFI, sheet, addendum): it remembers what it flagged."""
    alerts = []
    issued = next((a for a in ctx['revisions']['addenda'] if a['addendum'] == addendum), None)
    revised = {s['sheet']: s for s in (issued or {}).get('sheets', [])}
    for r in rfis:
        if r['status'] not in ('rough', 'drafted', 'submitted', 'returned', 'cost_review', 'forwarded') or r['drawing_set'] >= addendum:
            continue
        text = ((r.get('final') or {}).get('references') or r['rough'].get('sheets_as_written', '')) + ' ' + \
               ((r.get('final') or {}).get('question') or r['rough']['message'])
        for s in find_sheets(text):
            key = f"{r['id']}|{s}|{addendum}"
            if s in revised and key not in seen:
                seen.add(key)
                alerts.append({'key': key, 'rfi_id': r['id'], 'sheet': s, 'addendum': addendum,
                               'message': f"{s} was revised in Addendum {addendum}; {r['id']} was written from the Addendum "
                                          f"{r['drawing_set']} set. Check whether the question still applies.",
                               'evidence': revised[s]['evidence']})
    return alerts


def due_soon(rfis, today=None, days=5):
    today = today or DEMO_TODAY
    out = []
    for r in rfis:
        if r['status'] not in ('submitted', 'returned', 'cost_review', 'forwarded'): continue
        d = parse_date((r.get('final') or {}).get('needed_by', ''), today)
        if d and date.fromisoformat(d) <= today + timedelta(days=days):
            out.append({'rfi_id': r['id'], 'needed_by': d, 'days_left': (date.fromisoformat(d) - today).days})
    return out
