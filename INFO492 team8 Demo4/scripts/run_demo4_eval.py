"""Demo #4 evaluation on REAL data: can the close-out agent stop RFIs being closed while a promised drawing change
is missing, and how often does it get it wrong?

    python3 scripts/run_demo4_eval.py                 # code + AI on the 108 real Dett RFIs (2 runs) + stakeholder set
    python3 scripts/run_demo4_eval.py --code-only     # no AI, no network
    python3 scripts/run_demo4_eval.py --synthetic     # also the two synthetic stress-test sets (not the headline)
    python3 scripts/run_demo4_eval.py --rescore       # no new AI calls: re-score the saved real_log.csv against the
                                                      # current hand labels (run this after the labels come in)

Data, all real unless marked:
  real Dett log    data/source_rfis.csv: 108 answered RFIs from a public school project (PBC Chicago, 2023), checked
                   against the drawing lists actually attached to each addendum (data/addendum_drawing_lists.json).
  right answers    data/dett_labels/labels.csv: for every RFI the code check or the agent stopped, our stakeholder's
                   call (scripts/make_review_sheet.py makes his review sheet). Other people can be added as labelers;
                   if two disagree, data/dett_labels/adjudicated.csv settles it. RFIs nobody stopped are not labeled,
                   so misses are only visible where one method stopped an RFI and the other did not.
  stakeholder      data/kevin/closeout_cases.json: real examples from our stakeholder's projects, anonymized and
                   labeled (scripts/import_kevin.py). Used when present.
  synthetic        data/closeout_cases.json, data/closeout_cases_messy.json: real answers with planted problems.
                   Only with --synthetic; reported separately as stress tests.

Errors are reported at two points, because "0 errors" only says what reached the next person:
  1. the agent's recommendation, before any person looks:
       right               recommendation equals the hand label
       missed problem      the label says do not close yet, the tool says "ok to close". The dangerous error:
                           if the PM trusts the tool, the RFI is closed too early.
       false alarm         the label says ok to close, the tool says anything else: costs the PM time.
  2. what would reach the field if the PM followed every recommendation = missed problems. A "check" or "hold"
     always goes to a person, so those mistakes are caught at the PM step.

Outputs: results/demo4/summary.json, real_log.csv (every RFI, both methods, the hand label), per_case.csv
(stakeholder and synthetic sets), real_flags_for_review.csv
"""
import argparse
import csv
import json
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agents  # noqa: E402
import closeout  # noqa: E402
from core import ROOT, settings  # noqa: E402

OUT = ROOT / 'results' / 'demo4'
LABELS = ROOT / 'data' / 'dett_labels'
SYNTHETIC = [('tidy (synthetic)', ROOT / 'data' / 'closeout_cases.json'), ('messy (synthetic)', ROOT / 'data' / 'closeout_cases_messy.json')]
KEVIN = ROOT / 'data' / 'kevin' / 'closeout_cases.json'
VALID = {'ok_to_close', 'keep_open', 'hold', 'check'}
TRANSIENT = ('rate limit', 'quota', 'http 503', 'http 500', 'http 502', 'http 504', 'could not reach')


def with_retry(fn, sleep):
    for attempt in range(4):
        try:
            out = fn(); time.sleep(sleep); return out
        except ValueError as e:
            if any(t in str(e).lower() for t in TRANSIENT) and attempt < 3:
                time.sleep(20 * (attempt + 1)); continue
            return {'error': str(e)}
    return {'error': 'failed four times'}


def hand_labels():
    """Final label per RFI: the label if one person labeled it or two agreed; the adjudicated label otherwise."""
    by = defaultdict(list)
    if (LABELS / 'labels.csv').exists():
        for r in csv.DictReader(open(LABELS / 'labels.csv', encoding='utf-8')):
            lab = (r.get('label') or '').strip()
            if lab in VALID and (r.get('labeler') or '').strip():
                by[r['source_id'].strip()].append((r['labeler'].strip(), lab))
    adj = {}
    if (LABELS / 'adjudicated.csv').exists():
        for r in csv.DictReader(open(LABELS / 'adjudicated.csv', encoding='utf-8')):
            if (r.get('final_label') or '').strip() in VALID: adj[r['source_id'].strip()] = r['final_label'].strip()
    final, double, agree, disputed = {}, 0, 0, []
    for sid, labs in by.items():
        kinds = {l for _, l in labs}
        if len(labs) > 1:
            double += 1; agree += len(kinds) == 1
        if len(kinds) == 1: final[sid] = labs[0][1]
        elif sid in adj: final[sid] = adj[sid]
        else: disputed.append(sid)
    stats = {'labeled_rfis': len(by), 'double_labeled': double, 'agreed': agree, 'disputed_unsettled': len(disputed),
             'adjudicated': sum(1 for s in adj if s in by)}
    return final, stats


def score(pairs):
    """pairs: (expected, recommendation) for calls that returned."""
    stop = [(e, r) for e, r in pairs if e != 'ok_to_close']
    fine = [(e, r) for e, r in pairs if e == 'ok_to_close']
    return {'scored': len(pairs), 'right': [sum(e == r for e, r in pairs), len(pairs)],
            'problems_stopped': [sum(r != 'ok_to_close' for _, r in stop), len(stop)],
            'missed_problems': [sum(r == 'ok_to_close' for _, r in stop), len(stop)],
            'false_alarms': [sum(r != 'ok_to_close' for _, r in fine), len(fine)],
            'wrong_but_caught_by_pm': sum(e != r and r != 'ok_to_close' for e, r in pairs)}


def real_summary(real, runs):
    labeled = [x for x in real if x['hand_label']]
    rl = {'rfis': len(real), 'labeled': len(labeled), 'label_mix': dict(Counter(x['hand_label'] for x in labeled)),
          'flags': {'code_only': dict(Counter(x['code_only'] for x in real))},
          'vs_hand_labels': {'code_only': score([(x['hand_label'], x['code_only']) for x in labeled])}}
    for k in range(1, runs + 1):
        rl['flags'][f'agent_run{k}'] = dict(Counter(x[f'agent_run{k}'] or 'failed call' for x in real))
        rl['vs_hand_labels'][f'agent_run{k}'] = score([(x['hand_label'], x[f'agent_run{k}']) for x in labeled if x[f'agent_run{k}']])
        rl['vs_hand_labels'][f'agent_run{k}']['failed_calls'] = sum(1 for x in labeled if not x[f'agent_run{k}'])
    if runs >= 2:
        both = [x for x in real if x['agent_run1'] and x['agent_run2']]
        rl['agent_runs_agree'] = [sum(x['agent_run1'] == x['agent_run2'] for x in both), len(both)]
    return rl


def rescore():
    """Re-score the saved real_log.csv against the current hand labels, without new AI calls."""
    final, stats = hand_labels()
    real = list(csv.DictReader(open(OUT / 'real_log.csv', encoding='utf-8')))
    runs = sum(1 for k in real[0] if k.startswith('agent_run') and k[9:].isdigit())
    for x in real:
        x['hand_label'] = final.get(x['source_id'], '')
    summary = json.loads((OUT / 'summary.json').read_text(encoding='utf-8'))
    summary['hand_labels'] = stats
    summary['real_log'] = real_summary(real, runs)
    summary['rescored_at'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
    with open(OUT / 'real_log.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(real[0])); w.writeheader(); w.writerows(real)
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({'hand_labels': stats, 'real_log': summary['real_log']}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs', type=int, default=2)
    ap.add_argument('--sleep', type=float, default=4.0, help='seconds between AI calls (free-tier rate limits)')
    ap.add_argument('--code-only', action='store_true')
    ap.add_argument('--synthetic', action='store_true', help='also run the synthetic stress-test sets')
    ap.add_argument('--rescore', action='store_true', help='re-score saved results against the current hand labels')
    args = ap.parse_args()
    if args.rescore:
        return rescore()
    cfg = settings()
    use_ai = not args.code_only
    if use_ai and not cfg.get('key'):
        raise SystemExit('AI is not connected (run python3 setup_ai.py) or use --code-only.')
    runs = args.runs if use_ai else 0
    data = agents.load('addendum_drawing_lists.json')
    OUT.mkdir(parents=True, exist_ok=True)
    final, label_stats = hand_labels()

    # ---- 1. the real Dett log
    lists = closeout.DrawingLists(data)
    real = []
    for r in csv.DictReader(open(ROOT / 'data' / 'source_rfis.csv', encoding='utf-8')):
        code = closeout.code_closeout(r, lists)
        row = {'source_id': r['source_id'], 'addendum': r['addendum'], 'pdf_page': r['pdf_page'],
               'hand_label': final.get(r['source_id'], ''), 'code_only': code['recommendation']}
        for k in range(1, runs + 1):
            a = with_retry(lambda: closeout.closeout_agent(r, lists, cfg), args.sleep)
            row[f'agent_run{k}'] = a.get('recommendation', '')
            row[f'agent_run{k}_error'] = a.get('error', '')
            row[f'agent_run{k}_guard'] = ' | '.join(a.get('guard', []))
            if k == 1:
                row['agent_commitment'] = a.get('commitment', ''); row['agent_reasons'] = ' | '.join(a.get('reasons', []))[:700]
        row.update(code_reasons=' | '.join(code['reasons'])[:600], question=r['question'][:400],
                   response=r['response'][:900], url=f"{r['url']}#page={r['pdf_page']}")
        real.append(row)
        print('real', r['source_id'], code['recommendation'], *[row.get(f'agent_run{k}') or row.get(f'agent_run{k}_error') for k in range(1, runs + 1)], flush=True)

    summary = {'run_at': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'model': cfg.get('model') if use_ai else None,
               'runs': runs, 'hand_labels': label_stats}
    summary['real_log'] = real_summary(real, runs)

    # ---- 2. stakeholder set and (optional) synthetic stress tests
    sets = []
    if KEVIN.exists():
        cases = json.loads(KEVIN.read_text(encoding='utf-8'))['cases']
        if cases and all(c.get('expected') in VALID for c in cases): sets.append(('stakeholder (real)', cases))
    if args.synthetic:
        sets += [(n, json.loads(p.read_text(encoding='utf-8'))['cases']) for n, p in SYNTHETIC]
    rows = []
    for name, cases in sets:
        for c in cases:
            cl = closeout.case_lists(c, data)
            calls = [('code only', 0, lambda: closeout.code_closeout(c, cl))]
            calls += [('agent', k + 1, lambda: closeout.closeout_agent(c, cl, cfg)) for k in range(runs)]
            for method, run, fn in calls:
                out = fn() if method == 'code only' else with_retry(fn, args.sleep)
                rows.append({'set': name, 'case_id': c['case_id'], 'kind': c['kind'], 'method': method, 'run': run,
                             'expected': c['expected'], 'recommendation': out.get('recommendation', ''),
                             'guard_drops': len(out.get('guard', [])), 'error': out.get('error', ''),
                             'reasons': ' | '.join(out.get('reasons', []))[:900]})
                print(name, c['case_id'], method, run, rows[-1]['recommendation'] or rows[-1]['error'], flush=True)
    summary['other_sets'] = {}
    for name, cases in sets:
        rs = [r for r in rows if r['set'] == name]
        entry = {'cases': len(cases), 'code_only': score([(r['expected'], r['recommendation']) for r in rs if r['method'] == 'code only'])}
        for k in range(1, runs + 1):
            ok = [r for r in rs if r['method'] == 'agent' and r['run'] == k]
            entry[f'agent_run{k}'] = dict(score([(r['expected'], r['recommendation']) for r in ok if not r['error']]),
                                          failed_calls=sum(1 for r in ok if r['error']))
        summary['other_sets'][name] = entry

    with open(OUT / 'real_log.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(real[0])); w.writeheader(); w.writerows(real)
    flagged = [x for x in real if x['code_only'] != 'ok_to_close'
               or any(x.get(f'agent_run{k}') not in ('', 'ok_to_close') for k in range(1, runs + 1))]
    with open(OUT / 'real_flags_for_review.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(real[0])); w.writeheader(); w.writerows(flagged)
    if rows:
        with open(OUT / 'per_case.csv', 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
