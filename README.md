# INFO492-Team-8

**Thesis:** Adding an AI review step to an existing subcontractor RFI form can reduce median GC first-review time by at least 25% compared with the same form completed without AI assistance, without increasing information errors.

**Website:** https://muhamed-hashi.github.io/INFO492-Team-8/ (served from `index.html` via GitHub Pages)

## Table of contents

| What | Where |
|---|---|
| Demo 1: finding missing details | [`team8-demo1/`](team8-demo1/) |
| Demo 2: checking drawing references | [`team8-demo2/`](team8-demo2/) |
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

## Stakeholder interviews

Transcripts of our interviews with construction industry stakeholders are in [`interviews/`](interviews/). [TO ADD: one line per interview: role, date, file name]

## Class feedback

[`class_feedback/`](class_feedback/) holds the class feedback on Demos 1 and 2, the prompt we used, and the LLM-generated summary. [TO ADD: file names and the model used]

## AI assistance

The prototypes were built with AI coding assistance. The thesis, dataset choice, case review and reported results are the team's.
