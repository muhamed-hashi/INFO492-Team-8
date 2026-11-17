# Second real set: GWA "Response to RFI No. 1" (44 items) against our stakeholder's problem list

Run with `python3 scripts/run_gwa_eval.py`. Raw output: `summary.json`, `gwa_log.csv` (every item: his categories,
the code baseline, each agent run with its flags, reasons and the per-question breakdown).
Run 2026-11-17 20:14 UTC, gemini-3.5-flash-lite, 2 AI runs (88 calls; 2 timed out in run 2, items 2 and 10).

Answer key: our stakeholder's problem list (`data/gwa/stakeholder_problem_list.csv`). He listed problems on 37 of
44 items; items 12, 21, 24, 30, 31, 34, 41 have none. Not a blind test: the check was written after we saw his list.

## Code-only baseline (keywords + counting, no AI)

| What | His items | Found | Missed | Flagged, not on his list |
|---|---|---|---|---|
| Not fully answered (will come back) | 10 | 8 | 37, 39 | 43 |
| Answer changes scope | 3 | 3 | – | 2, 21, 28, 42, 43 |
| Several questions in one item | 4 | 3 | 17 | 28, 29, 31, 32, 33, 34, 36, 43 |
| Points to something not in the text | 1 | 1 | – | 6, 7, 37 |
| Same answer given to another question | 2 | 2 | – | 10, 27, 30, 34, 35 |
| No date (printed date column) | 20 named | 18 | 4, 29 (both have printed dates) | 12 more; his list ends in "etc." |

Recommendation: 15 "check", 29 "ok to close". Of the 13 items where he found an answer problem (not fully answered
or scope change), it stops 11 and would close 37 (the answer is a pasted picture of an unrelated specification) and
39 (the copied answer). It also stops 2, 21, 28 and 43, which he did not list as answer problems; 21 is one of
the 7 items he found no problem with.

Why the baseline looks good here, and why we do not trust it: its keywords ("refer to", "will be … available",
"delete", "is acceptable") were written after reading this document. On the Dett log, the same kind of keyword
rule stopped 13 of 108 RFIs, mostly false alarms.

## Agent (AI + guard + code)

| What | His items | Run 1 found | Run 2 found | Missed (run 1 / run 2) |
|---|---|---|---|---|
| Not fully answered (will come back) | 10 | 6 | 7 | 16, 20, 39, 42 / 20, 39, 42 |
| Answer changes scope | 3 | 3 | 3 | – |
| Several questions in one item | 4 | 3 | 3 | 17 (code count, same as baseline) |
| Points to something not in the text | 1 | 1 | 1 | – |

Recommendation:

| | Code only | Agent run 1 | Agent run 2 |
|---|---|---|---|
| "Check" / "ok to close" / failed call | 15 / 29 / 0 | 33 / 11 / 0 | 30 / 12 / 2 |
| His 13 answer problems stopped | 11 | 10 | 11 |
| ...closed anyway | 37, 39 | 16, 20, 39 | 20, 39 |
| Stops on items where he listed some problem (37 items) | 14 | 29 | 26 |
| Stops on the 7 items he found no problem with | 1 (21) | 4 (21, 30, 34, 41) | 4 (21, 30, 34, 41) |

The two runs give the same recommendation on 38 of the 42 items where both calls returned, and the same flags on 29.
Guard: 2 items per run had a quote dropped (for example, a "question" the AI paraphrased instead of quoting).

## Reading

- **The agent is strict, not precise.** It stops 30–33 of 44 items. Most extra stops land on items where our
  stakeholder found a different problem: 13 ("Is this acceptable?" is never answered; he lists a copied spec), 14
  (which angle, 50° or 40°: "Existing screen is set at 50 degrees"; he lists a contradicting spec), 18 (a third
  elevation; he lists a three-way conflict), 1 and 44 (drawings never provided). So those items do need a person,
  but not for the reason he gave. On the 7 items he found fine, it stops 4; one of them, 21 ("NEMA 4X 304L stainless
  steel is acceptable" instead of the specified polycarbonate), may be a real substitution worth recording; that is
  a question for him.
- **What it misses matters most.** 20 ("a soft starter can be considered as part of a future upgrade") is closed in
  both runs: the AI read the answer as complete. 39 is a copied answer; code flags it, but a copied answer does not
  stop closing on its own (items 10/30 repeat an answer legitimately). 16 ("Follow provided specification", when the
  two specifications disagree) was closed in run 1 and stopped in run 2.
- **The keyword baseline looks better here but is not trustworthy:** its keywords were written after reading this
  document. On the Dett log, the same kind of rule stopped mostly the wrong RFIs.
- Nothing closes on its own: every "check" goes to the PM, so a false alarm costs his time and a miss (20, 39) is
  what could slip through.
- Next change we would test (on a new log, not this one): stop on copied answers to different questions, and count
  "can be considered in future" as deferred.

## What neither method looks for

Most of his list: unclear scope (8 items), contradicting or copied specifications (13, 14, 16, 18), duplicate
questions (2, 27, 28, 29), typos, drawings that were never issued or are restricted (1, 38, 43, 44), conflicting
deadlines (22), inconsistent tags (35). These are problems in the bid documents that the RFIs reveal; an answer
check cannot see them.
