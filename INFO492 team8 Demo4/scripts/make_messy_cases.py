"""Build data/closeout_cases_messy.json: 40 harder close-out cases. Deterministic (seed 4920), no AI.

    python3 scripts/make_messy_cases.py

Why: our professor said the first test set was too clean (every answer well written, one problem per case,
and the agent scored 100%). Real RFI answers and logs are written fast: abbreviations, missing hyphens, sheet
numbers split by a line break, extra chatter, and sometimes more than one problem in one answer.

Every case still starts from a REAL Dett answer whose revised sheets are in that addendum's drawing list, so the
right answer is known from how the case was built (no person or AI labels it). Then:

1. Field-style noise on every case (team-written rules, below): "Drawing" -> "dwg"/"sht", "revised" ->
   "rev'd"/"rev.", "included in this addendum" -> "incl. in this add."/"attached", sheet numbers written as
   E304, e-304 or "E- 304", lower case, and a short chatter sentence ("pls coordinate w/ GC").
2. One or two planted problems:

    kind                 n   planted                                                      right answer
    clean               10   noise only                                                   ok_to_close
    see_also             5   + a reference to a real sheet not in this addendum           ok_to_close
    missing              5   one revised sheet removed from this case's drawing list       hold
    deferred             5   the revision sentence says it comes later (messy wording)    keep_open
    typo                 5   a sheet number mistyped                                      check
    missing+see_also     3   both                                                         hold
    typo+see_also        3   both                                                         check
    deferred+missing     4   one sheet deferred; another, still "rev'd ... attached", is   keep_open
                             missing from the drawing list

When two problems are planted, the right answer follows one fixed priority, the same one a PM would use:
keep_open (something is still to come) > hold (a promised sheet is missing) > check (a person must confirm a
sheet number) > ok_to_close. The agent and the code baseline were NOT tuned on these cases.
"""
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
import agents  # noqa: E402
import closeout  # noqa: E402
from make_closeout_cases import revised_sentence, typo  # noqa: E402

SEED = 4920
# deferred+missing needs answers that name several sheets, which are few, so those cases are built first
PLAN = (['deferred+missing'] * 4 + ['clean'] * 10 + ['see_also'] * 5 + ['missing'] * 5 + ['deferred'] * 5
        + ['typo'] * 5 + ['missing+see_also'] * 3 + ['typo+see_also'] * 3)
EXPECTED = {'clean': 'ok_to_close', 'see_also': 'ok_to_close', 'missing': 'hold', 'deferred': 'keep_open',
            'typo': 'check', 'missing+see_also': 'hold', 'typo+see_also': 'check', 'deferred+missing': 'keep_open'}
DEFERRED = ["rev'd {s} to come w/ the permit set.", '{s} TBD - not in this pkg, will reissue.',
            'arch still working on {s}, updated sht later.', '{s} will be reissued after award.',
            'updated {s} to follow.', "{s} not rev'd yet, pending design team.", '{s} revision coming next round.',
            'will send {s} once updated.', '{s}: changes pending, not attached.']
SEE_ALSO = ['also see {y}.', 'coord w/ {y}.', 'ref {y} for existing.', 'cf. sht {y}.']
CHATTER = ['pls coordinate w/ GC.', 'see attached.', 'contractor to field verify.', 'confirm w/ super on site.',
           'thx.', 'per mtg.']


def write_sheet(sheet, rng):
    p, n = sheet.split('-', 1)
    return rng.choice([f'{p}{n}', f'{p}-{n}', f'{p.lower()}-{n}', f'{p}- {n}'])


def noisy(text, sheets, rng):
    """Field-style rewrite of a real answer; the meaning (which sheets, revised or not) does not change."""
    t = text
    for a, b in [(r'\bDrawings?\b', lambda: rng.choice(['dwg', 'sht', 'Dwg'])), (r'\bsheets?\b', lambda: 'sht'),
                 (r'\brevised\b', lambda: rng.choice(["rev'd", 'rev.', 'revised'])),
                 (r'\bincluded in this [Aa]ddendum\b', lambda: rng.choice(['incl. in this add.', 'attached', 'in this addendum'])),
                 (r'\bContractors?\b', lambda: 'GC'), (r'\bapproximately\b', lambda: 'approx')]:
        t = re.sub(a, lambda m: b(), t)
    for s in sorted(set(sheets), key=lambda x: (-len(x), x)):
        t = re.sub(re.escape(s).replace('\\-', r'-?'), lambda m: write_sheet(s, rng), t)
    if rng.random() < 0.4: t = t.lower()
    t = re.sub(r'\.\.+', '.', t.strip())
    return ' '.join((t + ' ' + rng.choice(CHATTER)).split())


def main():
    data = agents.load('addendum_drawing_lists.json')
    lists = closeout.DrawingLists(data)
    import csv
    rows = list(csv.DictReader(open(ROOT / 'data' / 'source_rfis.csv', encoding='utf-8')))
    pool = []
    for r in rows:
        f = closeout.facts(r)
        found, missing, _ = closeout.verify(f['sheets'], f['target_addendum'], lists)
        if f['revision_words'] and f['sheets'] and not missing and not f['defer_words'] \
                and revised_sentence(r['response'], f['sheets'][0]):
            pool.append(r)
    rng = random.Random(SEED)
    rng.shuffle(pool)
    multi = [r for r in pool if len(closeout.facts(r)['sheets']) >= 2]
    all_sheets = sorted({closeout.norm(d['sheet']) for a in data['addenda'] for d in a['drawings']
                         if re.match(r'^[A-Z]{1,2}-\d{3}[A-Z]?$', closeout.norm(d['sheet']))})
    cases, used = [], set()
    for kind in PLAN:
        source = multi if kind == 'deferred+missing' else pool
        for r in source:
            if r['source_id'] in used and len(used) < len(pool): continue
            f = closeout.facts(r); target = f['target_addendum']; sheets = f['sheets']; s = sheets[0]
            text, remove, planted = r['response'], [], []
            if 'typo' in kind:
                t = typo(s, lists, swap_first=rng.random() < 0.5)
                if not t or s not in lists.near(target, t): continue
                text = re.sub(re.escape(s).replace('\\-', '-?'), t, text); planted.append(f'{s} mistyped as {t}')
                sheets = [t if x == s else x for x in sheets]
            if kind.startswith('deferred'):
                sent = revised_sentence(text, s)
                others = [x for x in sheets if x != s and x.replace('-', '') in sent.upper().replace('-', '')]
                if kind == 'deferred' and others: continue
                repl = rng.choice(DEFERRED).format(s=s)
                if kind == 'deferred+missing':
                    # split the sentence: s is deferred, the other sheets stay "revised and attached", and one of
                    # them is removed from this case's drawing list (promised but not issued)
                    if not others or lists.near(target, others[0]): continue
                    repl += f" rev'd {', '.join(others)} attached."
                    remove.append([target, others[0]]); planted.append(f'{others[0]} removed from the Addendum {target} list')
                text = text.replace(sent, ' ' + repl); planted.append(f'{s} deferred')
            if kind.startswith('missing'):
                if lists.near(target, s): continue
                remove.append([target, s]); planted.append(f'{s} removed from the Addendum {target} list')
            if 'see_also' in kind:
                y = rng.choice([x for x in all_sheets if not lists.item(target, x) and x not in sheets and not lists.near(target, x)])
                text = text.rstrip() + ' ' + rng.choice(SEE_ALSO).format(y=y); planted.append(f'reference to {y} added')
                sheets = sheets + [y]
            text = noisy(text, sheets, rng)
            # the noise must not hide a sheet from code (otherwise the case tests the parser, not the reading)
            if any(x not in closeout.sheets_in(text) for x in sheets):
                continue
            used.add(r['source_id'])
            cases.append({'case_id': f'M{len(cases) + 1:02d}', 'kind': kind, 'source_id': r['source_id'],
                          'addendum': int(r['addendum']), 'question': r['question'], 'response': text,
                          'remove_from_list': remove, 'expected': EXPECTED[kind], 'planted': '; '.join(planted) or 'noise only'})
            break
        else:
            raise SystemExit(f'Could not build a {kind} case.')
    out = {'note': __doc__.split('\n\n')[1].strip(), 'seed': SEED, 'cases': cases}
    (ROOT / 'data' / 'closeout_cases_messy.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')
    print(f'{len(cases)} messy cases from a pool of {len(pool)} verified real answers.')


if __name__ == '__main__':
    main()
