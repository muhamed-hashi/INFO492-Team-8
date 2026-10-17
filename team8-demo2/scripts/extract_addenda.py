"""Extract the real RFIs and the drawing list from the six Dett addenda PDFs.

The PDFs are public but large (up to 47 MB), so they are NOT stored in this repo.
Download them from the PBC project page (links in docs/DATA_PROVENANCE.md) into
a folder, then run:

    pip install pypdf
    python3 scripts/extract_addenda.py path/to/folder_with_pdfs

Outputs (already included in the repo, so you only need this to reproduce them):
    data/source_rfis.csv     - every RFI question + architect response (108 rows)
    data/drawing_index.json  - every drawing sheet listed or cited in the addenda
"""
import csv
import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PBC = 'https://pbcchicago.com/wp-content/uploads/'
URLS = {
    1: PBC+'2023/05/AD_PBC_PXM_RNDettESAnnexandRenoC1604_AddendumNo1_20230523_Final.pdf',
    2: PBC+'2023/05/AD_PBC_PXM_RNDettESAnnexandRenoC1604_AddendumNo2_20230530_Final.pdf',
    3: PBC+'2023/06/AD_PBC_PXM_RNDettESAnnexandRenoC1604_AddendumNo3_20230605_Final.pdf',
    4: PBC+'2023/06/AD_PBC_PXM_RNDettESAnnexandRenoC1604_AddendumNo4_20230606_Final.pdf',
    5: PBC+'2023/06/AD_PBC_PXM_RNDettESAnnexandRenoC1604_AddendumNo5_20230609_Final.pdf',
    6: PBC+'2023/06/AD_PBC_PXM_RNDettESAnnexandRenoC1604_AddendumNo6_20230615_Final.pdf',
}
SHEET = r'[A-Z]{1,3}-?\s?\d{3}[A-Z]?'
LIST_LINE = re.compile(rf'^\s*\d+\.\s+({SHEET}|[A-Z]{{1,3}}\d-\d{{2}}),\s*(.+?),?\s*dated\s+(\d\d/\d\d/\d{{4}})', re.M)
CITED = re.compile(r'\b([A-Z]{1,3})-?\s?(\d{3}[A-Z]?)\b')
NOT_SHEETS = {'RT', 'RS', 'QT', 'TB', 'LX', 'LP', 'KN', 'EQP', 'WT', 'MUA', 'RTU', 'HW', 'ERW', 'CU', 'IDF', 'MDF',
              'RM', 'PSI', 'SF', 'HP', 'TYP', 'DE', 'AE', 'AX', 'CLSM'}


def norm(sheet):
    m = re.match(r'^([A-Z]{1,3})-?\s?(\d.*)$', sheet.strip().upper())
    return f'{m.group(1)}-{m.group(2)}' if m else sheet.strip().upper()


def body_pages(reader, n):
    """Pages of the addendum itself (they carry the 'Addendum No. N  Page x of y' header)."""
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ''
        if 'C1604_Addendum No.' not in text[:400]:
            break
        yield i + 1, text


def main(folder):
    folder = Path(folder)
    rfis, index = [], {}
    for n in range(1, 7):
        pdf = next(folder.glob(f'*AddendumNo{n}_*.pdf'), None) or next(folder.glob(f'*No{n}*.pdf'), None)
        if not pdf:
            print(f'Addendum {n}: PDF not found in {folder}, skipped'); continue
        reader = PdfReader(str(pdf))
        pages = list(body_pages(reader, n))
        # --- drawing list ("37. A-210, CLRM WING ENLARGED OFFICE SUITE 103/101 PLAN & RCP, dated 05/26/2023")
        for page_no, text in pages:
            for sheet, title, date in LIST_LINE.findall(text):
                index.setdefault(norm(sheet), {'title': ' '.join(title.split()), 'source_label': f'Dett Addendum {n}, PDF page {page_no}',
                                               'url': URLS[n], 'page': page_no, 'basis': f'drawing list, dated {date}'})
        # --- RFIs
        full = '\n'.join(f'<<PAGE {p}>>\n{t}' for p, t in pages)
        for m in re.finditer(r'RFI-(\d+)\.\s*\n?\s*Question:(.*?)Response:(.*?)(?=RFI-\d+\.|This Addendum includes|ITEM NO\.|END OF ADDENDUM|$)',
                             full, re.S):
            page = max([int(p) for p in re.findall(r'<<PAGE (\d+)>>', full[:m.start()])] or [1])
            clean = lambda s: ' '.join(re.sub(r'<<PAGE \d+>>|Date of Issue:.*?\n|PBC:.*?Page \d+ of \d+|\(REMAINDER OF PAGE INTENTIONALLY LEFT BLANK\)', ' ', s).split())
            q, r = clean(m.group(2)), clean(m.group(3))
            rfis.append({'source_id': f'Dett-A{n}-RFI{m.group(1)}', 'addendum': n, 'rfi_no': int(m.group(1)),
                         'pdf_page': page, 'question': q, 'response': r, 'url': URLS[n]})
    # sheets cited in RFI questions/responses are also real project sheets
    for r in rfis:
        for prefix, num in CITED.findall(r['question'] + ' ' + r['response']):
            if prefix in NOT_SHEETS:
                continue
            index.setdefault(f'{prefix}-{num}', {'title': '', 'source_label': f"Cited in {r['source_id']}",
                                                 'url': r['url'], 'page': r['pdf_page'], 'basis': 'cited in RFI text'})
        r['sheets_cited'] = ';'.join(sorted({f'{p}-{x}' for p, x in CITED.findall(r['question']) if p not in NOT_SHEETS}))
    with open(ROOT/'data'/'source_rfis.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['source_id', 'addendum', 'rfi_no', 'pdf_page', 'sheets_cited', 'question', 'response', 'url'])
        w.writeheader(); w.writerows(rfis)
    index = dict(sorted(index.items()))
    (ROOT/'data'/'drawing_index.json').write_text(json.dumps(index, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(f'{len(rfis)} RFIs -> data/source_rfis.csv; {len(index)} sheets -> data/drawing_index.json')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
