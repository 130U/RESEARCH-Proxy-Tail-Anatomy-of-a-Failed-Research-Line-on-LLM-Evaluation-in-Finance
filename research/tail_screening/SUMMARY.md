# Final assessment of the stability trials

2026-11-16 | Executed results

**Decision: this round does not scale up to 512 items. Four-run rank aggregation gives a clear improvement, but the selected method still narrowly failed one item of the confirmation gate on the new 128 items.** This does not falsify the original tail hypothesis, and it is not a conclusion that the population is significantly below the threshold.

All scoring ran in fresh, isolated model sessions; no model was trained. In total there were 64 scoring tasks: 8 on the 128-item development set; 48 for the method comparison on 32 completely new items; 8 for the confirmation on another batch of 128 completely new items. In addition, 2 whole-batch pairwise tasks produced no output and are recorded separately. The three batches cover 288 non-overlapping lexical families; repeated scoring does not increase the sample size.

| 32-item stage 1 | Worst equal-budget recall | Maximum widening factor for 90% recall | Conclusion |
|---|---:|---:|---|
| Pairwise comparison / Luna | 62.5% | 2.25 | Failed |
| Pairwise comparison / Sol | 87.5% | 1.875 | Failed |
| Four-run aggregation / Luna | 87.5% | 2.75 | Failed |
| Four-run aggregation / Sol | 100% | 1.00 | Passed as a single model, moved to a new sample |

In stage 1 the main p=25%, nominal 8 items; after rounding, 90% requires all 8. Both joint two-model methods failed; only Sol four-run aggregation was selected for confirmation as a new branch, and the original joint-gate conclusion was not changed.

**128-item confirmation result:** the overall Spearman between the two four-run aggregation panels is 0.9929. Of the eight direction/tail checks at the main p=10% and 20%, seven passed. In the negative 10% tail, the actual lists had 14 and 12 items with an overlap of 11; recall in one direction was 11/14=78.6% < 80%, and in the reverse direction 11/12=91.7%. The maximum q90/p=1.25≤1.5, the maximum boundary-tie expansion 16.7%≤20%, and all outputs were rankable. The failure is close to the threshold and cannot be described as severe instability.

For m=1→2→4, the worst equal-budget recall on the confirmation set was 64.3%→71.4%→78.6%, and the maximum widening factor 2.969→1.875→1.250. Aggregation does improve things. The decision is made at the pre-fixed m=4, the failing result is kept, and we do not add repeats or lower the threshold on the confirmation set and then change the verdict to success. Going from 32 to 128 also changed the sample pool and the tail fraction at the same time, so the result cannot be attributed to the increase in sample size alone.

**Theory and novelty:** the general conditional-extremes assumption gives qγ(p)=p^{α+o(1)}, not the general C p^α; α=1 can still have a diverging factor. The Gaussian α=ρ² has clear prior work. Copula modeling of LLM cascades, tail dependence explaining extreme prediction, and recall-constrained proxy screening have all been studied. The originality of the narrow question is not confirmed, and the prior-art check still has a gap for the full text of Yeo–David (1984).

**Recommendation:** record this round as a complete measurement-feasibility result. The reference model is not objective truth; these within-candidate-pool aggregated scores have not yet established a stable document-level continuous measurement, so they cannot be used to fit an asymptotic LLM α or to claim investment value. If a follow-up trial is set up, first specify a verifiable economic/semantic target, then confirm any changes on completely new data, instead of hiding this round's negative result.

Detailed results are in [stage 1](stage1_report.md) and [the new 128 items](stage2_report.md); the [recomputation notes](REPRODUCE_CURRENT.md) give the commands.
