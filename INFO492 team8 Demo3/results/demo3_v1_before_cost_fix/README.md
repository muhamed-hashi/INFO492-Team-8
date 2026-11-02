# Demo 3 evaluation, version 1 (before the cost/scope prompt change)

First full run: `python3 scripts/run_demo3_eval.py --runs 1`, 2026-10-31, gemini-3.5-flash-lite.

Kept unchanged so the before/after comparison is visible. After this run we changed ONE thing,
item 4 (possible_cost_or_scope) in `prompts/check_agent.txt`, because the check agent flagged 10 of 12
completed RFIs as possible cost/scope items. The new wording follows our interviewee's description of
RFIs that set up a change order ("the drawings do not show X, please confirm whether it is required"),
and treats "which of two conflicting documents applies" as a normal clarification.

The change was made after seeing results on the same 12 cases, so the second run is not an
independent test of the new prompt. Nothing else (data, other prompts, code) was changed.
