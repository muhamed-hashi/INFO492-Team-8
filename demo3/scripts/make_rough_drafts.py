"""
Generate the Demo 3 rough RFI drafts (simulated) from real Dett Elementary RFIs.

Source: Public Building Commission of Chicago, Contract C1604,
Robert Nathaniel Dett Elementary School Annex and Renovations,
Addendum No. 5 (June 9, 2023) and Addendum No. 6 (June 15, 2023).
https://pbcchicago.com/opportunities/advertisement-for-bids-contract-c1604-robert-nathaniel-dett-elementary-school-annex-and-renovations/

Each draft rewrites one real bid-stage question as a rough construction-stage
message from a subcontractor to the GC, following patterns described in our
GC practitioner interview (interviews/Kevin_Chen_GC-assistant-PM.md).

Run:  python3 scripts/make_rough_drafts.py
Writes: data/rough_drafts.json, data/rough_drafts.csv
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

A5 = "Dett Addendum No. 5 (2023-06-09)"
A6 = "Dett Addendum No. 6 (2023-06-15)"

# Sheet numbers that exist in the Dett sheet matrix (Addendum 6 cover sheet).
# Used only to check that our answer key cites real sheets.
SHEET_INDEX = {
    "A-210", "A-221", "A-300", "A-301", "A-301B", "A-303A", "A-502", "A-503",
    "A-703", "P-100A", "P-201", "P-202", "E-010", "E-202", "E-203", "E-204",
    "E-600", "E-702", "PV-600",
}

# Interview patterns (Kevin Chen, GC assistant PM) used as planted issues.
PATTERNS = {
    "vague_location": "Location is unclear ('here', 'the hallway') - interview: most common missing item",
    "missing_sheet": "No sheet or detail number given",
    "wrong_or_incomplete_sheet": "Sheet number incomplete or ambiguous (e.g., 'A2', '5/A-50') - interview: 2-3 in 10 RFIs",
    "outdated_reference": "Cites a detail that a later revision replaced - interview: subs keep using the bid set",
    "missing_deadline": "No needed-by date, or only 'ASAP' - interview: 'if everything is ASAP, nothing is ASAP'",
    "missing_impact": "Does not say what work is held up or what it costs",
    "multi_question": "Several questions in one message - interview: GC has to split them",
    "photo_without_description": "Says 'see pic' without saying what the photo shows",
    "scope_cost_hint": "Wording hints at extra cost / scope ('hiding money') - interview: GC checks contract with PM",
}

DRAFTS = [
    {
        "draft_id": "R01",
        "source_rfi": "Dett-A5-RFI3",
        "source_file": A5,
        "source_page": 2,
        "trade": "Casework / millwork",
        "difficulty": "hard",
        "rough_draft": (
            "hallway by the office suite + the 2 multipurpose rms - cab detail says "
            "solid surface top but the other note says plam?? which one. per 6/A-703. see pic"
        ),
        "source_question": (
            "Sheet A-210 detail 1. In Hallway 101 there are keynotes A.18 & A.19. There are no "
            "elevations, but from these keynotes and the detail associated with KN A.18 (6/A-703), "
            "this is a new base cabinet with a solid surface top, which contradicts KN A.19 which "
            "states to replace with a plastic laminate countertop. Please advise. Note: Same for Room 105, 107"
        ),
        "source_response": "Drawings A-210 and A-221 have been revised and are included in this addendum.",
        "related_revision": "Addendum 5 Change 3: A-221 KN A.18 now refers to detail 1/A-703 instead of 6/A-703, for all instances in the set.",
        "correct_location": "Hallway 101; Rooms 105 and 107",
        "correct_references": ["A-210 (detail 1)", "A-221", "KN A.18", "KN A.19", "1/A-703"],
        "planted_issues": ["vague_location", "missing_sheet", "outdated_reference",
                           "missing_deadline", "missing_impact", "photo_without_description"],
        "expected_followups": [
            "Which rooms exactly? (Hallway 101, Rooms 105 and 107?)",
            "Which plan sheet and keynotes are in conflict? (A-210 detail 1, KN A.18 vs A.19?)",
            "Detail 6/A-703 was replaced by 1/A-703 in Addendum 5 - which drawing set are you using?",
            "What does the photo show?",
            "When do you need an answer, and what work is waiting?",
        ],
        "invented_details": ["construction-stage setting", "photo mention"],
    },
    {
        "draft_id": "R02",
        "source_rfi": "Dett-A5-RFI4",
        "source_file": A5,
        "source_page": 2,
        "trade": "Casework / millwork",
        "difficulty": "medium",
        "rough_draft": "drop sink in the hallway millwork - no elev. is it a base cab? what top? need to order ASAP",
        "source_question": (
            "Sheet A-210 detail 1. In Hallway 101 there is a KN A.34 which states provide a "
            "stainless-steel drop sink in millwork. There is no elevation of this millwork. Is this a "
            "base cabinet? Does it receive a plastic laminate top or solid surface top? Please advise."
        ),
        "source_response": "Key Note A.34 has been superseded by a text note. Drawing A-210 has been revised and is included in this addendum.",
        "related_revision": "Addendum 5 Change 2: A-210 updated scope for removing and providing millwork.",
        "correct_location": "Hallway 101",
        "correct_references": ["A-210 (detail 1)", "KN A.34"],
        "planted_issues": ["vague_location", "missing_sheet", "missing_deadline", "multi_question"],
        "expected_followups": [
            "Which hallway? (Hallway 101?)",
            "Which sheet and keynote? (A-210 detail 1, KN A.34?)",
            "'ASAP' - what date do you need it by to keep the order on schedule?",
        ],
        "invented_details": ["ordering pressure"],
    },
    {
        "draft_id": "R03",
        "source_rfi": "Dett-A5-RFI7",
        "source_file": A5,
        "source_page": 3,
        "trade": "Plumbing",
        "difficulty": "hard",
        "rough_draft": (
            "staff toilets in service wing - P2 says connect new WC + lav but the underfloor dwg "
            "says existing no work. which is it?? also need a fixture schedule. addendums keep "
            "changing scope, were not carrying extra fixtures unless directed"
        ),
        "source_question": (
            "In addendum #3 for PBC Robert Nathaniel Dett 3 pages contradict each other: In the top left "
            "corner of page P-100A, there is an unlisted bathroom that says; EXISTING, NO WORK ... AND on "
            "page P-201 it follows suit but calls out the fixtures & rooms (staff toilet 140 & 143) THEN On "
            "page P-202, in detail 2 ... it says 'connect new plumb fixture to ex san' calling out for 2 new "
            "WC-1 & L-1s. A schedule of all plumbing fixtures should be provided for most accurate plumbing quote."
        ),
        "source_response": "Drawings P-201 and P-202 have been revised and are included in this addendum.",
        "related_revision": "Addendum 5 Changes 18-19: P-201 and P-202 revised annotations for toilet rooms 140, 143, 160.",
        "correct_location": "Staff Toilet 140 and 143",
        "correct_references": ["P-100A", "P-201", "P-202 (detail 2)", "WC-1", "L-1"],
        "planted_issues": ["vague_location", "wrong_or_incomplete_sheet", "multi_question",
                           "scope_cost_hint", "missing_deadline"],
        "expected_followups": [
            "Which rooms? (Staff Toilet 140 and 143?)",
            "'P2' - do you mean P-201 or P-202? Which detail?",
            "Underfloor drawing - is that P-100A?",
            "Split the fixture schedule request from the conflict question?",
            "When do you need an answer?",
        ],
        "invented_details": ["construction-stage setting"],
    },
    {
        "draft_id": "R04",
        "source_rfi": "Dett-A5-RFI8",
        "source_file": A5,
        "source_page": 3,
        "trade": "Solid surface wall panels",
        "difficulty": "medium",
        "rough_draft": (
            "AX42 on A-30 elevs is pointing at the joints between the solid surface panels but the "
            "note is about an operable partition closure panel?? doesnt make sense. what mfr for the "
            "joints. happens all over the elevs"
        ),
        "source_question": (
            "Sheet A-301B of the drawings, elevations 1 & 3, show a keynote AX.42 pointing to joints "
            "between the solid surface wall panels. The keynote AX.42 description is 'Provide "
            "acoustically-sealed full height operable partition closure panel, per manufacturer'. ... "
            "Please clarify what this note means and what manufacturer is being referenced for these joints."
        ),
        "source_response": "Drawings A-300, A-301, A-301B, A-303A have been revised and are included in this addendum.",
        "related_revision": "Addendum 5 Changes 4-7: KN AX.42 revised to AX.41 at solid surface locations on A-300, A-301, A-301B, A-303A.",
        "correct_location": "Annex hallway link and service corridor (A-301B elevations 1 and 3)",
        "correct_references": ["A-301B (elevations 1 and 3)", "A-300", "A-301", "A-303A", "KN AX.42"],
        "planted_issues": ["wrong_or_incomplete_sheet", "vague_location", "missing_deadline", "missing_impact"],
        "expected_followups": [
            "'A-30' is not a sheet - do you mean A-301B (or A-300 / A-301)?",
            "Which elevations / where in the building?",
            "When do you need an answer?",
        ],
        "invented_details": [],
    },
    {
        "draft_id": "R05",
        "source_rfi": "Dett-A5-RFI9",
        "source_file": A5,
        "source_page": 3,
        "trade": "Tile",
        "difficulty": "medium",
        "rough_draft": (
            "kinder toilet rms - finish sched says T-1 on the floor but the legend says T-1 is "
            "existing wall tile to remain. so what goes on the floor? and whats the pattern for T-2"
        ),
        "source_question": (
            "Per addendum #3 Sheet A-502, Toilet Rooms 108B, 109A, 110B, 111A call for T-1 floor finish. "
            "However, Sheet A-503 references T-1 finish as 'Existing Wall Tile to Remain'. Please confirm "
            "floor finish for these toilet rooms as well as tile patterns for T-2."
        ),
        "source_response": "Per Addendum No. 03, Kindergarten Toilet Rooms 108B, 109A, 110B, 111A have existing wall tile to remain.",
        "related_revision": None,
        "correct_location": "Kindergarten Toilet Rooms 108B, 109A, 110B, 111A",
        "correct_references": ["A-502", "A-503"],
        "planted_issues": ["vague_location", "missing_sheet", "multi_question", "missing_deadline", "missing_impact"],
        "expected_followups": [
            "Which toilet rooms? (108B, 109A, 110B, 111A?)",
            "Which sheets? (Finish schedule A-502 and legend A-503?)",
            "When do you need an answer, and is tile ordering on hold?",
        ],
        "invented_details": [],
    },
    {
        "draft_id": "R06",
        "source_rfi": "Dett-A5-RFI10",
        "source_file": A5,
        "source_page": 3,
        "trade": "Tile",
        "difficulty": "control (complete)",
        "rough_draft": (
            "RFI - Toilet Rooms 140, 143, 160. A-502 calls for T-2 6in ceramic cove base, and T-1 wall "
            "tile existing to remain. Is the cove base installed over the existing tile? Any patching of "
            "the existing wall tile? Pls send a detail for cove base to floor tile. Need answer by 9/22 "
            "to order tile - floor tile in these rooms is on hold until then."
        ),
        "source_question": (
            "Per addendum #3 Sheet A-502, Toilet Rooms 140, 143, and 160 call for T-2 6\" ceramic cove base "
            "finish and T-1 wall finishes existing to remain. Is the cove base to be installed over the "
            "existing tile and will there be any patch work associated with the existing wall tile? Please "
            "provide more detail on installation of cove base and abutment to floor tile."
        ),
        "source_response": "Drawing A-502 has been revised and is included in this addendum.",
        "related_revision": "Addendum 5 Change 8: A-502 updated finishes on finish schedule.",
        "correct_location": "Toilet Rooms 140, 143, 160",
        "correct_references": ["A-502"],
        "planted_issues": [],
        "expected_followups": [],
        "invented_details": ["needed-by date 9/22", "impact statement"],
    },
    {
        "draft_id": "R07",
        "source_rfi": "Dett-A5-RFI2",
        "source_file": A5,
        "source_page": 2,
        "trade": "Security / low voltage",
        "difficulty": "medium",
        "rough_draft": "new cameras showed up on the elec dwgs after the last addendum but no type/model. what cameras r we installing??",
        "source_question": (
            "Per the addendum, cameras have been added on the electrical drawings, E-202, E-203 & E-204 but "
            "no clarification of what type of cameras are in these new locations. Please clarify the type of new cameras."
        ),
        "source_response": "Drawings E-010, E-202, E-203, E-204 have been revised and are included in this addendum.",
        "related_revision": "Addendum 5 Changes 12-16: camera type and model clarified on E-010, E-201 to E-204.",
        "correct_location": "Classroom wing, floors 1-3 (new camera locations)",
        "correct_references": ["E-202", "E-203", "E-204", "E-010"],
        "planted_issues": ["missing_sheet", "vague_location", "outdated_reference", "missing_deadline", "missing_impact"],
        "expected_followups": [
            "Which sheets and floors? (E-202, E-203, E-204?)",
            "Which addendum are you working from? Camera models were added in Addendum 5.",
            "When do you need an answer?",
        ],
        "invented_details": [],
    },
    {
        "draft_id": "R08",
        "source_rfi": "Dett-A6-RFI2",
        "source_file": A6,
        "source_page": 2,
        "trade": "Electrical / PV",
        "difficulty": "medium",
        "rough_draft": "PV feed conduit size dont match between the elec dwgs. E-60 vs the PV single line. which one?? need answer asap",
        "source_question": (
            "Drawing E600 says the feed to the PV equipment is to be in a 3-1/2\" conduit. Drawing PV-600 "
            "says the conduit size is 2-1/2\". Please clarify this conduit size."
        ),
        "source_response": "Drawings E600 and PV600 has been updated and are included in this addendum.",
        "related_revision": "Addendum 6 Changes 12 and 14: E-600 and PV-600 updated to show 3\" conduit.",
        "correct_location": "Feed to PV equipment",
        "correct_references": ["E-600", "PV-600"],
        "planted_issues": ["wrong_or_incomplete_sheet", "missing_deadline", "missing_impact"],
        "expected_followups": [
            "'E-60' - do you mean E-600? Is the PV single line PV-600?",
            "What sizes does each drawing show?",
            "'ASAP' - what date, and what is waiting?",
        ],
        "invented_details": [],
    },
    {
        "draft_id": "R09",
        "source_rfi": "Dett-A6-RFI3",
        "source_file": A6,
        "source_page": 2,
        "trade": "Electrical",
        "difficulty": "control (complete)",
        "rough_draft": (
            "RFI - E-702 individual metering schedule. Detail shows CTs but no meters. Need a typical wiring "
            "diagram for one meter monitoring several circuits, plus product spec for the meters and CTs. "
            "Need by 10/2 for the metering submittal - metering gear order is on hold until then."
        ),
        "source_question": (
            "Drawing E-702 shows a schedule of individual metering required. The detail shows current "
            "transformers, but the meters are not shown. Please provide a wiring diagram for a typical "
            "situation where a meter is to monitor several circuits. Also provide a product specification "
            "for the meters and current transformers."
        ),
        "source_response": "Scope has been clarified on Drawing E-702 and is included in this addendum.",
        "related_revision": "Addendum 6 Change 13: E-702 updated metering detail.",
        "correct_location": "Panels listed in the E-702 metering schedule",
        "correct_references": ["E-702"],
        "planted_issues": [],
        "expected_followups": [],
        "invented_details": ["needed-by date 10/2", "impact statement"],
    },
    {
        "draft_id": "R10",
        "source_rfi": "Dett-A6-RFI4",
        "source_file": A6,
        "source_page": 2,
        "trade": "Casework / millwork",
        "difficulty": "control (complete)",
        "rough_draft": (
            "RFI - Care Room 101E, A-210. Cabinet next to the sink - is that casework in our scope? "
            "No detail or elevation. If it's ours pls send detail + elev. Need by 9/29 for shop dwgs."
        ),
        "source_question": "Sheet A-210 in Care Room 101E is this casework next to the sink area. If so, please provide detail and elevation.",
        "source_response": "The item next to the sink is furniture by Owner.",
        "related_revision": None,
        "correct_location": "Care Room 101E",
        "correct_references": ["A-210"],
        "planted_issues": [],
        "expected_followups": [],
        "invented_details": ["needed-by date 9/29", "shop drawing impact"],
    },
]


# Standard sub-to-GC RFI form, filled in roughly (what the reviewer and the AI see).
# Fields follow the parts of a standard RFI that the subcontractor fills in.
# Dates are invented for the exercise.
FORM_FIELDS = ["date", "from", "to", "subject", "location", "references", "question",
               "proposed_solution", "needed_by", "impact", "attachments"]

FORMS = {
    "R01": {"date": "9/12", "from": "Casework sub", "to": "GC", "subject": "countertop??",
            "location": "hallway by office suite + 2 MP rms", "references": "6/A-703",
            "question": "cab detail says solid surface top but other note says plam. which one",
            "proposed_solution": "", "needed_by": "", "impact": "", "attachments": "pic"},
    "R02": {"date": "9/12", "from": "Casework sub", "to": "GC", "subject": "drop sink",
            "location": "hallway", "references": "",
            "question": "drop sink in the millwork - no elev. is it a base cab? what top?",
            "proposed_solution": "", "needed_by": "ASAP", "impact": "need to order", "attachments": ""},
    "R03": {"date": "9/13", "from": "Plumbing sub", "to": "GC", "subject": "staff toilets",
            "location": "service wing staff toilets", "references": "P2, underfloor dwg",
            "question": "P2 says connect new WC + lav but underfloor dwg says existing no work. which is it?? also need a fixture schedule",
            "proposed_solution": "not carrying extra fixtures unless directed", "needed_by": "", "impact": "",
            "attachments": ""},
    "R04": {"date": "9/15", "from": "Solid surface sub", "to": "GC", "subject": "AX42 at panel joints",
            "location": "", "references": "A-30 elevs",
            "question": "AX42 points at the joints between solid surface panels but the note is about an operable partition closure panel?? doesnt make sense. what mfr for the joints. happens all over the elevs",
            "proposed_solution": "", "needed_by": "", "impact": "", "attachments": ""},
    "R05": {"date": "9/14", "from": "Tile sub", "to": "GC", "subject": "T-1 floor?",
            "location": "kinder toilet rms", "references": "finish sched, legend",
            "question": "finish sched says T-1 on the floor but legend says T-1 is existing wall tile to remain. so what goes on the floor? and whats the pattern for T-2",
            "proposed_solution": "", "needed_by": "", "impact": "", "attachments": ""},
    "R06": {"date": "9/14", "from": "Tile sub", "to": "GC", "subject": "cove base over existing tile",
            "location": "Toilet Rms 140, 143, 160", "references": "A-502",
            "question": "A-502 calls T-2 6in ceramic cove base, T-1 wall tile existing to remain. Is cove base installed over existing tile? Any patching of existing wall tile? Pls send detail for cove base to floor tile.",
            "proposed_solution": "", "needed_by": "9/22",
            "impact": "need to order tile, floor tile in these rooms on hold", "attachments": ""},
    "R07": {"date": "9/11", "from": "Security / low voltage sub", "to": "GC", "subject": "camera types",
            "location": "", "references": "elec dwgs, last addendum",
            "question": "new cameras showed up after the last addendum but no type/model. what cameras r we installing??",
            "proposed_solution": "", "needed_by": "", "impact": "", "attachments": ""},
    "R08": {"date": "9/18", "from": "Electrical sub", "to": "GC", "subject": "PV conduit size",
            "location": "", "references": "E-60, PV single line",
            "question": "conduit size dont match between elec dwgs. which one??",
            "proposed_solution": "", "needed_by": "ASAP", "impact": "", "attachments": ""},
    "R09": {"date": "9/19", "from": "Electrical sub", "to": "GC", "subject": "meter wiring + spec",
            "location": "panels on E-702 metering schedule", "references": "E-702",
            "question": "Detail shows CTs but no meters. Need a typical wiring diagram for one meter monitoring several circuits, plus product spec for the meters and CTs.",
            "proposed_solution": "", "needed_by": "10/2",
            "impact": "metering submittal, gear order on hold until then", "attachments": ""},
    "R10": {"date": "9/15", "from": "Casework sub", "to": "GC", "subject": "cabinet by sink - our scope?",
            "location": "Care Room 101E", "references": "A-210",
            "question": "cabinet next to the sink - is that casework in our scope? no detail or elev. if ours pls send detail + elev",
            "proposed_solution": "", "needed_by": "9/29", "impact": "shop dwgs", "attachments": ""},
}


def check(drafts):
    for d in drafts:
        form = FORMS[d["draft_id"]]
        assert list(form) == FORM_FIELDS, f"{d['draft_id']}: form fields out of order"
    ids = [d["draft_id"] for d in drafts]
    assert len(ids) == len(set(ids)) == 10, "need 10 unique drafts"
    for d in drafts:
        for p in d["planted_issues"]:
            assert p in PATTERNS, f"{d['draft_id']}: unknown pattern {p}"
        for ref in d["correct_references"]:
            sheet = ref.split(" ")[0]
            if sheet.startswith(("A-", "E-", "P-", "PV-")) and "/" not in sheet:
                assert sheet in SHEET_INDEX, f"{d['draft_id']}: {sheet} not in sheet index"
        if not d["planted_issues"]:
            assert d["expected_followups"] == [], f"{d['draft_id']}: control should have no follow-ups"


def main():
    check(DRAFTS)
    records = []
    for d in DRAFTS:
        r = {"draft_id": d["draft_id"], "form": FORMS[d["draft_id"]]}
        r.update({k: v for k, v in d.items() if k != "draft_id"})
        r["invented_details"] = r["invented_details"] + ["RFI form dates"]
        r["expected_followup_count"] = len(d["expected_followups"])
        r["is_simulated"] = True
        records.append(r)

    out_dir = ROOT / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "rough_drafts.json", "w", encoding="utf-8") as f:
        json.dump({"patterns": PATTERNS, "drafts": records}, f, indent=2, ensure_ascii=False)

    form_cols = [f"form_{k}" for k in FORM_FIELDS]
    cols = ["draft_id"] + form_cols + ["source_rfi", "source_file", "source_page", "trade", "difficulty",
            "rough_draft", "planted_issues", "expected_followup_count", "expected_followups",
            "correct_location", "correct_references", "source_question", "source_response",
            "related_revision", "invented_details", "is_simulated"]
    with open(out_dir / "rough_drafts.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in records:
            row = {c: r.get(c) for c in cols}
            for k in FORM_FIELDS:
                row[f"form_{k}"] = r["form"][k]
            for c in ("planted_issues", "expected_followups", "correct_references", "invented_details"):
                row[c] = "; ".join(r[c])
            w.writerow(row)

    print(f"Wrote {len(records)} drafts to {out_dir}")


if __name__ == "__main__":
    main()
