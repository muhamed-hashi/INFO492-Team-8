# What changed since Demo 2

**Baseline commit:** `934c5f3` — *demo 2 website update and add readme* (2026-10-23 area)  
**Compared to:** `HEAD` (`1c31a78`, *Update README.md*) as of Step 0 sync (2026-11-07)

## How we picked the baseline

- There is **no** git tag `demo-2` in this repository.
- We used **`934c5f3`** because it is the last commit whose message explicitly marks the Demo 2 deliverable (website + readme). Everything after it is stakeholder material, class feedback, or Demo 3 work.
- We did **not** use “last commit on `main`” as the baseline; that would be `HEAD` and would show zero history, which is not useful for this document.
- **`team8-demo2/` was not modified** in `934c5f3..HEAD`. Demo 2 code, eval scripts, and frozen results remain intact on `main`.

## Plain-language summary by area

### Agent & protocol

A full **Demo 3 prototype** landed in a new folder, `INFO492 team8 Demo3/` (~13k lines), committed in `e9ca3f9` by Daniiiel67. It is a separate app from `team8-demo2/`, not a refactor of Demo 2 in place.

| Piece | What it does |
|-------|----------------|
| `draft_agent` | Turns a rough field message into a structured RFI draft; **code** does sheet lookup and revision checks (same split as Demo 2); **LLM** rewrites wording and proposes questions; **guard** strips location/date/impact the message does not support. |
| `check_agent` | GC-side review on submitted RFIs (code + AI). |
| `watch_agent` | Code-only replay of addenda; flags RFIs citing sheets revised after the writer’s drawing set. |
| `triage_agent` | Code-only queue ordering for the architect (no design answers). |
| `protocol.py` | Role permissions, message envelope, hash-chained audit log; agents cannot change RFI status. |

**Preserved Demo 2 design:** `core.py` in Demo 3 still carries deterministic `reference_check` / sheet normalization and `ai_reference_review` for fit-and-typo judgment; `agents.lookup()` in Demo 3 mirrors the code-first reference path.

**Not yet aligned with the Demo 3 product brief (this planning doc):**

- No **per-RFI refinement loop** (check → ask sub → re-check until pass or max iterations).
- No **photo** ingestion path (Chen: WeChat message + photo).
- **`check_agent` false “return to sub”** on otherwise-complete RFIs (8/24 in saved eval; vague-location rule).
- Offline eval compares as-sent / checklist / draft agent, but **not** a unified before/after harness that also runs **Demo 2’s clean reference set** side by side with the messy set.
- Primary metric in README root thesis line still mentions **25% GC review time** in places; Demo 3 README partially pivots to “without a clarification round.”

### Evals & metrics

- `scripts/run_demo3_eval.py` scores 12 **simulated rough RFIs** (`rough_rfis.json` + `rough_answer_key.json`).
- Main offline measure today: **`needs_return_after`** (proxy for “GC would send back for missing info / refs”).
- Secondary: missing-item catch rate, reference catch, guard-blocked invented fields, check-agent false returns, watch-agent alert replay.
- **`/study`**: human GC reviewers time rough vs agent-drafted pairs; saves `runtime/study.csv` (still emphasizes review **time** as a pilot).
- Committed results: `results/demo3/` (post cost/scope prompt fix) and `results/demo3_v1_before_cost_fix/` (before fix).
- **Demo 2 evals unchanged**; `python3 -m unittest discover tests` in `team8-demo2/` passes (29 tests).

### Data

- **12 messy RFIs** (`rough_rfis.json`) derived from real Dett source rows but rewritten as informal site messages (generator: `scripts/generate_rough_rfis.py`). Clearly simulated; provenance in `docs/DATA_PROVENANCE.md`.
- **Revisions timeline** (`revisions.json`) built from addenda for watch-agent / superseded-set scenarios.
- **Kevin Chen interview** added under `interviews/` (PDF transcript, 12 pages). Stub `Kevin_Chen_GC-assistant-PM.md` is effectively empty (1 line).
- Class feedback summary: `class_feedback/README`.

### UI

- Demo 3 local app on port **8766**: multi-role PIN sign-in, RFI lifecycle, control panel, metrics export, study page.
- Demo 2 app on **8765** unchanged.
- Root `index.html` / GitHub Pages site updated in `cff7768` and `1c31a78` to point at Demo 3 folder.

### Infra & ops

- Still **local-only**: `runtime/state.json`, `audit.jsonl`, `study.csv` under Demo 3; API key in `~/.team8_rfi_gemini.json`.
- **`MAX_AI_CALLS`** per app session (default 300), not daily spend cap or public rate limiting.
- No hosted database, deploy config, health check, or `.env.example` at repo root.
- Folder name **`INFO492 team8 Demo3`** (spaces) complicates imports, deploy paths, and packaging.

---

## Contributions by teammate (`934c5f3..HEAD`)

### Daniiiel67

| Commit | Summary |
|--------|---------|
| `cff7768` | Root `README.md`: Demo 3 section, links, thesis wording updates. |
| `e9ca3f9` | **Entire Demo 3 tree**: app, agents, protocol, data, eval script, results, tests, static UI (~13k lines). |
| `1c31a78` | Root `README.md` tweaks for Demo 3 table. |

### V1mkito (Vincent)

| Commit | Summary |
|--------|---------|
| `41c25b3`–`8525dd0` | Early interview file churn (since removed/renamed). |
| `05e4fd2` | Created `interviews/Kevin_Chen_GC-assistant-PM.md` (stub). |
| `10e74cd`, `3cde35a` | `interviews/README`. |
| `6b416f1`, `bc34641`, `eeb264f` | **Kevin Chen transcript PDF** (final name: `GC interview transcript with Kevin Chen.pdf`). |

### muhamed-hashi

| Commit | Summary |
|--------|---------|
| `bf61dba`, `00a3e70`, `dbc636c` | **Class feedback** LLM summary → `class_feedback/README`. |

---

## Mapping changes to Kevin Chen interview & peer feedback

| Finding (source) | Addressed in repo? | Where / gap |
|------------------|-------------------|-------------|
| Real cost is **clarification round-trips (1–2 days)**, not 5–10 min first review (Chen) | **Partially** | `needs_return_after` in `run_demo3_eval.py`; `docs/EVALUATION.md` mentions round trips. Review **time** still prominent in `/study` and root thesis line. |
| Subs send **WeChat/SMS + photo**; GC rewrites formal RFI (Chen) | **Partially** | `rough_rfis.json` informal wording; **no photo upload** or ingestion UI. |
| Gaps: **location, drawing #, old revision, unclear question, impact/deadline** (Chen) | **Mostly** | Draft/check agents + answer key fields; eval does not yet tag gap **reasons** per Chen’s categories in the report JSON. |
| Tool must use **latest drawings**, explain reason/source (Chen) | **Yes (local)** | Code lookup + revision alerts; messages cite sheet/index. Not versioned index DB or deploy-time index updates. |
| **~3/10 false alarms → people stop reading** (Chen) | **Partially** | False returns counted in eval; **no dashboard warning at 20%**; Demo 2 zero false alarms on reference cases not re-surfaced in Demo 3 UI. |
| Agent **suggests only**; human decides (Chen + peers) | **Yes** | `protocol.py`, prompts, UI copy. |
| Peers: **show before/after** since Demo 1/2, measurable stakeholder impact | **Not yet** | No in-app “What changed since Demo 2” page; this file is Step 0 toward Goal 5. |
| Peers: **speak up / mic** | N/A (presentation) | — |
| Peers: time reviewers with/without agent | **Partially** | `/study` exists; small n, classmates not GCs. |
| Honesty about 25% target (peers praised) | **Mixed** | Demo 3 README still opens with 25% thesis sentence; offline eval pivots to clarification rounds. |

---

## Half-finished, broken, or inconsistent

| Issue | Severity | Notes |
|-------|----------|-------|
| Two apps (`team8-demo2` vs `INFO492 team8 Demo3`) | Plan | Duplicate `core.py`; risk of drift. Demo 3 claims Demo 2 reference prompt “reused unchanged” — verify on every change. |
| `check_agent` **false returns** (8/24) | Quality | Documented in `results/demo3/NOTES.md`; location vagueness. |
| Draft agent **barely beats checklist** on `needs_return_after` (7/24 vs 4/12 checklist) | Metrics | Denominator differs (2 AI runs); needs clearer primary metric definition. |
| `Kevin_Chen_GC-assistant-PM.md` empty | Docs | PDF is canonical; markdown link in README is misleading. |
| No `demo-2` tag | Release | Harder to reproduce “Demo 2 freeze” for auditors. |
| Demo 3 eval requires **live Gemini** to reproduce `results/demo3/` | Repro | JSON committed; re-run may differ. Unit tests use fake AI and pass (12 tests). |
| GC + architect multi-party flow | Scope | Built for class narrative; **your Demo 3 brief** centers sub → agent → GC; may keep simplified roles for public demo. |
| GitHub Pages serves static `index.html` only | Deploy | Demo 3 Python app not hosted. |

---

## Impact on the Demo 3 implementation plan (Goals 1–5)

### Already done (reuse, don’t redo)

- Deterministic sheet index + revision logic and LLM-only wording/fit split.
- Simulated **messy** 12-case set + answer key + offline eval script + committed result snapshot.
- Anti-invention guard on draft fields.
- Role-based protocol, audit trail, watch-agent replay.
- Basic “as sent vs helped” comparison and study pilot for time.
- Stakeholder PDF + class feedback summary in repo.

### Conflicts or rework needed

- **Unify product surface:** merge or symlink Demo 3 into a deployable package (folder rename, single `app`, shared `core` with `team8-demo2` frozen for regression).
- **Metrics:** make **% resolved without clarification round** primary everywhere (README, thesis, dashboard); demote review time; add gap-reason taxonomy in harness output.
- **Harness:** extend eval to full before/after on **clean Demo 2 set + messy set**; store JSON report + in-app results page.
- **Iteration loop:** app today is one draft cycle; Goals 3–4 need configurable max iterations with persistence.
- **Deploy & auth:** PIN demo users ≠ magic link / invite codes for Chen + class; move state off `runtime/*.json`.
- **Goal 5 page:** render this document in the app with before/after layout tied to interview quotes.

### What can stay as-is for Demo 2 regression

- Run from `team8-demo2/`: `python3 scripts/run_reference_eval.py`, `run_real_eval.py`, unittest suite — **do not change** reference lookup semantics in Demo 2 folder.

---

## Commit log detail (`934c5f3..HEAD`)

```
1c31a78 Update README.md
e9ca3f9 Add files via upload          # full Demo 3 tree
dbc636c Rename demo_feedback_summary.md to README
00a3e70 Add feedback summary to demo_feedback_summary.md
bf61dba feedback summary added
eeb264f Add files via upload          # Kevin Chen PDF
bc34641 Delete interviews/GC interview Script with Kevin Chen.pdf
6b416f1 Add files via upload
3cde35a Update README
10e74cd Create README
05e4fd2 Create Kevin_Chen_GC-assistant-PM.md
8525dd0 Delete Interview
41c25b3 Create Interview
cff7768 Update README.md
```

**Diff stat:** 44 files changed, ~13,170 insertions, 2 deletions (entirely new Demo 3 tree, interviews, feedback, README).

---

*This file is the source for Goal 5 (“What changed since Demo 2”). Update it when implementation phases land.*
