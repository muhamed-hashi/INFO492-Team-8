# Demo #4 results on real data

Run 2026-11-17 04:41 UTC, `python3 scripts/run_demo4_eval.py`, gemini-3.5-flash-lite, 2 AI runs over the 108 real
answered RFIs of the Dett project, each checked against the drawing lists actually attached to the addenda.
Raw output: `summary.json`, `real_log.csv` (every RFI, both methods), `real_flags_for_review.csv` (every RFI either
method stopped). **Our stakeholder's review of the stopped RFIs is pending**; when it is in,
`python3 scripts/run_demo4_eval.py --rescore` adds how many stops he agreed with.

## What each method would do with the real log

| | OK to close | Check | Hold | Keep open | Failed AI call | Stopped |
|---|---|---|---|---|---|---|
| Code only (keywords + drawing lists) | 95 | 9 | 4 | 0 | – | **13** |
| Agent, run 1 | 101 | 3 | 2 | 0 | 2 | **5** |
| Agent, run 2 | 103 | 2 | 2 | 1 | 0 | **5** |

- The two agent runs gave the same recommendation on 104 of the 106 RFIs where both calls returned.
- 15 different RFIs were stopped by at least one method; they are the stakeholder's review list.

## The RFIs that were stopped, and what the documents show

These are facts from the answers and the drawing lists, not verdicts; the verdicts come from our stakeholder.

| RFI | Code | Agent (run 1 / 2) | What the answer says, and what the drawing lists show |
|---|---|---|---|
| A3-RFI53, A3-RFI54 | hold | hold / hold | "Refer to sheets … M-301, 2/M-600 and M-801 … All sheets have been revised and included in this addendum." M-301, M-600, M-801 (and P-500 in RFI53) are **not** among the 159 drawings attached to Addendum 3; they were issued in Addenda 1–2. |
| A3-RFI21 | check | check / check | "dimensions have been added to 12/Sd300 revised and included". No SD-300 exists; S-300 is item 18 in Addendum 3. Both now ask a person: "Did the answer mean S-300?" |
| A3-RFI2 | ok | check / check | The PDF text reads "as revisedA-502 and A-503" (no space). Code could not see A-502, so the guard dropped the AI's claim about it and asked a person instead of closing silently. Real, messy text the parser missed. |
| A1-RFI5 | ok | check / ok | "Please refer to Item No. 1 Change No. 1 above." The answer points elsewhere in the addendum; run 1 called it unclear. |
| A3-RFI33 | check | ok / **keep open** | Bid date moved "(pending confirmation of PBC's revised Board Meeting date)". The two runs disagree. |
| A1-RFI6, A2-RFI15, A3-RFI6, A3-RFI28, A3-RFI29, A3-RFI39, A5-RFI5 | hold or check | ok / ok | The change is to a specification section, not a drawing. Code stops them on the word "revised"; the agent closes with a note that the specification was not verified. |
| A3-RFI49, A3-RFI57 | hold / check | ok / ok | The answer refers to one sheet and revises another (A-601 / G-001; A-432 / A-434); the revised sheet is in the list. |

## Reading

- On real answers, the keyword rule stops 13 of 108 RFIs, mostly because the word "revised" appears; the agent
  stops 5. If our stakeholder confirms that the specification-only and refer-to cases are fine, most of the
  rule's stops are false alarms, which is the "wrong 3 times in 10, people stop reading" problem he described.
- The agent is not perfect or fully stable: 2 calls failed, the runs disagree on 2 RFIs, and A3-RFI2 shows real
  PDF text breaking our parser. Those mistakes go to a person ("check"), not to the field.
- Two real answers (A3-RFI53/54) promise revised mechanical sheets that the Addendum 3 drawing list does not
  contain. Whether they were issued some other way (for example in the Issue for Construction set) the public
  documents do not say; that is the question a PM would ask the architect before closing.
- Not measured: problems that both methods let through (RFIs nobody stopped are not reviewed).

Synthetic stress tests (`--synthetic`, not the headline; code-only numbers): tidy set 28/40 right, 6 of 22 planted
problems missed; messy set 17/40 right, 18 of 25 missed. The first AI run (Nov 15, tidy set, before four fixes) is
in [../demo4_run1_clean_set/NOTES.md](../demo4_run1_clean_set/NOTES.md).
