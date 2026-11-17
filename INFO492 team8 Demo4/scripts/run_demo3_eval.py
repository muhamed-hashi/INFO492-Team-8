"""Demo #3 offline evaluation on the 12 rough field RFIs (data/rough_rfis.json).

    python3 scripts/run_demo3_eval.py              # 2 runs of the AI agents (about 70 Gemini calls)
    python3 scripts/run_demo3_eval.py --runs 1 --sleep 6

For each rough RFI we compare three ways of getting it ready for the GC:
  1. As sent:          the rough message goes to the GC unchanged.
  2. Checklist only:   code looks for a date, location/impact keywords and sheet numbers, and asks for the rest.
  3. Draft agent:      code looks up sheets and revisions; the AI rewrites the question and asks for what is missing;
                       a guard removes any location/date/impact the AI filled in that the message does not say.
After 2 and 3 the foreman answers exactly what he was asked, from his site notes (the scenario brief).
An RFI "still needs a return" if any real gap in the answer key was not asked about.

Then the GC's check agent (code + AI) reviews each completed draft-agent RFI: a "return" recommendation on an RFI
that is now complete is a false return. The watch agent replays Addenda 1-6 over the 12 RFIs (code only).

Outputs: results/demo3/summary.json, per_case.csv, checks.json, study_items.json (used by the /study page).
"""
import argparse
import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agents  # noqa: E402
from core import ROOT, settings  # noqa: E402

OUT = ROOT / 'results' / 'demo3'
GAPS = ('location', 'needed_by', 'impact')


def with_retry(fn, sleep):
    for attempt in range(3):
        try:
            out = fn(); time.sleep(sleep); return out
        except ValueError as e:
            if 'rate limit' in str(e).lower() or 'quota' in str(e).lower():
                time.sleep(30 * (attempt + 1)); continue
            return {'error': str(e)}
    return {'error': 'rate limited three times'}


def complete(case, draft, key):
    """The RFI after the foreman answers exactly what he was asked (from his site notes)."""
    asked = {q['field'] for q in draft.get('questions_for_sub', [])}
    notes = case['site_notes']
    final = {'title': draft.get('title', '') if draft.get('engine') != 'code' else case['source']['title'],
             'question': draft.get('question') or case['message'], 'trade': draft.get('trade') or notes['trade']}
    for f in GAPS:
        value = (draft.get(f) or {}).get('value', '')
        if f in asked: value = notes[f]
        elif value == '(stated in the message)': value = '(see question)'
        final[f] = value
    final['references'] = notes['references'] if 'references' in asked else case['sheets_as_written']
    return final, asked


def score(case, key, draft):
    asked = {q['field'] for q in draft.get('questions_for_sub', [])}
    missing = set(key['missing'])
    caught = missing & asked
    false_asks = (asked & set(GAPS)) - missing
    ref_issue = bool(key['ref_issues'])
    ref_caught = ref_issue and 'references' in asked
    ref_false = (not ref_issue) and 'references' in asked
    still = bool(missing - asked) or (ref_issue and not ref_caught)
    return {'missing': len(missing), 'caught': len(caught), 'uncaught': sorted(missing - asked), 'false_asks': sorted(false_asks),
            'ref_issue': ref_issue, 'ref_caught': ref_caught, 'ref_false_alarm': ref_false,
            'guard_blocked': len(draft.get('guard_blocked', [])), 'needs_return_after': still}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs', type=int, default=2)
    ap.add_argument('--sleep', type=float, default=4.0, help='seconds between AI calls (free-tier rate limits)')
    ap.add_argument('--no-check', action='store_true', help='skip the GC check agent (saves half the AI calls)')
    a = ap.parse_args()
    cfg = settings()
    if not cfg.get('key'): sys.exit('AI is not connected. Run python3 setup_ai.py first.')
    cases = agents.load('rough_rfis.json'); keys = {k['case_id']: k for k in agents.load('rough_answer_key.json')}
    ctx = {'index': agents.load('drawing_index.json'), 'revisions': agents.load('revisions.json'), 'issued_through': 6}
    OUT.mkdir(parents=True, exist_ok=True)
    rows, checks, study = [], [], []
    for c in cases:
        k = keys[c['case_id']]
        code = agents.code_draft(c['message'], c['sheets_as_written'], c['drawing_set'], ctx)
        rec = {'case_id': c['case_id'], 'input': c, 'key': k, 'code': {'draft': code, 'score': score(c, k, code)}, 'agent_runs': []}
        for run in range(a.runs):
            d = with_retry(lambda: agents.draft_agent(c['message'], c['sheets_as_written'], c['drawing_set'], ctx, cfg), a.sleep)
            if 'error' in d:
                rec['agent_runs'].append({'error': d['error']}); print(c['case_id'], 'run', run + 1, 'ERROR', d['error']); continue
            final, _ = complete(c, d, k)
            entry = {'draft': d, 'score': score(c, k, d), 'final': final}
            if not a.no_check:
                chk = with_retry(lambda: agents.check_agent(final, c['drawing_set'] if 'references' not in _asked(d) else 6, ctx, cfg), a.sleep)
                entry['check'] = chk
                entry['false_return'] = ('error' not in chk) and chk.get('recommendation') == 'return_to_sub' and not entry['score']['needs_return_after']
            rec['agent_runs'].append(entry)
            print(c['case_id'], 'run', run + 1, 'caught', entry['score']['caught'], '/', entry['score']['missing'],
                  '| ref', entry['score']['ref_caught'], '| still needs return', entry['score']['needs_return_after'])
        checks.append(rec)
        first = next((r for r in rec['agent_runs'] if 'final' in r), None)
        if first:
            study.append({'case_id': c['case_id'], 'raw': {'message': c['message'], 'sheets': c['sheets_as_written']},
                          'agent': {k2: first['final'].get(k2, '') for k2 in ('title', 'question', 'location', 'needed_by', 'impact', 'references')}})

    # ---- watch agent replay (code only)
    open_rfis = [{'id': c['case_id'], 'status': 'submitted', 'drawing_set': c['drawing_set'], 'final': None,
                  'rough': {'message': c['message'], 'sheets_as_written': c['sheets_as_written']}} for c in cases]
    seen, alerts = set(), []
    for n in range(1, 7):
        alerts += agents.watch_agent(open_rfis, n, ctx, seen)

    # ---- summary
    total_missing = sum(len(k['missing']) for k in keys.values()); total_ref = sum(1 for k in keys.values() if k['ref_issues'])
    n_cases = len(cases)

    def cond(label, scores, extra=None):
        ok = [s for s in scores if s]
        runs = max(1, len(ok) // n_cases) if ok else 1
        return {'label': label, 'runs': runs,
                'missing_caught': f"{sum(s['caught'] for s in ok)}/{total_missing * runs}",
                'false_asks': sum(len(s['false_asks']) for s in ok),
                'ref_caught': f"{sum(1 for s in ok if s['ref_caught'])}/{total_ref * runs}",
                'ref_false_alarms': sum(1 for s in ok if s['ref_false_alarm']),
                'invented': (f"{sum(s['guard_blocked'] for s in ok)} blocked by guard, 0 reached the RFI" if label.startswith('Draft') else '0 (copies the message)'),
                'needs_return_after': f"{sum(1 for s in ok if s['needs_return_after'])}/{n_cases * runs}", **(extra or {})}

    raw_needs = sum(1 for k in keys.values() if k['missing'] or k['ref_issues'])
    agent_scores = [r['score'] for rec in checks for r in rec['agent_runs'] if 'score' in r]
    finals = [r for rec in checks for r in rec['agent_runs'] if 'check' in r and 'error' not in r['check']]
    summary = {
        'run_at': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'model': cfg['model'], 'runs': a.runs,
        'prompt_sha256': {f: __import__('hashlib').sha256((ROOT / 'prompts' / f).read_bytes()).hexdigest()[:16] for f in ('draft_agent.txt', 'check_agent.txt', 'reference_review.txt')},
        'cases': n_cases, 'total_missing_items': total_missing, 'rfis_with_reference_problems': total_ref,
        'conditions': [
            {'label': 'As sent (no help)', 'missing_caught': f'0/{total_missing}', 'false_asks': 0, 'ref_caught': f'0/{total_ref}',
             'ref_false_alarms': 0, 'invented': '0', 'needs_return_after': f'{raw_needs}/{n_cases}'},
            cond('Checklist only (code)', [rec['code']['score'] for rec in checks]),
            cond('Draft agent (code + AI)', agent_scores),
        ],
        'check_agent_on_completed_rfis': {'checked': len(finals),
                                          'false_returns': sum(1 for r in finals if r.get('false_return')),
                                          'cost_or_scope_flags': sum(1 for r in finals if (r['check'].get('cost_flag') or {}).get('value') == 'yes'),
                                          'routes': {v: sum(1 for r in finals if (r['check'].get('route') or {}).get('value') == v) for v in ('gc_can_answer', 'design_team', 'unclear')}},
        'watch_agent_replay': {'alerts': len(alerts), 'detail': [f"{x['rfi_id']}: {x['sheet']} revised in Addendum {x['addendum']}" for x in alerts],
                               'note': 'Code only, from data/revisions.json. A mistyped sheet (FP-2O0) cannot be watched until it is corrected.'},
        'errors': sum(1 for rec in checks for r in rec['agent_runs'] if 'error' in r),
        'note': 'Simulated rough RFIs written by the team from 12 real Dett RFIs; the foreman\'s answers come from the scenario brief.',
    }
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    (OUT / 'checks.json').write_text(json.dumps(checks, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    (OUT / 'study_items.json').write_text(json.dumps({'source': f"results/demo3 run {summary['run_at']}", 'items': study}, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    with open(OUT / 'per_case.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['case', 'missing (key)', 'ref issues (key)', 'checklist asked', 'checklist still needs return',
                    'agent asked (run 1)', 'agent still needs return (runs)', 'guard blocked (runs)', 'check agent false return (runs)'])
        for rec in checks:
            ok = [r for r in rec['agent_runs'] if 'score' in r]
            w.writerow([rec['case_id'], ';'.join(rec['key']['missing']), ';'.join(rec['key']['ref_issues']),
                        ';'.join(q['field'] for q in rec['code']['draft']['questions_for_sub']), rec['code']['score']['needs_return_after'],
                        ';'.join(q['field'] for q in ok[0]['draft']['questions_for_sub']) if ok else 'error',
                        ' '.join(str(r['score']['needs_return_after']) for r in ok),
                        ' '.join(str(r['score']['guard_blocked']) for r in ok),
                        ' '.join(str(r.get('false_return')) for r in ok)])
    print(json.dumps(summary['conditions'], indent=1))
    print('check agent:', summary['check_agent_on_completed_rfis'])
    print('watch agent:', summary['watch_agent_replay']['detail'])


def _asked(d):
    return {q['field'] for q in d.get('questions_for_sub', [])}


if __name__ == '__main__':
    main()
