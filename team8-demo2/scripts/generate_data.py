"""Generate the 24 simulated subcontractor -> GC RFIs used in Demo #2.

    python3 scripts/generate_data.py

Deterministic: no LLM, no randomness except a fixed shuffle seed, so anyone can
re-run it and get identical files.

How each case is made (the rules from our thesis document):
  1. Start from a REAL RFI in the Dett addenda (data/source_rfis.csv).
  2. Keep the same problem and drawing numbers; rewrite it in a subcontractor's
     voice for the construction phase and add what a sub would include
     (location, trade, response-needed date, impact). Those added details are
     SIMULATED and labelled as such.
  3. For every seed we make two versions:
       - a complete version  (expected flags: none)
       - a defective version (one or two fields deliberately broken)
     Some defects are obvious (blank, "TBD", "ASAP"); some are subtle
     ("Next week", "Second floor bathroom", a vague question) so we can see
     whether the AI adds anything over a simple checklist.
  4. Two complete versions are "tricky": a blank location field whose location
     is stated in the question, and a short-but-specific question. A good
     checker should NOT flag those.

Outputs: data/cases.json, data/answer_key.json  (drawing_index.json and
source_rfis.csv come from scripts/extract_addenda.py)
"""
import copy
import csv
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# --------------------------------------------------------------------------- seeds
# Each seed = one real Dett RFI rewritten as a construction-phase sub -> GC RFI.
# question/references keep the real problem and real sheet numbers.
# location wording is from the real RFI where it had one; trade, needed_by and impact are simulated.
SEEDS = [
    dict(seed='S01', source='Dett-A2-RFI12', title='Fixture type for Gym Office 173A', trade='Electrical',
         location='Annex Level 1, Gym Office 173A',
         question='Drawing E-301 does not specify a light fixture type in Gym Office 173A (Annex Level 1), and the fixture '
                  'schedule on E-801 does not say which type applies there. Please confirm the fixture type to be installed in Gym Office 173A.',
         references='E-301, E-801', needed_by='2023-10-13',
         impact='Ceiling rough-in for Gym Office 173A starts the week of Oct 16; fixtures must be ordered before then (about 3-week lead time).'),
    dict(seed='S02', source='Dett-A3-RFI10', title='Number of 2" conduits MDF to IDF', trade='Electrical',
         location='Level 1, conduit route between the MDF room and the IDF room',
         question='Drawing E-700 shows (4) 2-inch conduits from the IDF room to the MDF room, but Drawing E-500 calls for (5) 2-inch '
                  'conduits. Please confirm how many 2-inch conduits are required between the MDF and IDF rooms.',
         references='E-700, E-500', needed_by='2023-11-03',
         impact='Conduit installation between the MDF and IDF rooms is on hold; a late answer delays the start of low-voltage cabling.'),
    dict(seed='S03', source='Dett-A2-RFI5', title='Floor finish conflict, terrazzo vs VCT', trade='Flooring',
         location='Classroom wing Level 2, Room 221 Accessible All-Gender Toilet Room',
         question='The finish schedule on A-502 lists this room with a terrazzo floor, but Drawing ID-015 shows the same room as VCT. '
                  'Please confirm which floor finish is to be installed.',
         references='A-502, ID-015', needed_by='2023-11-10',
         impact='Floor preparation and finish ordering for this room are on hold; terrazzo needs different substrate preparation than VCT.'),
    dict(seed='S04', source='Dett-A3-RFI48', title='Caisson concrete strength', trade='Concrete / foundations',
         location='Annex foundations, all caissons shown on S-101',
         question='Sheet S-001 states that caisson concrete is 4,500 psi, while the Caisson Schedule on S-301 states 4,000 psi. '
                  'Please confirm the required compressive strength for the caissons.',
         references='S-001, S-301, S-101', needed_by='2023-09-20',
         impact='The concrete mix design submittal and the first caisson pours (scheduled 2023-09-25) are on hold.'),
    dict(seed='S05', source='Dett-A3-RFI6', title='Locker width, tier and base', trade='Specialties (lockers)',
         location='Classroom wing corridors, Levels 1-3 (lockers shown on A-102B, A-103B, A-104B)',
         question='The lockers scale at 15 inches wide on the floor plans, but Specification 10 51 13 lists 12-inch-wide lockers. '
                  'Please confirm the locker width, whether lockers are single- or double-tier, and what base is required under them.',
         references='A-102B, A-103B, A-104B; Spec 10 51 13', needed_by='2023-12-01',
         impact='The locker order (6-8 week lead time) cannot be released until size, tier and base are confirmed.'),
    dict(seed='S06', source='Dett-A5-RFI3', title='Countertop material conflict at Hallway 101', trade='Casework',
         location='Classroom wing Level 1, Hallway 101; same condition in Rooms 105 and 107',
         question='On Sheet A-210 detail 1, Hallway 101 has keynotes A.18 and A.19. KN A.18 and detail 6/A-703 show a new base cabinet '
                  'with a solid surface top, but KN A.19 says to replace with a plastic laminate countertop. Please confirm which '
                  'countertop material to provide. The same conflict occurs in Rooms 105 and 107.',
         references='A-210, A-703', needed_by='2024-01-12',
         impact='Casework shop drawings cannot be finalized; countertop fabrication takes about 4 weeks.'),
    dict(seed='S07', source='Dett-A3-RFI24', title='Fire pump feeder size', trade='Electrical',
         location='Service wing Level 1, Pump Room (fire pump feeder)',
         question='Drawing E-600 shows feeder S4-8 (1-1/4" conduit with 5 #8) to the fire pump, but Drawing FP-200 lists the fire pump '
                  'as 40 HP, which needs a much larger feeder. Please confirm the fire pump feeder size.',
         references='E-600, FP-200', needed_by='2023-10-27',
         impact='The fire pump feeder and conduit cannot be ordered or installed; fire pump acceptance testing is on the critical path to occupancy.'),
    dict(seed='S08', source='Dett-A6-RFI2', title='PV feed conduit size', trade='Electrical (PV)',
         location='PV feed from the roof array to the main electrical room',
         question='Drawing E-600 says the feed to the PV equipment is in a 3-1/2" conduit, while Drawing PV-600 shows 2-1/2". '
                  'Please confirm the conduit size for the PV feed.',
         references='E-600, PV-600', needed_by='Before roof membrane installation, scheduled 2024-02-05',
         impact='Roof penetrations and the conduit run for the PV feed are on hold until the size is confirmed.'),
    dict(seed='S09', source='Dett-A3-RFI43', title='Missing detail for keynote AE.18', trade='Masonry',
         location='Classroom wing exterior, south and north elevations, at locations tagged AE.18',
         question='Keynote AE.18 on Sheets A-401 and A-402 refers to detail 3/A-433, but that detail does not exist on A-433. '
                  'Please identify the correct detail for keynote AE.18.',
         references='A-401, A-402, A-433', needed_by='2023-10-06',
         impact='Masonry repair at AE.18 locations cannot be priced or scheduled until the detail is identified.'),
    dict(seed='S10', source='Dett-A3-RFI63', title='Cove fixture type in large toilet rooms', trade='Electrical',
         location='Annex Level 1, the two large toilet rooms (including Restroom 177)',
         question='The cove fixtures in the two large toilet rooms are now tagged Type C8, but Type C8 is a pole-mounted site fixture. '
                  'Please confirm that these cove fixtures should be Type C7, as previously shown.',
         references='E-301, E-801', needed_by='2023-12-15',
         impact='The lighting fixture order for the annex toilet rooms is on hold.'),
    dict(seed='S11', source='Dett-A3-RFI38', title='RT-1 vs RT-11 flooring', trade='Flooring',
         location='Rooms scheduled for RT-1 or RT-11 on the A-502 finish schedule',
         question='Is RT-1 flooring the same as RT-11?',
         references='A-502, A-503', needed_by='2023-11-17',
         impact='Resilient flooring order for the classroom wing is waiting on this answer.'),
    dict(seed='S12', source='Dett-A5-RFI10', title='Cove base over existing wall tile', trade='Tile',
         location='Classroom wing Level 1, Toilet Rooms 140, 143 and 160',
         question='The finish schedule on A-502 calls for T-2 6-inch ceramic cove base in these toilet rooms, with T-1 existing wall '
                  'tile to remain. Is the cove base installed over the existing wall tile, and is any patching of the existing tile '
                  'required? Please provide the installation detail for the cove base and its transition to the floor tile.',
         references='A-502, A-503', needed_by='2023-12-20',
         impact='Tile work in these toilet rooms is scheduled to start 2024-01-08 and will be held.'),
]

# --------------------------------------------------------------------------- defects
# seed -> (variant name, {field: new value}, expected flags)
# value None means "use a sheet number that does not exist" (computed below).
DEFECTS = {
    'S01': ('subtle_deadline',      {'needed_by': 'Next week'}, ['needed_by']),
    'S02': ('subtle_vague_question', {'question': 'We found an issue with the conduit quantities on the drawings, please advise what to do.'}, ['question']),
    'S03': ('subtle_vague_location', {'location': 'Second floor bathroom'}, ['location']),
    'S04': ('bad_reference',         {'references': None}, ['references']),
    'S05': ('placeholder_impact',    {'impact': 'TBD'}, ['impact']),
    'S06': ('vague_question',        {'question': 'Please clarify the countertops in these rooms.'}, ['question']),
    'S07': ('blank_impact',          {'impact': ''}, ['impact']),
    'S08': ('placeholder_deadline',  {'needed_by': 'ASAP'}, ['needed_by']),
    'S09': ('blank_deadline',        {'needed_by': ''}, ['needed_by']),
    'S10': ('missing_reference+subtle_impact', {'references': 'See drawings', 'impact': 'Could cause problems later.'}, ['references', 'impact']),
    'S11': ('placeholder_impact',    {'impact': 'N/A'}, ['impact']),
    'S12': ('blank_location',        {'location': ''}, ['location']),
}
# Complete versions that a naive checklist would wrongly flag (expected flags: none).
TRICKY_CLEAN = {
    'S01': ('clean_location_in_question', {'location': ''}),   # room is named in the question
    'S11': ('clean_short_question', {}),                         # short but specific question
}


def nonexistent_sheet(sheet, index):
    """Same discipline prefix, a number that is NOT in the drawing index (deterministic)."""
    m = re.match(r'^([A-Z]+)-(\d{3})', sheet)
    prefix, num = m.group(1), int(m.group(2))
    for step in range(5, 100):
        cand = f'{prefix}-{num + step:03d}'
        if cand not in index:
            return cand
    raise ValueError(sheet)


def generate():
    index = json.loads((ROOT/'data'/'drawing_index.json').read_text(encoding='utf-8'))
    sources = {r['source_id']: r for r in csv.DictReader(open(ROOT/'data'/'source_rfis.csv', encoding='utf-8'))}
    items = []
    for seed in SEEDS:
        src = sources[seed['source']]
        complete = {k: seed[k] for k in ('title', 'location', 'trade', 'question', 'needed_by', 'impact', 'references')}
        for sheet in re.findall(r'[A-Z]{1,3}-\d{3}[A-Z]?', complete['references']):
            assert sheet in index, f"{seed['seed']}: {sheet} not in drawing index"
        source = {'id': src['source_id'], 'addendum': int(src['addendum']), 'rfi': int(src['rfi_no']),
                  'pdf_page': int(src['pdf_page']), 'url': src['url'],
                  'type': 'public bid-stage RFI, rewritten as a construction-stage subcontractor RFI (simulated)',
                  'original_question': src['question']}
        # complete version
        variant, change = TRICKY_CLEAN.get(seed['seed'], ('clean', {}))
        clean = {**complete, **change}
        items.append((seed['seed'], variant, clean, complete, [], source, src['response']))
        # defective version
        variant, change, flags = DEFECTS[seed['seed']]
        broken = copy.deepcopy(complete)
        for field, value in change.items():
            if value is None:  # bad reference: swap the 2nd sheet for one that does not exist
                sheets = [s.strip() for s in complete['references'].split(',')]
                sheets[1] = nonexistent_sheet(sheets[1].split(';')[0], index)
                value = ', '.join(sheets)
            broken[field] = value
        items.append((seed['seed'], variant, broken, complete, flags, source, src['response']))

    random.Random(492).shuffle(items)  # so case numbers do not reveal which version is defective
    cases, keys = [], []
    for i, (seed, variant, initial, complete, flags, source, response) in enumerate(items, 1):
        cid = f'D{i:02d}'
        cases.append({'case_id': cid, 'is_simulated': True, 'source': source, 'initial': initial,
                      'brief': {'known_details': complete,
                                'simulation_note': 'SIMULATED. The problem and sheet numbers come from a real Dett RFI; the '
                                                   'construction-stage framing, trade, dates and impact were written by Team 8 '
                                                   'for this exercise. Historical answers are not shown to the AI.'}})
        keys.append({'case_id': cid, 'seed': seed, 'variant': variant, 'expected_flags': flags,
                     'historical_response': response, 'source': source['id'],
                     'scoring_note': 'Team-made label: the fields we deliberately broke. A complete version expects no flags.'})
    for name, data in [('cases.json', cases), ('answer_key.json', keys)]:
        (ROOT/'data'/name).write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    n_def = sum(1 for k in keys if k['expected_flags'])
    print(f'Generated {len(cases)} simulated cases ({n_def} defective, {len(cases)-n_def} complete) '
          f'with {sum(len(k["expected_flags"]) for k in keys)} planted defects.')


if __name__ == '__main__':
    generate()
