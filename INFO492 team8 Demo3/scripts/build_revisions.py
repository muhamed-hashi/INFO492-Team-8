"""Build data/revisions.json: which drawing sheets were issued or revised in each Dett addendum.

    python3 scripts/build_revisions.py

Deterministic, no LLM. Uses only real data already in this repo:
  1. data/drawing_index.json  - the addendum whose "attached Drawings" list first contains each sheet
  2. data/source_rfis.csv      - architect responses that say "refer to revised Drawing X ... in this addendum"

Limitation (also in docs/DATA_PROVENANCE.md): extract_addenda.py kept only the FIRST drawing list that
contains a sheet, so a sheet re-issued again in a later list is only caught here if an RFI response
mentions it. The watch agent therefore sees fewer revisions than really happened, never more.
"""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATES = {1: '2023-05-23', 2: '2023-05-30', 3: '2023-06-05', 4: '2023-06-06', 5: '2023-06-09', 6: '2023-06-15'}
SHEET = r'[A-Z]{1,3}-?\d{3}[A-Z]?'


def norm(s):
    m = re.match(r'^([A-Z]{1,3})-?(\d{3}[A-Z]?)$', s.strip().upper())
    return f'{m.group(1)}-{m.group(2)}' if m else s.strip().upper()


def main():
    index = json.loads((ROOT / 'data' / 'drawing_index.json').read_text(encoding='utf-8'))
    events = {}   # (addendum, sheet) -> evidence

    for sheet, info in index.items():
        m = re.match(r'Dett Addendum (\d+), PDF page (\d+)', info.get('source_label', ''))
        if m and info.get('basis', '').startswith('drawing list'):
            events[(int(m.group(1)), sheet)] = f"Listed in the drawings attached to Addendum {m.group(1)} (PDF page {m.group(2)}), {info['basis']}"

    with open(ROOT / 'data' / 'source_rfis.csv', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            for m in re.finditer(rf'revised\s+(?:drawings?|sheets?)?\s*({SHEET}(?:\s*(?:,|and|&)\s*{SHEET})*)', r['response'], re.I):
                for s in re.findall(SHEET, m.group(1)):
                    key = (int(r['addendum']), norm(s))
                    events.setdefault(key, f"Architect's response to {r['source_id']} refers to a revised {norm(s)} in this addendum")

    addenda = []
    for n, date in DATES.items():
        sheets = [{'sheet': s, 'title': index.get(s, {}).get('title', ''), 'evidence': ev}
                  for (a, s), ev in sorted(events.items()) if a == n]
        addenda.append({'addendum': n, 'date': date, 'sheets': sheets})
    out = {'source': 'Dett Elementary School Annex and Renovations (PBC Chicago, C1604), Addenda 1-6',
           'note': 'Sheets issued or revised in each addendum. Real data; see scripts/build_revisions.py for the limitation.',
           'addenda': addenda}
    (ROOT / 'data' / 'revisions.json').write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('data/revisions.json: ' + ', '.join(f"A{a['addendum']}={len(a['sheets'])}" for a in addenda))


if __name__ == '__main__':
    main()
