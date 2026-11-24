# From total-contamination-count audits to the final statistic: this round's exact computations

**Round seven interpretation update:** the table below and its original pre-specified results are unchanged. A later review proved that the balanced total-contamination-count gate also reaches 88 and the same asymptotic separation from the rectangle; so the result here is the cost of the rectangular intermediate commitment and is not enough to prove that position awareness is necessary. The round-seven draft lists this control in full, and labels the other position-gain example, 38 versus 48, as an exploratory derivation made after the review. The equivalence between general non-rectangular safe count regions and the direct method is also made explicit in the new manuscript.

Date: 2026-11-16. Source level: local pen-and-paper derivations and exact computations on hand-made mathematical inputs; no model training, real contamination audit or new literature check. [Pre-execution budget](impact_budget.md), [IA1–IA8 proofs](../theory/impact_audit.md), [original 20-cell results](threshold_results.json).

## What was obtained and what was not

An audit aimed directly at the final bad configurations can indeed cost strictly less than a procedure that "first guarantees a safe contamination-count rectangle and then derives the final interval"; this round gives a generalizable construction and the corresponding algorithm. In the pre-fixed structure with r=6 and 20 documents per stratum, the global optimum cost of the direct design is 88 and the strongest joint zero-finding rectangle costs 114. Both target the same alpha=1/20, the same accuracy interval [.9,1] and the same fixed stratified uniform sampling.

This is not an advantage over all possible audit methods, nor a result on an actual financial model. The rectangle method also promises that its intermediate count box is itself covered, while the direct method promises only the final statistic. The advantage comes from proving fewer intermediate facts that are not needed; its boundary with prior work has not yet been checked. All initial heads being correct is a hand-made structure and cannot be used to prove real-task accuracy or historical provenance.

**Of the complete 20 cells, 9 improve strictly and 11 do not, with a median improvement of 0; only 3 cells exceed 20%.** So the maximum of 26.67% or the single cell at 22.81% cannot be used to claim that the whole pre-specified family passes the median 20% investment gate. If the r=6 sub-family is studied later, the assumptions and a confirmatory design must be frozen separately, and the results seen this time must not be packaged as a blind-test success.

## Baseline correction

In the preliminary discussion it was easy to take the sum of the per-stratum miss risks as the strongest rectangle. The independent discussion pointed out that, within the same procedure class "report the fixed box only when all findings are zero, otherwise the full range", the exact worst-case coverage-failure risk is the **maximum** of the miss probabilities of the out-of-bound strata. True contamination outside the box exceeds at least one stratum; putting a group of contamination just over budget in the hardest stratum, with all other strata clean, attains the maximum.

The main comparison therefore uses this max version. The Bonferroni-sum version is only a more conservative additional control. For r=6, N=20, its optimal cost is 119, higher than the correct main baseline of 114; choosing only 119 would exaggerate the gain of the direct design.

## Threshold family and exactness

Each stratum's N documents influence only the corresponding head, with h=2r−1 heads in total; all heads vote for the true class at the fixed test point. If fewer than r strata contain contamination the output is unchanged; if at least r strata contain contamination, all test points can be made wrong, so the bad configurations are those with at least one contaminated document in each of any r strata. The executed script represents this abstract structure with one point labelled 0; two classes and consistent votes over several points are mathematical extensions of the same probability formula and are not passed off as a trained/run voting experiment.

The risk under quotas n_h is the maximum of `prod(1−n_h/N)` over all r-stratum subsets. The minimum per-stratum quota of the balanced design is found by inverting with rational integer powers; floating-point roots are not used to decide boundaries. When stratum sizes and costs are equal, after sorting only the r smallest quotas determine the risk, and the other quotas can be lowered to the r-th without increasing risk. Enumerating non-decreasing r-tuples therefore gives the global optimum within the declared fixed design class.

The strongest rectangle must prove a contamination count of 0 for at least r strata; its exact minimum cost is `r*ceil(N*(1−alpha))`. The minimum cost of the sum rectangle is `r*N−floor(N*alpha)`. The definitions, the constructions attaining the lower bounds and the applicable class are in IA6–IA8.

## Complete pre-specified grid

Every cell has alpha=.05, accuracy target [.9,1] and stratum cost 1; the cost is the number of audited documents, and planning CPU time is recorded separately. The direct column is the global optimum, not just one balanced scheme tried.

| r | Strata h | N per stratum | Direct optimum | Strongest rectangle optimum | Relative saving |
|---:|---:|---:|---:|---:|---:|
| 2 | 3 | 2 | 4 | 4 | 0% |
| 2 | 3 | 5 | 10 | 10 | 0% |
| 2 | 3 | 10 | 20 | 20 | 0% |
| 2 | 3 | 20 | 38 | 38 | 0% |
| 3 | 5 | 2 | 6 | 6 | 0% |
| 3 | 5 | 5 | 15 | 15 | 0% |
| 3 | 5 | 10 | 30 | 30 | 0% |
| 3 | 5 | 20 | 57 | 57 | 0% |
| 4 | 7 | 2 | 8 | 8 | 0% |
| 4 | 7 | 5 | 20 | 20 | 0% |
| 4 | 7 | 10 | 39 | 40 | 2.50% |
| 4 | 7 | 20 | 76 | 76 | 0% |
| 5 | 9 | 2 | 9 | 10 | 10.00% |
| 5 | 9 | 5 | 23 | 25 | 8.00% |
| 5 | 9 | 10 | 42 | 50 | 16.00% |
| 5 | 9 | 20 | 84 | 95 | 11.58% |
| 6 | 11 | 2 | 10 | 12 | 16.67% |
| 6 | 11 | 5 | 22 | 30 | 26.67% |
| 6 | 11 | 10 | 44 | 60 | 26.67% |
| 6 | 11 | 20 | 88 | 114 | 22.81% |

The zero-finding risk is the probability that, under a bad truth, the audit happens to miss the contamination completely; it is not the probability that an actual audit will succeed, nor the posterior probability of contamination after observing zero findings. A given design may also find errors and abstain, so optimal audit cost cannot be read as optimal total research benefit.

## Negative controls and asymptotic results

For the two-stratum AND structure with N=20, both the direct design and the strongest rectangle reach the optimal cost of 19 with audit quotas [0,19]; a joint structure does not by itself bring savings. Even where there is a gain, integer rounding makes neighbouring sizes behave differently, so no monotone efficiency trend can be extrapolated from this table.

Another result, proven but not executed as a large-scale experiment: with fixed alpha and N=r², the direct balanced design costs at most `2N*log(1/alpha)+2r` and the rectangle at least `r*N*(1−alpha)`, so the lower bound on the cost ratio grows linearly in r. The total corpus size grows at the same time as (2r−1)r², and all votes are hand-made oracle structures. This is the structural cost of the intermediate rectangle commitment, not an arbitrary-factor saving in an actual language model, and not a certification of novelty.

## Actual execution and reproduction

The threshold script [threshold_design.py](threshold_design.py) uses the Python 3.12.14 standard library; the standalone 20-cell scan took 0.702440 seconds, and the later integration rerun 0.680830 seconds (current JSON). The largest exact search domain is 230,230 non-decreasing tuples; cost pruning does not lose any smaller feasible cost. The 5 independent tests took 0.363 seconds and cross-validate against full small-domain enumeration of uncompressed quotas, sampling outcomes and safe boxes; they do not only verify some hand-picked success point.

```powershell
python -m unittest research.planning.test_threshold_design -v
python -m research.planning.threshold_design
```

The checker for general asymmetric influence graphs and its independent review are recorded separately; this page does not use the compressed threshold formula as evidence of scalability to arbitrary graphs. The population must be frozen first, the influence graph must cover arbitrary joint deletions, and the historical audit truth must be valid. Missing any one of these, the current result is still only a conditional mathematical design.
