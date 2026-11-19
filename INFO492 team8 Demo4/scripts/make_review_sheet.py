"""Make the workbook for our stakeholder's Demo #4 test session: data/kevin_review_demo4.xlsx

    python3 scripts/run_demo4_eval.py && python3 scripts/run_gwa_eval.py   # first: the AI runs
    python3 scripts/make_review_sheet.py      # needs openpyxl
    python3 scripts/import_review.py FILLED.xlsx   # afterwards: his answers -> label files, then --rescore both evals

Tabs:
  How to test   what the team member running the session does and writes down (live use of the system)
  Dett (15)     every real Dett RFI that the code check or the agent stopped, with the tool's reasons. His call per
                RFI measures false alarms on real data. It cannot measure misses (RFIs nobody stopped are not shown).
  GWA (12)      12 items of the public GWA log, shown BLIND: question and answer only, no tool output and no
                problem list. Chosen by a fixed rule (run_gwa_eval.review_sample) where the AI-made problem list and
                our agent disagree. His calls are the only human answer key for the GWA set.
"""
import csv
import json
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import run_gwa_eval  # noqa: E402

NAMES = {'ok_to_close': 'OK to close', 'keep_open': 'Keep open', 'hold': 'Hold', 'check': 'Check', '': 'failed call'}
YELLOW = PatternFill('solid', fgColor='FFF4CC')
WRAP = Alignment(wrap_text=True, vertical='top')

HOW_TO = [
    ('Kevin Demo #4 test (about 20 minutes). The team member running it fills in the right-hand column.', ''),
    ('', ''),
    ('Before', 'Open https://info492-team-8.onrender.com and check the landing page says Demo #4 (Close-out). Kevin shares his screen.'),
    ('1. Sign in (2 min)', 'Kevin clicks "Sign in by role" and signs in as Project Manager (PIN 3333). Write down anything that confused him.'),
    ('2. Close-out list (3 min)', 'He opens Close-out and looks at the 108 real RFIs. Ask: "Which would you open first, and why?"'),
    ('3. Run the agent (8 min)', 'He opens A3-RFI57, A3-RFI53 and A3-RFI21, clicks "Run close-out agent" on each, reads the recommendation and evidence, and decides (close / keep open / ask architect). Record what he decided and whether he agreed with the agent.'),
    ('4. Ask the architect (2 min)', 'On A3-RFI53 he sends a question to the architect. Sign in as Architect (PIN 4444) in a private window and reply; he sees the reply.'),
    ('5. Review sheets (rest of the time)', 'Tab "Dett (15)": one call per row. Tab "GWA (12)": one call per row, from the question and answer only. If time runs out, finish them later; do not guess for him.'),
    ('6. Two questions, write his words', 'a) "Would you use this before closing RFIs? What would stop you?"  b) "What is the one thing you would change?"'),
    ('', ''),
    ('Write down', ''),
    ('Minutes he used the system', ''),
    ('What he did, in order', ''),
    ('Where he hesitated or was confused', ''),
    ('Did he agree with the agent on 57 / 53 / 21?', ''),
    ('Quote (a)', ''),
    ('Quote (b)', ''),
]


def dett_tab(ws):
    flagged = list(csv.DictReader(open(ROOT / 'results' / 'demo4' / 'real_flags_for_review.csv', encoding='utf-8')))
    ws.append(['Real RFIs our tool would NOT simply close. For each: what should a PM do before closing it? '
               'ok_to_close / keep_open (something still to come) / hold (a promised sheet was not issued) / check (unclear).'])
    ws['A1'].font = Font(bold=True)
    ws.append(['source_id', 'question', 'architect_answer', 'pdf_page_link', 'code_check_says', 'agent_says',
               'agent_reason', 'your_call', 'your_note'])
    for c in ws[2]: c.font = Font(bold=True)
    for x in flagged:
        ws.append([x['source_id'], x['question'], x['response'], x['url'], NAMES.get(x['code_only'], x['code_only']),
                   NAMES.get(x.get('agent_run1', ''), x.get('agent_run1', '')), x.get('agent_reasons', ''), '', ''])
    dv = DataValidation(type='list', formula1='"ok_to_close,keep_open,hold,check"', allow_blank=True)
    ws.add_data_validation(dv); dv.add(f'H3:H{ws.max_row}')
    for col, w in zip('ABCDEFGHI', [16, 40, 60, 18, 14, 14, 50, 14, 30]): ws.column_dimensions[col].width = w
    for row in ws.iter_rows(min_row=3):
        for c in (row[1], row[2], row[6]): c.alignment = WRAP
        row[7].fill = YELLOW
    return len(flagged)


def gwa_tab(ws):
    items = {i['no']: i for i in json.loads((ROOT / 'data' / 'gwa' / 'rfi1_items.json').read_text(encoding='utf-8'))}
    log = list(csv.DictReader(open(ROOT / 'results' / 'gwa' / 'gwa_log.csv', encoding='utf-8')))
    sample = run_gwa_eval.review_sample(log)
    ws.append(['Public RFI log (Guam Waterworks, 2026). Read the question and the answer. Could a GC close this RFI, '
               'or will it come back? ok_to_close / another_round (not fully answered, deferred, only "refer to") / '
               'scope_change (the answer changes the work; log a change) / not_sure.'])
    ws['A1'].font = Font(bold=True)
    ws.append(['item', 'question', 'picture_in_question (read by OCR, may have errors)', 'answer', 'pdf_page',
               'your_call', 'your_note'])
    for c in ws[2]: c.font = Font(bold=True)
    for n in sample:
        it = items[n]
        ans = it['response'] + (('\n[picture in the answer, OCR] ' + it['response_picture_text']) if it.get('response_picture_text') else '')
        ws.append([n, it['question'], it.get('question_picture_text', '')[:1500], ans, it['page'], '', ''])
    dv = DataValidation(type='list', formula1='"ok_to_close,another_round,scope_change,not_sure"', allow_blank=True)
    ws.add_data_validation(dv); dv.add(f'F3:F{ws.max_row}')
    for col, w in zip('ABCDEFG', [7, 50, 40, 50, 9, 16, 30]): ws.column_dimensions[col].width = w
    for row in ws.iter_rows(min_row=3):
        for c in (row[1], row[2], row[3]): c.alignment = WRAP
        row[5].fill = YELLOW
    return sample


def main():
    wb = Workbook()
    how = wb.active; how.title = 'How to test'
    for a, b in HOW_TO: how.append([a, b])
    how['A1'].font = Font(bold=True); how['A11'].font = Font(bold=True)
    how.column_dimensions['A'].width = 38; how.column_dimensions['B'].width = 110
    for row in how.iter_rows():
        for c in row: c.alignment = WRAP
    for r in range(12, 18): how.cell(row=r, column=2).fill = YELLOW
    n_dett = dett_tab(wb.create_sheet('Dett (15)'))
    sample = gwa_tab(wb.create_sheet('GWA (12)'))
    out = ROOT / 'data' / 'kevin_review_demo4.xlsx'
    wb.save(out)
    print(f'Dett: {n_dett} RFIs; GWA blind sample: {sample} -> {out.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
