# Data provenance and synthetic-data justification (Demo #3)

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
