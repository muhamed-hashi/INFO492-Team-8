# Evaluation plan

## What Demo #1 tests

Can an AI check identify useful missing context in a subcontractor's RFI before submission? This tests a proposed mechanism behind the team's thesis. It does not by itself prove that median GC first-review time falls by 25% without more errors.

Start with the six labeled scenarios. A successful run requires a real model response marked `engine: ai` in the exported audit. Rule practice and mocked software tests are separate.

## First, test the checker

1. Have a teammate check each case and annotation against its source. Record any correction before testing the model.
2. Use a fresh session and the original draft for every case. Run the AI once on that original draft and save the returned findings. Log failures too; do not silently discard an unsuccessful case.
3. Compare findings to the **whole** RFI, not just empty form fields. Mark each suggestion useful, unnecessary, incorrect or uncertain, with a short reason. An empty field whose fact is clear elsewhere need not be flagged.
4. Record how many agreed missing facts were found and missed. Report unnecessary suggestions separately. D06 helps reveal unnecessary requests when no field has been deliberately removed.
5. After this initial check, edit and hand off the request if testing the rest of the flow. Keep all check history; evaluate the first check separately from later revisions.

These are pilot annotations by students, not validated expert ground truth. Do not promise perfect recall or construction expertise from six cases.

## Then, an optional first timing pilot

Use the **same form, instructions and scenario facts** with and without AI. Manual participants should also try to produce a good request. Do not send an intentionally poor manual draft unchanged merely to make AI look faster.

One possible small design is 12 reviews: each of the six cases in both conditions, assigned to two separate GC reviewers so each reviewer sees a case only once. Balance which cases and conditions each reviewer gets. For example:

| Reviewer | D01 | D02 | D03 | D04 | D05 | D06 |
|---|---|---|---|---|---|---|
| GC-A | Manual | AI | Manual | AI | Manual | AI |
| GC-B | AI | Manual | AI | Manual | AI | Manual |

Randomize the review order within each row. Hide condition assignments and AI suggestions from the GC reviewers. Counterbalance preparation order too. A coordinator can prepare the packets, but their learning across versions remains a limitation. If a teammate has already studied a case, use a different reviewer for that case or clearly report the familiarity and exclude it from the first-review comparison. This is a small exploratory design, not a powered study.

GC reviewers open only the final review screen and must not watch the preparation or recording rehearsal. Use reviewer aliases. The UI conceals conditions for the task, but it is not a secure blinded study platform: participants could inspect other local pages if they choose.

## Definitions

| Measure | Operational definition |
|---|---|
| Preparation time | Start preparation to saving the human-approved packet; includes source reading, AI waiting and editing |
| GC first-review time | Opening/revealing the RFI to clicking “move forward” or “needs clarification” |
| Clarification request | A “needs clarification” decision; report count and denominator in each condition |
| Information error | A distinct factual assertion or reference in the final RFI that contradicts the agreed scenario/source, or presents an unsupported guess as fact |
| Unnecessary AI suggestion | A request for information already supplied, not needed under the agreed rubric, or based on an incorrect reading |

First review is a readiness decision. It is not technical resolution, official acceptance, queue waiting time or total project delay.

After review, an evaluator compares each final packet against the agreed scenario brief and applicable source. Count each distinct error once, describe it, and enter the count. Do not count a deliberate simulation date as a historical error. Missing context is captured separately through omissions and clarification decisions. Resolve disagreements consistently. “Not assessed” must remain blank; it is not zero.

The GC timer stops on the decision, so feedback written afterward should not be included. Mark interruptions and prior exposure. Changing away from the review tab marks an interruption; reviews with that flag are excluded from displayed medians. Record other disruptions yourself. The timer is server wall-clock time, so long pauses or system sleep are not valid active-review data.

## Interpretation

The dashboard computes:

`100 × (median manual review time − median AI review time) / median manual review time`

It reports no improvement number until both conditions contain completed, uninterrupted reviews. Rules are never included in the AI condition. Read the result together with case mix, reviewer experience, errors, clarification decisions and preparation time. Faster rejection of an incomplete RFI is not automatically a benefit.

The dashboard shows mean information errors for **scored** cases only. Compare conditions only after equivalent scoring coverage and comparable case difficulty. With a small sample, observing no increase is preliminary; it does not establish statistical non-inferiority. A confidence interval or a larger study would be needed for a stronger claim.

Before formal testing, export rehearsal data and start a fresh database. Export CSV for summary and JSON for the full audit. Never present software-test records, one-person rehearsals, or generated example numbers as participant evidence.

If only the checker can be tested this week, say so in the demo note: describe detection successes, misses and false positives, then explain that the 25% time claim is still untested.
