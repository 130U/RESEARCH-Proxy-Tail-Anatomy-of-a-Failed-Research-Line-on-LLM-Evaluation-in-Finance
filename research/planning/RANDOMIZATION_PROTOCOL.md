# Round nine: the audit minimax problem when random quotas are allowed

Date: 2026-11-16. Strictly offline: no training, source scraping, real label audit or external sending. Prompted by the round eight pooled counterexample; the candidate formula and the old results have already been seen, so this is an exploratory theory check, not a blind pre-registration. The original G0/G1 do not change.

## 1. Object of study and the non-degenerate output convention

There are d strata of N documents each, with unit audit cost. The threat family is defined exactly as the sets that have one bad document in each of at least r strata. If it is only an outer envelope of the failure sets of the actual model interval, optimality applies only to this conservative threat family and cannot automatically be read as optimality for the real model. A correct audit returns bad/good for a document; the true bad set must be fixed before the sampling randomness is realized. Any distribution that selects exactly m distinct documents is allowed; per-stratum quotas need not be fixed, and correlated sampling is allowed.

**When all findings are zero the output must be the fixed I; any finding outputs the full range.** This convention rules out never certifying and extra random abstention. If one only required "certify only on zero findings", zero-cost permanent abstention would make the risk optimization degenerate, and the optimality below would not hold. The report discusses the worst-case probability of an erroneous certificate only within this non-degenerate output class, and does not claim to cover all confidence procedures.

The candidate optimal strategy randomly chooses some whole strata for a census, then spot-checks the remainder in another random stratum. First prove a lower bound for any audit design, then verify that the strategy attains it; comparing only fixed-quota schemes is not enough. Check the exact minimum sample size of SRS over the whole population, and keep it as a simple alternative.

## 2. Fixed scope and comparisons

Everywhere α=1/20, and the bad-set structure is homogeneous r-of-d. The 32 applicable cases from round eight are reused:

- threshold: r=2,3,4,5,6, N=2,5,10,20, d=2r−1, 20 cells in total.
- and: d=r=2,3,4,5,6,8,12,20, N=2, 8 cells in total.
- sharpness: N=4,8,16,32, r=N², d=2r−1, 4 cells in total.

The strata in the 16 star cases of round eight have asymmetric roles and are outside the scope of this theorem; they are explicitly listed as not applicable and cannot be used to prove optimality for general hypergraphs.

For each cell, list the optimal arbitrary-random-sampling cost, the optimal pooled SRS cost, the returned risk, and the risk with one document fewer. The first two are both exact integer optima. Also prove that a uniform prior over r documents gives a lower bound on the total-K gate for any random audit, attained by pooled SRS, so this simple reference also allows arbitrary random quotas. Import the round eight fixed-quota costs: the first 28 cells are exact, and the last 4 keep their upper and lower bounds without claiming exactness. Every comparison states its design class; hand-made constructions cannot be read as utility for a real model.

All 32 cells are kept; failures/timeouts are not dropped. Reporting only the cells with a gain is not allowed. The original 20% investment gate is not automatically retroactively passed by this round's exploration.

## 3. Compute and review budget (before the run)

- Standard-library Python, CPU, no GPU/new installs; wall-clock budget for the main table 30 seconds, target <5 seconds; expected memory <128MB, not to be called measured unless measured.
- Author unit-test budget 10 seconds, expected memory <100MB; the independent enumeration uses populations of ≤10 documents and enumerates the true document subsets and minimal bad sets, budget 30 seconds, expected memory <128MB.
- Each single risk uses exact integer binomial coefficients or Fraction, with bisection over the sample size; the largest main case has total population 65504 and bad-set size 1024. Simulated coverage must not pass as exact evidence.
- Budget for the complete integration reproduction 120 seconds, expected memory <512MB; main-line model training is not rerun. The real exit code of every command is logged.

Write the proofs and the kernel first, then run the main table, and finally have it reviewed by a review program that does not import the author's kernel. Hashes of the source code, protocol and old inputs are written into the results. If something passes only finite enumeration, it is called only implementation support; generality relies on pen-and-paper proofs and is not claimed as formal verification.

## 4. Adversarial questions that must be answered

1. Does the uniform minimal-bad-set prior really give a lower bound for any random design? Can the risk of extreme quotas be made the same for every bad set by symmetrization?
2. Are r=1, N=1, m=0, full audit and the ≤m hard budget handled correctly? Does the zero-result path of an adaptive design change the lower bound?
3. If the bad set can be chosen after seeing the sampling result, if labels can be wrong, or if stratum sizes or costs are unequal, which parts no longer hold?
4. What are the boundaries between the mandatory-certificate-on-all-zero convention, the actual certification probability and historical provenance facts?
5. Does the simple optimal strategy show again that the complex audit framework is not necessary? With no network access, no novelty judgment is made, and the conditional theorem is not equated with a finished financial language model.

Deliver the proofs, the complete 32-row table, the exact program, an independent review and a revision of the conclusions.
