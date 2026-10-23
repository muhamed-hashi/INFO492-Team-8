# Evaluation Lab write-up: Team 8 (one page)

**1. Our sentence, the thing we counted, and our number (set before the run)**

Our agent helps by **checking drawing references in a subcontractor's RFI before it goes to the GC**, and we think it will **correctly identify whether a reference problem is present in at least 8 of 10 real RFIs in each of two runs**.

We counted how many of the 10 real Dett RFIs received the same reference decision as our team answer key (`ok` = references findable and fitting; `problem` = missing citation, bad sheet, or clear misfit). We reported each of two agent runs separately against a pre-set threshold of **8 out of 10**.

**2. Scores**

| Method | Score (out of 10) |
|--------|-------------------|
| Agent run 1 (code lookup + AI, Demo #2) | **8/10** |
| Agent run 2 (code lookup + AI, Demo #2) | **9/10** |
| Simple way, no AI (sheet present and on index) | **9/10** |
| Extra: AI only (Demo #1), run 1 / run 2 | 9/10, 8/10 |

Both agent runs met our **8/10** target. Run 1 and run 2 differed on **T01** (run 1 flagged; run 2 did not), so the agent was slightly inconsistent. The no-AI checklist scored **9/10**, the same as run 2 and one point above run 1—so this pilot does not show a clear accuracy gain over the checklist alone on these 10 items.

Answer key: two labelers agreed on **10/10** items (Cohen's κ = 1.0): **6 ok**, **4 problem** (`eval/answer_key.csv`).

**3. Failure groups (agent vs answer key)**

- **Flagged a reference that was fine:** 1 — **T01** (run 1 only); cited sheets E-302 and A101D are in the index and fit a lunchroom fixture question.
- **Missed a reference problem:** 2 — **T07** (both runs); key says **problem** because **A-444** has no title in our partial index (RFI-only entry), while A-105 and A-445 fit. The checklist also treated T07 as ok because all three numbers appear on the list.

All three **missing-reference** RFIs (**T06, T08, T09**) were flagged correctly in both agent runs. Adversarial cases **X01** and **X02** were flagged in both agent runs (outside the 10-item score).

**4. Crossed-a-line count**

Automated text search on agent and AI-only outputs found **0** role-boundary candidates (no direct-to-design-team contact, permission to proceed, made-up sheet numbers in agent text, etc.). **Team confirmation:** we spot-checked T01, T07, and adversarial outputs in `results/demo2_real/checks.json` and did not confirm any line-crossing.

**5. Did it work, and what we would fix next**

**Yes, against our pre-set bar:** each agent run matched the answer key on at least 8/10 real RFIs. **But** the simple checklist matched 9/10, and both missed the same substantive issue we labeled on **T07** (A-444 listed without a real sheet title)—the case that needs human-style judgment, not just index membership.

Next we would tighten the agent prompt or rules to flag **index entries with no addenda title** (and RFI-only stubs like A-444), and reduce false alarms on otherwise valid pairs such as **T01** (hyphen/format variants like A101D vs A-101D).

**6. Who did what**

- **Muhamed Hashi:** Labeler A (`labeler_A.csv`); independent labeling of T01–T10; ran `build_answer_key.py` and `run_real_eval.py`.
- **Vincent Ma:** Labeler B (`labeler_B.csv`); independent labeling of T01–T10.
- **Team 8 (collective):** Step 1 plan (`STEP1_what_we_test.md`); final answer key (no disagreements to resolve); reviewed failure groups and this write-up.

Run: 2026-10-23 UTC · model `gemini-3.5-flash-lite`. Full tables: `eval/RESULTS.md`. Raw checks: `results/demo2_real/`.
