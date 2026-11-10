# Demo 3: Rough RFI Drafts and Timed Review Test

Prepared by Vincent Ma, Team 8 (subcontractor perspective).

## 1. Why we made rougher drafts

In Demos 1 and 2, our simulated RFIs were rewritten from Dett bid-stage questions. Those questions were written by estimators in an office, so they were clean and well organized. In our GC interview, Kevin Chen (assistant PM at a small GC in St. Louis) said that real construction RFIs are much messier: a foreman often types them on a phone, with abbreviations, half sentences and a photo. He said our rewritten data was "probably much cleaner than real RFIs."

For Demo 3 ("improve the draft"), the AI needs realistic drafts to improve. So we rewrote 10 real Dett RFIs into rough subcontractor-to-GC messages.

## 2. Source data

- Project: Robert Nathaniel Dett Elementary School Annex and Renovations, Chicago (PBC Contract C1604).
- Source: Addendum No. 5 (June 9, 2023) and Addendum No. 6 (June 15, 2023), public on the PBC project page.
- 7 drafts come from Addendum 5 RFIs (2, 3, 4, 7, 8, 9, 10) and 3 from Addendum 6 RFIs (2, 3, 4).
- Each record keeps the original question, the architect's response, and any related drawing revision, so a reviewer can check the answer.

Files:

| File | What it holds |
|---|---|
| `scripts/make_rough_drafts.py` | Generation script. Re-running it rebuilds both data files. |
| `data/rough_drafts.json` | 10 drafts (rough RFI forms plus answer key) and the list of planted issue types. |
| `data/rough_drafts.csv` | Same data as a table. `form_*` columns are the RFI form; the other columns are the answer key. |
| `data/timed_review_log_template.csv` | Empty log for the timed review test. |

Only the `form_*` fields (or `rough_draft`) may be given to the AI or the reviewers. All other columns are the answer key.

## 3. How we rewrote each RFI

**Format.** Each draft uses the part of a standard RFI form that a subcontractor fills in: date, from, to, subject, location, references, question, proposed solution, needed by, impact, attachments. The interview showed that even when subs use a template (his company uses a Word form based on AIA G716), they fill it in roughly: blank fields, "ASAP", wrong sheet numbers. So every form has all the fields, but the content is rough. These fields also match the RFI form in our Demo 1 app. The `form` fields are what the reviewer and the AI see. A one-line text version (`rough_draft`) is kept for agents that take plain text.

Rules:

1. Keep the original technical problem. Never invent a new problem.
2. Fill the form in a foreman's voice: short, abbreviations ("dwg", "rm", "plam"), little punctuation. Leave fields blank where the sub would skip them.
3. Plant only the problems Kevin described (table below). Every planted problem is listed in `planted_issues`.
4. Keep the correct answer in the record: `correct_location`, `correct_references`, `source_question`, `source_response`.
5. Mark every record `is_simulated: true` and list anything invented in `invented_details` (for example, needed-by dates).

Planted issue types (from the interview):

| Code | Meaning | Interview evidence |
|---|---|---|
| `vague_location` | "the hallway", "here" | Location is the most common missing item |
| `missing_sheet` | No sheet or detail number | Reviewer cannot find the drawing |
| `wrong_or_incomplete_sheet` | "P2", "A-30", "E-60" | 2-3 in 10 RFIs have a reference problem; "A2" example |
| `outdated_reference` | Cites a replaced detail or an older addendum | Subs keep using the bid set |
| `missing_deadline` | No date, or only "ASAP" | "If everything is ASAP, nothing is ASAP" |
| `missing_impact` | Does not say what work is waiting | Needed to set priority and control change orders |
| `multi_question` | Several questions in one message | GC has to split them |
| `photo_without_description` | "see pic" only | Photo with no explanation (floor sink example) |
| `scope_cost_hint` | Hints at extra cost | Subs use RFIs to set up change orders |

## 4. The 10 drafts at a glance

| ID | Source | Trade | Planted issues | Expected GC follow-ups |
|---|---|---|---|---|
| R01 | A5-RFI3 | Casework | location, sheet, outdated ref, deadline, impact, photo | 5 |
| R02 | A5-RFI4 | Casework | location, sheet, deadline, multi-question | 3 |
| R03 | A5-RFI7 | Plumbing | location, ambiguous sheet, multi-question, cost hint, deadline | 5 |
| R04 | A5-RFI8 | Solid surface | wrong sheet, location, deadline, impact | 3 |
| R05 | A5-RFI9 | Tile | location, sheet, multi-question, deadline, impact | 3 |
| R06 | A5-RFI10 | Tile | none (control) | 0 |
| R07 | A5-RFI2 | Security | sheet, location, outdated ref, deadline, impact | 3 |
| R08 | A6-RFI2 | Electrical / PV | wrong sheet, deadline, impact | 3 |
| R09 | A6-RFI3 | Electrical | none (control) | 0 |
| R10 | A6-RFI4 | Casework | none (control) | 0 |

The 3 control drafts are complete. They check that the AI does not "fix" an RFI that is already fine (false alarms).

`expected_followups` lists the questions a GC would need to ask the sub before forwarding the RFI. This is our measure of back-and-forth, which Kevin said costs "days, not minutes."

## 5. Timed review test plan

**Goal.** Test whether drafts improved by the AI (and approved by the sub) get a faster first review and fewer follow-up questions than the same drafts without AI, without adding errors.

**Two conditions for each draft.**
- **Without AI:** the rough draft, as written.
- **With AI:** the same draft after the AI suggests fixes and a teammate in the sub role approves them. The sub may only add information that is in the scenario brief or source documents.

**Reviewers.** People from our partner GC team, not our own team, because we know the answers. Reviewers must not see the answer key or which condition they have.

**Fair assignment.** No reviewer sees both versions of the same draft, because the second look would be faster.
- Form A: R01-R05 without AI, R06-R10 with AI.
- Form B: R01-R05 with AI, R06-R10 without AI.
- Half the reviewers get Form A, half get Form B. Shuffle the order inside each form.
- Start with one practice RFI that is not counted.

**What the reviewer does for each RFI.**
1. Open the RFI (timer starts).
2. Decide "can move forward" or "needs more information" (timer stops).
3. Write down every question they would ask the sub.

**What we record.**

| Measure | How |
|---|---|
| First-review time | Seconds from open to decision (the app already records this) |
| Decision | Move forward / needs more information |
| Follow-up questions | Count of the reviewer's questions; compare to `expected_followups` |
| Sub preparation time | Time the sub spends approving AI suggestions (with-AI drafts only) |
| Information errors | Any fact in the improved draft that does not match `source_question`, `correct_location` or `correct_references` (a wrong sheet, room or item). Checked by a teammate after the test. |
| False alarms | AI suggestions on control drafts R06, R09, R10 that ask for something already given |

**How we report it.** Compare median review time and median follow-up count between the two conditions, and report error and false-alarm counts. With 10 drafts and a few reviewers, this is a small pilot, so we report the numbers as descriptive results only and do not claim the 25% target is proven.

**Logging template.** One row per reviewer per draft:

`reviewer_id, form, draft_id, condition, review_seconds, decision, followup_questions, followup_count, notes`

## 6. Limitations

- These are still simulated: the problems are real Dett questions, but the rough wording, dates and impacts were written by us.
- Our team wrote both the drafts and the answer key, so the test may be easier than real RFIs.
- No photos are included; "see pic" only stands in for an unclear photo.
- Small sample (10 drafts), so results can show direction but not prove the thesis.
