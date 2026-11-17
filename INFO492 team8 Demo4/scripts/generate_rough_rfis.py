"""Generate the 12 rough field RFIs used in Demo #3 (data/rough_rfis.json, data/rough_answer_key.json).

    python3 scripts/generate_rough_rfis.py

Deterministic, no LLM at run time. Each rough RFI is a short message a foreman might send the GC from
site, written by our team from one of the same 12 real Dett RFIs used in Demo #2 (SEEDS below, copied
from team8-demo2/scripts/generate_data.py). The drafting was AI-assisted and reviewed by the team.

Why rough messages: our stakeholder interview (interviews/ in the repo root) said construction-stage
RFIs often arrive as a short text plus a photo, and most often miss the location, the response date and
the impact; sheet numbers are present but often imprecise or from an older drawing set. Demo #2 used
complete, cleanly written RFIs, which the interviewee said are cleaner than real ones.

What is real: the problem in each question and the sheet numbers (from the Dett addenda), and which
sheets were revised in which addendum (data/revisions.json). What is simulated: the message wording,
the drawing set each foreman is using, and the "site notes" (location, date, impact) the foreman knows.
Labels live only in data/rough_answer_key.json, which is never sent to an agent.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# The complete version of each RFI (what the foreman knows; used as his answers to the agent's questions).
SEEDS = [
    {'seed': 'S01', 'source': 'Dett-A2-RFI12', 'title': 'Fixture type for Gym Office 173A', 'trade': 'Electrical', 'location': 'Annex Level 1, Gym Office 173A', 'question': 'Drawing E-301 does not specify a light fixture type in Gym Office 173A (Annex Level 1), and the fixture schedule on E-801 does not say which type applies there. Please confirm the fixture type to be installed in Gym Office 173A.', 'references': 'E-301, E-801', 'needed_by': '2023-10-13', 'impact': 'Ceiling rough-in for Gym Office 173A starts the week of Oct 16; fixtures must be ordered before then (about 3-week lead time).'},
    {'seed': 'S02', 'source': 'Dett-A3-RFI10', 'title': 'Number of 2" conduits MDF to IDF', 'trade': 'Electrical', 'location': 'Level 1, conduit route between the MDF room and the IDF room', 'question': 'Drawing E-700 shows (4) 2-inch conduits from the IDF room to the MDF room, but Drawing E-500 calls for (5) 2-inch conduits. Please confirm how many 2-inch conduits are required between the MDF and IDF rooms.', 'references': 'E-700, E-500', 'needed_by': '2023-11-03', 'impact': 'Conduit installation between the MDF and IDF rooms is on hold; a late answer delays the start of low-voltage cabling.'},
    {'seed': 'S03', 'source': 'Dett-A2-RFI5', 'title': 'Floor finish conflict, terrazzo vs VCT', 'trade': 'Flooring', 'location': 'Classroom wing Level 2, Room 221 Accessible All-Gender Toilet Room', 'question': 'The finish schedule on A-502 lists this room with a terrazzo floor, but Drawing ID-015 shows the same room as VCT. Please confirm which floor finish is to be installed.', 'references': 'A-502, ID-015', 'needed_by': '2023-11-10', 'impact': 'Floor preparation and finish ordering for this room are on hold; terrazzo needs different substrate preparation than VCT.'},
    {'seed': 'S04', 'source': 'Dett-A3-RFI48', 'title': 'Caisson concrete strength', 'trade': 'Concrete / foundations', 'location': 'Annex foundations, all caissons shown on S-101', 'question': 'Sheet S-001 states that caisson concrete is 4,500 psi, while the Caisson Schedule on S-301 states 4,000 psi. Please confirm the required compressive strength for the caissons.', 'references': 'S-001, S-301, S-101', 'needed_by': '2023-09-20', 'impact': 'The concrete mix design submittal and the first caisson pours (scheduled 2023-09-25) are on hold.'},
    {'seed': 'S05', 'source': 'Dett-A3-RFI6', 'title': 'Locker width, tier and base', 'trade': 'Specialties (lockers)', 'location': 'Classroom wing corridors, Levels 1-3 (lockers shown on A-102B, A-103B, A-104B)', 'question': 'The lockers scale at 15 inches wide on the floor plans, but Specification 10 51 13 lists 12-inch-wide lockers. Please confirm the locker width, whether lockers are single- or double-tier, and what base is required under them.', 'references': 'A-102B, A-103B, A-104B; Spec 10 51 13', 'needed_by': '2023-12-01', 'impact': 'The locker order (6-8 week lead time) cannot be released until size, tier and base are confirmed.'},
    {'seed': 'S06', 'source': 'Dett-A5-RFI3', 'title': 'Countertop material conflict at Hallway 101', 'trade': 'Casework', 'location': 'Classroom wing Level 1, Hallway 101; same condition in Rooms 105 and 107', 'question': 'On Sheet A-210 detail 1, Hallway 101 has keynotes A.18 and A.19. KN A.18 and detail 6/A-703 show a new base cabinet with a solid surface top, but KN A.19 says to replace with a plastic laminate countertop. Please confirm which countertop material to provide. The same conflict occurs in Rooms 105 and 107.', 'references': 'A-210, A-703', 'needed_by': '2024-01-12', 'impact': 'Casework shop drawings cannot be finalized; countertop fabrication takes about 4 weeks.'},
    {'seed': 'S07', 'source': 'Dett-A3-RFI24', 'title': 'Fire pump feeder size', 'trade': 'Electrical', 'location': 'Service wing Level 1, Pump Room (fire pump feeder)', 'question': 'Drawing E-600 shows feeder S4-8 (1-1/4" conduit with 5 #8) to the fire pump, but Drawing FP-200 lists the fire pump as 40 HP, which needs a much larger feeder. Please confirm the fire pump feeder size.', 'references': 'E-600, FP-200', 'needed_by': '2023-10-27', 'impact': 'The fire pump feeder and conduit cannot be ordered or installed; fire pump acceptance testing is on the critical path to occupancy.'},
    {'seed': 'S08', 'source': 'Dett-A6-RFI2', 'title': 'PV feed conduit size', 'trade': 'Electrical (PV)', 'location': 'PV feed from the roof array to the main electrical room', 'question': 'Drawing E-600 says the feed to the PV equipment is in a 3-1/2" conduit, while Drawing PV-600 shows 2-1/2". Please confirm the conduit size for the PV feed.', 'references': 'E-600, PV-600', 'needed_by': 'Before roof membrane installation, scheduled 2024-02-05', 'impact': 'Roof penetrations and the conduit run for the PV feed are on hold until the size is confirmed.'},
    {'seed': 'S09', 'source': 'Dett-A3-RFI43', 'title': 'Missing detail for keynote AE.18', 'trade': 'Masonry', 'location': 'Classroom wing exterior, south and north elevations, at locations tagged AE.18', 'question': 'Keynote AE.18 on Sheets A-401 and A-402 refers to detail 3/A-433, but that detail does not exist on A-433. Please identify the correct detail for keynote AE.18.', 'references': 'A-401, A-402, A-433', 'needed_by': '2023-10-06', 'impact': 'Masonry repair at AE.18 locations cannot be priced or scheduled until the detail is identified.'},
    {'seed': 'S10', 'source': 'Dett-A3-RFI63', 'title': 'Cove fixture type in large toilet rooms', 'trade': 'Electrical', 'location': 'Annex Level 1, the two large toilet rooms (including Restroom 177)', 'question': 'The cove fixtures in the two large toilet rooms are now tagged Type C8, but Type C8 is a pole-mounted site fixture. Please confirm that these cove fixtures should be Type C7, as previously shown.', 'references': 'E-301, E-801', 'needed_by': '2023-12-15', 'impact': 'The lighting fixture order for the annex toilet rooms is on hold.'},
    {'seed': 'S11', 'source': 'Dett-A3-RFI38', 'title': 'RT-1 vs RT-11 flooring', 'trade': 'Flooring', 'location': 'Rooms scheduled for RT-1 or RT-11 on the A-502 finish schedule', 'question': 'Is RT-1 flooring the same as RT-11?', 'references': 'A-502, A-503', 'needed_by': '2023-11-17', 'impact': 'Resilient flooring order for the classroom wing is waiting on this answer.'},
    {'seed': 'S12', 'source': 'Dett-A5-RFI10', 'title': 'Cove base over existing wall tile', 'trade': 'Tile', 'location': 'Classroom wing Level 1, Toilet Rooms 140, 143 and 160', 'question': 'The finish schedule on A-502 calls for T-2 6-inch ceramic cove base in these toilet rooms, with T-1 existing wall tile to remain. Is the cove base installed over the existing wall tile, and is any patching of the existing tile required? Please provide the installation detail for the cove base and its transition to the floor tile.', 'references': 'A-502, A-503', 'needed_by': '2023-12-20', 'impact': 'Tile work in these toilet rooms is scheduled to start 2024-01-08 and will be held.'},]

# drawing_set: the addendum whose drawing set the foreman is working from (0 = bid set).
# missing: which of location / needed_by / impact the message does NOT state (a reviewer would have to ask).
# ref_issues: problems with the sheet numbers as written: partial (a needed sheet is not cited),
#   nonexistent (not in the index), typo, missing (no sheet number), superseded (cited sheet was revised
#   in a later addendum than the foreman's drawing set).
ROUGH = [
    dict(id='F01', seed='S01', drawing_set=1, sheets='E301, E-801',
         message='no fixture type shown for the gym office 173A on E301, fixture schedule E-801 doesnt say either. what fixture do we put in there',
         missing=['needed_by', 'impact'], ref_issues=['superseded'],
         note='Location is stated. E-301 was revised in Addenda 2 and 3, after the Addendum 1 set the foreman is using.'),
    dict(id='F02', seed='S02', drawing_set=3, sheets='E-700, E-500',
         message='E-700 shows (4) 2" conduits from IDF to MDF but E-500 calls for (5). how many do we run?? need this asap',
         missing=['needed_by', 'impact'], ref_issues=[],
         note='"asap" is not a date. Location (MDF to IDF route) is stated.'),
    dict(id='F03', seed='S03', drawing_set=2, sheets='ID-015',
         message='2nd floor bathroom - finish schedule says terrazzo but ID-015 shows VCT. which one',
         missing=['location', 'needed_by', 'impact'], ref_issues=['partial'],
         note='Several toilet rooms on Level 2; the room is not identified. The finish schedule sheet (A-502) is not cited.'),
    dict(id='F04', seed='S04', drawing_set=3, sheets='S-001, S-301',
         message='Annex caissons: S-001 says 4,500 psi concrete, caisson schedule on S-301 says 4,000 psi. Which strength is right? '
                 'Mix design and first pours (9/25) are on hold, need the answer by 9/20.',
         missing=[], ref_issues=[],
         note='Complete control case: location, date and impact are all stated.'),
    dict(id='F05', seed='S05', drawing_set=2, sheets='A-102',
         message='lockers scale 15in wide on A-102 but spec 10 51 13 says 12in. single or double tier? and what base goes under them',
         missing=['location', 'needed_by', 'impact'], ref_issues=['nonexistent'],
         note='There is no A-102; the floor plans are A-102B, A-103B and A-104B. Which corridors is not stated.'),
    dict(id='F06', seed='S06', drawing_set=2, sheets='6/A-703',
         message='Hallway 101 has keynotes A.18 and A.19 - A.18 and 6/A-703 show solid surface top, A.19 says plastic laminate. '
                 'which countertop? same thing in rooms 105 and 107',
         missing=['needed_by', 'impact'], ref_issues=['partial'],
         note='The plan sheet with the keynotes (A-210) is not cited.'),
    dict(id='F07', seed='S07', drawing_set=1, sheets='E-600, FP-2O0',
         message='feeder S4-8 to the fire pump on E-600 (1-1/4" w/ 5 #8) looks way too small for the 40hp pump on FP-2O0. '
                 'confirm feeder size, fire pump test is on the critical path',
         missing=['location', 'needed_by'], ref_issues=['typo', 'superseded'],
         note='Letter O typed for zero in FP-200. E-600 was revised in Addenda 2 and 3. Impact is stated.'),
    dict(id='F08', seed='S08', drawing_set=6, sheets='E-600, PV-600',
         message='PV feed from roof array to main elec room: E-600 says 3-1/2" conduit, PV-600 shows 2-1/2". which size. need it before the roofers start',
         missing=['needed_by', 'impact'], ref_issues=[],
         note='"before the roofers start" is not a date. Location is stated.'),
    dict(id='F09', seed='S09', drawing_set=3, sheets='A-401, A-402, A-433',
         message='keynote AE.18 on A-401/A-402 points to detail 3/A-433 but there is no detail 3 on that sheet. which detail do we use? '
                 'cant price or schedule the masonry repair at those spots',
         missing=['location', 'needed_by'], ref_issues=[],
         note='Which elevations is not stated. Impact is stated.'),
    dict(id='F10', seed='S10', drawing_set=3, sheets='see drawings',
         message='toilet room cove lights are tagged C8 now, C8 is the pole light. should be C7 like before right? see drawings',
         missing=['location', 'needed_by', 'impact'], ref_issues=['missing'],
         note='No sheet number. Which toilet rooms is not stated.'),
    dict(id='F11', seed='S11', drawing_set=3, sheets='A-502',
         message='Is RT-1 the same as RT-11 on the A-502 finish schedule? Resilient flooring order for the classroom wing is waiting on this, '
                 'need an answer by 11/17.',
         missing=[], ref_issues=[],
         note='Complete control case: short but specific; the rooms are those scheduled for RT-1/RT-11.'),
    dict(id='F12', seed='S12', drawing_set=1, sheets='A-502',
         message='toilet rooms 140, 143, 160 - T-2 cove base goes over the existing T-1 wall tile? any patching needed? need the detail',
         missing=['needed_by', 'impact'], ref_issues=[],
         note='Location is stated. A-502 has not been revised since Addendum 1.'),
]


def main():
    seeds = {s['seed']: s for s in SEEDS}
    rough, key = [], []
    for r in ROUGH:
        s = seeds[r['seed']]
        rough.append({'case_id': r['id'], 'is_simulated': True, 'drawing_set': r['drawing_set'],
                      'message': r['message'], 'sheets_as_written': r['sheets'],
                      'source': {'id': s['source'], 'seed': s['seed'], 'title': s['title']},
                      'site_notes': {k: s[k] for k in ('location', 'needed_by', 'impact', 'trade', 'references')}})
        key.append({'case_id': r['id'], 'missing': r['missing'], 'ref_issues': r['ref_issues'], 'note': r['note'],
                    'correct_references': s['references']})
    (ROOT / 'data' / 'rough_rfis.json').write_text(json.dumps(rough, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    (ROOT / 'data' / 'rough_answer_key.json').write_text(json.dumps(key, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    n_missing = sum(len(r['missing']) for r in ROUGH); n_ref = sum(1 for r in ROUGH if r['ref_issues'])
    print(f'{len(rough)} rough RFIs: {n_missing} missing items, {n_ref} with reference problems, '
          f'{sum(1 for r in ROUGH if not r["missing"] and not r["ref_issues"])} complete controls')


if __name__ == '__main__':
    main()
