"""Turn our stakeholder's anonymized close-out examples into a test set the evaluation can run.

    python3 scripts/import_kevin.py            # privacy check, then data/kevin/template_closeout.csv -> closeout_cases.json
    python3 scripts/import_kevin.py --check    # privacy check only (both CSV templates)

Rules (see data/kevin/README.md):
- Only anonymized text goes into the CSV templates. Original screenshots, emails and photos stay in data/kevin/raw/,
  which is in .gitignore and must never be uploaded.
- `expected` is filled in by a person on the team (or by our stakeholder), never by an AI.
- The script refuses to build the test set if the privacy check finds anything or a label is missing.
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEVIN = ROOT / 'data' / 'kevin'
VALID = {'ok_to_close', 'keep_open', 'hold', 'check'}
PATTERNS = {
    'phone number': re.compile(r'(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}'),
    'email address': re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+'),
    'dollar amount': re.compile(r'\$\s?\d|\d+\s?(?:dollars|USD)\b', re.I),
    'street address': re.compile(r'\b\d{2,6}\s+(?:[NSEW]\.?\s+)?[A-Z][a-z]+\s+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Dr|Drive|Ln|Lane|Way|Pkwy)\b'),
    'web link': re.compile(r'https?://\S+'),
}


def privacy_findings():
    names = []
    p = KEVIN / 'private_names.txt'      # one real name / company / project per line; never uploaded
    if p.exists():
        names = [n.strip() for n in p.read_text(encoding='utf-8').splitlines() if n.strip()]
    out = []
    for f in sorted(KEVIN.glob('*.csv')):
        for i, row in enumerate(csv.DictReader(open(f, encoding='utf-8')), start=2):
            for col, val in row.items():
                for label, rx in PATTERNS.items():
                    if val and rx.search(val): out.append(f'{f.name} line {i}, {col}: looks like a {label}')
                for n in names:
                    if val and n.lower() in val.lower(): out.append(f'{f.name} line {i}, {col}: contains a private name')
    return out


def main():
    findings = privacy_findings()
    for x in findings: print('PRIVACY:', x)
    if '--check' in sys.argv:
        print('No privacy problems found.' if not findings else f'{len(findings)} possible privacy problems.')
        return
    if findings:
        raise SystemExit('Fix the privacy problems above before building the test set.')
    rows = list(csv.DictReader(open(KEVIN / 'template_closeout.csv', encoding='utf-8')))
    if not rows:
        raise SystemExit('data/kevin/template_closeout.csv has no rows yet.')
    cases = []
    for r in rows:
        exp = (r.get('expected') or '').strip()
        if exp not in VALID or not (r.get('labeled_by') or '').strip():
            raise SystemExit(f'{r.get("case_id")}: expected must be one of {sorted(VALID)} and labeled_by must name a person.')
        cases.append({'case_id': r['case_id'].strip(), 'kind': 'stakeholder', 'source_id': f'kevin:{r["case_id"].strip()}',
                      'source_format': r.get('source_format', ''), 'addendum': 1, 'question': r.get('question', ''),
                      'response': r['answer'], 'issued_sheets': [s.strip() for s in re.split(r'[;,]', r.get('issued_sheets', '')) if s.strip()],
                      'expected': exp, 'labeled_by': r['labeled_by'].strip(), 'notes': r.get('notes', '')})
    out = {'note': 'Real close-out examples from our stakeholder (a GC assistant PM), anonymized; right answers labeled by '
                   'the team. Built by scripts/import_kevin.py from data/kevin/template_closeout.csv.', 'cases': cases}
    (KEVIN / 'closeout_cases.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')
    print(f'{len(cases)} stakeholder cases written to data/kevin/closeout_cases.json')


if __name__ == '__main__':
    main()
