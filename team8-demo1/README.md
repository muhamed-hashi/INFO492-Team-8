# Team 8 — RFI Check Before Submission

Working local prototype for INFO 492, Coordination Demo #1.

The default AI provider is Gemini. This repository contains the local prototype, simulated data, model prompts, and evaluation plan.

**Research question:** Does an AI check on the same RFI form reduce median GC first-review time by at least 25%, without increasing information errors?

The 25% figure is a proposed target, not an observed result. Demo #1 focuses on the first mechanism: identifying missing context before submission. The application also records preparation and first-review time for a later controlled pilot.


## Run locally

Requires Python 3.10 or newer and a modern browser. There are no third-party Python dependencies.

```bash
python3 app.py
```

Open <http://127.0.0.1:8765>. Keep the terminal open; press Ctrl+C to stop. On Windows, use `py app.py` if `python3` is unavailable. If the port is occupied, use `python3 app.py --port 8766` and open port 8766.

This is a local application. Uploading its files to GitHub stores the code; it does not run the Python server. A recorded walkthrough is an allowed assignment deliverable, so deployment is not needed for that route.

## Three explicit conditions

| Method | What runs | Interpretation |
|---|---|---|
| Without AI | The participant completes the form unaided | Control condition |
| With AI | An actual model request checks the supplied form | AI condition; requires an API key and successful response |
| Rule checklist | Deterministic checks for empty fields and short questions | Offline practice only; excluded from the AI comparison |

No failed AI request silently becomes a rule result. No AI output is accepted as a design answer or construction authorization.

### Connect the AI condition

```bash
python3 setup_ai.py
python3 app.py
```

The setup script now asks for a **Gemini API key** without displaying it and saves it locally. It defaults to `gemini-3.5-flash-lite`. Use an AI Studio project on the free tier if you want to use free quota. Availability and limits depend on the project; this app cannot verify billing tier and does not enable or change billing.

`GEMINI_API_KEY` (or `GOOGLE_API_KEY`) and `GEMINI_MODEL` environment variables override the local Gemini settings. To choose a different model, run `python3 setup_ai.py --model MODEL_ID`. The Gemini adapter uses generateContent with a JSON schema. It records the returned model version in the audit.

The OpenAI adapter remains available with `python3 setup_ai.py --provider openai`. Existing OpenAI keys are selected if no provider or Gemini key was set. `AI_PROVIDER` explicitly selects `gemini` or `openai`; it never silently switches on failure. Keep the provider and model fixed during an experiment, and do not pool results from different models without identifying them.

Never upload `config.local.json`, `.env`, or a key. The form contents and drawing identifier list are sent to the configured AI provider during an AI check. No historical answer key is included. Provider data policies still apply. Gemini free-tier content may be used to improve Google products. Use the public/simulated cases. OpenAI requests use `store: false`, which is not a claim of zero retention.

## Demonstration flow

1. Choose a simulated case and preparation method. Start preparation.
2. Read the scenario brief. In AI mode, run a check and inspect the suggestions.
3. Edit the form yourself using the scenario brief and source documents. The AI does not invent missing dates or approve changes.
4. Confirm the information and save the RFI for GC review.
5. A separate reviewer opens the GC screen on the same computer. Starting the review reveals the RFI and starts the timer. The screen hides the preparation condition and suggestions.
6. The reviewer selects “move forward” or “needs clarification.” The coordinator assesses errors separately and exports CSV and JSON records.

For remote teamwork, run the application on each person's computer or use a screen-sharing arrangement with one host. A localhost link cannot be opened on a teammate's other computer. Do not let a GC reviewer watch preparation for an experimental case. A screen-recorded walkthrough is practice, not unbiased timing evidence.

## Data and limits

Six **simulated** RFIs are adapted from the Public Building Commission of Chicago's Dett Elementary School Addenda 5 and 6. They are based on bid-stage questions, not a historical construction-stage RFI log. Construction dates, impacts, and some location wording are invented for the exercise. Each record identifies its source and page.

Drawing checks only match identifiers in a partial index. They do not validate drawing content, details, or the latest approved revision. All source documents remain authoritative over a generated suggestion.

- [Data provenance and generation](docs/DATA_PROVENANCE.md)
- [Evaluation plan and scoring](docs/EVALUATION.md)

## Repository contents

| Path | Purpose |
|---|---|
| `app.py`, `core.py` | Local server, timers, checks, AI adapter and exports |
| `static/` | Browser interface and GC review screen |
| `prompts/review.txt` | Actual system instructions used by the AI adapter |
| `scripts/generate_data.py` | Reproducible synthetic case generation |
| `data/cases.json` | Six labeled simulated inputs and participant briefs |
| `data/answer_key.json` | Evaluator-only pilot annotations; not served to the UI or sent to AI |
| `data/drawing_index.json` | Partial source index with page links |
| `tests/test_demo.py` | Automated software tests; not experimental results |
| `requirements.txt` | Runtime dependency declaration |

Results persist in `runtime/demo.sqlite3` on the host computer. Download the audit JSON to retain check inputs, outputs, model, prompt hash and timings. Export before starting a fresh study; with the server stopped, rename `runtime` to a backup directory to start with a new empty database. Do not mix rehearsal trials with experimental trials.

## Reproduce and test

```bash
python3 scripts/generate_data.py
python3 -m unittest discover -s tests -v
```

Generation overwrites the three generated JSON files, so preserve any team edits first. Tests use a temporary database and a mocked AI response. Passing tests does not establish model quality, participant performance, or the 25% thesis.

This prototype serves only on the local computer. It is not a production construction management service. Human approval saves a local packet; nothing is sent to a real GC.

## Submission checklist

- A recording or working live demo that shows actual behavior.
- This repository with code, data, generation script, prompts and dependencies.
- A note of no more than 500 words reporting real observations, including failures.
- Each student's truthful individual contribution statement.
- Test results explicitly distinguish connected AI from rule practice. No fabricated numbers.

Developed with AI assistance. The team should review the code, sources and generated data, run the connected model, and report its own observations before submission.

Gemini documentation: [model](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite), [pricing and free tier](https://ai.google.dev/gemini-api/docs/pricing), [generateContent](https://ai.google.dev/api/generate-content).

## Recorded checks and current status — October 12, 2026

The supplied results contain six Gemini checks on unedited simulated RFI drafts. AI and the rule checklist each identified all six expected missing-field labels. AI also raised two additional question-specific suggestions that still require human assessment. This is a small checker evaluation, not a human GC timing comparison. No 25% reduction or unchanged final-packet error rate has been demonstrated.

- [Results summary and limitations](results/summary.md)
- [Per-case results](results/per_case.csv)
- [Recorded inputs and AI outputs](results/ai_checks.json)

The CSV `seconds` field has undocumented timing boundaries and is not treated as GC first-review time. The team still needs to verify annotations, assess the extra suggestions, and complete its walkthrough, demo note, and individual contribution statements. Automated software tests use mocked model responses and are separate from these supplied model-output records.
