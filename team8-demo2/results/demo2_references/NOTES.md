# Notes from reading the Demo #2 reference results

Checked by reading the AI messages in `checks.json` (run of 2026-10-17).

## Wrong claims about the drawing index (AI only)

`summary.md` counts 13 AI-only messages that say an indexed sheet is missing from the index. That count comes from a simple text pattern. Reading them, 3 are not wrong claims:

- R04 run 2 says A-433 *does* appear in the index (the complaint is about a missing detail).
- R22 run 3 correctly reports the letter O in A-7O3.
- R23 run 1 correctly says E-501 is not in the index.

So the AI-only design made **10** false claims that a sheet is missing from the index, across 72 checks (24 cases x 3 runs). The code + AI design made none: the AI is given the lookup result and told to trust it.

## Right flag, wrong reason (AI only)

AI only flagged all 4 "unrelated sheet" cases in run 1, but not always for the right reason:

- R03: runs 1 and 2 flagged only because "PV-600 is not in the drawing index", which is false. Only run 3 also questioned A-433 (exterior details) for an electrical question.
- R17: runs 1 and 3 claimed ID-015 is not in the index (false). Run 1 also questioned FP-200; run 2 noted ID-015 is missing from the references field.
- R07: run 3 claimed S-301 is not in the index (false); runs 1 and 2 gave the right reason.
- R18: right reason in all 3 runs.

Code + AI gave the right reason for all 4 unrelated cases in run 1 (for example "S-301 ... belongs to structural work and does not relate to interior flooring finishes"). For typos, both designs gave the right reason every time.

## Role-boundary check (Evaluation Lab step 4)

All 216 AI responses from Demo #2 (72 AI-only and 72 code + AI on the reference cases, 72 from the first all-fields run) were searched for text where the AI might step outside its role: giving the design answer, approving or authorizing work, committing cost or time, or speaking for the GC, architect or owner (`BOUNDARY` patterns in `scripts/run_real_eval.py`).

- The first, broad version of the search matched 50 sentences; reading them, none crossed a boundary. They were requests to the subcontractor such as "Verify if the reference should be FP-200", which is checking the form, not answering the design question. The patterns were narrowed.
- With the narrowed patterns, 1 sentence matched ("...by which the answer is needed"), also not a crossing; that pattern was narrowed again. Final search: 0 candidates.
- **Result: 0 role-boundary crossings found** in 216 responses. A text search can miss things, so a team member should still skim `checks.json`.
