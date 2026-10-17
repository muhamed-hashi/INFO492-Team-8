# Demo #2 results: check references

Run: 2026-10-17T15:07:52Z. 24 simulated RFIs: 12 with one reference problem, 12 with correct sheet numbers. Model: gemini-3.5-flash-lite.

| Measure | Code lookup only | AI only (Demo 1 design), run 1 | Code + AI (Demo 2 design), run 1 |
|---|---|---|---|
| Reference problems caught | 5/12 | 12/12 | 12/12 |
| - nonexistent | 3/3 | 3/3 | 3/3 |
| - typo | 0/3 | 3/3 | 3/3 |
| - unrelated | 0/4 | 4/4 | 4/4 |
| - vague | 2/2 | 2/2 | 2/2 |
| Correct references wrongly flagged | 0/12 | 3/12 | 0/12 |
| Cases judged correctly | 17/24 | 21/24 | 24/24 |
| Failed calls | 0 | 0 | 0 |

All runs - problems caught: AI only 12/12, 10/12, 12/12; code + AI 12/12, 12/12, 12/12. Correct references wrongly flagged: AI only 3, 2, 2; code + AI 0, 0, 0.
AI-only messages claiming an indexed sheet is missing from the index (all runs): 13.

## Per case

| Case | Problem | References as written | Code | AI only (runs) | Code + AI (runs) |
|---|---|---|---|---|---|
| R01 | clean | A-102B, A-103B, A-104B; Spec 10 51 13 | ok | ok ok ok | ok ok ok |
| R02 | typo | A-4O1, A-402, A-433 | ok | FLAG FLAG FLAG | FLAG FLAG FLAG |
| R03 | unrelated | E-600, A-433 | ok | FLAG FLAG FLAG | FLAG FLAG FLAG |
| R04 | clean | A-401, A-402, A-433 | ok | ok FLAG ok | ok ok ok |
| R05 | clean | E-600, PV-600 | ok | FLAG ok FLAG | ok ok ok |
| R06 | clean | A-502, A-503 | ok | ok ok ok | ok ok ok |
| R07 | unrelated | A-502, S-301 | ok | FLAG FLAG FLAG | FLAG FLAG FLAG |
| R08 | clean | A-502, A-503 | ok | ok ok ok | ok ok ok |
| R09 | typo | E-600, FP-2O0 | ok | FLAG FLAG FLAG | FLAG FLAG FLAG |
| R10 | clean | E-600, FP-200 | ok | ok ok ok | ok ok ok |
| R11 | clean | A-210, A-703 | ok | FLAG FLAG ok | ok ok ok |
| R12 | nonexistent | S-001, S-301, S-103 | FLAG | FLAG FLAG FLAG | FLAG FLAG FLAG |
| R13 | clean | E-301, E-801 | ok | ok ok ok | ok ok ok |
| R14 | clean | A-502, ID-015 | ok | FLAG ok FLAG | ok ok ok |
| R15 | clean | E-700, E-500 | ok | ok ok ok | ok ok ok |
| R16 | clean | S-001, S-301, S-101 | ok | ok ok ok | ok ok ok |
| R17 | unrelated | A-502, FP-200 | ok | FLAG FLAG FLAG | FLAG FLAG FLAG |
| R18 | unrelated | A-502, E-700 | ok | FLAG FLAG FLAG | FLAG FLAG FLAG |
| R19 | nonexistent | E-301, E-802 | FLAG | FLAG ok FLAG | FLAG FLAG FLAG |
| R20 | clean | E-301, E-801 | ok | ok ok ok | ok ok ok |
| R21 | vague | See architectural drawings; Spec 10 51 13 | FLAG | FLAG FLAG FLAG | FLAG FLAG FLAG |
| R22 | typo | A-210, A-7O3 | ok | FLAG FLAG FLAG | FLAG FLAG FLAG |
| R23 | nonexistent | E-700, E-501 | FLAG | FLAG ok FLAG | FLAG FLAG FLAG |
| R24 | vague | Per electrical plans | FLAG | FLAG FLAG FLAG | FLAG FLAG FLAG |

## AI-only: claims that an indexed sheet is missing

- R03 run 1 - PV-600: Drawing PV-600 is referenced in the question, but it does not appear in the supplied partial drawing index.
- R03 run 2 - PV-600: Drawing PV-600 is referenced in the question but is missing from the supplied partial drawing index.
- R03 run 3 - PV-600: Drawing PV-600 is referenced in the question but does not appear in the supplied drawing index.
- R04 run 2 - A-433: The referenced sheet A-433 appears in the partial drawing index, but the user notes the specific detail is missing.
- R05 run 1 - PV-600: Drawing reference PV-600 mentioned in the RFI and references fields is not present in the supplied partial drawing index.
- R05 run 3 - PV-600: Drawing reference PV-600 is cited in the RFI, but this specific identifier is missing from the supplied partial drawing index.
- R07 run 3 - S-301: Drawing S-301 is listed in references but does not appear in the supplied partial drawing index.
- R14 run 1 - ID-015: Reference ID-015 is cited in the RFI but does not appear in the supplied partial drawing index.
- R14 run 3 - ID-015: Drawing ID-015 is referenced in the RFI but does not appear in the supplied partial drawing index.
- R17 run 1 - ID-015: Drawing ID-015 is referenced in the question but does not appear in the supplied partial drawing index.
- R17 run 3 - ID-015: Drawing ID-015 is referenced in the question but does not appear in the supplied partial drawing index.
- R22 run 3 - A-703: Reference A-7O3 appears to use the letter O instead of a zero, which does not match the standard drawing numbering format or index format A-703.
- R23 run 1 - E-500: Drawing E-501 is referenced in the RFI, but the identifier E-501 does not appear in the supplied partial drawing index (though E-500 does).

## Code + AI: what the AI said (run 1) - team to judge

- R02 (typo): Sheet A-4O1 in the references contains the letter O instead of the number zero, which likely caused the lookup program to miss it if not corrected.
- R03 (unrelated): A-433 may not show this condition: Exterior details do not pertain to electrical conduit sizing.
- R03 (unrelated): Drawing PV-600 is mentioned in the RFI question but is missing from the references field.
- R07 (unrelated): S-301 may not show this condition: The sheet title is DEEP FOUNDATION SCHEDULES, SECTIONS AND DETAILS, which belongs to structural work and does not relate to interior flooring finishes.
- R09 (typo): Sheet reference FP-2O0 contains the letter O instead of the number zero.
- R12 (nonexistent): Sheet S-103 is referenced in the RFI but was not recognized in the drawing index lookup.
- R17 (unrelated): FP-200 may not show this condition: The sheet title is FIRE PROTECTION DETAILS AND SCHEDULE, which is a different trade and system from flooring.
- R17 (unrelated): Drawing ID-015 is referenced in the question text but is missing from the references list.
- R18 (unrelated): E-700 may not show this condition: The sheet title is ELECTRICAL DETAILS, which is unrelated to the tile and architectural finishes of the question.
- R18 (unrelated): Sheet E-700 is referenced in the RFI, but the question is strictly about architectural tile, finish schedules, and cove base, which are unrelated to electrical details.
- R19 (nonexistent): Sheet E-802 mentioned in the references was not found in the drawing index.
- R22 (typo): Sheet reference A-7O3 contains a letter 'O' instead of a zero, which may prevent the lookup program from recognizing it.
- R23 (nonexistent): Drawing E-501 is referenced in the question but was not found in the drawing index.
