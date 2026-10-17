"""Demo #2 ("check references") evaluation.

    python3 scripts/run_reference_eval.py            # 3 AI runs per case (about 15 minutes)
    python3 scripts/run_reference_eval.py --runs 1   # quicker
    python3 scripts/run_reference_eval.py --code-only

24 cases from data/reference_cases.json: 12 with correct sheet numbers, 12 with one reference
problem (nonexistent sheet, typo, real-but-unrelated sheet, or no sheet number). Three ways to check:

  code     the drawing-index lookup alone (no AI)
  ai_only  the AI as in Demo #1: it sees the RFI and the list of sheet numbers and judges everything
           itself (prompts/review.txt). Only its findings on the references field are scored.
  code_ai  the Demo #2 design: code does the lookup; the AI gets the lookup and each sheet's title and
           judges whether the sheet fits the question or looks mistyped (prompts/reference_review.txt).

Labels come from data/reference_answer_key.json. Output: results/demo2_references/
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

KINDS = ['nonexistent', 'typo', 'unrelated', 'vague']
NEGATION = re.compile(r"(not|n't|missing|absent)\b[^.]{0,60}\bindex|index[^.]{0,40}\b(not|n't|missing)", re.I)


def retry(fn, tries=5):
    for attempt in range(tries):
        try:
            return fn(), None
        except ValueError as exc:
            msg = str(exc)
            if any(w in msg for w in ('rate limit', 'quota', 'did not finish', 'timed out', 'Could not reach')) and attempt < tries - 1:
                wait = 20 * (attempt + 1)
                print(f'      busy or limited, waiting {wait}s and retrying...', flush=True)
                time.sleep(wait)
                continue
            return None, msg


def wrong_index_claims(findings, index):
    """AI messages that say a sheet is missing from the index when the sheet IS in the index."""
    out = []
    for f in findings:
        text = f['message'] + ' ' + f.get('follow_up', '')
        named = [s for s in index if re.search(r'\b' + re.escape(s) + r'\b', text)]
        if named and NEGATION.search(text):
            out.append(f"{', '.join(named)}: {f['message']}")
    return out


def score(rows):
    """rows: (case_id, kind or 'clean', flagged bool or None)."""
    done = [r for r in rows if r[2] is not None]
    prob = [r for r in done if r[1] != 'clean']
    clean = [r for r in done if r[1] == 'clean']
    by = {k: (sum(1 for r in prob if r[1] == k and r[2]), sum(1 for r in prob if r[1] == k)) for k in KINDS}
    return {'caught': sum(1 for r in prob if r[2]), 'problems': len(prob),
            'clean_flagged': sum(1 for r in clean if r[2]), 'clean': len(clean),
            'correct': sum(1 for r in done if r[2] == (r[1] != 'clean')), 'scored': len(done),
            'failed': len(rows) - len(done), 'by_kind': by}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs', type=int, default=3)
    ap.add_argument('--model', default=core.GEMINI_MODEL_DEFAULT)
    ap.add_argument('--code-only', action='store_true')
    ap.add_argument('--pause', type=float, default=4.0, help='seconds between AI calls (free-tier limit)')
    args = ap.parse_args()
    os.environ['AI_PROVIDER'] = 'gemini'
    os.environ['GEMINI_MODEL'] = args.model
    runs = 0 if args.code_only else args.runs

    cases = core.load_json('reference_cases.json')
    key = {k['case_id']: k for k in core.load_json('reference_answer_key.json')}
    index = core.load_json('drawing_index.json')
    cfg = core.settings()
    if runs and not cfg['key']:
        sys.exit('No Gemini key found. Run: python3 setup_ai.py   (or use --code-only)')

    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    out = ROOT / 'results' / 'demo2_references'
    out.mkdir(parents=True, exist_ok=True)
    code_rows, ai_rows, hy_rows = [], [[] for _ in range(runs)], [[] for _ in range(runs)]
    audit, per_case, failures, wrong_claims = [], [], [], []
    calls = 0
    print(f'Demo 2 reference check: {len(cases)} cases, code lookup + {runs} AI run(s) of 2 methods, model {args.model if runs else "-"}')
    for n, case in enumerate(cases, 1):
        cid, rfi, k = case['case_id'], case['initial'], key[case['case_id']]
        kind = k['variant'] if k['reference_problem'] else 'clean'
        refs = core.reference_check(rfi, index)
        code_find = core.code_reference_findings(refs)
        code_flag = bool(code_find)
        code_rows.append((cid, kind, code_flag))
        rec = {'case_id': cid, 'kind': kind, 'change': k['change'], 'input': rfi, 'code_lookup': refs,
               'code_findings': code_find, 'ai_only_runs': [], 'code_ai_runs': []}
        ai_flags, hy_flags = [], []
        for r in range(runs):
            if calls:
                time.sleep(args.pause)
            res, err = retry(lambda: core.ai_check(rfi, index))
            calls += 1
            if res is None:
                failures.append(f'{cid} ai_only run {r + 1}: {err}')
                ai_rows[r].append((cid, kind, None)); ai_flags.append(None)
                rec['ai_only_runs'].append({'run': r + 1, 'error': err})
            else:
                ref_find = [f for f in res['findings'] if f['field'] == 'references']
                flag = bool(ref_find)
                claims = wrong_index_claims(ref_find, index)
                wrong_claims += [f'{cid} run {r + 1} - {c}' for c in claims]
                ai_rows[r].append((cid, kind, flag)); ai_flags.append(flag)
                rec['ai_only_runs'].append({'run': r + 1, 'flag': flag, 'reference_findings': ref_find,
                                            'wrong_index_claims': claims, 'output': res})
            time.sleep(args.pause)
            rev, err = retry(lambda: core.ai_reference_review(rfi, index, refs, cfg))
            calls += 1
            if rev is None:
                failures.append(f'{cid} code_ai run {r + 1}: {err}')
                hy_rows[r].append((cid, kind, None)); hy_flags.append(None)
                rec['code_ai_runs'].append({'run': r + 1, 'error': err})
            else:
                flag = code_flag or rev['flag']
                hy_rows[r].append((cid, kind, flag)); hy_flags.append(flag)
                rec['code_ai_runs'].append({'run': r + 1, 'flag': flag, 'review': rev})
        fmt = lambda fl: ' '.join('-' if f is None else ('FLAG' if f else 'ok') for f in fl)
        row = {'case_id': cid, 'kind': kind, 'change': k['change'], 'references': rfi['references'],
               'code': 'FLAG' if code_flag else 'ok', 'ai_only_runs': fmt(ai_flags), 'code_ai_runs': fmt(hy_flags)}
        per_case.append(row); audit.append(rec)
        print(f"  [{n:2}/{len(cases)}] {cid} {kind:11} code: {row['code']:4}  AI only: {row['ai_only_runs'] or '-':14}  code+AI: {row['code_ai_runs'] or '-'}", flush=True)

    sc = score(code_rows)
    sa = [score(x) for x in ai_rows]
    sh = [score(x) for x in hy_rows]
    (out / 'checks.json').write_text(json.dumps({'run_at': stamp, 'model': args.model if runs else None, 'runs': runs,
        'prompts': {p: core.hashlib.sha256((ROOT / 'prompts' / p).read_bytes()).hexdigest() for p in ('review.txt', 'reference_review.txt')},
        'cases': audit}, indent=2, ensure_ascii=False), encoding='utf-8')
    with open(out / 'per_case.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(per_case[0])); w.writeheader(); w.writerows(per_case)

    cols = [('Code lookup only', sc)] + ([('AI only (Demo 1 design), run 1', sa[0]), ('Code + AI (Demo 2 design), run 1', sh[0])] if runs else [])
    L = ['# Demo #2 results: check references', '',
         f'Run: {stamp}. {len(cases)} simulated RFIs: {sc["problems"]} with one reference problem, {sc["clean"]} with correct sheet numbers. '
         f'Model: {args.model if runs else "none"}.', '',
         '| Measure | ' + ' | '.join(c for c, _ in cols) + ' |', '|---' * (len(cols) + 1) + '|',
         '| Reference problems caught | ' + ' | '.join(f"{s['caught']}/{s['problems']}" for _, s in cols) + ' |']
    for kd in KINDS:
        L.append(f'| - {kd} | ' + ' | '.join(f"{s['by_kind'][kd][0]}/{s['by_kind'][kd][1]}" for _, s in cols) + ' |')
    L += ['| Correct references wrongly flagged | ' + ' | '.join(f"{s['clean_flagged']}/{s['clean']}" for _, s in cols) + ' |',
          '| Cases judged correctly | ' + ' | '.join(f"{s['correct']}/{s['scored']}" for _, s in cols) + ' |',
          '| Failed calls | ' + ' | '.join(str(s['failed']) for _, s in cols) + ' |', '']
    if runs:
        L.append('All runs - problems caught: AI only ' + ', '.join(f"{s['caught']}/{s['problems']}" for s in sa)
                 + '; code + AI ' + ', '.join(f"{s['caught']}/{s['problems']}" for s in sh)
                 + '. Correct references wrongly flagged: AI only ' + ', '.join(str(s['clean_flagged']) for s in sa)
                 + '; code + AI ' + ', '.join(str(s['clean_flagged']) for s in sh) + '.')
        L.append(f'AI-only messages claiming an indexed sheet is missing from the index (all runs): {len(wrong_claims)}.')
        L.append('')
    L += ['## Per case', '', '| Case | Problem | References as written | Code | AI only (runs) | Code + AI (runs) |', '|---|---|---|---|---|---|']
    L += [f"| {r['case_id']} | {r['kind']} | {r['references']} | {r['code']} | {r['ai_only_runs'] or '-'} | {r['code_ai_runs'] or '-'} |" for r in per_case]
    if runs:
        L += ['', '## AI-only: claims that an indexed sheet is missing', ''] + ([f'- {c}' for c in wrong_claims] or ['- none'])
        L += ['', '## Code + AI: what the AI said (run 1) - team to judge', '']
        for rec in audit:
            run = rec['code_ai_runs'][0] if rec['code_ai_runs'] else {}
            for f in run.get('review', {}).get('findings', []):
                L.append(f"- {rec['case_id']} ({rec['kind']}): {f['message']}")
    if failures:
        L += ['', '## Failed calls', ''] + [f'- {x}' for x in failures]
    (out / 'summary.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    print('\n' + '\n'.join(L[:16 + (3 if runs else 0)]))
    print('\nSaved: results/demo2_references/summary.md, per_case.csv, checks.json')


if __name__ == '__main__':
    main()
