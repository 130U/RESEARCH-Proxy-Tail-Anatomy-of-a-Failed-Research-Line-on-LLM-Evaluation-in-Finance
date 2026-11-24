# T1A: displayed precision and answer precision

Entry point for the conclusion: [one-page summary](ONE_PAGE.md). Branch `task/t1a`. Code and deliverables are all in this directory; the T1 files keep their `task/t1` baseline content unchanged. We did not rebind inputs, train models or call paid APIs.

## Results and scope

The input reads only the 8,281 rows of `research/t1_rounding/results/per_question.jsonl`; of these, 5,337 rows are analyzable and 2,944 are excluded. The excluded rows were not assigned as stable or zero-probability. Because the results had been observed before this task, this work is called a review and extension; it does not claim to be a new pre-registered confirmatory experiment.

| Growth-rate definition | Questions | Use |
|---|---:|---|
| T1's growth label | 1,458 | Keeps the original category; full confusion table |
| The label above and two inputs | 1,434 | Includes 9 originally undecided items |
| The above and decided by T1 | 1,425 | Replication of the original 97.8% and the four-bin table; Δ computed directly on the original inputs |
| Algebraically equal to ±1 or ±100 times `(b/a−1)`, units harmonized | 1,427 | Exact growth-rate rule, digit budget, Benford |
| Original T1 strict `subtract(b,a), divide(#0,a)` structure | 1,307 | Explains the denominator difference from the earlier growth_summary |

All 1,427 standard growth rates have same-sign, non-zero inputs; the Benford model excludes 31 growth-labeled questions that do not have this structure. Its observed 1% rate is 578/1,427=40.5046%. The per-item misclassifications of the original replication and of the standardized rule are 31 and 29, respectively, and must not be mixed.

The main zero-parameter rule is `abs(center-gold)+sum(abs(gradient_i)*halfwidth_i)>tau*abs(gold)`. For repeated variables, partial-derivative coefficients are combined first, then absolute values taken. At 1% this rule agrees with all 5,322 originally decided labels and with all 5,337 independently recomputed labels; all 15 originally undecided items become inside. Ignoring the gold offset gives 1 error.

The new range certification uses rationals: for 5,330 questions, sign-definite derivative intervals prove that the extrema are at corners; for 7, the property of being linear-fractional in each variable separately proves it. We always check that the original program's denominators are defined within the box; out-of-tolerance outer envelopes were not treated as actual out-of-tolerance cases. Exact tangency at the boundary counts as inside; strict crossing yields an interior witness by continuity.

The first-order rule has no general 100% guarantee. For example, with `a=100,b=300,h_a=h_b=0.5,gold=2,tau=0.01`, the first-order radius is exactly 0.02 and predicts inside; the true upper end `300.5/99.5−1≈2.0201005` exceeds 2.02. At tolerances of 0.1%, 0.5%, 1%, 2% and 5% on this data, the numbers of misclassifications are **2, 0, 0, 2, 1**; see the [per-item records](results/first_order_tau_mismatches.csv).

## Distributional prediction and probabilities

The Benford main model independently draws from the empirical marginal of growth rates and the empirical `(k_a,k_b)` digit pairs, and then independently draws `log10(M_a)~Uniform[0,1)`. Let `a=M_a,b=(1+g)M_a`, and build the last-digit units from each input's significant digits. The predictor does not read the original question's mantissa, the gold or the deterministic labels; the original range labels are used only in the comparison step. The exact threshold is integrated analytically by splitting at the decimal boundaries of the mantissa, with no parameter fitting.

This is stronger than "the leading digit follows Benford", and it also assumes that growth rate and digit counts are independent. The main prediction is 41.5192%, the joint-empirical-distribution sensitivity is 42.0971%, and the within-leading-digit uniform sensitivity is 41.3635%; the observed value is 40.5046%. Giving only the leading-digit probabilities while keeping the other independence assumptions above, the numerically identified range is 38.6904%–44.5891%, with the endpoints computed piecewise in double precision. Substituting the test distribution alone gives predicted/observed 40.0984%/40.3587%; this is still not extrapolation to test after fitting on train. At 1% the observed counts for the center band and the gold band are the same; other tolerances are kept separately in the JSON.

The probability is defined as the probability that the original program's output falls outside the gold acceptance band when each question's inputs take independent uniform values in the input box. **4,787 questions are computed with the closed-form CDF for linear-fractional functions of at most two variables (double precision), and 550 questions use 262,144 independent pseudo-random samples each.** Seeds are determined by a fixed prefix, the split and the ID; references to the same source share samples. Summing the probabilities does not require the true errors to be independent across questions; independent random numbers across questions are used only to control computational error.

Over all analyzable questions at 1%, the expected number out of tolerance is 731.4699/5,337=13.7056%, and the worst case is 1,469/5,337=27.5248%. For test the corresponding values are 98.6177/731=13.4908% and a worst case of 196/731=26.8126%. The estimated Monte Carlo standard error of the test expected fraction is about 0.00038 percentage points; this is only in-model computational error and does not include uncertainty from source binding, the uniform assumption, or the distribution of real filings. Per-question Wilson intervals are in the output; zero MC hits do not mean a strictly zero probability.

| Tolerance | test worst case / 731 | test uniform-model expectation / 731 | Expected questions |
|---|---:|---:|---:|
| 0.1% | 55.68% | 38.35% | 280.32 |
| 0.5% | 34.88% | 19.70% | 144.00 |
| 1% | 26.81% | 13.49% | 98.62 |
| 2% | 18.88% | 8.12% | 59.32 |
| 5% | 9.71% | 3.10% | 22.68 |

The original 17.09% uses the denominator of all 1,147 test questions. With the same denominator, the analyzed part contributes 8.60% under the uniform model, but the probability for the 416 excluded questions is unknown, so the coverage bound for all of test is 8.60%–44.87%; this is not a complete population probability estimate. Both the existence and the probability versions depend on the input box; they must be recomputed after T1B tightens the full-text constraints.

## Replication

Verified with Python 3.12.14, NumPy 2.5.3 and SymPy 1.14.0; plotting uses Matplotlib 3.11.2. Using a normal Python environment, run from the repository root:

```powershell
python -m pip install -r research/t1a_law/requirements.txt
python research/t1a_law/analyze.py
python research/t1a_law/benford.py
python research/t1a_law/probability.py
python research/t1a_law/plot_results.py
python -m unittest discover -s research/t1a_law -p "test_*.py"
python research/t1a_law/theory_checks.py
python research/t1a_law/test_benford.py
```

The first three analysis scripts support `--input` and `--output-dir`; the probability script defaults to `--samples 262144`. All default empirical inputs are the original T1 JSONL; the T1 analysis code is not read or imported. Rerunning with standard output replaces the derived results in this directory; the inputs are not changed. Scientific-notation and floating-point text may differ in the last digit across dependency versions.

The rational tests of the core formulas cover growth-rate corners, same and opposite signs, unequal precision, the remainder and the digit budget. The independent probability test uses rational polygon-clipping areas as an oracle; 240 synthetic acceptance bands and 114 real-question acceptance bands all pass. The independent numerical review executes 24,674 corners and agrees with all saved extrema; symbolic derivatives were also used to check 240 questions. These are implementation checks for this task; we do not claim external human review or formal proof.

## Files

| Content | File |
|---|---|
| One-page summary, proofs, prior-art check | [ONE_PAGE.md](ONE_PAGE.md), [PROOFS.md](PROOFS.md), [LITERATURE.md](LITERATURE.md) |
| One three-panel figure | [PNG](results/t1a_law.png), [PDF](results/t1a_law.pdf) |
| Per-question exact range, rule, and labels at each tolerance | [per_question.jsonl](results/per_question.jsonl) |
| Full confusion table and original replication | [summary.json](results/summary.json), [mentor_replication.csv](results/mentor_replication.csv) |
| Misclassifications of the original rule of thumb, after unit harmonization, and of the first-order rule at other tolerances | [simple_rule_mismatches.csv](results/simple_rule_mismatches.csv), [canonical_simple_mismatches.csv](results/canonical_simple_mismatches.csv), [first_order_tau_mismatches.csv](results/first_order_tau_mismatches.csv) |
| First-order misclassifications at 1% (zero rows, header kept) | [first_order_mismatches.csv](results/first_order_mismatches.csv) |
| Benford distribution inputs and comparison | [benford_summary.json](results/benford_summary.json), [benford_inputs_and_outcomes.csv](results/benford_inputs_and_outcomes.csv) |
| Per-question probabilities, numerical error and summary | [probabilities.jsonl](results/probabilities.jsonl), [probability_summary.json](results/probability_summary.json) |
| Tolerance curves for each split | [tolerance_curve.csv](results/tolerance_curve.csv) |

Cancellation and significant-digit theory are classical results; the rounding distortion of economic growth rates also already has a [1991 Chicago Fed study](https://www.chicagofed.org/-/media/publications/economic-perspectives/1991/ep-may-jun1991-part1-gittings-pdf.pdf). The usable claim of this project is a conditional benchmark precision audit; "first" or "no precedent" cannot be inferred from this prior-art check. The pinned official FinQA version uses [comparison of the five-decimal execution result](https://github.com/czyssrs/FinQA/blob/0f16e2867befa6840783e58be38c9efb9229d742/code/evaluate/evaluate.py); this directory does not call the 1% audit convention the official scoring rule.
