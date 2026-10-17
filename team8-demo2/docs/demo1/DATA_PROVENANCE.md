# Data provenance and generation justification

## Project lens

Robert Nathaniel Dett Elementary School Annex and Renovations, Public Building Commission of Chicago, Contract C1604. The team's selected project is the context for the prototype; the bundled inputs are **simulations**, not a complete project dataset or a construction-stage RFI log.

Primary source portal:
<https://pbcchicago.com/opportunities/advertisement-for-bids-contract-c1604-robert-nathaniel-dett-elementary-school-annex-and-renovations/>

Source PDFs inspected for this package:

- [Addendum 5, June 9, 2023](https://pbcchicago.com/wp-content/uploads/2023/06/AD_PBC_PXM_RNDettESAnnexandRenoC1604_AddendumNo5_20230609_Final.pdf)
- [Addendum 6, June 15, 2023](https://pbcchicago.com/wp-content/uploads/2023/06/AD_PBC_PXM_RNDettESAnnexandRenoC1604_AddendumNo6_20230615_Final.pdf)

Page numbers below are PDF pages counted from 1. Original RFIs in these addenda are **bid-stage questions and published responses**. Their references ground the scenario topics, not the invented operational circumstances.

| Case | Source | Topic, paraphrased | Fields intentionally removed |
|---|---|---|---|
| D01 | Addendum 5, RFI 2, PDF p. 2 | Camera specification | Location; response-needed date |
| D02 | Addendum 5, RFI 3, PDF p. 2 | Conflicting countertop notes | Drawing references |
| D03 | Addendum 5, RFI 7, PDF p. 3 | Existing/new plumbing scope | Effect on work |
| D04 | Addendum 6, RFI 2, PDF p. 2 | Conflicting PV conduit information | Response-needed date |
| D05 | Addendum 6, RFI 3, PDF p. 2 | Metering detail | Trade |
| D06 | Addendum 6, RFI 4, PDF p. 2 | Item beside the sink | None; complete-field control |

The team must check these pilot annotations before collecting experiment data. A missing field is not automatically a missing fact: the question itself might already supply it. Inferred trade labels are a particular source of legitimate disagreement.

## What is real and what is simulated

**Grounded in the sources:** project identity, selected issue topics, cited sheet identifiers, and brief evaluator-only summaries of published responses.

**Created for the exercise:** construction-stage framing, trade assignment, needed-by date `2026-10-23`, generic work-planning impact, some generalized location descriptions, the submitted draft wording and deliberate omissions. These are not claims about what happened on the project. The date is a fixed reproducible exercise value, not an inferred contractual deadline. No contractual risk score is supplied because a controlling contract and project facts have not been established for this simulation.

`brief.known_details` supplies the participant with the same available facts in both conditions. The AI receives only the draft form and the partial drawing identifier list. Historical design responses and expected missing-field labels remain in the evaluator file and are not sent to the model or served through the browser.

## Reproduction

Run from the repository root:

```bash
python3 scripts/generate_data.py
```

The script holds six short, manually prepared source paraphrases. It creates a complete simulated form for each one, removes the specified fields, then writes `cases.json`, `answer_key.json` and `drawing_index.json`. Generation is deterministic and makes no LLM calls. Rerunning overwrites those three files.

This method makes omissions inspectable and allows controlled tests without claiming access to private correspondence. It may make detection easier than in real RFIs. Later work should add genuinely ambiguous questions, information stated in the wrong field, unfamiliar references and independent cases, while keeping those changes labeled.

## Reference matching limitation

The 13-entry drawing index comes from selected references and revision lists in the two addenda. It is not a complete or authoritative drawing register. A match means the sheet identifier was observed there. It does not establish technical relevance, correct revision, or that a detail resolves the RFI. A missing match means only “not found in this partial index.”

## Research vs evidence of effectiveness

The team thesis cites [Procore's RFI guide](https://www.procore.com/library/rfi-construction), [Procore's AI drafting documentation](https://support.procore.com/products/online/user-guide/project-level/rfi/tutorials/draft-an-rfi-with-assist), and [Chin's 2009 information-flow paper](https://www.iglc.net/papers/details/629). They are background references, not evidence that this prototype has achieved a 25% improvement. The program's measured effect must come from the team's own logged tests. Software documentation: [Gemini generateContent](https://ai.google.dev/api/generate-content) for the default provider, and [Responses structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses) for the optional OpenAI adapter.
