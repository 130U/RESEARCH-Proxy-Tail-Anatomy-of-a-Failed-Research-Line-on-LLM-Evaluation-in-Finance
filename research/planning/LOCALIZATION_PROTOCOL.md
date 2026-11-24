# Round eight: the value of position information relative to strong simple audit baselines

Date: 2026-11-16. The previous round made substantive progress: the unified manuscript, the strong-baseline rebuttal and the PDF are complete. This round continues the original research goal that is not yet complete, focusing on the necessity of the mathematical contribution; it does not change G0/G1 and involves no main-line training, network access, weight downloads or external sending.

## 1. Known results and nature of the research

The original threshold 20 cells and 38 versus 48 have already been seen. This round's review discussion also raised a homogeneous ratio upper bound, a conjunction family and a star structure; these are exploratory derivations. What is frozen below is the execution scope and the full reporting rules; this **is not an ex-ante confirmatory pre-registration of these already-known examples**, and it does not retroactively declare any old 20% investment gate passed.

Framework: finite population, fixed true contamination, fixed stratified uniform sampling without replacement, independence across strata, certification only when all findings are zero, correct audit labels. Training randomness and the evaluation object are frozen in advance; no iid assumption on training samples. All numeric inputs are explicitly hand-made mathematical constructions, not real models, provenance audits or historical certificates.

## 2. Core questions and same-condition comparisons

1. Given stratum sizes N_h, quotas n_h and the safe total-count gate K≤s−1, the exact risk is the maximum miss probability over all configurations with total contamination count s. Implement prefix-greedy over non-increasing multiplier chains, and check it with an independent binomial-coefficient DP and small-domain enumeration of actual sampling.
2. Under the same target, compare: the direct bad-set design, the strongest joint zero-finding safe rectangle, and the strongest fixed-stratification total-K gate. Their output commitments differ, and this must be stated clearly.
3. Also list `min(strongest rectangle cost, strongest total-K cost)` as a simple baseline combination: before looking at audit results, choose the valid design with the lower cost based on frozen information; no extra multiple testing is needed. One must not pick only the weaker single comparator for each example.
4. For the original d=2r−1 threshold family, verify the constant bound on the position gain relative to the total-count gate and its sharpness; distinguish the original N=r² asymptotic path from other parameter paths.
5. For the all-strata conjunction and the star structure, check the genuine order difference and the simplest attaining construction. Every document must belong to some minimal bad configuration, ruling out creating an advantage by adding irrelevant documents; also acknowledge that a simple single-stratum clean gate may already reach the direct optimum.

A non-empty mathematical difference is not equated with a natural-model gain, algorithmic novelty or the necessity of training from scratch. The current literature ledger is not enough to judge priority for this round's narrow theorem.

## 3. Fixed computation scope

Everything uses α=1/20, accuracy target interval [9/10,1], and unit audit cost.

- Original homogeneous threshold family: r∈{2,3,4,5,6}, N∈{2,5,10,20}, d=2r−1, the complete 20 cells. Existing direct/box results are kept and checked; new: the optimal total-K cost and the difference from the simple baseline combination.
- Conjunction family: d=r∈{2,3,4,5,6,8,12,20}, N=2. d single-stratum influence heads plus d−1 trusted fixed-correct heads; bad if and only if every stratum has contamination. List the direct=box single-stratum gate and the exact total-K optimization, compared with the proven closed form.
- Star family: number of leaves L∈{1,2,5,10}, N∈{2,5,10,20}, L+1 strata in total. The centre influences L heads, each leaf influences its own head, plus 1 trusted fixed-correct head; bad if and only if the centre and at least one leaf contain contamination. List the centre clean gate, the strongest total K and the simple baseline combination.
- Sharp-constant sequence: N∈{4,8,16,32}, r=N², d=2r−1. Only check the feasible construction specified by the theorem and the analytic upper and lower cost bounds, **without calling them numerical solutions of the global exact optimum**. The smallest k with (1−1/N)^k≤α is solved by integer/rational comparison, avoiding floating-point root boundaries.

All cells are reported, including no improvement and exceeded run budgets; an exceeded budget does not return "optimal" or "no solution", and the grid must not be quietly shrunk to keep only successful items. Exploratory different α values or other structures are not mixed into the main table.

## 4. Compute and execution order

- Pure Python standard library; no GPU, model training or private text. The existing bundled/local Python is available; no dependencies are installed.
- Budget for unit and independent small-domain checks: 10 seconds of CPU wall clock; budget for the first full table: 60 seconds. Peak memory expected below 256MB; not reported as measured unless actually measured.
- Cumulative limits for a single general optimization: 500,000 search nodes, 250,000 risk evaluations, 2,000,000 multiplier steps; the DP at most 200,000 transitions. Input rationals have length/syntax limits before parsing, and scientific-notation exponent blow-up is forbidden. Exceeding a limit fails explicitly.
- For equal sizes and equal costs the proven k-smallest-quota reduction (k≤d) may be used: the tail is lowered to the k-th quota, but the risk must still compute the k largest factors of each chain and cannot reuse the direct method's product of the first k terms. If the implementation keeps the full d sorted enumeration, it is equally valid but cannot claim to use the reduction.
- First finish the code and meaningful small tests, then run the complete fixed scope, then have an independent review check the theory, implementation, full table and scientific claims; the original JSON and original PDF are kept, and old experiments are not overwritten.

## 5. Deliverables and decision for this round

Deliver complete conditional proofs, the exact total-count baseline code, the complete results JSON and analysis, an independent adversarial review, and an update of the decision notes. If the simple baseline combination already reproduces all the gains, this should be reported truthfully as a setback for the method's necessity; theoretical innovation must not be claimed on the strength of calculator complexity, the number of tests or more constructions. The original paper serves only as an existing stage manuscript; this round first provides supplementary material, to avoid rewriting it as a new main paper before the review is finished.
