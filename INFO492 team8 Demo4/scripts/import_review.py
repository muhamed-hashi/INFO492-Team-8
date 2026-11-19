"""Read our stakeholder's filled-in review workbook into the label files, then re-score without new AI calls.

    python3 scripts/import_review.py kevin_review_demo4_FILLED.xlsx
    python3 scripts/run_demo4_eval.py --rescore
    python3 scripts/run_gwa_eval.py --rescore

Only his own calls are imported (labeler "stakeholder"). Empty cells stay empty: nobody fills them in for him.
"""
import csv
import sys
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
DETT_OK = {'ok_to_close', 'keep_open', 'hold', 'check'}
GWA_OK = {'ok_to_close', 'another_round', 'scope_change', 'not_sure'}


def rows(ws):
    head = [c.value for c in ws[2]]
    for r in ws.iter_rows(min_row=3, values_only=True):
        yield dict(zip(head, r))


def main(path):
    wb = load_workbook(path, data_only=True)
    dett = [(r['source_id'], str(r['your_call']).strip(), r.get('your_note') or '') for r in rows(wb['Dett (15)'])
            if r.get('your_call') and str(r['your_call']).strip() in DETT_OK]
    labels = ROOT / 'data' / 'dett_labels' / 'labels.csv'
    kept = [r for r in csv.DictReader(open(labels, encoding='utf-8')) if r['labeler'] != 'stakeholder'] if labels.exists() else []
    with open(labels, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['source_id', 'labeler', 'label', 'notes']); w.writeheader()
        w.writerows(kept + [{'source_id': s, 'labeler': 'stakeholder', 'label': l, 'notes': n} for s, l, n in dett])
    gwa = [(int(r['item']), str(r['your_call']).strip(), r.get('your_note') or '') for r in rows(wb['GWA (12)'])
           if r.get('your_call') and str(r['your_call']).strip() in GWA_OK]
    with open(ROOT / 'data' / 'gwa' / 'kevin_calls.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['no', 'call', 'note'])
        w.writerows(gwa)
    print(f'Dett: {len(dett)} calls -> {labels.relative_to(ROOT)}; GWA: {len(gwa)} calls -> data/gwa/kevin_calls.csv')


if __name__ == '__main__':
    main(sys.argv[1])
