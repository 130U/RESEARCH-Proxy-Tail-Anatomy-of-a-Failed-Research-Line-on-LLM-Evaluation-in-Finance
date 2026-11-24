# One-page summary of the absolute-scoring replication

2026-11-16 | **Formal verdict: inconclusive (the pre-registered ties gate was triggered).** 1,000 new lexical families, eight rounds, all 250 real scoring calls completed. 8,000 main scores and 2,000 companion control scores were saved; the control comparison uses only the 200 scores of the 100 pre-specified targets. Fixed gpt-6-sol, low, fresh context, no paid model API, no training.

| Number of averaged scores m | Top 10% overlap | Bottom 10% overlap | Fixed Gaussian prediction (same for both tails) |
|---|---:|---:|---:|
| 1 | 84.1%–87.2% | 81.3%–86.1% | 84.3% |
| 2 | 85.6%–88.1% | 86.3%–88.0% | 88.8% |
| 4 | 91.1%–92.0% | 90.1%–91.0% | 92.1% |

The ranges come from the two reference directions; they are not confidence intervals. **In this sample, with four-score averages the point estimates for both tails reach 90% for the first time; the corresponding four 95% intervals all contain values below 90%, so we cannot promise that the population overlap stays above 90%.** [Full figure](results/stability.png) · [Statistics and intervals](results/tables.csv)

Direct reason for the inconclusive verdict: in rounds six and seven, the boundary tie group in the positive 10% tail has **22 items > 20 items**. The extra expansion of the list was only 18 and 17 items, but the new gate checks the whole tie group. The finer resolution of the four-score average cannot be used after the fact to waive the single-round gate. Each round used 77–80 distinct score values; several boundaries at 5% also failed.

Mean single-round reliability is **0.9748**, with a range of 0.9715–0.9777 over the 28 pairs. At 10%, every overlap point estimate is within 3.3 percentage points of the formula, but the difference intervals are wide and do not prove the pre-registered ±5 percentage point practical equivalence; there is also no clear evidence of a difference between the two tails. The 5% widening factors show local deviations (see the full report), so we cannot say the formula fits everywhere.

Same-batch correlation **0.9852**, different-batch **0.9713**; paired difference **0.0139**, 95% interval **[0.004, 0.028]**. This supports batch sensitivity, but it cannot identify its share of the total noise.

**Recommendation: close this round as an inconclusive replication result. Do not upgrade it to a new tail law, and do not change the scale and rerun on these 1,000 items.** Any continuation would first need a new measurement protocol, a statement of the remaining mechanism questions, and a new sample. Self-consistency is not correctness, and the economic budget choice between repetition and widening is still unresolved.

[Full report](REPORT.md) · [Frozen protocol](protocol.md) · [Recomputation notes](REPRODUCE.md) · [Literature gate](PRIOR_ART.md). Scoring had no failures or retries; two scheduler request errors were recovered without rescoring any valid batch.
