# Evaluation

Demo #4 (close-out) is first; the Demo #3 evaluation it builds on follows unchanged.

## Demo #4: close-out

### What it tests about the thesis

Thesis (updated after Demo #3): "Adding an AI review step to an existing subcontractor RFI form can reduce median
GC first-review time by at least 25% and reduce follow-up rounds to the subcontractor, compared with the same form
completed without AI assistance, without increasing information errors from submission through close-out."

Demo #3 tested the first part with GC reviewers. Demo #4 tests "without increasing information errors ... through
close-out": an answer that promises a revised drawing, closed before that drawing is issued, is an information
error that reaches the field.

### Errors at two points (after professor feedback on "0 errors")

Demo #3 reported "0 errors reached the GC", which hid that the AI did make mistakes (a wrong sheet number in R04,
a false alarm in R09) that the subcontractor caught before sending. Demo #4 reports both points:

| Point | Measure | Why it matters |
|---|---|---|
| 1. The agent's recommendation, before any person looks | **right recommendation**; **missed problems** (should not be closed, recommended "ok to close"); **false alarms** (fine, but not "ok to close") | missed problems are the dangerous errors; false alarms cost the PM time. Our interviewee: a tool that is wrong 3 times in 10 stops being read |
| 2. What would reach the field if the PM followed every recommendation | missed problems only | "check" and "hold" always go to a person, so those mistakes are caught at the PM step (`wrong_but_caught_by_pm`). On the real log we can only see misses among RFIs that one method stopped and the other did not |

The guard counts AI claims it dropped (sheet or quote not in the answer); since the fixes after the first run, any
drop turns an "ok to close" into "check", so a partial reading never closes an RFI silently.

### Data (real first)

The course asks for real industry data, no synthetic data, so the headline numbers come only from real documents.

| Set | Size | Real? | Right answer from |
|---|---|---|---|
| **Dett RFI log** | 108 answered RFIs | real (public bid documents, PBC Chicago 2023) | for every RFI the code check or the agent stops: **our stakeholder's call** (a GC assistant PM), made during his Demo #4 test from the answer, the addendum page and the tool's reasons (`scripts/make_review_sheet.py`, `data/dett_labels/labels.csv`) |
| **Stakeholder examples** | when received | real (our stakeholder's projects, anonymized) | labeled by the stakeholder or the team (`data/kevin/`) |
| tidy, messy | 40 + 40 | synthetic stress tests (real answers with planted problems) | by construction; run only with `--synthetic`, reported separately |

What this can and cannot show: the stakeholder review measures **false alarms on real data** (how many stops a PM
would call unnecessary) and which stops are real problems. It cannot measure **misses** (problems both methods let
through), because the RFIs nobody stopped are not reviewed; labeling all 108 by hand was beyond our time. Seeing the
tool's reasons may also lead the reviewer to agree more readily; we ask him for his own call, not a yes/no.

Categories he chooses from: *ok to close* (the answer changes no drawing, or every sheet it says was revised is in
that addendum's drawing list; a specification-only change counts as ok); *keep open* (something is still to come);
*hold* (a sheet it says was revised is not in the list); *check* (cannot tell).

Run: `python3 scripts/run_demo4_eval.py` (2 AI runs over the 108 real RFIs, about 220 Gemini calls) or
`--code-only`; `--synthetic` adds the stress tests. Output: `results/demo4/`. The first run (tidy set only, before the fixes) is kept in
`results/demo4_run1_clean_set/`. Case construction: [DATA_PROVENANCE.md](DATA_PROVENANCE.md#demo-4-additions).

Limits: the problems in both synthetic sets were planted by the team, so they show whether the agent can tell these
situations apart, not how often they happen; the noise rules are ours, not a sample of real writing (that is what
the stakeholder examples are for); "issued in the drawing list" is a necessary check, not proof the change was drawn.

### Second real set: did the answer actually answer? (GWA log, 44 items)

Our stakeholder's main complaint is back-and-forth. Close-out above asks "was the promised drawing issued?"; on
the GWA log we ask the question before it: **did the answer actually answer, or will this RFI come back?** The
**answer check** lists every separate thing a question asks (AI, with a quote from the question for each) and
whether the answer answered it, only partly, only pointed elsewhere, deferred it, or did not address it (with a
quote from the answer); it also says whether the answer changes scope (quote required). The guard drops any quote
that is not in the text, and any drop turns "ok to close" into "check". Code adds: no date, the same answer sentence
given to two different questions. Recommendation: *check* if anything is not fully answered or the scope changed,
else *ok to close*; intake flags (no date, several questions, copied answer) are shown but do not stop closing.

Right answer: not the problem list that came with the data set. A teammate made it with an AI tool, so agreement
with it only shows two AI readings agree; we report it as a reference (agree / not flagged / flagged, not on the list).
The answer key is **our stakeholder's blind call** on 12 items (question and answer only, no tool output) chosen by a
fixed rule where the list and our agent disagree: the list calls an answer problem but the agent closed it, the list
finds the item fine but the agent stopped it, and 6 random others. Per method we then report how many he says need a
person, how many of those it stopped, what it missed, and what it stopped that he would close; the same for the
AI-made list. Because the sample is disagreements, this shows which reading was right where it matters, not
accuracy over the whole log.

Run: `python3 scripts/run_gwa_eval.py` (2 AI runs, about 88 Gemini calls) or `--code-only`; `--rescore` re-scores
the saved log. Output: `results/gwa/`. Data and the not-blind caveat: [DATA_PROVENANCE.md](DATA_PROVENANCE.md#second-real-log-gwa-response-to-rfi-no-1-real-with-our-stakeholders-problem-list).

Limits: 44 items from one document; 12 human-judged items; the check was built after seeing the document and the
AI-made list; OCR of pasted pictures is imperfect.

# Demo #3 evaluation

## What it tests about the thesis

The thesis has two parts: faster GC first review, and no added information errors. Demo #3 tests the
"improve the draft" step and adds a measure our interview suggested: **round trips**. The interviewee said a
simple first review takes 5–10 minutes, but going back to the subcontractor costs one to two days.

| Question | Measure | Where |
|---|---|---|
| Does drafting catch what the GC would otherwise send back? | missing items asked about (of 23); RFIs that still need a return | `run_demo3_eval.py` |
| Does the agent add errors? | values the AI filled in that the message does not say (blocked by the guard, counted); questions asked about things already in the message (false asks) | `run_demo3_eval.py` |
| Does it beat a simple checklist? | the same measures for the checklist-only version | `run_demo3_eval.py` |
| Does the GC agent send good RFIs back? | "return" recommendations on completed RFIs (false returns) | `run_demo3_eval.py` |
| Is GC review faster? | time to decide and "go back to sub" rate, rough vs agent-drafted, by real people | `/study` page |
| Does the system help in use? | returns, alerts marked useful or wrong, escalations, edits to agent text | control panel |

## Offline evaluation (`python3 scripts/run_demo3_eval.py`)

For each of the 12 rough RFIs (`data/rough_rfis.json`):

1. **As sent:** the GC receives the rough message. It needs a return if the answer key lists any gap.
2. **Checklist only:** code looks for a date, location and impact keywords, and sheet numbers; it asks for the rest.
3. **Draft agent:** code looks up sheets and revisions; the AI rewrites the question and asks for what is missing;
   the guard removes unsupported values.

After 2 and 3, the foreman answers exactly what he was asked, from his site notes. An RFI still needs a
return if any gap in the answer key was not asked about. Then the check agent reviews each completed
draft-agent RFI; a "return" on a complete RFI is a false return. The watch agent replays Addenda 1–6.
Default: 2 runs of the AI parts.

## Timed review study (`/study`)

Reviewers play the GC. Each sees all 12 RFIs once: half as the rough message and half as the agent-drafted,
foreman-approved version (odd and even reviewer numbers get opposite halves, so each RFI is seen both ways).
The page records seconds to a decision and the decision: send to the architect, or go back to the sub.

Limits to state with any result: reviewers are classmates, not GCs; the agent-drafted version also contains
the foreman's answers, so the comparison is "rough message" vs "agent-assisted, foreman-approved RFI";
12 items and a few reviewers is a small pilot, not a test of the 25% target.
