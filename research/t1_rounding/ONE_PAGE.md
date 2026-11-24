# T1: continue the input-precision audit

2026-11-16 · same-day feasibility result

**Verdict: continue.** Of FinQA's 1,147 public test questions, 196 have an out-of-tolerance witness with consistent inputs, **17.09%** of all questions, above the original 5% threshold. What the fraction means: **under the assumptions of bound inputs, half-a-last-digit-unit rounding and independent input boxes, the output of the gold program can cross the 1% tolerance**. It does not directly indicate an annotation error, or that the answer cannot be determined from the full filing.

| Measurement | Result |
|---|---:|
| test questions that pass the strict parsing and source rules | 731 / 1,147 |
| Concrete feasible input witness outside the 1% tolerance | **196 / 1,147 = 17.09%** |
| Out of the cell at the gold's displayed digits | 375 / 1,147 = 32.69% |
| Growth-rate group, 1% rule | **90 / 230 = 39.13%** |
| All public train/dev/test, 1% rule | 1,469 / 8,281 = 17.74% |

In test, 416 questions were excluded and another 3 have unresolved interval decisions; they cannot be counted as stable. Every main count requires a concrete out-of-tolerance input; a loose interval outer envelope was never treated as a counterexample. The 1% and displayed-digit rules are the audit conventions set by the task; FinQA's official scoring actually compares the executed answer after rounding to five decimal places.

**An example.** BlackRock's rent and equipment expenses are displayed as 137 and 133 million dollars, and the program's growth rate is about 3.0075%. If the two true quantities are 136.5005 and 133.4995, they still display as 137 and 133, but the growth rate becomes 2.24795%, far beyond the 1% relative tolerance. Both references to the base use the same variable. [Per-question evidence and code](results/per_question.jsonl)

**Duplicate precision.** A complete scan of the 380 test pages produced 54 candidate location pairs. Item-by-item checking against the source text confirmed 35 pairs, rejected 16, and left 3 pending. For 23 questions we completed single-source substitution from a different disclosure location; 4 cross 1% and 13 cross the display cell. A two-role case, "both years are written as 2.6, while the precise table actually has 2.616 and 2.572", is listed separately. This is a confirmed lower bound for the searched pattern, not yet a census of all semantic duplicates.

**Mathematical result.** For a growth rate (g=b/a-1) with input half-widths (h_a,h_b), the first-order radius is ((|a|h_b+|b|h_a)/a^2). When the full rounding unit is the same (u) for both, the original task formula needs a (u/2) factor. In the strict growth-rate subset of 1,307 questions, shrinking the half-widths in simulation by factors of 1, 10, 100 and 1000 gives exact out-of-tolerance counts of **529, 143, 7, 0**. The first-order threshold prediction has no errors on this sample, but the first-order expression itself is not a strict bound. Rewriting units alone adds no information.

**Novelty and next step.** A targeted prior-art check found no complete match for this question. XBRL already has rounding intervals, interval arithmetic, and a specification for intersecting duplicate disclosures; these cannot be presented as new theory. What is worth continuing is the base-rate fraction and the nonlinear sensitivity. The next round should add the confirmed duplicate disclosures and accounting constraints to the feasible region and test the improvement against real, more precise disclosures; if the signal disappears after tightening, we stop claiming "undeterminable from the full text".

[One summary figure](results/rounding_summary.png) · [Full conventions, groups and recomputation](REPORT.md) · [Literature prior-art check](literature.md) · [Mathematical derivation](math_review.md)
