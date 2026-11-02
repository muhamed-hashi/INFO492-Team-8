# Notes from reading the Demo 3 results (run of 2026-11-01 02:38 UTC, 2 runs, gemini-3.5-flash-lite)

Checked by reading `checks.json`. Earlier run (before the cost/scope prompt change): `../demo3_v1_before_cost_fix/`.

## Drafting: agent vs checklist (12 rough RFIs, 23 missing items, 6 with reference problems)

| | As sent | Checklist only | Draft agent (2 runs) |
|---|---|---|---|
| Missing items asked about | 0/23 | 19/23 (83%) | 41/46 (89%) |
| Asked for something already in the message | 0 | 0 | 2 (F06 location, both runs) |
| Reference problems caught | 0/6 | 4/6 | 10/12 (83%) |
| Reference questions when nothing was wrong | 0 | 0 | 2 (F11, both runs) |
| Values the AI filled in that the message does not say | - | - | 2, both removed by the guard; 0 reached an RFI |
| Still needs a return after drafting | 10/12 | 4/12 (33%) | 7/24 (29%) |

The agent and the checklist are close. The agent's misses: F03 "2nd floor bathroom" accepted as a location (both runs),
F08 impact (both runs), F10 location (1 run), F06 the plan sheet with the keynotes not cited (both runs).

## GC check agent on the completed RFIs (24 checks)

- **Cost/scope flags: 0/24** (10/12 before the prompt change). None of the 12 cases asks for work outside the drawings,
  so 0 is plausible, but the new rule has not been tested on an RFI that really is a scope request.
- **8 "return" recommendations on RFIs scored complete:**
  - 6 are the AI judging a location too vague: "IDF to MDF" (F02), "Annex caissons" (F04), "Classroom wing" (F11), both runs each.
    Together with F03 above ("2nd floor bathroom" accepted), the AI's judgement of whether a location is specific is
    inconsistent. It cannot know how many rooms of a kind the building has without the project's room list.
  - 2 (F05, both runs) are correct catches by code: the agent's rewritten question still cites A-102 after the foreman
    corrected the references field. The draft agent should re-draft the question after the foreman answers.

## Watch agent replay (code only)

4 alerts, all correct by construction from `data/revisions.json`: F01 (E-301, Addenda 2 and 3) and F07 (E-600, Addenda 2 and 3).
The mistyped FP-2O0 cannot be watched until it is corrected.

## What this means

- Code did the reliable parts: sheet lookup, revisions, dates, the anti-invention guard (0 invented values reached an RFI).
- The AI added little over a checklist at finding gaps (89% vs 83%; 29% vs 33% still needing a return).
- AI judgements that need project knowledge (is this location specific? is this a scope change?) were the main source
  of errors. Next: give the agents the project's room list, and re-draft the question after the foreman's answers.
- These are simulated RFIs written by the team; review time is not measured here (see the /study page).
