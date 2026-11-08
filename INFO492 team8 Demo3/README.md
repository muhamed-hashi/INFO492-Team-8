# Team 8 Demo #3: RFI exchange between subcontractor, GC and design team

**Thesis:** Adding an AI review step to an existing subcontractor RFI form can reduce median GC first-review
time by at least 25% compared with the same form completed without AI assistance, without increasing
information errors.

**Demo #3 step in our plan: improve the draft.** The agent suggests a clearer question with sources, and the
subcontractor approves the final version. Demo #3 adds the other two parties: the GC checks and routes the
RFI, and the design team answers it. Each party has its own agent, and every agent only suggests or flags.

| Party | Human roles | Agent |
|---|---|---|
| Subcontractor | Foreman | `draft_agent`: rough site message → clearer RFI, asks for what is missing |
| GC | Site Manager / Assistant PM, Project Manager | `check_agent`: missing info, sheet numbers, revisions, route, cost/scope; `watch_agent`: new addenda and deadlines |
| Design team | Architect | `triage_agent`: orders the queue (code only, never answers) |

Roles, permissions, message format, escalation and the audit trail: [docs/PROTOCOL.md](docs/PROTOCOL.md).
Data sources and why the RFIs are simulated: [docs/DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md).

## Run it

Python 3.10 or newer, no packages to install. The AI uses Google Gemini.

```bash
python3 setup_ai.py        # once; paste your Gemini key (skip if you already did this for Demo #2)
python3 app.py             # open http://127.0.0.1:8766
```

### Deploy on Render (one public URL)

1. Push this repo to GitHub.
2. In [Render](https://render.com) → **New** → **Blueprint** → connect the repo → use the root [`render.yaml`](../render.yaml).
3. Set **GEMINI_API_KEY** on the web service (Environment).
4. Open the `.onrender.com` URL — everyone uses the same link; sign in by role (PINs shown in the app after you pick a user).

Persistent state lives on the attached disk at `DEMO3_RUNTIME=/var/data/runtime`. Health check: `GET /health`.
Optional: `WATCH_EVERY_SECONDS` (default 86400) runs the code-only watch agent in the web process.
Guardrails: `MAX_AI_CALLS_PER_DAY`, `AI_RATE_LIMIT_PER_IP` (see [`.env.example`](.env.example)).

Local production-style run:

```bash
export GEMINI_API_KEY=... DEMO3_RUNTIME=./runtime HOST=0.0.0.0 PORT=8766
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

### A two-minute walkthrough

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
python3 scripts/run_demo3_eval.py          # about 70 Gemini calls; --runs 1 halves it
python3 -m unittest discover tests         # no network needed
```

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
[results/demo3_v1_before_cost_fix/](results/demo3_v1_before_cost_fix/).

**Timed review study:** open `http://127.0.0.1:8766/study` on the computer running the app. Each reviewer gets
a number; odd and even numbers see opposite halves of the RFIs as rough messages vs agent-drafted. Times and
decisions are saved to `runtime/study.csv` and shown in the control panel (download from there).

## Files

| Path | What |
|---|---|
| `app.py` | Local web server, sign-in, RFI life cycle, control panel, study, export |
| `protocol.py` | Roles, permissions, agent limits, message envelope, hash-chained audit log |
| `agents.py` | The four agents; sheet lookup, revision check, date parsing, the anti-invention guard |
| `core.py` | Gemini call and the Demo #2 reference review, reused unchanged |
| `prompts/` | `draft_agent.txt`, `check_agent.txt`, `reference_review.txt` (from Demo #2) |
| `data/` | Real Dett data (`source_rfis.csv`, `drawing_index.json`, `revisions.json`), simulated `rough_rfis.json`, labels in `rough_answer_key.json`, demo `users.json` |
| `scripts/` | `generate_rough_rfis.py`, `build_revisions.py`, `run_demo3_eval.py` |
| `static/` | Front end and the study page |
| `results/demo3/` | Evaluation output |
| `tests/` | Unit and end-to-end tests with a fake AI |

Dependencies: Python 3.10+ standard library; Google Gemini API (`gemini-3.5-flash-lite` by default).
Your key stays in your home folder (`~/.team8_rfi_gemini.json`), never in this folder. `runtime/` holds local
state and is not uploaded.

## AI assistance

Built with AI coding assistance. The thesis, the design decisions, the case review and the reported results are the team's.
