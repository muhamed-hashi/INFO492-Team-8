# Demo #2 results

Run: 2026-10-17T01:54:27Z. 24 simulated RFIs (12 with planted defects, 12 complete), each checked on its unedited draft. Model: gemini-3.5-flash-lite. Prompt unchanged from Demo #1.

| Measure | Rule checklist (no AI) | AI (run 1) |
|---|---|---|
| Planted defects found | 8/13 (62%) | 11/13 (85%) |
| Defects missed | 5 | 2 |
| False alarms (flags on fields that were fine) | 1 | 6 |
| Complete RFIs wrongly flagged | 1/12 | 4/12 |
| Defective RFIs fully caught | 7/12 | 10/12 |
| "Ready to send" decision correct | 19/24 | 20/24 |
| Failed calls | 0 | 0 |

AI invented sheet numbers (all runs): 0.
Across runs, AI defects found: 11/13, 12/13, 11/13; false alarms: 6, 7, 6. Same flags in every run: 18/24 cases.

## Per case (run 1)

| Case | Planted defect | Expected | Rules | AI |
|---|---|---|---|---|
| D01 | clean | - | - | - |
| D02 | blank_deadline | needed_by | needed_by | needed_by |
| D03 | placeholder_deadline | needed_by | needed_by | needed_by |
| D04 | clean | - | - | - |
| D05 | clean | - | - | references |
| D06 | clean_short_question | - | - | references |
| D07 | placeholder_impact | impact | impact | references |
| D08 | clean | - | - | - |
| D09 | blank_impact | impact | impact | impact |
| D10 | clean | - | - | - |
| D11 | clean | - | - | references |
| D12 | bad_reference | references | references | references |
| D13 | clean | - | - | - |
| D14 | clean | - | - | - |
| D15 | clean | - | - | - |
| D16 | clean | - | - | - |
| D17 | subtle_vague_location | location | - | references |
| D18 | blank_location | location | location | location |
| D19 | subtle_deadline | needed_by | - | needed_by |
| D20 | clean_location_in_question | - | location | location |
| D21 | placeholder_impact | impact | impact | impact |
| D22 | vague_question | question | - | question |
| D23 | subtle_vague_question | question | - | question |
| D24 | missing_reference+subtle_impact | impact;references | references | impact;references |

## AI flags outside the answer key (run 1) - team to judge: useful or unnecessary?

- D05 (clean), references: Drawing PV-600 is referenced in the RFI but does not appear in the supplied partial drawing index.
- D06 (clean_short_question), references: Reference A-503 is listed in the RFI but does not appear in the provided partial drawing index.
- D07 (placeholder_impact), references: Drawing A-503 is referenced in the RFI but is missing from the supplied partial drawing index.
- D11 (clean), references: Detail 6/A-703 is mentioned in the question text as a reference, but only sheets A-210 and A-703 are listed in the references field.
- D17 (subtle_vague_location), references: Reference ID-015 is not present in the supplied partial drawing index.
- D20 (clean_location_in_question), location: The location field is blank, although the question and title reference Gym Office 173A.

## AI misses (run 1)

- D07 (placeholder_impact): impact
- D17 (subtle_vague_location): location
