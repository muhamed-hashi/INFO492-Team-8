# Evaluation plan (Demo #2: check references)

Demo #2 is the second of the four demos in our thesis document: *"Check references: test if the agent finds wrong or missing drawing numbers by checking our drawing list."* Demo #1's plan is in [docs/demo1/EVALUATION.md](demo1/EVALUATION.md).

## How we got here

1. **First run (October 16): all fields, 24 general cases** (`scripts/run_eval.py` → `results/demo2_general/`). Same AI and prompt as Demo #1, harder cases. The AI found 11/13 planted defects against the checklist's 8/13, but 5 of its 6 false alarms said a sheet was "not in the drawing index" when it was. The AI had the list of sheet numbers and still got the lookup wrong.
2. **Design change:** let code do what code is exact at (does this sheet exist?) and give the AI the part code cannot do (does this real sheet fit the question? does a number look mistyped?). The AI gets the lookup result and each sheet's title, and is told to trust the lookup.
3. **Main test (this plan, written before running the AI on the reference cases):** 24 reference cases, three ways of checking.

## Question

Can the agent find wrong or missing drawing references, and which split between code and AI does it best without flagging correct references?

## Setup

| Method | What it does |
|---|---|
| Code lookup only | Every sheet number is looked up in the 206-sheet index; flag if one is not there or none is cited |
| AI only (Demo #1 design) | Gemini sees the RFI and the list of sheet numbers and judges everything (`prompts/review.txt`); only its references findings are scored |
| Code + AI (Demo #2 design) | Code lookup, plus Gemini judging each found sheet's fit from its title and spotting mistyped numbers (`prompts/reference_review.txt`) |

Model `gemini-3.5-flash-lite`, as in Demo #1. Each AI method runs 3 times per case. Run: `python3 scripts/run_reference_eval.py` → `results/demo2_references/`.

## Measures

- Reference problems caught, out of 12, and by kind: nonexistent (3), typo (3), unrelated (4), vague (2)
- Correct references wrongly flagged, out of 12
- Cases judged correctly, out of 24; failed calls; consistency over 3 runs
- For AI only: messages claiming an indexed sheet is missing from the index (an information error)

The AI's "this sheet may not fit" notes are listed in the results for the team to judge.

## What we expect, and how we will read it

- Code alone should catch nonexistent and vague references and nothing else (5/12), with no false alarms. This is known before running, because the lookup is deterministic.
- **Supports the thesis's reference step:** code + AI catches clearly more than code alone (typos, unrelated sheets) while flagging few correct references, and makes no false claims about the index.
- **Weakens it:** the AI adds little over code, or catches more only by flagging many correct references. Then the AI's role in references should shrink to what code cannot do, or be dropped.
- This is not evidence about GC review time. That is Demo #4 in our thesis plan.

## Evaluation Lab (Week 3): real RFIs

The simulated cases tell us the agent catches the problems we planted. They cannot tell us how it behaves on real RFI text, where most references are fine and some RFIs cite no sheet at all. Following the Week 3 worksheet, all of this lives in `eval/`:

- **Step 1:** one sentence, one count (matches with the answer key on the 10 real RFIs), one number, written in `eval/STEP1_what_we_test.md` before the run.
- **Step 2:** 10 real Dett RFIs drawn by a fixed rule (7 that cite sheets, 3 that do not, none of the 12 seeds), labelled `ok` / `problem` / `unclear` by two people separately; agreement and Cohen's kappa reported; disagreements talked through and settled in `eval/answer_key.csv`, which is kept for Demos #3 and #4.
- **Step 3:** the agent twice; the simple way without AI, which for "checks something for problems" is a person reading down a checklist, here the checklist "sheet number present and on the drawing list" applied by code; and the Demo #1 design for reference. Two adversarial cases hide an instruction to the AI on top of a real reference problem.
- **Step 4:** failure groups, and crossed-a-line candidates for the subcontractor side (never contact the design team directly, never treat an answer as permission to proceed, never make up a drawing or spec number; plus never answer as the designer or approve work), counted separately from the score and confirmed by a person.
- **Step 5:** one page, `eval/WRITEUP_DRAFT.md` → final write-up by the team.

Run: `python3 scripts/build_answer_key.py`, then `python3 scripts/run_real_eval.py`.

## Optional: first GC timing pilot

The app records GC first-review time (`python3 app.py` → save an RFI → *Open the GC review screen*). Two people outside the team can review RFIs prepared with and without the AI check, without being told which, to try the procedure. Too few reviews to test the 25% target.
