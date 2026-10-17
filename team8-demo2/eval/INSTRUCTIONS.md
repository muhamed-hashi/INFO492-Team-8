# Step 2: Build the answer key

Two people label the same 10 real Dett RFIs **separately**: no talking about the items, no looking at each other's file, and no looking at the AI first. About 15 minutes each.

- Labeler A fills `eval/labeler_A.csv`, labeler B fills `eval/labeler_B.csv`. Open it in Excel, Numbers or Google Sheets and save or export it as CSV with the same name.
- Keep the columns as they are.

## The question for each row

> Imagine you are the GC's reviewer. From this RFI's drawing references, could you find the drawing(s) the question is about?

Write exactly one word in `label`:

| label | When |
|---|---|
| `ok` | The cited sheet number(s) exist and fit the question. |
| `problem` | A sheet number is missing, does not exist, looks mistyped, or clearly does not fit the question. |
| `unclear` | You cannot decide from what is shown. |

If you write `problem`, add a short `problem_kind`: `missing`, `nonexistent`, `typo`, `unrelated` or `other`. Use `note` for your reason; it helps in the next step.

`sheet_titles_from_index` shows what our 206-sheet drawing list says about each cited sheet. The list came from the addenda, not the full drawing set. The source PDF of each RFI is in `data/real_items.json` (`url`, `pdf_page`).

## Then: agree on the right answers

1. Run `python3 scripts/build_answer_key.py`. It writes `eval/answer_key.csv` with both labels side by side and shows where you disagree.
2. Where you disagree (or someone wrote `unclear`), talk it through, **agree on what counts as right**, and type the agreed `ok` or `problem` in `final_label`, with one line in `resolution_note`. Rows you already agree on are filled in for you.
3. Keep this file: the worksheet says you will use the answer key again in Demos #3 and #4.
