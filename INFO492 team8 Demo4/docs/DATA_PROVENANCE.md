# Data provenance and synthetic-data justification (Demo #4)

Demo #4 reuses all Demo #3 data unchanged and adds two files; see [Demo #4 additions](#demo-4-additions) at the end.

## Source project (real)

Robert Nathaniel Dett Elementary School Annex and Renovations, Chicago. Public Building Commission of
Chicago, Contract C1604. Bid documents and the six addenda are public:
<https://pbcchicago.com/opportunities/advertisement-for-bids-contract-c1604-robert-nathaniel-dett-elementary-school-annex-and-renovations/>

| File | What | Real or simulated |
|---|---|---|
| `data/source_rfis.csv` | All 108 RFIs from Addenda 1–6, question and architect response verbatim | Real (copied from Demo #2) |
| `data/drawing_index.json` | 206 drawing sheets with titles and the addendum page they come from | Real (copied from Demo #2) |
| `data/revisions.json` | Which sheets were issued or revised in each addendum | Real, built by `scripts/build_revisions.py` |
| `data/rough_rfis.json` | 12 rough field RFIs (F01–F12) | **Simulated**, see below |
| `data/rough_answer_key.json` | What each rough RFI is missing | Written by the team; never sent to an agent |
| `data/users.json` | Five demo users with roles | Fictional people and companies |

### Limitation of `revisions.json`

`extract_addenda.py` (Demo #2) kept only the first drawing list that contains each sheet. A sheet re-issued in
a later addendum is only recorded when an architect's response says so (for example "refer to revised
Drawing E-301 included in this addendum"). So the watch agent sees fewer revisions than really happened,
never more. E-301 (revised in Addenda 1, 2 and 3) and E-600 (Addenda 1, 2 and 3) are recorded fully.

## Why the RFIs are simulated, and how

The Dett RFIs are bid-stage questions from bidders to the architect. Our thesis is about construction-stage
RFIs from a subcontractor to the GC, and construction RFI logs are not public.

Demo #2 used complete, cleanly written RFIs. Our stakeholder interview (an assistant PM at a small GC; see
`interviews/` in the repo root) said real construction RFIs are rougher: often a short text and a photo,
most often missing the **location**, then the **response date** and the **impact**, with sheet numbers that
are present but imprecise or from an older drawing set. That is one interview at a small company, so we
used only the points that match our own Demo #2 data and published industry figures, and did not build
anything specific to that company (for example its messaging apps or languages).

Each rough RFI (F01–F12):

1. Starts from one of the same 12 real Dett RFIs used in Demo #2 (`source.id`), keeping the real problem and
   real sheet numbers.
2. Is rewritten as a short message a foreman might send from site (AI-assisted drafting, reviewed by the team).
3. Leaves out some of location, response date and impact, as the interview described; 23 missing items in total.
4. Has a reference problem in 6 of 12: a sheet revised after the foreman's drawing set (2, using real
   revision data), a non-existent sheet (A-102), a typo (FP-2O0 with the letter O), no sheet number, or a
   needed sheet not cited (2).
5. Includes 2 complete controls (F04, F11) that should not be flagged.
6. Has `site_notes`: the location, date and impact the foreman knows. In the evaluation, the foreman answers
   the agent's questions from these notes. They come from Demo #2's complete versions (team-written, not
   facts about the real project).

The prompts were written without the test messages' wording: they describe kinds of problems (a vague
place, a word like "asap" instead of a date, a mistyped sheet number) without using any phrase from F01–F12.

Generation is deterministic: `python3 scripts/generate_rough_rfis.py`.


## Demo #4 additions

| File | What | Real or synthetic |
|---|---|---|
| `data/addendum_drawing_lists.json` | Every drawing attached to each of Addenda 1–6 (90, 130, 159, 0, 19 and 14 sheets), with item number, title, date and PDF page | **Real**, extracted by `scripts/extract_drawing_lists.py` from the six public addendum PDFs |
| `data/closeout_cases.json` | 40 tidy close-out test cases with a known right answer | **Synthetic variants of real answers**, built by `scripts/make_closeout_cases.py` |
| `data/closeout_cases_messy.json` | 40 harder cases: field-style wording, 10 with two problems | **Synthetic variants of real answers**, built by `scripts/make_messy_cases.py` |
| `data/kevin/` | Real examples from our stakeholder, anonymized and labeled by the team | **Real** (requested, not received yet); privacy rules in [`data/kevin/README.md`](../data/kevin/README.md) |

### The drawing lists (real)

Each addendum has a section "This Addendum includes the following attached Drawings:" with numbered items such
as `106. E-304, THIRD FLOOR LIGHTING PLAN - CLRM WING, dated 05/26/2023`. The script keeps every item and stops
if the item numbers do not run 1..N without gaps (they do for all six). Unlike `revisions.json`, nothing is
inferred from RFI answers, so the close-out agent can check an answer against an independent source.

Each addendum also states: "Drawings/specifications corresponding to inquiry responses will be issued with the
Issue for Construction Documents, upon issuance of building permit." This is why "keep open: carry to the IFC
set" is a real close-out outcome, not one we invented.

Limit: a sheet appearing in a drawing list shows it was **issued** in that addendum, not that the specific change
was drawn on it. Addendum 2 re-issued 130 sheets at once, so "issued" is a necessary check, not proof. Confirming
the drawn change still needs a person (or a drawing comparison, which this demo does not do). For the same reason
we did not replace Demo #3's `revisions.json` with these lists: treating every re-issued sheet as "revised" made the
watch agent raise 7 alerts on 6 of the 12 test RFIs at Addendum 2 alone (Demo #3 data: 2).

### The real RFI log (real, no answer key)

The Close-out tab shows the 108 real answered RFIs in `data/source_rfis.csv`. The Dett RFIs are **bid-stage**
questions from bidders, answered in addenda; we use them as the project's answered-RFI log. We have no answer key
for them; flagged ones are listed in `results/demo4/real_flags_for_review.csv` for the team to judge by hand.

### The 40 tidy test cases (synthetic variants with known answers)

Every case starts from a real answer whose revised sheets really are in that addendum's drawing list (70 such
answers; checked by code). 12 are kept unchanged and 28 get exactly one planted change. The right answer comes
from how the case was built, so no person or AI labels them:

| Kind | n | What was changed | Right answer |
|---|---|---|---|
| clean | 12 | nothing | ok to close |
| see_also | 6 | a sentence referring to a real sheet that is not in this addendum ("Coordinate with E-205.") | ok to close (only referred to) |
| missing | 8 | the revised sheet removed from this case's copy of the addendum drawing list | hold |
| deferred | 8 | the sentence saying the sheet was revised rewritten to say the revision comes later (8 different sentences, written by the team; some avoid every word the code baseline looks for) | keep open |
| typo | 6 | the sheet number in the answer mistyped (two digits swapped, or a suffix letter added or dropped) | check |

The agent's prompt does not contain any of the planted sentences. Generation is deterministic (seed 492);
a test checks that rerunning the script gives the identical file.

### The 40 messy test cases (added after professor feedback)

Our professor said the tidy set (and Demo #3's "0 errors") looked too clean. The messy set keeps the same rule
(every case starts from a real answer whose revised sheets really are in the drawing list, so the right answer is
known by construction) but makes the text look like what a PM actually receives:

- **Noise on every case** (team-written rules in `scripts/make_messy_cases.py`): "Drawing" → "dwg"/"sht",
  "revised" → "rev'd"/"rev.", "included in this addendum" → "incl. in this add."/"attached", sheet numbers written
  as `E304`, `e-304` or `E- 304`, 40% of answers in lower case, and a chatter sentence ("pls coordinate w/ GC").
- **One or two problems**: 10 clean, 5 see-also, 5 missing, 5 deferred (field-style wording such as
  "updated A-421 to follow", "E-801: changes pending, not attached"), 5 typos, and 10 with two problems
  (missing + see-also, typo + see-also, deferred + missing).
- With two problems, the right answer follows one fixed priority: keep open > hold > check > ok to close.
- Every sheet named in a case can still be found by code (otherwise the case would test the parser, not the
  reading). Each case uses a different real answer (40 of the 70 eligible).
- The agent and the baseline were not tuned on these cases. The four code fixes made after the first run
  (guard drop → check, "P- 500" spacing, sheet numbers given without letters, SD-300 vs S-300) were made because of
  the first run's real-log results, before this set was built.

### Stakeholder examples (`data/kevin/`, in progress)

We asked our stakeholder for 5–10 real RFIs as they first arrived, the answers, an RFI log and what happened after
the answer. Originals stay off GitHub (`raw/` is git-ignored); only anonymized text goes into the CSV templates, a
person labels the right answer, and `scripts/import_kevin.py` refuses to build the test set if its privacy check
(names list, phone, email, $, street address, links) finds anything. When `data/kevin/closeout_cases.json` exists,
`scripts/run_demo4_eval.py` scores it as a third set.

### Second real log: GWA "Response to RFI No. 1" (real, with our stakeholder's problem list)

After the professor's "real, messier data" feedback, our stakeholder could not share his own RFIs (they sit in
private chats) but sent a **public** RFI response document and his own **problem list** for it.

- Document: Guam Waterworks Authority, Hagåtña WWTP Rehabilitation, IFB-06-ENG-2026, "Response to RFI No. 1"
  (44 questions from bidders and the engineer's answers, July 2026), published by GWA:
  <http://guamwaterworks.org/wp-content/uploads/2026/07/RFI_No._1_for_IFB-06-ENG-2026.pdf>. Public, so the PDF and
  the extracted text can go on GitHub; no private data.
- Extraction: `scripts/parse_gwa.py` (pdfplumber) → `data/gwa/rfi1_items.json`: item no., printed date, question,
  answer, page. 20 questions paste in a picture of the report they ask about, and item 37's answer is partly a
  picture; those pictures are read with OCR (tesseract) and kept in separate fields so typed text and OCR text are
  never mixed up. OCR has reading errors (for example item 4); we keep them, that is what a tool would get.
- Messiness is real, not planted: no printed date on 30 of 44 items, several questions in one item, answers that only say
  "refer to past plans", answers deferred to "bid opening", the same answer sentence given to two different
  questions, an answer that deletes scope, pictures instead of text.
- Answer key: `data/gwa/stakeholder_problem_list.csv`, our stakeholder's list (38 rows: item, issue type, evidence).
  He listed problems on 37 of the 44 items; 7 items (12, 21, 24, 30, 31, 34, 41) have none. Where his list and the
  printed PDF disagree on a plain fact, we report both and do not change his list: items 4 and 29 are on his
  "no date" list but carry printed dates (6/29/26, 6/30/26).
- Which of his issue types our check is meant to find is set by fixed keyword rules on his `issue_type` column
  (`CATEGORIES` in `scripts/run_gwa_eval.py`), not item by item. His other issue types (unclear scope, contradicting
  specifications, duplicate questions, typos, drawings never issued) are outside the check and reported as such.
- Not a blind test: the answer check (`closeout.answer_check`, `prompts/answer_check.txt`) and the code baseline's
  keywords were written after we had seen his list and this document. The prompt contains no item text or project
  words, but the keyword baseline in particular is optimistic here. A blind test needs a log he has not shown us.
