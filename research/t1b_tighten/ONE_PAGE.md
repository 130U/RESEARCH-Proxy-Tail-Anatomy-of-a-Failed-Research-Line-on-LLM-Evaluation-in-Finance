# T1B one-page summary: the conclusion holds; the fraction falls from 17.09% to 12.12%

**Finally retained: 139/1,147 = 12.12%, above the task threshold of 58 questions.** For each retained question we saved two sets of rational inputs that lie strictly inside the rounding intervals and exactly satisfy all confirmed linear constraints: one gives a result inside the gold's 1% tolerance, the other outside. This is an existence result, not the probability that models usually answer wrongly, and not the benchmark's annotation error rate.

Scope fixed in advance: the complete tables and text provided by FinQA; other pages of the original annual reports are not covered. Only T1's 196 test witnesses are covered; the semantic correctness of unreviewed questions is not extrapolated.

|Sequential attribution (mutually exclusive)|Questions|
|---|---:|
|Still has feasible values both inside and outside the tolerance|139|
|Duplicate disclosures move the numeric interval inside the tolerance|1|
|Further sum constraints move the interval inside the tolerance|0|
|After tightening, the whole interval is incompatible with gold|0|
|Of the rest, clear problems with question meaning, binding or quantity type|37|
|Of the rest, semantics cannot be confirmed; conservatively removed|19|
|Total|196|

The only question tightened numerically by duplicate disclosures, MSI/2008/page_69.pdf-2, also has a semantic doubt of its own ("decrease in loss" versus "growth"); the semantic review total is therefore **37 clear problems + 20 doubtful**, and that question must not be deducted a second time. CME/2010/page_69.pdf-2 becomes incompatible with gold only under the additional assumption that the listed components exhaust the total credit facilities; the original "including" is not enough to support this assumption, so it is kept only as a sensitivity analysis and does not enter the main count.

**Sample review:** with fixed seed 20261116, 40 questions were sampled: 27 passed, 8 had clear problems, 5 were doubtful. Clear errors are 20%; counting the doubtful ones as risk too, 32.5%, more than a quarter. The fix was carried out under the conservative convention: check units, years, economic roles, exact vs. rounded values, program coverage and denominator direction; review all 196 questions one by one, remove all 57 non-passing questions, and rerun T1 on the original 1147 questions to confirm that the original cohort of 196 is reproducible. gold was not silently corrected, and we do not claim that the other 951 questions passed semantic review.

**Computation and review:** 21 additional disclosures of the same fact, 511 confirmed linear relations; for 3 questions the input box narrowed because of duplicate disclosures, and for 9 questions the output range narrowed further because of sums. 196/196 final ranges reach exact extrema; the rest, if any, use proven outer envelopes. 588 stage certificates and 139 inside/outside witness pairs passed independent replay.

This item-by-item semantic review was performed and cross-checked by model sessions and **is not an independent human sign-off**. The mathematical proofs are conditional on the listed source bindings, rounding model and constraint inventory; we do not claim to exhaust all possible nonlinear semantic constraints in the documents. FinQA can define the displayed numbers themselves as arithmetic inputs, so this result still does not replace T1C's model-scoring experiment.

[Waterfall chart](results/waterfall.png) · [Full report](REPORT.md) · [Per-question summary](results/question_summary.csv) · [40-question review](results/sample40_review.csv) · [Per-question certificates](results/per_question.jsonl)
