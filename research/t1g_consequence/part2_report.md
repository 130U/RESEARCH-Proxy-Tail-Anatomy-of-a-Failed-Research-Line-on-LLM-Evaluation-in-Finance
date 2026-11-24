# Part Two: rounding consequences for comparison questions are rare, and there are fewer than 100 computed comparisons

The source level of all numbers below is **our experiment**; semantic interpretations come from the filing texts attached to the datasets. The identification method was written first in `part2_protocol.md`. The TAT-QA interval computations ran after the Part Three prediction was committed as `0c68d8a`.

| Dataset | Confirmed computed-comparison questions | Conclusion flippable on the input box | Share | Expected number of flipped questions under uniform rounding |
|---|---:|---:|---:|---:|
| FinQA, train/dev/test | 11 | 0 | 0% | 0 |
| TAT-QA, train/dev/test_gold | 14 | 2 | 14.29% | 0.278173 |
| Total | **25** | **2** | **8.00%** | **0.278173 (1.1127%)** |

**Verdict: rare; the sample is too small.** The combined 8.00% is below the task's 10% threshold, and 25 questions are far fewer than 100. TAT-QA alone, at 14.29%, exceeds the share threshold, but it has only 14 questions, which cannot hide the sample threshold. Part Two does not trigger the follow-up model answering.

These 25 include 3 questions that use explicitly exact settings: one with a fixed dividend, one with KPI weights set in advance, and one with a compensation incentive target. Removing these 3 still gives 2/22 = 9.09%, and the verdict is unchanged. Pure unit or sign conversions do not count as computed comparisons.

## Which questions they were identified from

Among all 8,281 FinQA questions there are 154 `greater(` programs, plus 2 questions with yes/no answers whose programs have no comparison. Of the 154 programs, 16 have final operands that refer to earlier operations; 5 of these involve only unit or sign conversion, leaving 11 that truly compare products, sums, differences, means, or ratios. All 156 candidates are kept in `part2_finqa_results.csv`. The rounding boxes of all 154 original comparison programs are stable; the other 2 questions are also stable after being reconstructed separately from the question text, and the original program errors were not counted as rounding consequences. Disagreements between the original `answer` and `exe_ans` are recorded separately and not mixed into the flip rate.

TAT-QA uses the official `req_comparison`, comparison symbols in the derivation, and comparison words in the question for broad recall, giving 1,817 non-arithmetic answer candidates. After formula/question screening and item-by-item comparison with the original tables, 14 questions were confirmed to require comparing computed results; most "which year grew faster" or "which year had the higher ratio" questions directly compare change rates or ratios that are already printed. The full candidate list and screening status are in `part2_inventory.csv`; the source coordinates, operations, exact ranges, and witnesses of the 14 questions are in `part2_tatqa_results.json`. The remaining broad-recall candidates include direct comparisons, counts, extraction, and explanations of causes; **they are not treated as computed-comparison questions with interval certification**.

The 40-question check was drawn by stratum with fixed seed 20261117: 20 candidates whose derivation strings appear to contain arithmetic symbols, and 20 other broad-recall candidates. After AI reading of the question, derivation, and table, only 11/20 in the first stratum were truly computed comparisons, and 0/20 in the second. False positives include row/column ranges such as `COL 3–5`, rating names such as `A1/A+`, row names such as `provided by/(used in)`, and directly reading a printed percentage. This result shows that regex hit counts cannot be taken as question counts. The item-by-item judgments are in `part2_semantic_review_40.csv`; **this is AI semantic reading, not human review**. This spot check tests identification precision and does not estimate the recall rate for the full dataset; 14 is the set confirmed by this reproducible identification and semantic screening, and we cannot claim to have exhausted every unannotated implicit comparison.

## The two flippable cases and their actual limits

**Audit fees: `ce5fc144-7926-472b-9f90-f6fcbc3410e7`.** The three fees are 2.4, 1.2, and 1.3 million in 2019, and 1.5, 1.2, and 2.1 million in 2018. The center totals are 4.9 vs. 4.8; the exact range of the difference is **[−0.2, 0.4] million**. The two 1.2 values belong to different years and different audit firms and are kept as different variables. The interior witness is 2.35005, 1.15005, 1.25005 for the three 2019 items and 1.45005, 1.24995, 2.14995 for the three 2018 items; the totals are 4.75015 and 4.84995, and the conclusion reverses. The probability under the independent uniform model can be computed analytically: the sum of six symmetric rounding errors crossing −0.1 is equivalent to the sum of six U(0,1) being less than 2, so the probability is **(2⁶−6)/6! = 29/360 = 8.05556%**.

**EPS percentage difference: `1d5aea847254a9c3a9771b7b1a9ae40b`.** 2018 uses 3.00 and 2.96, and 2019 uses 6.66 and 6.58; the center of the difference between the two growth expressions is 0.00135546, and the exact range is **[−0.00357017, 0.00629025]**. The interior witness and the recomputation on the original DAG are in the per-question JSON. Under the independent uniform model the flip probability is about **19.7617%**: first integrate analytically the rectangle area formed by the two numerators, then integrate numerically over the two denominators; the estimated numerical integration error is about 9.7×10⁻⁷ (in probability units). Two 131,072-point Sobol checks give 19.7517% and 19.7853%.

But the EPS case **cannot serve as evidence that "the whole document cannot determine the answer"**. The same table also prints the basic and diluted weighted-average share counts and states explicitly how EPS is computed. Cancelling the common net income, the compared quantity can be rewritten as "diluted shares / basic shares − 1". Even if each of the four share counts gets its own independent half-last-digit-unit box, the difference of the two ratios is still strictly positive, with range **[0.00113463, 0.00121373]**, so the conclusion that 2019 is smaller can be recovered from the full text. This computation is saved in `part2_eps_full_document_check.json`. This is a known full-text-constraint remedy for one of this round's two counterexamples; we do not pretend on this basis that a full-text constraint audit has been completed for all questions.

## The rule for comparing two growth rates

Let $`g_i=b_i/a_i-1`$, with $`a_i>h_{a_i}>0`$, $`b_i>0`$, and input half-widths $`h_{a_i},h_{b_i}`$. The exact upper and lower one-sided deviations around the center are

```math
e_i^+=\frac{h_{b_i}+(1+g_i)h_{a_i}}{a_i-h_{a_i}},\qquad
e_i^-=\frac{h_{b_i}+(1+g_i)h_{a_i}}{a_i+h_{a_i}}.
```

If at the center $`g_1>g_2`$, and the two sets of inputs are independent, then the strict order holds on the whole closed box if and only if

```math
g_1-g_2>e_1^-+e_2^+.
```

The first-order version approximates the denominator by $`a_i`$, that is, it compares the growth-rate difference with the sum of half-widths weighted by the absolute values of the two sets of derivatives. If the two expressions share inputs, the joint function $`D=g_1-g_2`$ must be analyzed; it is not enough to check whether the two marginal intervals intersect. For example, the intervals of $`A=x`$ and $`B=x+0.1`$ can intersect, but the order never flips.

In this set, 3 questions with 4 pairs of comparisons truly compare two growth expressions: FinQA's agriculture/automotive growth, TAT-QA's EPS difference, and US/Europe/Asia revenue growth. The exact rule agrees with the joint-range decision **4/4**; all computed comparisons produce 35 joint difference functions, and the first-order decision agrees **35/35**. The sample is very small; this is not a general accuracy guarantee. The plot data are in `part2_growth_plot.csv`; the EPS point is still the result on the "standard-solution input box" and must carry the note that the full text can recover it.

## Computation method and sources

All ranges use exact rationals, following T1a's certification by monotone derivatives / extrema of coordinate-wise linear-fractional functions. A counterexample is always a single interior point of shared inputs, not a splice of two incompatible endpoints; `part2_summarize.py` has checked that every counterexample lies entry by entry inside the box and that the original operations give the opposite answer. A lack of flipping probability samples was never treated as a proof of stability. The program depends on the T1 and T1a source code in adjacent read-only workspaces; the rerun commands are, in order, `part2_comparisons.py inventory`, `finqa`, `tatqa`, and `part2_summarize.py`.

The original data sources are [FinQA official data](https://github.com/czyssrs/FinQA/tree/0f16e2867befa6840783e58be38c9efb9229d742/dataset) and [TAT-QA official data](https://github.com/NExTplusplus/TAT-QA/tree/870accc41953dcde885aabeb963d94aabdc0fbc3/dataset_raw). We do not use "no candidate hit" to prove absence, do not call unit/direction errors in the standard program a rounding phenomenon, and do not call flippability on the input box a flip of the actual filing's true values.
