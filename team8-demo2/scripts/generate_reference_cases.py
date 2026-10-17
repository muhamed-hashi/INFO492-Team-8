"""Generate the 24 drawing-reference cases for Demo #2 ("check references").

    python3 scripts/generate_reference_cases.py

Deterministic: no LLM, fixed shuffle seed. Rerunning gives identical files.

Starting point: the 12 seed RFIs in data/cases.json (real Dett RFIs rewritten as subcontractor -> GC
RFIs), using each seed's complete form. Every seed gives two cases:
  - a CLEAN case: the real sheet numbers, unchanged;
  - a DEFECTIVE case with one reference problem, of one of four kinds:
      nonexistent  a sheet number that is not in the project drawing index (one digit changed)
      typo         a letter O typed in place of a zero, so the number is unreadable to a lookup
      unrelated    a real sheet from the index whose title has nothing to do with the question
      vague        no sheet number at all ("See drawings")
Which seed gets which kind is fixed below and chosen so each change is realistic for that RFI.

Outputs: data/reference_cases.json (what the app and the checkers see) and
data/reference_answer_key.json (labels; never sent to the AI or shown in the app).
"""
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# seed -> (kind, details). 'where': 'refs' changes only the references field, 'both' changes the
# question too (the subcontractor used the wrong number throughout).
PLAN = {
    'S04': ('nonexistent', {'sheet': 'S-101', 'where': 'refs'}),
    'S02': ('nonexistent', {'sheet': 'E-500', 'where': 'both'}),
    'S01': ('nonexistent', {'sheet': 'E-801', 'where': 'both'}),
    'S07': ('typo', {'sheet': 'FP-200'}),
    'S06': ('typo', {'sheet': 'A-703'}),
    'S09': ('typo', {'sheet': 'A-401'}),
    'S03': ('unrelated', {'replace': 'ID-015', 'with': 'FP-200'}),
    'S11': ('unrelated', {'replace': 'A-503', 'with': 'S-301'}),
    'S08': ('unrelated', {'replace': 'PV-600', 'with': 'A-433'}),
    'S12': ('unrelated', {'replace': 'A-503', 'with': 'E-700'}),
    'S05': ('vague', {'text': 'See architectural drawings; Spec 10 51 13'}),
    'S10': ('vague', {'text': 'Per electrical plans'}),
}
SHEET = re.compile(r'\b[A-Za-z]{1,4}-?\d{3}[A-Za-z]?\b')


def norm(s):
    return re.sub(r'[\s-]', '', s.upper())


def missing_number(sheet, index):
    """Change the last digit until the number is not in the index (deterministic)."""
    known = {norm(k) for k in index}
    m = re.match(r'^([A-Za-z]{1,4}-?\d\d)(\d)([A-Za-z]?)$', sheet)
    head, last, tail = m.groups()
    for step in range(1, 10):
        cand = f'{head}{(int(last) + step) % 10}{tail}'
        if norm(cand) not in known:
            return cand
    raise ValueError(f'no free number near {sheet}')


def typo(sheet):
    i = sheet.index('0', sheet.index('-') if '-' in sheet else 0)
    return sheet[:i] + 'O' + sheet[i + 1:]


def build():
    cases = json.loads((ROOT / 'data' / 'cases.json').read_text(encoding='utf-8'))
    key = {k['case_id']: k for k in json.loads((ROOT / 'data' / 'answer_key.json').read_text(encoding='utf-8'))}
    index = json.loads((ROOT / 'data' / 'drawing_index.json').read_text(encoding='utf-8'))
    seeds = {}
    for c in cases:
        k = key[c['case_id']]
        if k['seed'] not in seeds or k['variant'] == 'clean':
            seeds[k['seed']] = c
    assert set(seeds) == set(PLAN), 'every seed needs a plan'

    items = []
    for seed in sorted(PLAN):
        base = seeds[seed]
        form = dict(base['brief']['known_details'])
        kind, d = PLAN[seed]
        bad = dict(form)
        if kind == 'nonexistent':
            wrong = missing_number(d['sheet'], index)
            bad['references'] = form['references'].replace(d['sheet'], wrong)
            if d['where'] == 'both':
                bad['question'] = form['question'].replace(d['sheet'], wrong)
            change = f"{d['sheet']} -> {wrong} (not in the drawing index)"
        elif kind == 'typo':
            wrong = typo(d['sheet'])
            bad['references'] = form['references'].replace(d['sheet'], wrong)
            change = f"{d['sheet']} -> {wrong} in the references field (letter O for zero)"
        elif kind == 'unrelated':
            assert d['with'] in index and d['replace'] in form['references']
            bad['references'] = form['references'].replace(d['replace'], d['with'])
            change = (f"{d['replace']} ({index[d['replace']]['title']}) -> {d['with']} "
                      f"({index[d['with']]['title']}), a real sheet unrelated to the question")
        else:
            bad['references'] = d['text']
            change = f"sheet numbers replaced by \"{d['text']}\""
        assert bad != form
        for variant, f, problem in (('clean', form, False), (kind, bad, True)):
            items.append({'seed': seed, 'variant': variant, 'problem': problem, 'change': change if problem else '',
                          'form': f, 'correct_references': form['references'], 'source': base['source']})

    random.Random(492).shuffle(items)
    out_cases, out_key = [], []
    for n, it in enumerate(items, 1):
        cid = f'R{n:02d}'
        brief = dict(it['form'])
        brief['references'] = it['correct_references']
        out_cases.append({
            'case_id': cid, 'is_simulated': True, 'source': it['source'], 'initial': it['form'],
            'brief': {'known_details': brief,
                      'simulation_note': 'Simulated reference-check case built from a real Dett RFI. The brief lists the '
                                         'correct sheet numbers. Dates and impacts are invented for this exercise.'}})
        out_key.append({'case_id': cid, 'seed': it['seed'], 'variant': it['variant'],
                        'reference_problem': it['problem'], 'change': it['change'],
                        'scoring_note': 'Team-made label. A clean case keeps the real sheet numbers.'})
    return out_cases, out_key


def main():
    cases, key = build()
    for name, data in (('reference_cases.json', cases), ('reference_answer_key.json', key)):
        (ROOT / 'data' / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Wrote {len(cases)} cases ({sum(k["reference_problem"] for k in key)} with a reference problem).')
    for k in key:
        if k['reference_problem']:
            print(f"  {k['case_id']} {k['variant']:12} {k['change']}")


if __name__ == '__main__':
    main()
