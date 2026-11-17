# Real examples from our stakeholder (in progress)

Our professor's feedback on Demo #3: the data is too clean. Real RFIs start as a text, a WeChat message, a photo
or a half-filled form, and answers come back just as rough. This folder is where our stakeholder's real examples
go once he shares them. **Status: requested, not received yet.** Until then the evaluation uses the Dett data
and the messier synthetic set (`../closeout_cases_messy.json`).

## What we asked for

1. 5–10 RFIs the way they first came in from subs (texts, screenshots, emails, photos, half-filled forms).
2. The formal RFI and the answer for each, if available.
3. An RFI log export from one project (status, dates, days open).
4. For 2–3 answered RFIs: what happened next (did the revised sheet arrive, was there a change order).

If sharing files is hard: a 15-minute call where he walks us through 3 messy RFIs; we type them up and he checks them.

## Privacy rules (read before adding anything)

- Originals (screenshots, emails, photos, logs) go only in `raw/` on the laptop of the person who received them.
  `raw/` is in `.gitignore`. **Never drag `raw/` into a GitHub upload**: the web uploader ignores `.gitignore`.
- Before any text goes into a CSV here, remove names of people, companies and projects, phone numbers, emails,
  addresses and prices. Replace them with roles: "the electrical sub", "Building A", "Room 2xx".
- List the real names you removed in `private_names.txt` (also ignored by git). `scripts/import_kevin.py` checks
  every CSV against that list and common patterns (phone, email, $, street address, links) and stops if it finds one.
- Nothing from this folder is published until our stakeholder has seen the anonymized version and said OK.

## How to add close-out examples

Fill `template_closeout.csv`, one row per answered RFI:

| Column | What to write |
|---|---|
| `case_id` | K01, K02, … |
| `source_format` | text, WeChat, email, photo, form, Procore |
| `question` | the RFI question, anonymized |
| `answer` | the answer exactly as received (messy wording is the point), anonymized |
| `issued_sheets` | sheets actually issued with or after the answer (bulletin, ASI, sketch log), separated by `;` |
| `expected` | **a person's** call: `ok_to_close`, `keep_open`, `hold` or `check` (definitions in `../../README.md`) |
| `labeled_by` | who labeled it (a team member's name, or "stakeholder") |
| `notes` | anything odd |

Then:

```bash
python3 scripts/import_kevin.py --check     # privacy check only
python3 scripts/import_kevin.py             # builds data/kevin/closeout_cases.json
python3 scripts/run_demo4_eval.py           # now also scores the "kevin" set
```

`template_first_messages.csv` is for the first messages from site (sub → GC). It will feed the Demo #3 drafting
evaluation; `missing_items` lists what a GC had to ask for (location, date, impact, sheet), labeled by a person.
