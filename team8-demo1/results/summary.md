# Demo #1 results

AI checks on 6 of 6 simulated RFIs, each run once on the unedited draft. Model: gemini-3.5-flash-lite. Expected flags come from data/answer_key.json.

| | Rule checklist (no AI) | AI check |
|---|---|---|
| Missing fields found | 6/6 | 6/6 |
| Missed | 0 | 0 |
| Flags not in the answer key | 0 | 2 |
| Failed calls | 0 | 0 |

## Per case

| Case | Expected | Rule flags | AI flags |
|---|---|---|---|
| D01 | location;needed_by | location;needed_by | location;needed_by |
| D02 | references | references | question;references |
| D03 | impact | impact | impact |
| D04 | needed_by | needed_by | needed_by |
| D05 | trade | trade | trade |
| D06 | (none) | - | question |

## AI flags not in the answer key (team to judge: useful or unnecessary?)

- D02: question: The question mentions conflicting countertop material notes without specifying where the conflict occurs or which materials are in conflict.
- D06: question: The question asks about an item beside the sink without specifying a detail or tag number.

## Interpretation and limits

These files contain six recorded AI checks on simulated drafts. Counts use the expected field labels in the pilot answer key; they are not an expert validation of RFI quality. The AI and rule checklist both identified all six deliberately omitted fields. These results do not establish an advantage for AI over the rule checklist on omission detection. The two additional AI suggestions still need human assessment and must not automatically be counted as errors or benefits.

The `seconds` column is preserved as supplied. Its timing boundaries are not documented in the supplied files, so it is not used here as a performance measure and must not be interpreted as GC first-review time.

No human GC review decisions, review durations, or final-packet error assessments are included in these results. They do not establish the proposed 25% review-time reduction or an unchanged information-error rate. Six successful records are included; no failures are recorded in this set. This does not establish that no setup failures or other attempts occurred.

The original per-case CSV and AI-check JSON are retained unchanged. The summary was supplemented with these interpretation notes when preparing the repository upload.
