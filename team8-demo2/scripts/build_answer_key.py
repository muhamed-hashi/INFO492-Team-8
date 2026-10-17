"""Evaluation Lab, step 2: put the two labelers' answers side by side and start the answer key.

    python3 scripts/build_answer_key.py

Reads eval/labeler_A.csv and eval/labeler_B.csv. Writes eval/answer_key.csv with both labels, whether
they agree, and a final_label column: filled in where the two agree on ok/problem, left blank where
they disagree or someone wrote "unclear". The team then talks those rows through and fills them in.
An existing answer_key.csv keeps any final_label / resolution_note the team already typed.
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL = ROOT / 'eval'
LABELS = ('ok', 'problem', 'unclear')


def read(who):
    path = EVAL / f'labeler_{who}.csv'
    with open(path, encoding='utf-8-sig') as f:
        rows = {r['item_id']: r for r in csv.DictReader(f)}
    bad = [i for i, r in rows.items() if (r.get('label') or '').strip().lower() not in LABELS]
    if bad:
        sys.exit(f'{path.relative_to(ROOT)}: label missing or not ok/problem/unclear for {", ".join(sorted(bad))}.')
    return rows


def kappa(a, b, ids):
    n = len(ids)
    po = sum(a[i] == b[i] for i in ids) / n
    pe = sum((sum(a[i] == c for i in ids) / n) * (sum(b[i] == c for i in ids) / n) for c in LABELS)
    return po, (None if pe == 1 else (po - pe) / (1 - pe))


def main():
    A, B = read('A'), read('B')
    if set(A) != set(B):
        sys.exit('The two labeling files list different items.')
    ids = sorted(A)
    a = {i: A[i]['label'].strip().lower() for i in ids}
    b = {i: B[i]['label'].strip().lower() for i in ids}
    out = EVAL / 'answer_key.csv'
    old = {}
    if out.exists():
        with open(out, encoding='utf-8-sig') as f:
            old = {r['item_id']: r for r in csv.DictReader(f)}
    rows = []
    for i in ids:
        agree = a[i] == b[i] and a[i] in ('ok', 'problem')
        prev = old.get(i, {})
        rows.append({'item_id': i, 'question': A[i]['question'], 'references': A[i]['references'],
                     'label_A': a[i], 'note_A': A[i].get('note', ''), 'label_B': b[i], 'note_B': B[i].get('note', ''),
                     'agree': 'yes' if agree else 'NO',
                     'final_label': (prev.get('final_label') or '').strip() or (a[i] if agree else ''),
                     'resolution_note': prev.get('resolution_note', '')})
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    po, k = kappa(a, b, ids)
    todo = [r['item_id'] for r in rows if r['final_label'] not in ('ok', 'problem')]
    print(f'Labelers agree on {sum(a[i] == b[i] for i in ids)}/{len(ids)} items ({round(100 * po)}%), '
          f"Cohen's kappa {'n/a' if k is None else round(k, 2)}.")
    print(f'Wrote {out.relative_to(ROOT)}.')
    if todo:
        print('Talk these through, then type ok or problem in final_label (and a line in resolution_note): ' + ', '.join(todo))
    else:
        print('Answer key complete. Next: python3 scripts/run_real_eval.py')


if __name__ == '__main__':
    main()
