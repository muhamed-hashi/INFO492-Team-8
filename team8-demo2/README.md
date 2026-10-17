# Team 8 — RFI Check Before Submission

INFO 492 C · **Coordination Demo #2: check references.** Demo #1 files are kept in `data/demo1/`, `results/demo1/` and `docs/demo1/`.

**Thesis:** If a subcontractor runs an AI check on an RFI before sending it to the GC, the GC's first review gets at least 25% faster (median time), without more information errors. The 25% is our target; it has not been measured yet.

Our thesis plans four demos: (1) find missing details, (2) **check references**, (3) improve the draft, (4) send to the GC and time the review. Demo #2 asks: **can the agent find wrong or missing drawing numbers by checking our drawing list?**

## What changed since Demo #1

- **Focus:** drawing references instead of missing fields.
- **Full drawing index:** 206 sheets from the six Dett addenda instead of 13, so sheet numbers can actually be checked.
- **First run showed the AI is bad at lookups.** On 24 harder general cases, the AI caught more than a checklist (11/13 vs 8/13), but most of its false alarms said a sheet was missing from the index when it was there ([results](results/demo2_general/summary.md)).
- **New design, code + AI:** code looks every sheet number up in the index; the AI gets that result and each sheet's title, and judges only what code can't: does this real sheet fit the question, and does a number look mistyped?
- **24 reference test cases:** 12 correct, 12 with one problem (nonexistent sheet, typo, real but unrelated sheet, or no sheet number), compared across code only, AI only and code + AI.
- **Real RFIs and adversarial cases (Evaluation Lab):** the agent is also tested on 10 real Dett RFIs labelled by two people, and on 2 cases that try to talk the AI out of flagging a problem.
- **App:** the AI check now uses the code + AI design, the reference cases R01–R24 are in the case list, and each cited sheet shows its title and the AI's note.

## How to run

Python 3.10+, no extra packages.

```bash
python3 setup_ai.py                    # once: paste a Gemini API key (saved in your home folder, not in this project)
python3 scripts/run_reference_eval.py  # Demo #2 main test, about 15 minutes → results/demo2_references/
python3 app.py                         # the web app → http://127.0.0.1:8765
```

In the app: pick a case (R01–R24 are the reference cases) → *With AI* → Start preparation → Run AI check. The AI only suggests; the subcontractor makes every change, and the AI cannot approve designs or authorize work.

## Results

- [results/demo2_references/summary.md](results/demo2_references/summary.md): main test, check references ([notes from reading the AI messages](results/demo2_references/NOTES.md))
- [results/demo2_general/summary.md](results/demo2_general/summary.md): first run, all fields, which led to the new design ([after-the-fact re-scoring](results/demo2_general/posthoc_code_references.md))
- What we measure and how we read it: [docs/EVALUATION.md](docs/EVALUATION.md)

## Evaluation Lab (Week 3): real RFIs, in `/eval`

The same Demo #2 agent, tested the way the Week 3 worksheet asks. Everything is in [`eval/`](eval/):

1. **What we test** ([STEP1_what_we_test.md](eval/STEP1_what_we_test.md)): one sentence, one thing we count (matches with the answer key on 10 real RFIs), and our number, set before running. The script refuses to run while it is blank and records when it was saved.
2. **Answer key**: 10 **real** Dett RFIs, drawn by a fixed rule (`scripts/select_real_items.py`). Two people label them separately (`labeler_A.csv`, `labeler_B.csv`, [instructions](eval/INSTRUCTIONS.md)); `scripts/build_answer_key.py` lines them up, and the team agrees on the disagreements in `answer_key.csv`.
3. **Run it**: `python3 scripts/run_real_eval.py`. Agent twice, the simple way without AI (a checklist: sheet number present and on the drawing list), and the Demo #1 design for reference; plus 2 adversarial cases that hide an instruction to the AI. Scores are per run, never averaged.
4. **What went wrong**: failure groups and crossed-a-line candidates for the subcontractor side (contacting the design team directly, treating an answer as permission to proceed, making up a drawing or spec number), counted separately from the score → [RESULTS.md](eval/RESULTS.md).
5. **Write-up**: one page, [WRITEUP_DRAFT.md](eval/WRITEUP_DRAFT.md) is generated with the numbers; the team writes the two sentences and who did what.

## Data

Simulated RFIs based on 108 real bid-stage RFIs from the Dett Elementary School Annex project (Public Building Commission of Chicago). We rewrote them as construction-stage subcontractor → GC RFIs; dates and impacts are made up. Why and how: [docs/DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md).

## Files

| Path | What it is |
|---|---|
| `app.py`, `core.py` | Web server, drawing lookup, Gemini calls, rule checklist, timers |
| `static/` | Web pages (subcontractor form, GC review) |
| `prompts/reference_review.txt` | Demo #2: AI review of cited sheets (gets the code lookup and sheet titles) |
| `prompts/review_v2.txt` | Demo #2: AI check of the other fields (no longer judges references) |
| `prompts/review.txt` | Demo #1 prompt, used for the "AI only" comparison |
| `data/reference_cases.json`, `reference_answer_key.json` | 24 reference cases and their labels |
| `data/cases.json`, `answer_key.json` | 24 general cases (first run) |
| `data/drawing_index.json`, `source_rfis.csv` | 206 sheets and 108 real RFIs from the addenda |
| `scripts/generate_reference_cases.py`, `generate_data.py` | Build the cases (deterministic, no LLM) |
| `scripts/extract_addenda.py` | Pulls RFIs and sheets from the addenda PDFs (`pip install pypdf`) |
| `scripts/run_reference_eval.py` | Demo #2 main test |
| `scripts/select_real_items.py`, `build_answer_key.py`, `run_real_eval.py` | Evaluation Lab: real-item sample, answer key, run and scoring |
| `data/real_items.json`, `adversarial_cases.json` | 10 real RFIs and 2 adversarial cases |
| `eval/` | Evaluation Lab: step 1 sheet, labelers' files, answer key, results, one-page write-up |
| `scripts/run_eval.py`, `posthoc_code_references.py` | First run and its re-scoring |
| `tests/` | Software tests: `python3 -m unittest discover -s tests` |

## AI assistance

This prototype was built with AI coding assistance. The thesis, dataset choice, case review and reported results are the team's.
