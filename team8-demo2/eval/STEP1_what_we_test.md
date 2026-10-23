# Step 1: What we are testing

Team 8 | INFO 492 C | Demo #2: checking references

Planning draft prepared on October 17, 2026, with AI writing assistance. The proposed target below is for the upcoming evaluation on 10 real RFIs. The earlier 24 simulated-case results were already available when this plan was drafted. This is not a claim that those earlier tests were planned under this target.

## 1. What our agent does, in one sentence

Our agent helps by **checking drawing references in a subcontractor's RFI before it goes to the GC**, and we think it will **correctly identify whether a reference problem is present in at least 8 of 10 real RFIs in each of two runs**.

Code checks recognized sheet numbers against our available drawing index. The AI uses the lookup results and sheet titles to suggest possible mismatches or typing errors. It does not inspect the full drawings, confirm design correctness, or authorize work.

## 2. The one thing we count

Count how many of the 10 real RFIs receive the same decision as the team's final answer key: reference problem or no reference problem. A failed call receives no correct point and stays in the denominator of 10. Report the two runs separately.

Two people first label T01-T10 independently using the supplied source information. They then resolve disagreements and save the final key in eval/answer_key.csv. Do not use AI-generated labels as two people's independent labels. If the available evidence does not settle an item, document that limitation instead of guessing.

## 3. The number that means it worked

**8 out of 10**, or more, in each of the two runs.

This is a proposed small-pilot threshold, not an observed result or a number taken from a source. Confirm and freeze the plan before running this real-item evaluation. Report an unmet target honestly; do not lower it after seeing the results.

## 4. The no-AI comparison

Apply the existing code checklist to the same 10 RFIs: is a recognizable drawing number supplied, and is each recognized number in the available index? Report its score alongside both AI scores. This is an automated rule baseline, not a measured human review. Meeting 8/10 alone does not show that AI adds value if the baseline performs equally well or better.

Also record missed problems, unnecessary flags, failed calls, and any confirmed role-boundary crossings. Review flagged outputs manually; a keyword search finding nothing is not proof that no boundary was crossed. Run the two simulated adversarial cases separately, outside the main denominator of 10.

## 5. Scope and status

This evaluation tests the reference-checking step of our thesis. It does not measure human GC first-review time or establish the proposed 25% reduction. A missing entry in our available index does not prove a drawing does not exist.

Prepared for: Team 8, with AI writing assistance.
Date drafted: October 17, 2026.
Run completed: October 23, 2026 (`python3 scripts/run_real_eval.py`).

**Observed (10 real RFIs vs answer key):** agent **8/10** and **9/10**; no-AI checklist **9/10**. **Target met** (both agent runs ≥ 8/10).
