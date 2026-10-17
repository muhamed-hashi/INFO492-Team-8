"""Demo #2, first run (all fields, 24 general cases): run the rule checklist and the Gemini check on every case, then score both.

    python3 scripts/run_eval.py              # 3 AI runs per case (about 7 minutes)
    python3 scripts/run_eval.py --runs 1     # quicker, one AI run per case
    python3 scripts/run_eval.py --rules-only # no AI, no key needed

Each case is checked on its unedited draft. A checker "flags" a field when it returns a finding
for it. Drawing numbers are also looked up in data/drawing_index.json by code; a number that is
not in the index, or no sheet number at all, counts as a references flag. That lookup is the same
code for both checkers, so it does not favour either one.

Scores come from data/answer_key.json (the defects we planted). Output: results/demo2_general/
"""
import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402

SHEET = re.compile(r'\b[A-Za-z]{1,4}-?\d{3}[A-Za-z]?\b')


def lookup_flag(result):
    refs = result.get('references', [])
    return (not refs) or any(r['status'] != 'observed_in_partial_index' for r in refs)


def flagged(result):
    fields = {f['field'] for f in result['findings']}
    if lookup_flag(result):
        fields.add('references')
    return fields


def invented_sheets(result, rfi, index):
    """Sheet numbers the AI wrote that are neither in the RFI nor in the drawing index."""
    known = {core.normalize_sheet(k) for k in index}
    supplied = {core.normalize_sheet(s) for s in SHEET.findall(rfi['references'] + ' ' + rfi['question'])}
    text = result.get('summary', '') + ' ' + ' '.join(f['message'] + ' ' + f['follow_up'] for f in result['findings'])
    return sorted({s.upper() for s in SHEET.findall(text) if core.normalize_sheet(s) not in known | supplied})


def run_ai(rfi, index, tries=5):
    for attempt in range(tries):
        try:
            return core.ai_check(rfi, index), None
        except ValueError as exc:
            msg = str(exc)
            if ('rate limit' in msg or 'quota' in msg or 'did not finish' in msg or 'timed out' in msg) and attempt < tries - 1:
                wait = 20 * (attempt + 1)
                print(f'      busy or limited, waiting {wait}s and retrying...', flush=True)
                time.sleep(wait)
                continue
            return None, msg


def score(rows, checker):
    """rows: list of (case_id, expected set, flags set or None)."""
    done = [(c, e, f) for c, e, f in rows if f is not None]
    exp_total = sum(len(e) for _, e, _ in done)
    found = sum(len(e & f) for _, e, f in done)
    extra = sum(len(f - e) for _, e, f in done)
    clean = [(c, e, f) for c, e, f in done if not e]
    bad = [(c, e, f) for c, e, f in done if e]
    return {
        'checker': checker, 'scored': len(done), 'failed': len(rows) - len(done),
        'found': found, 'expected': exp_total, 'missed': exp_total - found, 'false_alarms': extra,
        'clean_flagged': sum(1 for _, _, f in clean if f), 'clean_total': len(clean),
        'bad_fully_caught': sum(1 for _, e, f in bad if e <= f), 'bad_total': len(bad),
        'ready_correct': sum(1 for _, e, f in done if (not f) == (not e)),
    }


def pct(a, b):
    return f'{a}/{b} ({round(100 * a / b)}%)' if b else '-'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs', type=int, default=3, help='AI runs per case (default 3)')
    ap.add_argument('--model', default=core.GEMINI_MODEL_DEFAULT, help='Gemini model (default: same as Demo 1)')
    ap.add_argument('--rules-only', action='store_true')
    ap.add_argument('--pause', type=float, default=4.0, help='seconds between AI calls (free-tier limit)')
    args = ap.parse_args()

    os.environ['AI_PROVIDER'] = 'gemini'
    os.environ['GEMINI_MODEL'] = args.model
    cases = core.load_json('cases.json')
    key = {k['case_id']: set(k.get('expected_flags', k.get('expected_missing_fields', []))) for k in core.load_json('answer_key.json')}
    variants = {k['case_id']: k.get('variant', '') for k in core.load_json('answer_key.json')}
    index = core.load_json('drawing_index.json')
    runs = 0 if args.rules_only else args.runs
    if runs and not core.settings()['key']:
        sys.exit('No Gemini key found. Run: python3 setup_ai.py   (or use --rules-only)')

    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    out = ROOT / 'results' / 'demo2_general'
    out.mkdir(parents=True, exist_ok=True)
    audit, per_case = [], []
    rule_rows, ai_rows = [], [[] for _ in range(runs)]
    invented_total, failures = 0, []

    print(f'Demo 2 evaluation: {len(cases)} cases, rule checklist + {runs} AI run(s), model {args.model if runs else "-"}')
    for n, case in enumerate(cases, 1):
        cid, rfi, exp = case['case_id'], case['initial'], key[case['case_id']]
        rules = core.rule_check(rfi, index)
        rf = flagged(rules)
        rule_rows.append((cid, exp, rf))
        row = {'case_id': cid, 'variant': variants[cid], 'expected': ';'.join(sorted(exp)),
               'rule_flags': ';'.join(sorted(rf)), 'rule_missed': ';'.join(sorted(exp - rf)),
               'rule_extra': ';'.join(sorted(rf - exp))}
        record = {'case_id': cid, 'variant': variants[cid], 'expected_flags': sorted(exp), 'input': rfi,
                  'rule_check': rules, 'ai_runs': []}
        flag_sets = []
        for r in range(runs):
            if n > 1 or r > 0:
                time.sleep(args.pause)
            result, error = run_ai(rfi, index)
            if result is None:
                failures.append(f'{cid} run {r + 1}: {error}')
                ai_rows[r].append((cid, exp, None))
                record['ai_runs'].append({'run': r + 1, 'error': error})
                flag_sets.append(None)
                continue
            af = flagged(result)
            inv = invented_sheets(result, rfi, index)
            invented_total += len(inv)
            ai_rows[r].append((cid, exp, af))
            flag_sets.append(af)
            record['ai_runs'].append({'run': r + 1, 'flags': sorted(af), 'invented_sheets': inv, 'output': result})
        if runs:
            first = flag_sets[0]
            ok = [f for f in flag_sets if f is not None]
            row.update({'ai_flags_run1': ';'.join(sorted(first)) if first is not None else 'FAILED',
                        'ai_missed_run1': ';'.join(sorted(exp - first)) if first is not None else '',
                        'ai_extra_run1': ';'.join(sorted(first - exp)) if first is not None else '',
                        'ai_same_all_runs': len(ok) == runs and all(f == ok[0] for f in ok),
                        'ai_flags_all_runs': ' | '.join((';'.join(sorted(f)) or '-') if f is not None else 'FAILED' for f in flag_sets)})
        per_case.append(row)
        audit.append(record)
        status = '' if not runs else f"  AI: {row['ai_flags_run1'] or '-'}"
        print(f"  [{n:2}/{len(cases)}] {cid} expected: {row['expected'] or '-':22} rules: {row['rule_flags'] or '-':22}{status}", flush=True)

    rs = score(rule_rows, 'Rule checklist (no AI)')
    ai_scores = [score(rows, f'AI run {i + 1}') for i, rows in enumerate(ai_rows)]

    (out / 'checks.json').write_text(json.dumps({'run_at': stamp, 'model': args.model if runs else None,
        'runs': runs, 'prompt_sha256': core.hashlib.sha256((ROOT / 'prompts' / 'review.txt').read_bytes()).hexdigest(),
        'cases': audit}, indent=2, ensure_ascii=False), encoding='utf-8')
    with open(out / 'per_case.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(per_case[0]))
        w.writeheader()
        w.writerows(per_case)

    cols = [rs] + ai_scores[:1]
    head = '| Measure | ' + ' | '.join(c['checker'].replace('AI run 1', 'AI (run 1)') for c in cols) + ' |'
    lines = [
        '# Demo #2 first run: all fields, 24 general cases', '',
        f'Run: {stamp}. {len(cases)} simulated RFIs ({rs["bad_total"]} with planted defects, {rs["clean_total"]} complete), '
        f'each checked on its unedited draft. Model: {args.model if runs else "none (rules only)"}. Prompt unchanged from Demo #1.', '',
        head, '|---' * (len(cols) + 1) + '|',
        '| Planted defects found | ' + ' | '.join(pct(c['found'], c['expected']) for c in cols) + ' |',
        '| Defects missed | ' + ' | '.join(str(c['missed']) for c in cols) + ' |',
        '| False alarms (flags on fields that were fine) | ' + ' | '.join(str(c['false_alarms']) for c in cols) + ' |',
        '| Complete RFIs wrongly flagged | ' + ' | '.join(f"{c['clean_flagged']}/{c['clean_total']}" for c in cols) + ' |',
        '| Defective RFIs fully caught | ' + ' | '.join(f"{c['bad_fully_caught']}/{c['bad_total']}" for c in cols) + ' |',
        '| "Ready to send" decision correct | ' + ' | '.join(f"{c['ready_correct']}/{c['scored']}" for c in cols) + ' |',
        '| Failed calls | ' + ' | '.join(str(c['failed']) for c in cols) + ' |', '',
    ]
    if runs:
        same = sum(1 for r in per_case if r['ai_same_all_runs'])
        lines += [f'AI invented sheet numbers (all runs): {invented_total}.']
        if runs > 1:
            lines += ['Across runs, AI defects found: ' + ', '.join(f"{s['found']}/{s['expected']}" for s in ai_scores)
                      + '; false alarms: ' + ', '.join(str(s['false_alarms']) for s in ai_scores)
                      + f'. Same flags in every run: {same}/{len(cases)} cases.']
        lines.append('')
    lines += ['## Per case (run 1)', '', '| Case | Planted defect | Expected | Rules | AI |', '|---|---|---|---|---|']
    for r in per_case:
        lines.append(f"| {r['case_id']} | {r['variant']} | {r['expected'] or '-'} | {r['rule_flags'] or '-'} | {r.get('ai_flags_run1', 'not run') or '-'} |")
    if runs:
        lines += ['', '## AI flags outside the answer key (run 1) - team to judge: useful or unnecessary?', '']
        for rec in audit:
            first = rec['ai_runs'][0] if rec['ai_runs'] else {}
            for f in first.get('output', {}).get('findings', []):
                if f['field'] not in rec['expected_flags']:
                    lines.append(f"- {rec['case_id']} ({rec['variant']}), {f['field']}: {f['message']}")
        lines += ['', '## AI misses (run 1)', '']
        misses = [f"- {r['case_id']} ({r['variant']}): {r['ai_missed_run1']}" for r in per_case if r.get('ai_missed_run1')]
        lines += misses or ['- none']
    if failures:
        lines += ['', '## Failed calls', ''] + [f'- {x}' for x in failures]
    (out / 'summary.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n' + '\n'.join(lines[:14 + (3 if runs else 0)]))
    print(f'\nSaved: results/demo2_general/summary.md, per_case.csv, checks.json')


if __name__ == '__main__':
    main()
