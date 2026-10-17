"""Post-hoc analysis of the Demo #2 run (no new AI calls).

    python3 scripts/posthoc_code_references.py

Most AI false alarms in Demo #2 were "sheet X is not in the drawing index" when sheet X was in the
index the AI received. This script asks: what if drawing references were judged by code only?
It re-scores the saved AI outputs in results/demo2_general/checks.json after dropping the AI's own
'references' findings (the code lookup still flags missing or unknown sheet numbers).

This analysis was designed AFTER seeing the results, so it is a hypothesis for Demo #3, not a result:
removing the index from the AI's input could also change how it handles the other fields.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = json.loads((ROOT / 'results' / 'demo2_general' / 'checks.json').read_text(encoding='utf-8'))


def lookup_flag(result):
    refs = result.get('references', [])
    return (not refs) or any(r['status'] != 'observed_in_partial_index' for r in refs)


def flags(result, ai_references):
    f = {x['field'] for x in result['findings'] if ai_references or x['field'] != 'references'}
    if lookup_flag(result):
        f.add('references')
    return f


def score(pairs):
    found = sum(len(e & f) for e, f in pairs)
    total = sum(len(e) for e, _ in pairs)
    alarms = sum(len(f - e) for e, f in pairs)
    clean_flagged = sum(1 for e, f in pairs if not e and f)
    clean_total = sum(1 for e, _ in pairs if not e)
    return found, total, alarms, clean_flagged, clean_total


runs = data['runs']
lines = ['# Post-hoc: drawing references judged by code only', '',
         'Designed after seeing the Demo #2 results. Re-scores the saved AI outputs; no new AI calls.', '',
         '| Run | AI as run: found | false alarms | complete RFIs flagged | Code-only references: found | false alarms | complete RFIs flagged |',
         '|---|---|---|---|---|---|---|']
for r in range(runs):
    a, b = [], []
    for case in data['cases']:
        run = case['ai_runs'][r]
        if 'output' not in run:
            continue
        exp = set(case['expected_flags'])
        a.append((exp, flags(run['output'], True)))
        b.append((exp, flags(run['output'], False)))
    sa, sb = score(a), score(b)
    lines.append(f'| {r + 1} | {sa[0]}/{sa[1]} | {sa[2]} | {sa[3]}/{sa[4]} | {sb[0]}/{sb[1]} | {sb[2]} | {sb[3]}/{sb[4]} |')

lines += ['', '## AI "references" findings that the code lookup contradicts (sheet is in the index)', '']
index = json.loads((ROOT / 'data' / 'drawing_index.json').read_text(encoding='utf-8'))
for case in data['cases']:
    for run in case['ai_runs']:
        for f in run.get('output', {}).get('findings', []):
            if f['field'] == 'references' and 'references' not in case['expected_flags']:
                named = [s for s in index if s in f['message']]
                lines.append(f"- {case['case_id']} run {run['run']}: \"{f['message']}\"" + (f' (in index: {", ".join(named)})' if named else ''))
out = ROOT / 'results' / 'demo2_general' / 'posthoc_code_references.md'
out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('\n'.join(lines))
print(f'\nSaved: {out.relative_to(ROOT)}')
