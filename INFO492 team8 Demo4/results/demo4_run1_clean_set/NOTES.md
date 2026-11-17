# Demo #4 close-out, first run (tidy set only, before the fixes)

Kept for comparison. The current results are in [../demo4/NOTES.md](../demo4/NOTES.md).

Run 2026-11-15 17:18 UTC, `python3 scripts/run_demo4_eval.py`, model gemini-3.5-flash-lite, 2 AI runs of the
40 test cases and 1 AI run over the 108 real RFIs. Raw output: `summary.json`, `per_case.csv`, `real_log.csv`,
`real_flags_for_review.csv`. How the cases were built: [../../docs/DATA_PROVENANCE.md](../../docs/DATA_PROVENANCE.md#demo-4-additions).

## Part 1: 40 test cases with a known right answer

| | Code only (keywords + drawing lists) | Agent run 1 | Agent run 2 |
|---|---|---|---|
| Planted problems caught (missing, deferred, typo) | 16/22 (73%) | 22/22 | 20/20 |
| False alarms on fine RFIs (clean, see also) | 6/18 (33%) | 0/17 | 0/15 |
| Exact recommendation | 28/40 (70%) | 39/39 | 35/35 |
| Failed AI calls (HTTP 503, Gemini busy; not scored) | – | 1 | 5 |

By kind, exact recommendation (code only / agent, both runs):

| Kind | Right answer | Code only | Agent |
|---|---|---|---|
| clean (12) | ok to close | 12/12 | 21/21 |
| see also (6) | ok to close | **0/6** | 11/11 |
| missing (8) | hold | 8/8 | 15/15 |
| deferred (8) | keep open | **2/8** | 15/15 |
| typo (6) | check | 6/6 | 12/12 |

Reading:
- The code-only rule fails exactly where reading is needed. It treats every sheet in an answer that mentions a
  revision as "revised", so a sentence like "Coordinate with E-205" put all 6 see-also cases on hold. It only
  catches "will come later" when the answer uses one of its keywords (2 of the 8 deferred sentences).
- Its 33% false-alarm rate is above the line our interviewee gave: if a tool is wrong 3 times in 10, people stop
  reading it.
- The agent got every scored case right in both runs. Code still does every lookup; the AI only says which sheets
  were revised and whether anything is still to come.
- 6 of 80 AI calls failed (Gemini returned HTTP 503). They are not counted as right or wrong; scores are per run
  over the calls that returned.
- The guard dropped 1 claim (C14, run 2): the AI's quote for M-908 was not word for word in the answer. The case
  was still right (the other two revised sheets were found), but M-908 went unchecked. Next step: treat any guard
  drop as "check" so nothing is silently skipped.

**Limit:** the 28 problems were planted by the team, one per case, in otherwise real answers. This shows the agent
can tell these situations apart; it does not show how often they happen on a real project, and real answers can
be messier.

## Part 2: the real Dett RFI log (108 answered RFIs, no answer key)

| | ok to close | keep open | hold | check | failed call |
|---|---|---|---|---|---|
| Code only | 96 | 0 | 4 | 8 | – |
| Agent | 101 | 1 | 3 | 1 | 2 |

The code-only rule stops 12 of 108 RFIs; the agent stops 5. Every RFI either method stopped is in
`real_flags_for_review.csv`, with empty `team_verdict` and `reviewer` columns for the team to fill in by hand.
What the documents show for each (facts checked by code against the drawing lists, not verdicts):

| RFI | Code | Agent | What the answer says, and what the drawing lists show |
|---|---|---|---|
| A3-RFI53, A3-RFI54 | hold | hold | "Refer to sheets … M-301, 2/M-600 and M-801 … All sheets have been revised and included in this addendum." M-301, M-600 and M-801 are **not** in the 159 drawings attached to Addendum 3 (they are in Addenda 1–2). P-500 in RFI53 is not either; our parser missed it because the answer writes "P- 500". |
| A3-RFI21 | hold | hold | "dimensions have been added to 12/Sd300 revised and included in this addendum." No sheet SD-300 exists; the question asks about S-300, which **is** item 18 in Addendum 3. Our near-match rule only links sheets with the same letters, so this should have been "check", not "hold". |
| A3-RFI33 | check | keep open | Bid due date moved "(pending confirmation of PBC's revised Board Meeting date)". A bid-date item, not a drawing; whether "pending" should keep it open is for the team to judge. |
| A3-RFI36 | ok to close | **check** | "The Finish Schedule and ID sheets 010, 011, 012, 013, 014, 015, 016, 021 have been revised". Code expands the series and finds all eight in Addendum 3; none of the sheet numbers the AI returned matched those, so the agent called the answer unclear and asked for a person. Here the agent was worse than code. |
| A1-RFI6, A2-RFI15, A3-RFI6, A3-RFI28, A3-RFI29, A3-RFI39, A5-RFI5 | hold or check | ok to close | The revision is to a specification section, not a drawing ("revised Specification 10.51.13", "Specification 07 42 13 … has been revised"). The agent closes with a note that code did not verify the specification. |
| A3-RFI57 | check | ok to close | A-432 is only referred to; A-434 "has been revised" and is item 79 in Addendum 3. |
| A3-RFI14, A3-RFI32 | ok to close | failed call | Gemini HTTP 503; code alone says ok to close. |

The real-data run is the more interesting result for the thesis: on real answers, two RFIs (53 and 54) promise
revised mechanical sheets that the Addendum 3 drawing list does not contain. Whether those sheets were issued
some other way (for example in the Issue for Construction set) we cannot tell from the public documents; that is
exactly the question a project manager would ask the architect before closing.
