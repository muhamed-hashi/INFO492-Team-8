"""Demo #4, second real data set: a public RFI log (Guam Waterworks Authority, IFB-06-ENG-2026, "Response to RFI
No. 1", 44 items, July 2026) checked against the problem list our stakeholder wrote for it.

    python3 scripts/run_gwa_eval.py               # code + AI answer check, 2 runs (about 88 AI calls)
    python3 scripts/run_gwa_eval.py --code-only   # no AI, no network
    python3 scripts/run_gwa_eval.py --rescore     # no new AI calls: re-score the saved gwa_log.csv

Data:
  data/gwa/rfi1_items.json            the 44 items as printed (scripts/parse_gwa.py; pasted pictures read by OCR)
  data/gwa/stakeholder_problem_list.csv  our stakeholder's list: item, issue type, evidence. This is the answer key.
                                      It was written by a person reading the PDF, before and without our tool.

Which of his issue types our check is meant to find is decided by the fixed keyword rules in CATEGORIES below
(applied to his "issue_type" column), not case by case. Everything else on his list (unclear scope, contradicting
specifications, duplicate questions, typos, drawings never issued, ...) is reported as "outside what the check looks
for": the check does not try, so it can only miss them.

Honest caveat: the answer check and these rules were written AFTER we had seen his list. The prompt is generic
(no item text, no project words), but this is not a blind test. A blind test needs a new log he has not shown us.

Outputs: results/gwa/summary.json, results/gwa/gwa_log.csv (every item, his categories, both methods).
"""
import argparse
import csv
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agents  # noqa: E402
import closeout  # noqa: E402
from core import ROOT, settings  # noqa: E402

DATA = ROOT / 'data' / 'gwa'
OUT = ROOT / 'results' / 'gwa'
FLAGS = ('no_date', 'multiple_questions', 'refers_to_missing', 'not_fully_answered', 'scope_change', 'copied_answer')
# his issue type (lower case) contains any of these -> that category
CATEGORIES = {
    'multiple_questions': ['multiple questions'],
    'not_fully_answered': ['incomplete response', 'dismissive response', 'ineffective response', 'vague response',
                           'evasive response', 'non-responsive', 'copy-pasted response', 'misaligned numbering'],
    'scope_change': ['change the design', 'scope deleted'],
    'refers_to_missing': ['vague reference'],
    'no_date': ['no date', 'missing dates'],
    'copied_answer': ['copy-pasted response'],
}
STOP_CATEGORIES = ('not_fully_answered', 'scope_change')   # what makes the recommendation "check" instead of "close"
TRANSIENT = ('rate limit', 'quota', 'http 503', 'http 500', 'http 502', 'http 504', 'could not reach')


def item_numbers(text):
    """'#39–#40' -> [39, 40]; '#3, #5, #13–#15' -> [3, 5, 13, 14, 15]."""
    out = []
    for a, b in re.findall(r'#(\d+)(?:\s*[–-]\s*#?(\d+))?', text):
        out += list(range(int(a), int(b or a) + 1))
    return out


def answer_key(path=DATA / 'stakeholder_problem_list.csv'):
    """{item: {category, ...}} plus the items he listed with any issue, and the issue types we do not look for."""
    key, listed, outside = {}, set(), Counter()
    for r in csv.DictReader(open(path, encoding='utf-8')):
        t = r['issue_type'].lower()
        if r['item'].lower().startswith('document-wide'):
            nums = item_numbers(r['evidence'])          # e.g. his "Missing dates" list (he ends it with "etc.")
        else:
            nums = item_numbers(r['item']); listed.update(nums)
        cats = {c for c, words in CATEGORIES.items() if any(w in t for w in words)}
        for n in nums:
            key.setdefault(n, set()).update(cats)
        parts = [p.strip() for p in re.split(r' / ', r['issue_type'])]
        outside.update(p for p in parts if not any(any(w in p.lower() for w in words) for words in CATEGORIES.values()))
    return key, listed, outside


def with_retry(fn, sleep):
    for attempt in range(4):
        try:
            out = fn(); time.sleep(sleep); return out
        except ValueError as e:
            if any(t in str(e).lower() for t in TRANSIENT) and attempt < 3:
                time.sleep(20 * (attempt + 1)); continue
            return {'error': str(e)}
    return {'error': 'failed four times'}


def method_columns(log):
    cols = ['code']
    k = 1
    while f'agent_run{k}_rec' in (log[0] if log else {}):
        cols.append(f'agent_run{k}'); k += 1
    return cols


def score(log, key, listed):
    n_items = len(log)
    clean = [r for r in log if int(r['no']) not in listed]
    out = {'items': n_items, 'items_he_listed': len(listed), 'items_he_did_not_list': [int(r['no']) for r in clean],
           'methods': {}}
    for m in method_columns(log):
        rows = [r for r in log if not r.get(f'{m}_error')]
        res = {'failed_calls': n_items - len(rows), 'categories': {}}
        for c in FLAGS:
            his = {n for n, cats in key.items() if c in cats}
            flagged = {int(r['no']) for r in rows if c in r[f'{m}_flags'].split()}
            seen = {int(r['no']) for r in rows}
            res['categories'][c] = {
                'his_items': sorted(his), 'found': sorted(his & flagged), 'missed': sorted((his & seen) - flagged),
                'flagged_not_on_his_list': sorted(flagged - his)}
        stop_his = {n for n, cats in key.items() if cats & set(STOP_CATEGORIES)}
        stopped = {int(r['no']) for r in rows if r[f'{m}_rec'] != 'ok_to_close'}
        res['recommendation'] = {
            'counts': dict(Counter(r[f'{m}_rec'] for r in rows)),
            'his_answer_problems': sorted(stop_his), 'stopped_of_those': sorted(stop_his & stopped),
            'closed_of_those': sorted({int(r['no']) for r in rows} & stop_his - stopped),
            'stopped_not_on_his_answer_list': sorted(stopped - stop_his),
            'stopped_of_items_he_did_not_list': sorted(stopped - listed),
            # a stop on an item where he found some other problem (unclear scope, contradicting spec, ...) is not
            # a stop for the reason he gave, but the item does need a person; a stop on his 7 clean items does not
            'stopped_on_items_with_any_problem_he_listed': len(stopped & listed),
            'stopped_on_items_he_found_fine': len(stopped - listed)}
        out['methods'][m] = res
    agents_ = [m for m in method_columns(log) if m != 'code']
    if len(agents_) >= 2:
        both = [r for r in log if not r.get(f'{agents_[0]}_error') and not r.get(f'{agents_[1]}_error')]
        out['run_agreement'] = {'items_both_returned': len(both),
                                'same_recommendation': sum(r[f'{agents_[0]}_rec'] == r[f'{agents_[1]}_rec'] for r in both),
                                'same_flags': sum(r[f'{agents_[0]}_flags'] == r[f'{agents_[1]}_flags'] for r in both)}
    return out


def rescore():
    log = list(csv.DictReader(open(OUT / 'gwa_log.csv', encoding='utf-8')))
    key, listed, outside = answer_key()
    old = json.loads((OUT / 'summary.json').read_text()) if (OUT / 'summary.json').exists() else {}
    summary = {**{k: old[k] for k in ('run_at', 'model', 'runs') if k in old}, 'rescored_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
               **score(log, key, listed), 'his_issue_types_outside_the_check': dict(outside)}
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2))
    print_summary(summary)


def print_summary(s):
    print(f"\n{s['items']} items; he listed problems on {s['items_he_listed']}; no problem listed: {s['items_he_did_not_list']}")
    for m, res in s['methods'].items():
        print(f"\n== {m}  (failed calls: {res['failed_calls']})")
        for c, v in res['categories'].items():
            print(f"  {c:20s} his {len(v['his_items']):2d}  found {len(v['found']):2d}  missed {v['missed']}  not on his list {v['flagged_not_on_his_list']}")
        r = res['recommendation']
        print(f"  recommendation {r['counts']}; his answer problems {len(r['his_answer_problems'])}, stopped {len(r['stopped_of_those'])}, "
              f"closed {r['closed_of_those']}; extra stops {r['stopped_not_on_his_answer_list']}; on items he did not list {r['stopped_of_items_he_did_not_list']}")
    if 'run_agreement' in s:
        print('\nrun agreement', s['run_agreement'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs', type=int, default=2)
    ap.add_argument('--sleep', type=float, default=4.0, help='seconds between AI calls (free-tier rate limits)')
    ap.add_argument('--code-only', action='store_true')
    ap.add_argument('--rescore', action='store_true')
    args = ap.parse_args()
    if args.rescore:
        return rescore()
    cfg = settings()
    use_ai = not args.code_only
    if use_ai and not cfg.get('key'):
        raise SystemExit('AI is not connected (run python3 setup_ai.py) or use --code-only.')
    runs = args.runs if use_ai else 0
    items = json.loads((DATA / 'rfi1_items.json').read_text(encoding='utf-8'))
    key, listed, outside = answer_key()
    copied = closeout.copied_answers(items)
    OUT.mkdir(parents=True, exist_ok=True)
    log = []
    for it in items:
        n = it['no']
        code = closeout.answer_check_code(it, copied.get(n, ()))
        row = {'no': n, 'date': it['date'], 'his_categories': ' '.join(sorted(key.get(n, ()))), 'he_listed': n in listed,
               'code_rec': code['recommendation'], 'code_flags': ' '.join(k for k in FLAGS if code['flags'].get(k)),
               'code_error': '', 'code_reasons': ' | '.join(code['reasons'])[:600]}
        for k in range(1, runs + 1):
            a = with_retry(lambda: closeout.answer_check(it, cfg, copied.get(n, ())), args.sleep)
            row[f'agent_run{k}_rec'] = a.get('recommendation', '')
            row[f'agent_run{k}_flags'] = ' '.join(f for f in FLAGS if (a.get('flags') or {}).get(f))
            row[f'agent_run{k}_error'] = a.get('error', '')
            row[f'agent_run{k}_guard'] = ' | '.join(a.get('guard', []))
            row[f'agent_run{k}_reasons'] = ' | '.join(a.get('reasons', []))[:900]
            row[f'agent_run{k}_questions'] = json.dumps(a.get('questions', []), ensure_ascii=False)[:1500]
        row.update(question=it['question'][:600], response=it['response'][:900], page=it['page'],
                   has_picture=bool(it.get('question_picture_text') or it.get('response_picture_text')))
        log.append(row)
        print(n, code['recommendation'], *[row.get(f'agent_run{k}_rec') or row.get(f'agent_run{k}_error')[:60] for k in range(1, runs + 1)], flush=True)
    with open(OUT / 'gwa_log.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(log[0])); w.writeheader(); w.writerows(log)
    summary = {'run_at': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'model': cfg.get('model') if use_ai else None,
               'runs': runs, **score([{k: str(v) for k, v in r.items()} for r in log], key, listed),
               'his_issue_types_outside_the_check': dict(outside)}
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2))
    print_summary(summary)
    print(f'\nwrote {OUT.relative_to(ROOT)}/summary.json and gwa_log.csv')


if __name__ == '__main__':
    main()
