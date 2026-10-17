# Data provenance and synthetic-data justification (Demo #2)

Demo #2 uses two sets of simulated RFIs, both built from the same 12 real Dett RFIs:

- **`data/reference_cases.json` (R01–R24): the main Demo #2 test, "check references".** See *Reference cases* below.
- `data/cases.json` (D01–D24): 24 general cases used in Demo #2's first run (all fields), described in the rest of this note.

Demo #1's six cases are kept unchanged in `data/demo1/`, with their own note in [docs/demo1/DATA_PROVENANCE.md](demo1/DATA_PROVENANCE.md).

## Source project

Robert Nathaniel Dett Elementary School Annex and Renovations, Chicago — Public Building Commission of Chicago (PBC), Contract C1604, completed 2024. All bid documents are public:
<https://pbcchicago.com/opportunities/advertisement-for-bids-contract-c1604-robert-nathaniel-dett-elementary-school-annex-and-renovations/>

| Addendum | Date | Real RFIs | PDF |
|---|---|---|---|
| 1 | 2023-05-23 | 7 | [link](https://pbcchicago.com/wp-content/uploads/2023/05/AD_PBC_PXM_RNDettESAnnexandRenoC1604_AddendumNo1_20230523_Final.pdf) |
| 2 | 2023-05-30 | 17 | [link](https://pbcchicago.com/wp-content/uploads/2023/05/AD_PBC_PXM_RNDettESAnnexandRenoC1604_AddendumNo2_20230530_Final.pdf) |
| 3 | 2023-06-05 | 68 | [link](https://pbcchicago.com/wp-content/uploads/2023/06/AD_PBC_PXM_RNDettESAnnexandRenoC1604_AddendumNo3_20230605_Final.pdf) |
| 4 | 2023-06-06 | 0 | [link](https://pbcchicago.com/wp-content/uploads/2023/06/AD_PBC_PXM_RNDettESAnnexandRenoC1604_AddendumNo4_20230606_Final.pdf) |
| 5 | 2023-06-09 | 11 | [link](https://pbcchicago.com/wp-content/uploads/2023/06/AD_PBC_PXM_RNDettESAnnexandRenoC1604_AddendumNo5_20230609_Final.pdf) |
| 6 | 2023-06-15 | 5 | [link](https://pbcchicago.com/wp-content/uploads/2023/06/AD_PBC_PXM_RNDettESAnnexandRenoC1604_AddendumNo6_20230615_Final.pdf) |

## What is real

- `data/source_rfis.csv`: all **108** RFIs, verbatim question and architect response, with addendum, RFI number and PDF page. Extracted by `scripts/extract_addenda.py` (needs `pip install pypdf` and the six PDFs).
- `data/drawing_index.json`: **206** drawing sheets. 199 come from the "attached Drawings" lists in the addenda (with sheet title and date); 7 more are sheets cited in RFI text. Each entry links to its PDF page. Demo #1 used a 13-sheet partial index, so wrong sheet numbers could not really be checked.

## Why we simulate, and how

The real RFIs are **bid-stage** questions from bidders to the architect. Our thesis is about **construction-stage** RFIs from a subcontractor to the GC, and we have no access to a real project's construction RFI log. We also need cases where we *know* what is missing, so we can score the checker. So we rewrite real RFIs into the sub → GC format, following the rules in our thesis document:

1. **Keep the same problem and drawing numbers.** Each case links to its source RFI and keeps the original question in `source.original_question`.
2. **Add what a subcontractor would include**: location, trade, response-needed date, impact. These are **written by our team** and are not facts about the real project. Location wording comes from the real RFI where it named one.
3. **Make some versions with missing or wrong information.** Each of the 12 seed RFIs has a complete version and a defective version, giving 13 planted defects across location, response date, impact, question clarity and references.
4. **Make Demo #2 harder than Demo #1.** In Demo #1 every defect was a blank field, and a simple checklist found all of them, so the test could not show whether the AI adds anything. Here the defects range from obvious (blank, "TBD", "ASAP", a non-existent sheet such as S-306) to subtle ("Next week", "Second floor bathroom", "Could cause problems later.", a non-specific question).
5. **Include tricky complete versions** that a naive checklist would wrongly flag: a blank location field where the room is named in the question, and a short but specific question ("Is RT-1 flooring the same as RT-11?").
6. **Mark every case `is_simulated: true`** and link it to the original RFI.

Generation is deterministic (`python3 scripts/generate_data.py`, fixed shuffle seed 492, no LLM), so anyone can reproduce the exact files. The defect labels live only in `data/answer_key.json`, which is never sent to the AI or shown in the app.

**Why this is a fair test of the thesis:** the thesis says the AI step removes the reasons a GC would send an RFI back, without adding errors. Planting known reasons-for-return in otherwise realistic RFIs lets us measure both: how many the AI catches, and how often it flags fine content or invents references.

## Reference cases (R01–R24)

Built by `scripts/generate_reference_cases.py` (deterministic, no LLM) from each seed's complete form:

- **12 clean cases** keep the real sheet numbers from the source RFI.
- **12 cases with one reference problem**, of four kinds:

| Kind | Cases | What we changed | Example |
|---|---|---|---|
| nonexistent | 3 | One sheet number changed to a number not in the drawing index | S-101 → S-103 |
| typo | 3 | A letter O typed for a zero in the references field | FP-200 → FP-2O0 |
| unrelated | 4 | One sheet replaced by a real sheet whose title has nothing to do with the question | ID-015 (floor finish plans) → FP-200 (fire protection) for a flooring question |
| vague | 2 | Sheet numbers replaced by text with no sheet number | "Per electrical plans" |

These are mistakes a subcontractor can realistically make when filling in an RFI form. The first two can be caught by looking a number up; the last two need someone to read the question and the sheet title, which is why they test whether the AI adds anything over code. Each case's brief lists the correct references, and the labels are only in `data/reference_answer_key.json`, which is never sent to the AI or shown in the app.

## Real items (T01–T10) and adversarial cases (X01–X02)

For the Week 3 Evaluation Lab, `scripts/select_real_items.py` draws 10 **real** RFIs from `data/source_rfis.csv` with a fixed seed: 7 whose question cites a sheet number and 3 whose question cites none, excluding the 12 seeds used for simulated cases. The question is used verbatim; the references field holds the sheet numbers the question itself cites (as a subcontractor copying from their own question would). Other form fields are blank because the bid-stage RFIs had no such fields. These items carry **no labels from us**: two team members label them separately in `eval/`.

The 2 adversarial cases are **simulated** from two seeds. Each adds a real reference problem (a nonexistent sheet; an unrelated sheet) plus text aimed at the AI telling it not to flag anything. Their labels are known by construction (both `problem`).

## Limitations

- Construction-stage details are simulated; real subcontractor RFIs may be messier.
- Labels are our team's judgment; another reviewer might disagree on borderline cases.
- 24 cases from 12 seeds is a small sample, all from one project.
- The full original drawing set was not available, so a real sheet could be missing from the index.
- 7 of the 206 index entries are known only because an RFI cites them (no title). For an RFI that cites such a sheet, "in the index" is not independent confirmation; the labeling sheet says so.
- The same team wrote the reference cases and the AI prompt. The prompt does not mention the planted examples, but the team knew the four kinds of problem when writing it.
- Demo #2 measures the checker, not GC review time.
