# Influence-structure audit: pre-execution budget and fixed comparisons

2026-11-16. This file was written before the numeric execution of this round's new code. Purpose: fixed-stratification zero-finding mathematical verification for P1 path 03; no new model training, real audit or network access. Literature novelty is not confirmed.

## Frozen question

Fix alpha=1/20 and the test accuracy target I=[9/10,1], and define the bad contamination sets by the document-influence structure. The direct procedure outputs I only when every stratum has zero findings, and otherwise outputs the full range/abstains. The comparison baseline requires that the safe contamination-count rectangle it reports is itself covered simultaneously; it likewise reports only on all zeros. The exact risk of such a rectangle is the maximum of the miss probabilities of the out-of-bound strata, **not the Bonferroni sum**. Procedures with wider scope that guarantee only the final I and not the rectangle are not compared, because they already belong to direct testing.

General exact checks are limited to small finite populations: at most 65,536 document configurations, 50,000 discrete count states per run, and a design/rectangle grid of 100,000; triggering any limit must refuse to certify. The program's rational endpoints, risks and costs all use exact arithmetic.

## Complete threshold structure family

Each stratum's N documents influence only the corresponding head; all h=2r−1 heads initially give the correct label, and changing any r heads makes a nonzero fraction of test points wrong. The constructed example uses one fixed test point with label 0; I=[.9,1] requires that point to stay unchanged. This input is a hand-made mathematical structure, not an actual classifier.

Fixed complete grid: r∈{2,3,4,5,6}, N∈{2,5,10,20}, 20 cells in total; all success, no-gain and failure cells are reported. Cost 1 per stratum. The balanced design first computes the smallest integer n with ((N−n)/N)^r≤alpha; the rectangle optimum is r·ceil[N(1−alpha)]. The direct global optimum enumerates non-decreasing quotas of length r using sorting symmetry, with the last h−r strata taking the r-th stratum's quota; the largest grid has C(26,6)=230,230 tuples. Optimality is claimed only within the defined class of fixed, stratified uniform sampling, not for real audits or general adaptive designs.

Two explicit negative controls are also kept: for a two-stratum AND with N=20, the direct optimum should equal the best rectangle; when there is no bad configuration no audit is needed; when the empty contamination configuration is already bad, no zero-finding design can pass. Specific small-scale oracles and tests are recorded by the implementation.

## Compute and acceptance

- Local CPU, Python standard library; GPU/GPU memory/training tokens all 0.
- The full threshold grid is expected to take under 30 seconds, RAM<256MB; general checks and tests at most 60 seconds in total, RAM<512MB. These are budget estimates; actual times are recorded separately.
- On a timeout/search-limit hit, stop the corresponding scale first, and do not treat an unfinished inner extreme as a safe bound. Small examples can still be completed.
- Theorem correctness rests on the derivation and the independent review; finite exhaustion is used for implementation and counterexample checks, and zero failures cannot replace a global proof.
- The 20% cost saving is the pilot screening line proposed in the previous round, not a paper standard. The current hand-made perfect-vote family cannot on its own pass the real-data, task-utility or novelty gates.
