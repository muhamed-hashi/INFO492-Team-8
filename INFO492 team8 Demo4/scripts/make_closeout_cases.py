"""Build data/closeout_cases.json: 40 close-out test cases with a known right answer. Deterministic, no AI.

    python3 scripts/make_closeout_cases.py

Every case starts from a REAL Dett RFI answer whose revised sheets really are in that addendum's drawing
list (checked by code). Some cases are kept as they are; others get one planted problem. The right answer
comes from how the case was built, so nobody (and no AI) has to label it:

    clean      (12)  real answer, unchanged                                   -> ok_to_close
    see_also   ( 6)  + "see Drawing Y" where Y is a real sheet NOT in this     -> ok_to_close
                     addendum (Y is only referred to, not revised)
    missing    ( 8)  the revised sheet is removed from this case's copy of     -> hold
                     the addendum drawing list (promised but not issued)
    deferred   ( 8)  the sentence saying the sheet was revised is rewritten    -> keep_open
                     to say the revision will come later
    typo       ( 6)  the sheet number in the answer gets a typo: a missing or  -> check
                     extra suffix letter, or two digits swapped

The rewrite sentences below were written by the team for this test and are deliberately varied; some do
not use any of the words the code baseline looks for. They are not taken from the agent's prompt.
"""
import csv
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import agents  # noqa: E402
import closeout  # noqa: E402

SEED = 492
DEFERRED = [
    'A revised Drawing {s} will be issued with the construction set.',
    '{s} will be updated to show this and released once the building permit is issued.',
    'This change is not on the drawings yet; the architect will reissue {s} in a later bulletin.',
    'Drawing {s} is being revised and will go out with the permit set.',
    'The design team is still revising {s}; the updated sheet is not part of this addendum.',
    'Revisions to {s} are pending and are not included here.',
    '{s} has not been revised yet. The change will appear on the next issue of the drawings.',
    'An updated {s} is to be provided after award.',
]
SEE_ALSO = ['Also see Drawing {y} for the existing conditions.', 'Coordinate with {y}.',
            'For context, refer to {y} in the Contract Documents.']
REVISED_SENTENCE = re.compile(r'[^.]*\brevis\w*[^.]*(?:\.|$)', re.I)


def revised_sentence(text, sheet):
    """The sentence that says `sheet` was revised (it must name the sheet, with or without the hyphen)."""
    plain = sheet.replace('-', '')
    return next((m.group(0) for m in REVISED_SENTENCE.finditer(text)
                 if sheet in m.group(0).upper() or plain in m.group(0).upper().replace('-', '')), None)


def typo(sheet, lists, swap_first):
    """A typo of `sheet` that is in no drawing list but that the near-match rule can still link back:
    two neighbouring digits swapped, or a suffix letter added or dropped. Alternates between the two kinds."""
    m = re.match(r'^([A-Z]{1,3})-(\d+)([A-Z]?)$', sheet)
    p, n, suf = m.groups()
    suffix = [f'{p}-{n}' if suf else f'{p}-{n}B']
    swaps = [f'{p}-{n[:i]}{n[i + 1]}{n[i]}{n[i + 2:]}{suf}' for i in range(len(n) - 1) if n[i] != n[i + 1]]
    options = swaps + suffix if swap_first else suffix + swaps
    return next((o for o in options if not lists.where(o)), None)


def main():
    data = agents.load('addendum_drawing_lists.json')
    lists = closeout.DrawingLists(data)
    rows = list(csv.DictReader(open(ROOT / 'data' / 'source_rfis.csv', encoding='utf-8')))
    pool = []
    for r in rows:
        out = closeout.code_closeout(r, lists)
        f = out['facts']
        if out['recommendation'] == 'ok_to_close' and out['evidence'] and not f['defer_words'] \
                and len(f['sheets']) == len(out['evidence']) and revised_sentence(r['response'], f['sheets'][0]):
            pool.append(r)
    rng = random.Random(SEED)
    rng.shuffle(pool)
    deferred = rng.sample(DEFERRED, len(DEFERRED))          # each rewrite sentence used once
    see_also = rng.sample(SEE_ALSO, len(SEE_ALSO)) * 2
    all_sheets = sorted({closeout.norm(d['sheet']) for a in data['addenda'] for d in a['drawings']
                         if re.match(r'^[A-Z]{1,2}-\d{3}[A-Z]?$', closeout.norm(d['sheet']))})
    plan = ['clean'] * 12 + ['see_also'] * 6 + ['missing'] * 8 + ['deferred'] * 8 + ['typo'] * 6
    if len(pool) < len(plan):
        raise SystemExit(f'Only {len(pool)} usable real answers; need {len(plan)}.')
    cases, i = [], 0
    for kind in plan:
        while True:
            r = pool[i]; i += 1
            target = closeout.facts(r)['target_addendum']
            sheets = closeout.facts(r)['sheets']
            s = sheets[0]
            case = {'case_id': f'C{len(cases) + 1:02d}', 'kind': kind, 'source_id': r['source_id'],
                    'addendum': int(r['addendum']), 'question': r['question'], 'response': r['response'],
                    'remove_from_list': [], 'expected': 'ok_to_close', 'planted': ''}
            if kind == 'see_also':
                y = rng.choice([x for x in all_sheets if not lists.item(target, x) and x not in sheets
                                and not lists.near(target, x)])
                case['response'] = r['response'].rstrip() + ' ' + see_also.pop().format(y=y)
                case['planted'] = f'Added a reference to {y}, which is not in Addendum {target}.'
            elif kind == 'missing':
                if lists.near(target, s): continue
                case['remove_from_list'] = [[target, s]]
                case['expected'] = 'hold'
                case['planted'] = f'Removed {s} from this case\'s copy of the Addendum {target} drawing list.'
            elif kind == 'deferred':
                sentence = revised_sentence(r['response'], s)
                if len(sheets) > 1 and any(x != s and x.replace('-', '') in sentence.upper().replace('-', '') for x in sheets):
                    continue                     # keep it simple: the rewritten sentence names one sheet only
                case['response'] = ' '.join(r['response'].replace(sentence, ' ' + deferred.pop().format(s=s)).split())
                case['expected'] = 'keep_open'
                case['planted'] = f'Rewrote the sentence saying {s} was revised so that the revision comes later.'
            elif kind == 'typo':
                t = typo(s, lists, swap_first=sum(c['kind'] == 'typo' for c in cases) % 2 == 0)
                if not t or s not in lists.near(target, t): continue
                case['response'] = re.sub(re.escape(s).replace('\\-', '-?'), t, r['response'])
                if t not in closeout.sheets_in(case['response']): continue
                case['expected'] = 'check'
                case['planted'] = f'Changed {s} to {t} in the answer.'
            cases.append(case)
            break
    out = {'note': __doc__.split('\n\n')[1].strip(), 'seed': SEED, 'cases': cases}
    (ROOT / 'data' / 'closeout_cases.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')
    print(f'{len(cases)} cases from a pool of {len(pool)} verified real answers.')


if __name__ == '__main__':
    main()
