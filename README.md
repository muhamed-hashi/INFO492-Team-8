# INFO492-Team-8

**Thesis** (updated after Demo 3; additions in bold): Adding an AI review step to an existing subcontractor RFI form can reduce median GC first-review time by at least 25% **and reduce follow-up rounds to the subcontractor**, compared with the same form completed without AI assistance, without increasing information errors **from submission through close-out**.

**Website:** https://muhamed-hashi.github.io/INFO492-Team-8/ (served from `index.html` via GitHub Pages)

**Demo 3 (live):** https://info492-team-8.onrender.com

## Table of contents

| What | Where |
|---|---|
| Demo 1: finding missing details | [`team8-demo1/`](team8-demo1/) |
| Demo 2: checking drawing references | [`team8-demo2/`](team8-demo2/) |
| Demo 3: sub ↔ GC ↔ design-team RFI exchange | [`INFO492 team8 Demo3/`](INFO492%20team8%20Demo3/) |
| Demo 3: rough RFI drafts (R01–R10) and stakeholder timed review test | [`demo3/`](demo3/) |
| Demo 4 (Protect): RFI close-out | [`INFO492 team8 Demo4/`](INFO492%20team8%20Demo4/) |
| Stakeholder interview transcripts | [`interviews/`](interviews/) |
| LLM summary of class feedback on Demos 1–2 | [`class_feedback/`](class_feedback/) |
| Team website | [`index.html`](index.html) |

## Demo 1: finding missing details

An AI check for missing fields in an RFI before it goes to the GC.

| | Location |
|---|---|
| Code | [`app.py`](team8-demo1/app.py), [`core.py`](team8-demo1/core.py), [`static/`](team8-demo1/static/), [`scripts/`](team8-demo1/scripts/) |
| Data | [`data/`](team8-demo1/data/): simulated RFIs, answer key, drawing index; sources in [`docs/DATA_PROVENANCE.md`](team8-demo1/docs/DATA_PROVENANCE.md) |
| LLM prompts | [`prompts/review.txt`](team8-demo1/prompts/review.txt) |
| Dependencies | [`requirements.txt`](team8-demo1/requirements.txt): Python 3.10+ standard library; Google Gemini API |
| Results | [`results/`](team8-demo1/results/) |
| How to run | [`team8-demo1/README.md`](team8-demo1/README.md) |

## Demo 2: checking drawing references

Code looks up every cited sheet number in a 206-sheet drawing index; the AI judges whether each sheet fits the question and spots typos.

| | Location |
|---|---|
| Code | [`app.py`](team8-demo2/app.py), [`core.py`](team8-demo2/core.py), [`static/`](team8-demo2/static/), [`scripts/`](team8-demo2/scripts/), [`tests/`](team8-demo2/tests/) |
| Data | [`data/`](team8-demo2/data/): 24 simulated reference cases, 10 real Dett RFIs, 2 adversarial cases, drawing index, 108 source RFIs; sources in [`docs/DATA_PROVENANCE.md`](team8-demo2/docs/DATA_PROVENANCE.md) |
| LLM prompts | [`prompts/`](team8-demo2/prompts/): `reference_review.txt` (Demo 2 design), `review.txt` (Demo 1 design, used as the AI-only comparison), `review_v2.txt` |
| Dependencies | [`requirements.txt`](team8-demo2/requirements.txt): Python 3.10+ standard library; Google Gemini API (`gemini-3.5-flash-lite`); `pypdf` only to re-extract data from the addenda PDFs |
| Results, simulated cases | [`results/demo2_references/`](team8-demo2/results/demo2_references/) |
| Evaluation Lab, 10 real RFIs | [`eval/`](team8-demo2/eval/) (labels, answer key, [`RESULTS.md`](team8-demo2/eval/RESULTS.md), write-up) and [`results/demo2_real/`](team8-demo2/results/demo2_real/) |
| How to run | [`team8-demo2/README.md`](team8-demo2/README.md) |

## Demo 3: RFI exchange between subcontractor, GC and design team

A foreman's rough site message becomes a clearer RFI (draft agent, foreman approves); the GC's agents check it and watch for drawing revisions; the architect's agent orders the queue. Agents only suggest or flag; people with the right role decide. Main measure: RFIs the GC can act on without a clarification round.

| | Location |
|---|---|
| Code | [`app.py`](INFO492%20team8%20Demo3/app.py), [`agents.py`](INFO492%20team8%20Demo3/agents.py), [`protocol.py`](INFO492%20team8%20Demo3/protocol.py), [`core.py`](INFO492%20team8%20Demo3/core.py), [`static/`](INFO492%20team8%20Demo3/static/), [`scripts/`](INFO492%20team8%20Demo3/scripts/), [`tests/`](INFO492%20team8%20Demo3/tests/) |
| Data | [`data/`](INFO492%20team8%20Demo3/data/): 12 rough RFIs from real Dett RFIs (simulated wording), answer key, drawing index, addendum revisions; sources in [`docs/DATA_PROVENANCE.md`](INFO492%20team8%20Demo3/docs/DATA_PROVENANCE.md) |
| LLM prompts | [`prompts/`](INFO492%20team8%20Demo3/prompts/): `draft_agent.txt`, `check_agent.txt`, `reference_review.txt` |
| Dependencies | [`requirements.txt`](INFO492%20team8%20Demo3/requirements.txt): Python 3.10+ standard library; Google Gemini API |
| Protocol (roles, messages, escalation, audit trail) | [`docs/PROTOCOL.md`](INFO492%20team8%20Demo3/docs/PROTOCOL.md) |
| Results | [`results/demo3/`](INFO492%20team8%20Demo3/results/demo3/) and [`NOTES.md`](INFO492%20team8%20Demo3/results/demo3/NOTES.md); first run kept in [`results/demo3_v1_before_cost_fix/`](INFO492%20team8%20Demo3/results/demo3_v1_before_cost_fix/) |
| How to run | [`README.md`](INFO492%20team8%20Demo3/README.md) |
| Rough drafts and timed review plan | [`demo3/docs/demo3_rough_drafts_and_timed_review.md`](demo3/docs/demo3_rough_drafts_and_timed_review.md), data in [`demo3/data/`](demo3/data/), generator [`demo3/scripts/make_rough_drafts.py`](demo3/scripts/make_rough_drafts.py) |
| Stakeholder test results (2 GC reviewers) | [`demo3/Team 8 – Demo 3 Timed Review Test Results.pdf`](demo3/Team%208%20%E2%80%93%20Demo%203%20Timed%20Review%20Test%20Results.pdf) |

## Demo 4 (Protect): RFI close-out

Before the GC closes an RFI the architect has answered, the close-out agent checks that every drawing change the answer promised was actually issued: code looks each sheet up in the real drawing lists attached to Dett Addenda 1–6; the AI only reads what the answer committed to (revised vs only referred to, anything still to come), with a quote for every claim; the project manager decides (close, keep open for the IFC set, or ask the architect). Tests the "without increasing information errors ... through close-out" part of the thesis. After professor feedback that our data was too clean, Demo 4 adds a messy test set (field-style wording, two problems in some answers), reports the agent's errors before a person checks as well as what would reach the field, and has a privacy-checked intake for real examples from our stakeholder ([`data/kevin/`](INFO492%20team8%20Demo4/data/kevin/)).

| | Location |
|---|---|
| Code | [`closeout.py`](INFO492%20team8%20Demo4/closeout.py), [`app.py`](INFO492%20team8%20Demo4/app.py), [`protocol.py`](INFO492%20team8%20Demo4/protocol.py), [`static/`](INFO492%20team8%20Demo4/static/), [`scripts/`](INFO492%20team8%20Demo4/scripts/), [`tests/`](INFO492%20team8%20Demo4/tests/) |
| Data | [`data/addendum_drawing_lists.json`](INFO492%20team8%20Demo4/data/addendum_drawing_lists.json) (real, every drawing attached to each addendum), [`data/closeout_cases.json`](INFO492%20team8%20Demo4/data/closeout_cases.json) and [`data/closeout_cases_messy.json`](INFO492%20team8%20Demo4/data/closeout_cases_messy.json) (40 tidy + 40 messy synthetic variants of real answers with known right answers), the 108 real RFIs; sources in [`docs/DATA_PROVENANCE.md`](INFO492%20team8%20Demo4/docs/DATA_PROVENANCE.md#demo-4-additions) |
| LLM prompts | [`prompts/closeout_agent.txt`](INFO492%20team8%20Demo4/prompts/closeout_agent.txt) (plus the Demo 3 prompts) |
| Dependencies | [`requirements.txt`](INFO492%20team8%20Demo4/requirements.txt): Python 3.10+ standard library; Google Gemini API; `pdftotext` only to re-extract the drawing lists |
| Protocol | [`docs/PROTOCOL.md`](INFO492%20team8%20Demo4/docs/PROTOCOL.md) |
| Results | [`results/demo4/`](INFO492%20team8%20Demo4/results/demo4/) and [`NOTES.md`](INFO492%20team8%20Demo4/results/demo4/NOTES.md) |
| How to run | [`README.md`](INFO492%20team8%20Demo4/README.md) |

## Stakeholder interviews

Transcripts of our interviews with construction industry stakeholders are in [`interviews/`](interviews/). Interview 1: assistant project manager at a small general contractor in St. Louis, October 2026, conducted in Chinese and translated into English ([`GC interview transcript with Kevin Chen.pdf`](interviews/GC%20interview%20transcript%20with%20Kevin%20Chen.pdf)).

## Class feedback

[`class_feedback/README`](class_feedback/README) holds the LLM-generated summary of peer and TA feedback on Demos 1 and 2.

## AI assistance

The prototypes were built with AI assistance. The thesis, dataset choice, case review and reported results are the team's.

