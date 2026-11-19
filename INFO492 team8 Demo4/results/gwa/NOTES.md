# Second real set: GWA "Response to RFI No. 1" (44 items)

Run with `python3 scripts/run_gwa_eval.py`. Raw output: `summary.json`, `gwa_log.csv` (every item: the reference
list's categories, the code baseline, each agent run with its flags, reasons and the per-question breakdown).
Run 2026-11-17 20:14 UTC, gemini-3.5-flash-lite, 2 AI runs (88 calls; 2 timed out in run 2, items 2 and 10).

## What we compare against, and why it is not an answer key

The document is real and public; our stakeholder sent it. The problem list that came with it
(`data/gwa/ai_problem_list.csv`) was **made by a teammate with an AI tool**, not by our stakeholder. Scoring our AI
against another AI's reading is circular, so below it is only a **reference**: "agree" means two AI readings
agree, not that either is right. It also has plain errors: items 4 and 29 are on its "no date" list but carry
printed dates (6/29/26, 6/30/26).

The human answer key is **our stakeholder's own call on 12 items**, made blind (question and answer only, no tool
output, no list) in his Demo #4 session: `data/kevin_review_demo4.xlsx`, tab "GWA (12)", imported by
`scripts/import_review.py` and scored by `--rescore`. **Pending.** The 12 were chosen by a fixed rule
(`review_sample` in the script) where the list and our agent disagree in both runs: the 2 items the list calls an
answer problem but the agent closed (20, 39), the 4 items the list finds fine but the agent stopped (21, 30, 34, 41),
and 6 drawn at random (seed 492) from the other disagreements (1, 7, 13, 14, 28, 35). Because they are
disagreements, his calls tell us which reading was right where it matters, not the accuracy on the whole log.

Not a blind test of the check either: the answer check and the baseline keywords were written after we had seen
this document and the list.

## Code-only baseline (keywords + counting, no AI)

| What | On the list | Agree | Not flagged | Flagged, not on the list |
|---|---|---|---|---|
| Not fully answered (will come back) | 10 | 8 | 37, 39 | 43 |
| Answer changes scope | 3 | 3 | – | 2, 21, 28, 42, 43 |
| Several questions in one item | 4 | 3 | 17 | 28, 29, 31, 32, 33, 34, 36, 43 |
| Points to something not in the text | 1 | 1 | – | 6, 7, 37 |
| Same answer given to another question | 2 | 2 | – | 10, 27, 30, 34, 35 |
| No date (printed date column) | 20 named | 18 | 4, 29 (both have printed dates) | 12 more; the list ends in "etc." |

Its keywords ("refer to", "will be … available", "delete", "is acceptable") were written after reading this
document, so its close agreement here means little. On the Dett log the same kind of rule stopped 13 of 108 RFIs,
mostly false alarms.

## Agent (AI + guard + code)

| What | On the list | Run 1 agrees | Run 2 agrees | Not flagged (run 1 / run 2) |
|---|---|---|---|---|
| Not fully answered (will come back) | 10 | 6 | 7 | 16, 20, 39, 42 / 20, 39, 42 |
| Answer changes scope | 3 | 3 | 3 | – |
| Several questions in one item | 4 | 3 | 3 | 17 (code count, same as baseline) |
| Points to something not in the text | 1 | 1 | 1 | – |

| | Code only | Agent run 1 | Agent run 2 |
|---|---|---|---|
| "Check" / "ok to close" / failed call | 15 / 29 / 0 | 33 / 11 / 0 | 30 / 12 / 2 |
| The list's 13 answer problems: stopped | 11 | 10 | 11 |
| ...closed anyway | 37, 39 | 16, 20, 39 | 20, 39 |
| Stops on the 37 items the list names any problem on | 14 | 29 | 26 |
| Stops on the 7 items the list finds fine | 1 (21) | 4 (21, 30, 34, 41) | 4 (21, 30, 34, 41) |

The two runs give the same recommendation on 38 of the 42 items where both calls returned, and the same flags on 29.
Guard: 2 items per run had a quote dropped (for example, a "question" the AI paraphrased instead of quoting).

## Reading (before our stakeholder's calls)

- **Our agent is much stricter than the other AI reading.** It stops 30–33 of 44 items. Many of its extra stops
  are on items where the list names a different problem: 13 ("Is this acceptable?" is never answered), 14 ("Which
  installation angle?" answered only with "Existing screen is set at 50 degrees"), 18 (a third elevation), 1 and 44
  (drawings never provided). Whether those are real is what our stakeholder decides.
- **The cases that decide it:** 20 ("a soft starter can be considered as part of a future upgrade") is closed by
  the agent in both runs; 39 is a copied answer, which code flags but which does not stop closing on its own
  (items 10/30 repeat an answer legitimately); 21 ("NEMA 4X 304L stainless steel is acceptable" instead of the
  specified polycarbonate) is stopped as a scope change though the list finds it fine. All are in his sample.
- Nothing closes on its own: every "check" goes to the PM, so a false alarm costs his time and a miss is what could
  slip through.
- Next change we would test (on a new log, not this one): stop on copied answers to different questions, and count
  "can be considered in future" as deferred.

## What neither method looks for

Most of the list: unclear scope (8 items), contradicting or copied specifications (13, 14, 16, 18), duplicate
questions (2, 27, 28, 29), typos, drawings that were never issued or are restricted (1, 38, 43, 44), conflicting
deadlines (22), inconsistent tags (35). These are problems in the bid documents that the RFIs reveal; an answer
check cannot see them.
