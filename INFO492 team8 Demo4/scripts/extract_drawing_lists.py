"""Rebuild data/addendum_drawing_lists.json from the six Dett addendum PDFs.

    python3 scripts/extract_drawing_lists.py /path/to/folder/with/the/six/addendum/PDFs

Needs `pdftotext` (poppler). Deterministic, no AI.

Each addendum has a section "This Addendum includes the following attached Drawings:" followed by a
numbered list such as "106. E-304, THIRD FLOOR LIGHTING PLAN - CLRM WING, dated 05/26/2023".
This script keeps EVERY numbered item in that section (Demo 2's extract_addenda.py kept only the first
list that contained a sheet, which is why Demo 4 does not reuse data/revisions.json for close-out).
It checks that the item numbers run 1..N with no gaps and stops if they do not.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ITEM = re.compile(r'^\s*(\d{1,3})\.\s*([A-Z]{1,3}[0-9]{0,1}-?[0-9]{1,3}[A-Za-z]?|COVER)\s*,\s*(.+?)'
                  r'(?:,?\s*(?:dated\s*)*(\d{2}/\d{2}/\d{4}))?\.?\s*$', re.M)
URL = 'https://pbcchicago.com/wp-content/uploads/2023/{m}/AD_PBC_PXM_RNDettESAnnexandRenoC1604_AddendumNo{n}_{d}_Final.pdf'
DATES = {1: ('05', '20230523'), 2: ('05', '20230530'), 3: ('06', '20230605'), 4: ('06', '20230606'),
         5: ('06', '20230609'), 6: ('06', '20230615')}


def drawings_in(pdf):
    text = subprocess.run(['pdftotext', '-layout', str(pdf), '-'], capture_output=True, text=True, check=True).stdout
    items, started = [], False
    for page_no, page in enumerate(text.split('\f'), 1):
        if 'following attached Drawings' in page:
            started = True
            page = page.split('following attached Drawings', 1)[1]
        elif not started:
            continue
        for m in ITEM.finditer(page):
            items.append({'no': int(m.group(1)), 'sheet': m.group(2), 'title': ' '.join(m.group(3).split()),
                          'dated': m.group(4) or '', 'pdf_page': page_no})
    nums = [i['no'] for i in items]
    if nums and nums != list(range(1, len(nums) + 1)):
        raise SystemExit(f'{pdf.name}: item numbers are not 1..N; check the parser before using this file.')
    return items


def main(folder):
    folder = Path(folder)
    addenda = []
    for n in range(1, 7):
        pdf = next(folder.glob(f'*AddendumNo{n}_*.pdf'))
        m, d = DATES[n]
        addenda.append({'addendum': n, 'url': URL.format(m=m, n=n, d=d), 'drawings': drawings_in(pdf)})
        print(f'Addendum {n}: {len(addenda[-1]["drawings"])} drawings')
    old = json.loads((ROOT / 'data' / 'addendum_drawing_lists.json').read_text(encoding='utf-8'))
    old['addenda'] = addenda
    (ROOT / 'data' / 'addendum_drawing_lists.json').write_text(json.dumps(old, indent=1, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
