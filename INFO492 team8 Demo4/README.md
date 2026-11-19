# Team 8 Demo #4 (Protect): RFI close-out

**Thesis** (updated after Demo #3; additions in bold): Adding an AI review step to an existing subcontractor RFI
form can reduce median GC first-review time by at least 25% **and reduce follow-up rounds to the subcontractor**,
compared with the same form completed without AI assistance, without increasing information errors **from
submission through close-out**.

**Where we want the agent to end up:** one agent per party following each RFI from the first rough message on
site to close-out. The sub's agent turns a text into a clear RFI (Demo #3), the GC's agents check references and
revisions (Demos #2–#3), and before anyone closes the RFI, an agent checks that every drawing change the answer
promised was actually issued (Demo #4). Agents suggest and cite their evidence; at every step a person decides.

**What Demo #4 adds:** Demo #3 tested the first half of the thesis with GC reviewers (median first review
6.5 → 4.5 min). Demo #4 protects the second half, "without increasing information errors", at the end of an
RFI's life. An architect's answer often says "refer to revised Drawing E-304 included in this addendum". That
is a commitment. Before the GC closes the RFI, the **close-out agent** checks that every drawing change the
answer promised was actually issued, and recommends:

| Recommendation | When |
|---|---|
| OK to close | every sheet the answer says was revised is in the drawing list attached to that addendum (with item no. and PDF page as evidence), or the answer changed nothing on the drawings |
| Keep open: carry to IFC set | the answer says the change will be issued later. Every Dett addendum says changes from RFI answers "will be issued with the Issue for Construction Documents" |
| Hold | a sheet the answer says was revised is not in that addendum's drawing list |
| Check | a person should look: the sheet number looks like a typo of a listed sheet, or the answer is unclear |

Split of work: **code** finds sheet numbers, looks them up in the real drawing lists and finds near matches;
the **AI** only reads what the answer committed to (revised vs only referred to, anything still to come), with a
quote for every claim; a **guard** drops claims whose sheet or quote is not in the answer; the **project manager**
decides (close, keep open, or ask the architect). Closing against the advice needs a written reason and is
recorded as an override. Everything from Demo #3 still works unchanged.

| Party | Human roles | Agents |
|---|---|---|
| Subcontractor | Foreman | `draft_agent` (Demo #3) |
| GC | Site Manager / Assistant PM, Project Manager | `check_agent`, `watch_agent` (Demo #3); **`closeout_agent`** (Demo #4) |
| Design team | Architect | `triage_agent` (Demo #3); answers **close-out questions** from the PM (Demo #4) |

Roles, permissions, messages, close-out flow and the audit trail: [docs/PROTOCOL.md](docs/PROTOCOL.md).
Data (real drawing lists, synthetic test cases): [docs/DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md#demo-4-additions).
What we measure and the limits: [docs/EVALUATION.md](docs/EVALUATION.md).

## Results

Run 2026-11-17, gemini-3.5-flash-lite, 2 AI runs. Full reading: [results/demo4/NOTES.md](results/demo4/NOTES.md).

Our course asks for real industry data, not synthetic data, so the headline evaluation uses only real documents:
the **108 answered RFIs** of the Dett project, checked against the drawing lists actually attached to each addendum.

| On the 108 real RFIs | Code only | Agent run 1 | Agent run 2 |
|---|---|---|---|
| Stopped (not "ok to close") | 13 | 5 | 5 |
| of which hold / check / keep open | 4 / 9 / 0 | 2 / 3 / 0 | 2 / 2 / 1 |
| Failed AI calls | – | 2 | 0 |

The two agent runs agree on 104 of 106 RFIs. Most of the code's stops are specification changes or sheets that are
only referred to. Both methods hold A3-RFI53 and A3-RFI54: the answers say "All sheets have been revised and
included in this addendum", but M-301, M-600 and M-801 are not among the 159 drawings attached to Addendum 3.
One real answer ("as revisedA-502", no space) broke our parser; the guard turned it into a "check" instead of a
silent close.

**Stakeholder test (Nov 18, recorded):** our stakeholder judged the live GC check on 7 rough sub RFIs
(F01–F07). "The AI never once made anything up", and a well-written RFI went straight through; but it sent back 6
of 7, mostly because it checks whether a field is filled instead of reading the text ("location missing"), and it
missed what matters most (a suggested fix, urgency, an undersized fire-pump feeder). Per-RFI calls and transcript:
[`stakeholder_test/`](stakeholder_test/README.md). Not yet done: his call on the 15 Dett RFIs that were stopped at
close-out and on 12 GWA items (`data/kevin_review_demo4.xlsx`); until then close-out false alarms are not
judged by someone from industry, and misses both methods let through are not measured.

Errors are reported at two points: what the agent recommends before anyone looks (right, missed problems, false
alarms), and what would reach the field if the PM followed every recommendation (missed problems only).

Code-only baseline on the real log so far: it stops 13 of 108 RFIs (4 hold, 9 check). The first AI run (Nov 15,
before four fixes) is in [`results/demo4_run1_clean_set/NOTES.md`](results/demo4_run1_clean_set/NOTES.md); among
real RFIs it found two answers (A3-RFI53, A3-RFI54) that say "All sheets have been revised and included in this
addendum" while M-301, M-600 and M-801 are not among the 159 drawings attached to Addendum 3.

**Second real set** (sent by our stakeholder): a public RFI log, Guam Waterworks Authority "Response to RFI No. 1"
(44 bidder questions and answers, July 2026), messy as found (no dates, several questions per item, pasted pictures,
"refer to past plans" answers). The new **answer check** asks whether each answer actually answered every question,
or whether the RFI will come back. Its problem list was made by a teammate **with an AI tool**, so we use it only as a
reference, not an answer key: our agent stops 30–33 of 44 items, far more than that list, and closes 2 items it calls
answer problems. Our stakeholder judges 12 of the disagreements blind in his Demo #4 session; those calls are the
answer key. Reading and limits: [results/gwa/NOTES.md](results/gwa/NOTES.md).

Two synthetic sets (real answers with planted problems, tidy and messy wording) remain as **stress tests only**,
run with `--synthetic` and reported separately. On the messy set the code-only baseline stops 7 of 25 planted
problems, which is why we do not rely on keyword rules.

## Changes after Demo #3 feedback

| Feedback | What we changed |
|---|---|
| Professor: data too clean, "0 errors" not believable; course: real industry data only | Headline evaluation on the 108 real Dett RFIs; errors reported at two points (agent's recommendation, and what would reach the field); synthetic sets kept only as stress tests |
| Peer review (10 of 17): stakeholder testing looked like a retold interview | Our stakeholder uses the live Demo #4 system for ~20 minutes and judges every real RFI the tool stopped; we report what he did and decided |
| Peer review: agents may disagree on whether an RFI has enough information, causing back-and-forth | When every required field is filled in but the AI alone wants to return the RFI, the GC sees "The agents disagree" and decides; nothing is returned automatically |
| Peer review: verify against hallucination when each party runs its own agent | Every AI claim must quote the source text; a guard drops claims whose sheet or quote is not there, and any drop turns "ok to close" into "check" |
| Peer review: ~300 AI calls a day is a scaling limit | Kept as a demo guardrail (`MAX_AI_CALLS_PER_DAY`); a real deployment needs a paid quota. Code does all lookups, so most checks cost no AI call |

## Why close-out (and how it connects to Demos #1–#3)

| Demo | Step | What we learned |
|---|---|---|
| #1 | find missing details | AI and a checklist both found 6/6 planted gaps; AI added 2 extra flags |
| #2 | check drawing references | AI alone invents lookup errors; code lookup + AI judgement caught 12/12 with 0 false flags |
| #3 | improve the draft; sub ↔ GC ↔ design exchange | with GC reviewers: median first review 6.5 → 4.5 min, follow-ups 27 → 2. The AI made 2 mistakes in 10 drafts (a wrong sheet number, a false alarm); the sub caught both before sending |
| #4 | close out | does an answered RFI's promised drawing change actually exist before the RFI is closed? |

Our interviewee said the real cost is back-and-forth and rework, and that he would only trust a tool that
"checks and reminds, uses the latest drawings, explains why, and lets a person decide". Demo #4 follows that: it
cites the addendum page for every sheet it confirms and never closes anything itself.

## Run it

Python 3.10 or newer, no packages to install. The AI uses Google Gemini.

```bash
python3 setup_ai.py        # once; paste your Gemini key (skip if you already did this for Demo #2 or #3)
python3 app.py             # open http://127.0.0.1:8767
```

### Deploy on Render (one public URL)

1. Push this repo to GitHub.
2. In [Render](https://render.com) → **New** → **Blueprint** → connect the repo → use the root [`render.yaml`](../render.yaml).
3. Set **GEMINI_API_KEY** on the web service (Environment).
4. Open the `.onrender.com` URL — everyone uses the same link; sign in by role (PINs shown in the app after you pick a user).

Persistent state lives on the attached disk at `DEMO4_RUNTIME=/var/data/runtime` (`DEMO3_RUNTIME` also works).
To deploy Demo #4 next to Demo #3, add a second service to `render.yaml` with `rootDir: INFO492 team8 Demo4`
(same start command and environment). Health check: `GET /health`.
Optional: `WATCH_EVERY_SECONDS` (default 86400) runs the code-only watch agent in the web process.
Guardrails: `MAX_AI_CALLS_PER_DAY`, `AI_RATE_LIMIT_PER_IP` (see [`.env.example`](.env.example)).

Local production-style run:

```bash
export GEMINI_API_KEY=... DEMO4_RUNTIME=./runtime HOST=0.0.0.0 PORT=8767
python3 app.py
```

Demo users (fictional people and companies; PINs are for this local demo only):

| User | Role | PIN |
|---|---|---|
| Foreman A (demo) | Foreman, electrical subcontractor | 1111 |
| Foreman B (demo) | Foreman, finishes subcontractor | 1112 |
| Site Manager (demo) | Site Manager / Assistant PM, GC | 2222 |
| Project Manager (demo) | Project Manager, GC | 3333 |
| Architect (demo) | Architect, design team | 4444 |

To be signed in as two people at once, use a different browser or a private window for the second person (or sign out and back in).

### Close-out walkthrough (Demo #4, about two minutes)

0. The **landing page** explains the four steps (draft, check, answer, close out) → **Sign in by role**.
1. **Project Manager** (PIN 3333) → **Close-out**. The list is the project's real answered RFIs (108);
   "Needs a look" shows the ones the code check flagged.
2. Open **A3-RFI57**: the code check says *Check* because the answer names A-432 and says a detail "has been
   revised". **Run close-out agent**: it reads that A-432 is only referred to and A-434 was revised, confirms
   A-434 is item 79 on page 16 of Addendum 3 (link opens the PDF page), and recommends *OK to close*.
   **Close RFI**.
3. Open **A3-RFI53**: the answer says "All sheets have been revised and included in this addendum", but M-301,
   M-600 and M-801 are not in the Addendum 3 drawing list. Run the agent → *Hold*. **Ask architect** with a note.
4. **Architect** (PIN 4444) → **Close-out questions** → reply.
5. **Project Manager** → the reply is shown → close with a note. Metrics shows closed, kept open, asked, and
   overrides; every step is in the RFI's audit trail.

### Demo #3 walkthrough (still works)

1. **Foreman A** → New RFI → pick test scenario **F03** → Create → **Ask the draft agent**. The agent rewrites
   the question, marks what came from the message, and asks for what is missing. Fill those in from
   "Your site notes", then **Approve and send to GC**.
2. **Site Manager** → open the RFI → **Run check agent** → Return, Answer, or Forward.
3. **Project Manager** → Control panel → **Issue next addendum**: the watch agent flags open RFIs that cite a sheet
   revised in that addendum. Revision alerts → mark each alert useful or wrong.
4. **Architect** → Triage queue → open the RFI → respond.
5. Every RFI page has its audit trail. The project manager's control panel shows the live numbers and can export the RFI log.

`python3 app.py --watch-every 60` issues the next addendum automatically every 60 seconds (the always-on loop).
The project clock starts at Addendum 1 (`DEMO_START_ADDENDUM`). The simulated project date is 2023-09-15 (`DEMO_TODAY`): the Dett drawings and addenda are from May–June 2023, so the construction-stage scenario is set a few months later, and every response date in the test RFIs is relative to it.

## Evaluate

```bash
python3 scripts/run_demo4_eval.py          # Demo #4: real log, 2 AI runs (~220 Gemini calls); --code-only needs none; --synthetic adds stress tests
python3 scripts/make_review_sheet.py       # Demo #4: stakeholder session workbook (test steps, Dett and GWA tabs; needs openpyxl)
python3 scripts/import_review.py FILLED.xlsx  # his calls -> data/dett_labels/labels.csv and data/gwa/kevin_calls.csv
python3 scripts/run_demo4_eval.py --rescore   # Demo #4: score the saved run against the review, no AI calls (same for run_gwa_eval.py)
python3 scripts/run_demo3_eval.py          # Demo #3 drafting (unchanged)
python3 scripts/run_gwa_eval.py            # Demo #4: second real log (GWA), answer check, 2 AI runs (~88 calls); --code-only needs none
python3 -m unittest discover tests         # 42 tests, no network needed
```

### Demo #3 evaluation (unchanged)

The evaluation compares three ways of preparing the 12 rough RFIs (as sent, checklist only, draft agent),
then runs the GC's check agent on the completed RFIs and replays the six addenda through the watch agent.
Results go to `results/demo3/` and appear in the control panel. Method: [docs/EVALUATION.md](docs/EVALUATION.md).

**Main measure (after our stakeholder interview and class feedback):** how many rough RFIs the GC can act on without a clarification round. As sent: 17%. Checklist only: 67%. Draft agent: 71% (two runs). Review time is still measured on the /study page.

**Results so far** (2 runs, gemini-3.5-flash-lite; full reading in [results/demo3/NOTES.md](results/demo3/NOTES.md)):

| | As sent | Checklist only | Draft agent (code + AI) |
|---|---|---|---|
| Missing items asked about (23 per run) | 0% | 83% | 89% |
| Reference problems caught (6 per run) | 0/6 | 4/6 | 10/12 |
| Still needs a return to the sub | 10/12 | 4/12 | 7/24 |
| Invented facts that reached an RFI | - | 0 | 0 (2 removed by the guard) |

The GC check agent wrongly sent back 6 of 24 complete RFIs for a "vague" location (and accepted "2nd floor bathroom").
Its cost/scope flags fell from 10/12 to 0/24 after one prompt change made after the first run; that run is kept in
[the Demo #3 folder](../INFO492%20team8%20Demo3/results/demo3_v1_before_cost_fix/).

**Timed review study:** open `http://127.0.0.1:8767/study` on the computer running the app. Each reviewer gets
a number; odd and even numbers see opposite halves of the RFIs as rough messages vs agent-drafted. Times and
decisions are saved to `runtime/study.csv` and shown in the control panel (download from there).

## Files

| Path | What |
|---|---|
| `closeout.py` | **Demo #4** close-out: drawing-list lookup, near matches, code-only baseline, the close-out agent and its guard; the **answer check** (did the answer answer every question?) |
| `app.py` | Local web server, sign-in, RFI life cycle, close-out, control panel, study, export |
| `protocol.py` | Roles, permissions, agent limits, message envelope, hash-chained audit log |
| `agents.py` | The four Demo #3 agents; sheet lookup, revision check, date parsing, the anti-invention guard |
| `core.py` | Gemini call and the Demo #2 reference review, reused unchanged |
| `prompts/` | `closeout_agent.txt`, `answer_check.txt` (Demo #4), `draft_agent.txt`, `check_agent.txt`, `reference_review.txt` (from Demo #2) |
| `data/` | Real Dett data (`source_rfis.csv`, `drawing_index.json`, `revisions.json`, **`addendum_drawing_lists.json`**), synthetic **`closeout_cases.json`** (tidy) and **`closeout_cases_messy.json`**, **`kevin/`** (stakeholder examples: templates, privacy rules), **`dett_labels/`** (stakeholder review of stopped RFIs), **`gwa/`** (second real log; an AI-made problem list used only as a reference), **`kevin_review_demo4.xlsx`** (stakeholder session: test steps, Dett and GWA review tabs), simulated `rough_rfis.json`, labels in `rough_answer_key.json`, demo `users.json` |
| `scripts/` | **`parse_gwa.py`, `run_gwa_eval.py`, `extract_drawing_lists.py`, `make_review_sheet.py`, `import_kevin.py`, `import_review.py`, `run_demo4_eval.py`, `make_closeout_cases.py`, `make_messy_cases.py`**, `generate_rough_rfis.py`, `build_revisions.py`, `run_demo3_eval.py`, `watch_worker.py` |
| `static/` | Front end and the study page |
| `results/demo4/` | Demo #4 evaluation output (code-only until the labels and AI run are in) |
| `results/gwa/` | Answer check on the GWA log (reference: AI-made list; answer key: stakeholder's blind calls, pending) |
| `results/demo4_run1_clean_set/` | First Demo #4 run (tidy set only, before the fixes), kept for comparison |
| `results/demo3/` | Demo #3 evaluation output (copied from the Demo #3 folder) |
| `tests/` | Unit and end-to-end tests with a fake AI |

Dependencies: Python 3.10+ standard library; Google Gemini API (`gemini-3.5-flash-lite` by default);
`pdftotext` (poppler) only to re-extract the drawing lists from the addendum PDFs; `pdfplumber`, `pytesseract`
(tesseract) only to re-parse the GWA PDF.
Your key stays in your home folder (`~/.team8_rfi_gemini.json`), never in this folder. `runtime/` holds local
state and is not uploaded.

## AI assistance

Built with AI assistance. The thesis, the design decisions, the case review and the reported results are the team's.
