# Demo #2 results: check references

Run: 2026-10-23T01:21:25Z. 24 simulated RFIs: 12 with one reference problem, 12 with correct sheet numbers. Model: gemini-3.5-flash-lite.

| Measure | Code lookup only | AI only (Demo 1 design), run 1 | Code + AI (Demo 2 design), run 1 |
|---|---|---|---|
| Reference problems caught | 5/12 | 10/12 | 12/12 |
| - nonexistent | 3/3 | 1/3 | 3/3 |
| - typo | 0/3 | 3/3 | 3/3 |
| - unrelated | 0/4 | 4/4 | 4/4 |
| - vague | 2/2 | 2/2 | 2/2 |
| Correct references wrongly flagged | 0/12 | 4/12 | 0/12 |
| Cases judged correctly | 17/24 | 18/24 | 24/24 |
| Failed calls | 0 | 0 | 0 |

All runs - problems caught: AI only 10/12, 12/12, 10/12; code + AI 12/12, 12/12, 12/12. Correct references wrongly flagged: AI only 4, 3, 4; code + AI 0, 0, 0.
AI-only messages claiming an indexed sheet is missing from the index (all runs): 20.

## Per case

| Case | Problem | References as written | Code | AI only (runs) | Code + AI (runs) |
|---|---|---|---|---|---|
| R01 | clean | A-102B, A-103B, A-104B; Spec 10 51 13 | ok | ok ok ok | ok ok ok |
| R02 | typo | A-4O1, A-402, A-433 | ok | FLAG FLAG FLAG | FLAG FLAG FLAG |
| R03 | unrelated | E-600, A-433 | ok | FLAG FLAG FLAG | FLAG FLAG FLAG |
| R04 | clean | A-401, A-402, A-433 | ok | ok ok ok | ok ok ok |
| R05 | clean | E-600, PV-600 | ok | FLAG FLAG FLAG | ok ok ok |
| R06 | clean | A-502, A-503 | ok | FLAG FLAG ok | ok ok ok |
| R07 | unrelated | A-502, S-301 | ok | FLAG FLAG FLAG | FLAG FLAG FLAG |
| R08 | clean | A-502, A-503 | ok | ok ok ok | ok ok ok |
| R09 | typo | E-600, FP-2O0 | ok | FLAG FLAG FLAG | FLAG FLAG FLAG |
| R10 | clean | E-600, FP-200 | ok | ok ok FLAG | ok ok ok |
| R11 | clean | A-210, A-703 | ok | FLAG FLAG FLAG | ok ok ok |
| R12 | nonexistent | S-001, S-301, S-103 | FLAG | FLAG FLAG FLAG | FLAG FLAG FLAG |
| R13 | clean | E-301, E-801 | ok | ok ok ok | ok ok ok |
| R14 | clean | A-502, ID-015 | ok | FLAG ok FLAG | ok ok ok |
| R15 | clean | E-700, E-500 | ok | ok ok ok | ok ok ok |
| R16 | clean | S-001, S-301, S-101 | ok | ok ok ok | ok ok ok |
| R17 | unrelated | A-502, FP-200 | ok | FLAG FLAG FLAG | FLAG FLAG FLAG |
| R18 | unrelated | A-502, E-700 | ok | FLAG FLAG FLAG | FLAG FLAG FLAG |
| R19 | nonexistent | E-301, E-802 | FLAG | ok FLAG ok | FLAG FLAG FLAG |
| R20 | clean | E-301, E-801 | ok | ok ok ok | ok ok ok |
| R21 | vague | See architectural drawings; Spec 10 51 13 | FLAG | FLAG FLAG FLAG | FLAG FLAG FLAG |
| R22 | typo | A-210, A-7O3 | ok | FLAG FLAG FLAG | FLAG FLAG FLAG |
| R23 | nonexistent | E-700, E-501 | FLAG | ok FLAG ok | FLAG FLAG FLAG |
| R24 | vague | Per electrical plans | FLAG | FLAG FLAG FLAG | FLAG FLAG FLAG |

## AI-only: claims that an indexed sheet is missing

- R03 run 1 - PV-600: Drawing PV-600 is referenced in the question but does not appear in the supplied partial drawing index.
- R03 run 2 - PV-600: Drawing PV-600 is referenced in the question but is not listed in the supplied partial drawing index, which should be verified.
- R03 run 3 - PV-600: Drawing PV-600 is referenced in the question regarding conduit size, but it does not appear in the supplied partial drawing index.
- R05 run 1 - PV-600: Reference sheet PV-600 is not listed in the provided partial drawing index.
- R05 run 2 - PV-600: Drawing reference PV-600 cited in the RFI is not present in the supplied partial drawing index.
- R06 run 1 - A-503: Drawing A-503 listed in references is not present in the supplied partial drawing index.
- R06 run 2 - A-503: The reference sheet A-503 is listed in the RFI, but this specific sheet identifier does not appear in the provided partial drawing index.
- R07 run 1 - S-301: Reference S-301 is listed in the RFI but does not appear in the supplied partial drawing index.
- R07 run 2 - S-301: Drawing S-301 is listed in the references but does not appear in the supplied partial drawing index.
- R07 run 3 - S-301: Reference S-301 is listed in the RFI, but S-301 does not appear in the supplied partial drawing index.
- R09 run 1 - FP-200: Drawing reference FP-2O0 contains a letter O instead of a zero, which may not match drawing FP-200 in the index.
- R09 run 2 - FP-200: Reference FP-2O0 contains a letter O instead of a zero, which does not match standard drawing numbering and is absent from the partial drawing index (which lists FP-200).
- R09 run 3 - FP-200: Reference FP-2O0 contains a letter O instead of a zero and does not exactly match the partial drawing index sheet FP-200.
- R10 run 3 - FP-200: Drawing reference FP-200 is not found in the supplied partial drawing index, though this index may be incomplete.
- R14 run 1 - ID-015: Referenced drawing ID-015 is not present in the supplied partial drawing index.
- R14 run 3 - ID-015: Reference ID-015 is not found in the supplied partial drawing index.
- R17 run 2 - ID-015: Reference ID-015 is cited in the question but does not appear in the supplied partial drawing index.
- R19 run 2 - E-801: Reference E-802 is listed in the RFI, but does not appear in the supplied partial drawing index which only goes up to E-801 for electrical schedule sheets.
- R22 run 2 - A-703: Reference sheet A-7O3 appears to contain a letter 'O' instead of the number '0', which does not match the drawing index format.
- R23 run 2 - E-700: References E-700 and E-501 are cited in the RFI, but E-501 is missing from the supplied partial drawing index (though E-700 is present).

## Code + AI: what the AI said (run 1) - team to judge

- R02 (typo): The reference A-4O1 uses the letter 'O' instead of the number '0'.
- R03 (unrelated): Drawing PV-600 is mentioned in the RFI question as showing the 2-1/2" conduit, but it was omitted from the references section.
- R07 (unrelated): S-301 may not show this condition: The sheet title is DEEP FOUNDATION SCHEDULES, SECTIONS AND DETAILS, which is for structural foundations rather than flooring finishes.
- R07 (unrelated): Sheet S-301 is referenced for a flooring finish question, but it appears to be a structural foundation sheet.
- R09 (typo): Sheet reference FP-2O0 appears to use the letter 'O' instead of the number '0'.
- R17 (unrelated): FP-200 may not show this condition: The title is FIRE PROTECTION DETAILS AND SCHEDULE which is a different trade and system than interior architectural finishes.
- R17 (unrelated): Drawing ID-015 is referenced in the question text but is missing from the references list.
- R18 (unrelated): E-700 may not show this condition: The sheet title is ELECTRICAL DETAILS, which is a different trade and system from the architectural tile finishes asked about.
- R19 (nonexistent): Sheet E-802 mentioned in references and question was not recognized in the drawing index.
- R22 (typo): Sheet reference A-7O3 appears to contain a letter 'O' instead of a zero ('0').
- R23 (nonexistent): Drawing E-501 was not found in the drawing index and may be mistyped.
