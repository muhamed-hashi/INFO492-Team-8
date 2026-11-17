"""Make the stakeholder review sheet: every real RFI that the code check or the agent stopped.

    python3 scripts/run_demo4_eval.py          # first: the AI run on the 108 real RFIs
    python3 scripts/make_review_sheet.py       # needs openpyxl; writes data/dett_labels/stakeholder_review.xlsx

Our stakeholder (a GC assistant PM) goes through this sheet during his Demo #4 test call and says, for each stopped
RFI, what a PM should really do. His answers go into data/dett_labels/labels.csv (labeler = "stakeholder"), and
`python3 scripts/run_demo4_eval.py --rescore` reports how many of the tool's stops he agreed with.

This measures false alarms on real data. It does not measure misses (RFIs both methods let through that should
have been stopped); that would need every one of the 108 RFIs labeled, which we did not do.
"""
import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
NAMES = {'ok_to_close': 'OK to close', 'keep_open': 'Keep open', 'hold': 'Hold', 'check': 'Check', '': 'failed call'}


def main():
    flagged = list(csv.DictReader(open(ROOT / 'results' / 'demo4' / 'real_flags_for_review.csv', encoding='utf-8')))
    wb = Workbook(); ws = wb.active; ws.title = 'Review'
    ws.append(['Real RFIs our tool would NOT simply close. For each: what should a PM do before closing it? '
               'ok_to_close / keep_open (something still to come) / hold (a promised sheet was not issued) / check (unclear).'])
    ws['A1'].font = Font(bold=True)
    head = ['source_id', 'question', 'architect_answer', 'pdf_page_link', 'code_check_says', 'agent_says', 'agent_reason',
            'your_call', 'your_note']
    ws.append(head)
    for c in ws[2]: c.font = Font(bold=True)
    for x in flagged:
        ws.append([x['source_id'], x['question'], x['response'], x['url'], NAMES.get(x['code_only'], x['code_only']),
                   NAMES.get(x.get('agent_run1', ''), x.get('agent_run1', '')), x.get('agent_reasons', ''), '', ''])
    dv = DataValidation(type='list', formula1='"ok_to_close,keep_open,hold,check"', allow_blank=True)
    ws.add_data_validation(dv); dv.add(f'H3:H{ws.max_row}')
    for col, w in zip('ABCDEFGHI', [16, 40, 60, 18, 14, 14, 50, 14, 30]): ws.column_dimensions[col].width = w
    for row in ws.iter_rows(min_row=3):
        for c in (row[1], row[2], row[6]): c.alignment = Alignment(wrap_text=True, vertical='top')
        row[7].fill = PatternFill('solid', fgColor='FFF4CC')
    out = ROOT / 'data' / 'dett_labels' / 'stakeholder_review.xlsx'
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    print(f'{len(flagged)} RFIs to review -> {out.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
