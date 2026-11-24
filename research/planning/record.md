# Theoretical numeric check: exact audit-size frontier for observed vote margins

Date: 2026-11-15. Status: the offline mathematical component is implemented and checked; this is not Phase 1 model training or a real-corpus certificate.

## Question and budget

Given how much contamination the actual vote margins of a fixed model can tolerate, work backwards to the minimum number of documents that must be audited in the zero-finding case. The budget was written in [budget.md](budget.md) before the run: CPU, standard library, expected within 30 seconds, 0 GPU memory, 0 training tokens.

## Definition and computation

Fix N suspect documents and an error-probability budget alpha, audit n documents, and observe x=0. The existing exact inverter defines

`K_u(0) = max{K: P_Hyp(N,K,n)(X<=0) > alpha}`.

For a non-negative integer B<N, the hypergeometric CDF is non-increasing in K, so

```math
K_u(0)\le B \iff
\frac{\binom{N-(B+1)}{n}}{\binom Nn}\le\alpha.
```

The right-hand side is non-increasing in n, and binary search returns the first integer for which it holds. The upper end of the search, N−B, makes the zero-finding probability 0. If B≥N then n=0; negative B, non-integer B/N or invalid alpha are rejected. Integer comb and Fraction are used, with no floating-point approximation of probabilities; when K=B+1<n, the equivalent form `comb(N-n,K)/comb(N,K)` is used to reduce binomial-coefficient computation. The coverage output calls the existing `audit_upper` again and checks both that n passes and that n−1 does not.

For the j-th point, let a_j be the winner under the smallest-index tie rule, and define

```math
r_j=\left\lfloor\frac{\min_{d\ne a_j}(n_{a_j}-n_d-𝟏\{d\lt a_j\})}{2}\right\rfloor.
```

The point satisfies the vote-margin certificate if and only if the given integer shard budget is at most r_j. To certify a fraction q∈(0,1], let r=ceil(qJ), take B as the r-th of all r_j sorted in descending order, and then find the minimum n. Coverage levels are discrete in r/J and are not forcibly interpolated; plateau segments are kept in the output.

**This is conditional planning.** Without knowing the true K, there is no guarantee that the audit will find zero errors, and `P_(K=B+1)(X=0)` must not be taken as the probability of actually obtaining a certificate. Any x>0 must be inverted again with the actual x. The model/population and the sampling mechanism are fixed first; this program is not an anytime-valid rule.

## Actual configuration

- The identity of the current base repository and the new components is bound by the commit in this round's overall report and by [source_hashes.json](source_hashes.json); the new planning code had not been committed separately at execution time.
- Python 3.12.14, local Windows CPU; no random simulation, hence no seed.
- Input: 4 population/vote scenarios set by hand in the script; these are not EDGAR measured counts at all.
- Generating all frontiers took 0.730 seconds; the 8 unittests took 0.086 seconds and all passed. Source level: **our experiment planning**.

## Results

alpha=1/20; everything below is exact integer output under hand-set parameters:

| Hypothetical population N | Shards m | Target coverage q | Required budget B | Minimum fixed audit n with zero findings |
|---:|---:|---:|---:|---:|
| 1000 | 11 | 1/6, 1/3 | 5 | 393 |
| 1000 | 11 | 1/2 | 3 | 527 |
| 1000 | 11 | 2/3 | 1 | 777 |
| 1000 | 11 | 5/6, 1 | 0 | 950 |
| 10000 | 31 | 1/6, 1/3 | 15 | 1707 |
| 10000 | 31 | 1/2 | 10 | 2383 |
| 10000 | 31 | 2/3 | 6 | 3481 |
| 10000 | 31 | 5/6 | 3 | 5271 |
| 10000 | 31 | 1 | 0 | 9500 |
| 20 | 2 | 1/2 | 1 | 16 |
| 20 | 2 | 1 | 0 | 19 |
| 0 | 2 | 1/2, 1 | 1, 0 | 0 |

The full input vote counts, the r_j of each point, the exact fractional gate probabilities, and the inversion results for n and n−1 are in [frontier_results.json](frontier_results.json). A point with vote margin 0 needs K_u=0; with N=1000 and alpha=.05, sampling only 950 documents with zero findings is exactly enough to exclude K=1, because the probability of missing a single error is (1000−950)/1000=.05. This is a statistical exclusion and does not prove that the population in fact has no errors.

## Check coverage

1. N=0,…,18, B=0,…,N+1, alpha∈{1/20,1/2,3/4}, exhaustive over n: the gate condition agrees with the existing audit_upper, and the minimum n agrees exactly.
2. For all K/n with N<10, the two forms of the zero-finding probability are equal; the empty-population and full-audit boundaries behave correctly.
3. For N≤30, check that n does not increase when B increases, does not decrease when alpha is stricter, and does not decrease when N increases.
4. For all three-class vote compositions with m≤8, an independent reachable-label enumeration checks that the winner is unique at the r_j budget.
5. For m=2, the half-and-half tie exception when all votes go to the smallest-index class; compared with all votes going to the other class, the radius differs.
6. Non-integer qJ is rounded up; the frontier n does not decrease with target coverage; invalid matrices, floating-point alpha/q, booleans and negative budgets are rejected.

## Conclusion and limits

This component replaces the approximate "3N/n" screen with an exact integer audit design under concrete vote margins, and shows that high coverage can be determined by a few points with zero vote margin. It does not change the contamination model, the shared-core assumption or the definition of statistical coverage, and it does not prove usefulness for any real task. The actual size of the suspect window, the model's vote margins, the quality of the timestamp audit and the audit cost still need independent evidence. This round respected the outreach restriction and did not contact anyone externally or download data.
