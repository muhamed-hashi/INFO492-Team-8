# Post-hoc: drawing references judged by code only

Designed after seeing the Demo #2 results. Re-scores the saved AI outputs; no new AI calls.

| Run | AI as run: found | false alarms | complete RFIs flagged | Code-only references: found | false alarms | complete RFIs flagged |
|---|---|---|---|---|---|---|
| 1 | 11/13 | 6 | 4/12 | 11/13 | 1 | 1/12 |
| 2 | 12/13 | 7 | 5/12 | 12/13 | 1 | 1/12 |
| 3 | 11/13 | 6 | 5/12 | 11/13 | 1 | 1/12 |

## AI "references" findings that the code lookup contradicts (sheet is in the index)

- D03 run 2: "Drawing reference PV-600 is listed in the references but does not appear in the supplied partial drawing index." (in index: PV-600)
- D05 run 1: "Drawing PV-600 is referenced in the RFI but does not appear in the supplied partial drawing index." (in index: PV-600)
- D05 run 2: "Drawing PV-600 referenced in the RFI is not present in the supplied partial drawing index." (in index: PV-600)
- D05 run 3: "Drawing reference PV-600 is listed in the RFI and appears in the partial drawing index, while E-600 also appears in the index." (in index: E-600, PV-600)
- D06 run 1: "Reference A-503 is listed in the RFI but does not appear in the provided partial drawing index." (in index: A-503)
- D06 run 2: "Reference A-503 is listed in the RFI, but check whether it is present in the supplied partial drawing index." (in index: A-503)
- D07 run 1: "Drawing A-503 is referenced in the RFI but is missing from the supplied partial drawing index." (in index: A-503)
- D07 run 2: "Referenced sheets A-502 and A-503 do not appear in the supplied partial drawing index." (in index: A-502, A-503)
- D07 run 3: "Referenced sheets A-502 and A-503 do not appear in the provided partial drawing index." (in index: A-502, A-503)
- D11 run 1: "Detail 6/A-703 is mentioned in the question text as a reference, but only sheets A-210 and A-703 are listed in the references field." (in index: A-210, A-703)
- D11 run 2: "References list sheets A-210 and A-703, but specific detail numbers mentioned in the question (such as detail 1 and detail 6) are omitted from the formal references field." (in index: A-210, A-703)
- D11 run 3: "The references list sheet A-703 but omit the specific detail number referenced in the question text." (in index: A-703)
- D13 run 3: "The references E-301 and E-801 appear in the supplied drawing index, but human verification should confirm they are the most current sheets depicting the cove fixture tags." (in index: E-301, E-801)
- D14 run 2: "Drawing ID-015 is referenced in the RFI but does not appear in the provided partial drawing index." (in index: ID-015)
- D14 run 3: "Drawing ID-015 is referenced in the RFI but does not appear in the supplied partial drawing index list." (in index: ID-015)
- D17 run 1: "Reference ID-015 is not present in the supplied partial drawing index." (in index: ID-015)
