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
