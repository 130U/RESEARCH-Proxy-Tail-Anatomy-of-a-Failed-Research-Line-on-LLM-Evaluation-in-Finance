# Stage 1 stability comparison and explicit conclusion

> Completed later: the only passing method, Sol four-run aggregation, passed seven items and narrowly failed one in the [confirmation on 128 completely new items](stage2_report.md), so under the original gate it is not scaled up to 512 items. The text below keeps the facts as they stood when the stage 1 branch choice was made; the final assessment is in [SUMMARY.md](SUMMARY.md).

2026-11-16. 48 formal scoring session calls on 32 new samples have been completed: 3968 judgments for pairwise comparison and 16 results for multiple rankings. All outputs covered the specified IDs, with no inconclusive items. There were also 2 whole-batch attempts with 496 pairs that produced no output; their failure records are kept separately.

**Explicit conclusion: both joint two-model plans failed; only "Sol + four-run rank aggregation" passed the single-model stability conditions and is worth moving to validation on a new sample.** The pass criteria were not relaxed, and a single-model pass was not rewritten as a pass of the two-model route.

The main check uses the nominal 25% tail, i.e. 8 items. The two aggregations of the same model must satisfy, for the upper and lower tails and in both directions: equal-budget recall of at least 80%, a widening factor of no more than 1.5 for 90% recall, and tie expansion of no more than 20%. These are working thresholds, not significance tests. After rounding, 90% of 8 items actually requires all 8, so a single fairly deep miss widens the result markedly.

| Method and model | Overall rank correlation between the two groups | Worst equal-budget tail recall | Maximum repeat widening factor | Maximum tie expansion | Single-model conclusion |
|---|---:|---:|---:|---:|---|
| Pairwise comparison, Luna | 0.825 | 62.5% | 2.25 | 25% | Failed |
| Pairwise comparison, Sol | 0.920 | 87.5% | 1.875 | 0% | Failed: pass-through too wide at the positive tail |
| Four-run rank aggregation, Luna | 0.865 | 87.5% | 2.75 | 0% | Failed: miss too deep at the positive tail |
| Four-run rank aggregation, Sol | 0.987 | 100% | 1.00 | 0% | Passed |

Left-right swap inconsistency rates for pairwise comparison: Luna's two panels 248/496 and 230/496 (50.0%, 46.4%); Sol's 56/496 and 63/496 (11.3%, 12.7%). The numbers of strictly opposite preferences are 131 and 113, and 14 and 8, respectively. After merging conflicts into ties, Luna still has 8/508 and 7/543 strict three-edge cycles; Sol has no observed cycles among 1964 and 2125 strict triangles. Zero cycles do not prove transitivity in the population, and inconsistency cannot be attributed only to input position.

Multiple aggregation gives a substantive improvement, but it did not fix every model. The m=1, 2, 4 results reserved in advance show: Sol's worst equal-budget recall rose from 36.4% to 100%, and the maximum repeat factor fell from 2.875 to 1; m=2 and m=4 are identical on these main metrics. Luna's equal-budget recall also improved to 87.5%, but at the positive tail it still had to pass through 22 items to recover 8, a factor of 2.75. One cannot show only the higher correlation coefficient or pick the best single run.

## Next stage started

The pairwise method and the Luna branch are kept as failure results, and these branches are not scaled up. For the only passing method, Sol four-run aggregation, a separate single-model validation branch, selected after stage 1, is set up: 128 new samples are drawn from families never used before, keeping the prompt, m=4 and all tie-handling rules; the main checks change to 10% and 20%, with the other thresholds unchanged. This branch only validates the repeatability of the reference ranking and does not yet complete the cheap/expensive model tail comparison. If it fails, the failure is kept, and it is not tuned further on the same validation set and then called a success.

These 32 items, the fixed p and the number of repeats cannot identify the asymptotic α, and this is not a validation against stock returns. The reference model is not ground truth. All combination ranges are repeat sensitivity, not confidence intervals; within-batch comparisons share context.

Basis: [full numbers](methods_stage1_all.json), [four-panel figure](methods_stage1_all.png), [item-by-item pass conditions](stage1_report.md), [frozen design and notes on the single-model branch](methods_protocol.md), [aggregation formulas and sources](aggregation_math.md), [analysis code](analyze_agent_methods.py). The raw inputs and outputs are in `research/private/agent_tail_methods/stage1_n32/`.
