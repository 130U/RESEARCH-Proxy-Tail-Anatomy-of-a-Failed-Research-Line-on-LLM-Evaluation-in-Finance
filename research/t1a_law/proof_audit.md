# T1A mathematical review record

Date: 2026-11-16 (America/New_York). The objects of review are PROOFS.md and the Benford piecewise integral; this record uses the "mathematical proof review" skill's method of splitting into units, an assumption ledger, counterexample checks and closing out fixes. The proofs are a single Markdown document with formula labels D1–D3, I1, T1–T25; there are no cross-references to appendices, no unexpanded proof sketches, and no need for a LaTeX indexer. The mathematical writing and the algebraic/numerical self-review were done in one pass; the Benford implementation was written separately and is reviewed independently here. This is not an external expert review.

## 1. Dependency and assumption ledger

| Unit | Depends on | Required assumptions | Method and status |
|---|---|---|---|
| T1–T3: four-corner range, maximum radius | D1, I1 | Denominator does not touch zero on the whole box; the relative form also needs a non-zero center growth rate; opposite signs and unequal widths allowed | Monotonicity, construction of attainable corners; **Verified / COMPLETE** |
| T4–T8: first-order term, remainder, two-sided range | I1, T2 | The two-sided simple form additionally requires both inputs to have the same sign and the corresponding numerator interval not to cross zero | Algebraic identities and uniform inequalities; **Verified / COMPLETE** |
| T9–T13: last-digit unit rules | T3 | The same-unit simple form needs the same last-digit unit; T10–T12 need same-sign centers; the effective unit needs a positive total half-width | Direct substitution; **Verified / COMPLETE** |
| T14–T15: gold band | T1–T3 | Exact output scale non-zero; gold and displayed center kept separate | Interval containment; **Verified / COMPLETE** |
| Section 4 and T16: difference, ratio, sum, general programs | T2, linear error | The general remainder needs twice continuous differentiability; shared sources combined first | Linear extrema, integral Taylor; **Verified / COMPLETE** |
| T17–T20: digit budget | D3, T3 | Both centers non-zero; decimal digits correspond to half-a-last-digit-unit widths; precision counterfactual with fixed centers | Exact algebraic rearrangement; **Verified / COMPLETE** |
| T21–T22: uniform convolution | Independent uniform assumption | Main formula for non-zero widths; uniform/point-mass branches for degenerate cases | Rectangle clipping area and inclusion–exclusion; **Verified / COMPLETE** |
| T23–T24: growth-rate probability | T21, making the denominator positive | Independent uniform within each question; closed acceptance band; point masses handled separately | Event equivalence and CDF; **Verified / COMPLETE** |
| Section 7, T25: Benford model | T3, T18 | Full log-uniform mantissa, additional independence; same sign, non-zero growth; at least 1 digit | Exact integral of piecewise thresholds; **Verified / COMPLETE** |

The proof dependencies are D1 → I1/T1 → T2/T3 → last digit/digits/Benford; and separately D1 + independent uniform → T21 → T23 → T24. There are no cycles. All constants, signs, positive-denominator conditions and non-strict/strict inequalities in the formulas were checked item by item. Verified here means the formula has been checked under the listed assumptions; it does not mean that the financial source binding or the probabilistic assumptions have been confirmed by real data.

## 2. Corrections to the original claims and their closeout

| Issue | Severity | Why the original claim was insufficient | Final state and evidence |
|---|---|---|---|
| Δ=100 treated as an unconditional boundary | S1 | A large same-sign decline can be stable with Δ<100; positive growth can still be out of tolerance at Δ=100 | **CLOSED-WEAKENED**: T10–T12 give the exact formula and approximation conditions; two rational counterexamples in Section 2 |
| "k−log(1/g) meaningful digits" undefined | S1 | The mantissa constant can approach one digit, negative growth needs an absolute value; a relative error bound does not guarantee the rounded characters | **CLOSED-WEAKENED**: define p=−log10 R; T17–T20 give the exact budget and semantic limits |
| Offset between gold and center ignored | S1 | The symmetric center band and the gold band are not the same acceptance set | **CLOSED-VERIFIED**: T14 compares both ends exactly; T15 is marked as only a first-order prediction |
| Leading-digit Benford insufficient to identify the out-of-tolerance rate | S1 | Density within the leading digit and correlation with digits/growth rate unspecified | **CLOSED-WEAKENED**: Section 7 makes the additional assumptions explicit; marginal main model and joint sensitivity kept separate |
| CDF subtracted directly at degenerate points | S2 | If the distribution has mass at the lower acceptance bound, F(lower) wrongly counts equality as out of tolerance | **CLOSED-VERIFIED**: T24 uses the left limit; the code decides constant outputs directly |
| Within-leading-digit identification bounds are floating-point approximations | S2 | Empty/full interval decisions and endpoints use floating-point arithmetic, not symbolic certification | **Limitation made explicit**: I removed the extra empty/full decision tolerance and compares directly with the per-segment thresholds; after T25 and in the README, the double-precision numerical limitation is still stated explicitly |

After the fixes, no S0/S1 mathematical issues remain open. The original coarse rule can still serve as a zero-parameter empirical classifier, but "high empirical agreement" cannot be upgraded to an unconditional theorem.

## 3. Independent computational checks performed

Environment: 130U-FinLLM/.venv/Scripts/python.exe next to the repository, Python standard library; fixed seed 20261116. T1 files were neither read nor written, no external raw data was used, and thresholds were not changed.

Run:

~~~powershell
& '../130U-FinLLM/.venv/Scripts/python.exe' research/t1a_law/theory_checks.py
& '../130U-FinLLM/.venv/Scripts/python.exe' research/t1a_law/test_benford.py
~~~

**All 7,974 items** of theory_checks.py pass:

| Check | Count | Method |
|---|---:|---|
| T2 radius equals the maximum true deviation over the four corners | 2,000 | Exact Fraction; positive/negative denominators, positive/negative numerators, opposite signs, unequal widths |
| T4 identity, T5 remainder, T6 two-sided bound | 2,000 | Pointwise comparison with rational perturbations inside the box |
| T23 CDF versus independent rectangle clipping area | 1,967 | CDF inclusion–exclusion formula against independent polygon half-plane clipping and shoelace area; exact fractions equal |
| T19 digit inequality equivalent to the T3 radius condition | 1,000 | Across decimal exponents, 1–8 digits and five tolerances |
| T11 equal-last-digit threshold equivalent to the four-corner radius condition | 1,000 | Rising/falling, five tolerances |
| Point masses, zero half-widths and closed acceptance boundaries | 5 | Hand-computed benchmarks |
| Counterexamples in both directions for Δ=100 | 2 | Exact rational comparison |

Independent Benford integral check: 100 settings with positive/negative growth (ensuring same-sign year-over-year quantities), 1–6 digits, unequal precision, five tolerances; 32,768 log-mantissa midpoints per setting, 3,276,800 synthetic points in total. The four-corner growth rate was computed directly at each point and compared with the production code's analytic piecewise integral:

- Maximum absolute error: 0.000021205411849356537 (about 0.00212 percentage points).
- Pre-set discretization error tolerance: 3/32768 = 0.000091552734375.
- All 100 settings pass; we also checked that the log-uniform and within-leading-digit uniform results fall inside the numerical interval of the leading-digit model.

This independent integral was first run as an inline script with the same content, and was then saved as test_benford.py for replication. The numerical checks are a counterexample search and implementation verification; the general mathematical conclusions rely on the complete proofs in PROOFS.md and are not replaced by random samples.

## 4. What was checked and what was not

Checked: the full mathematical derivation, key degenerate cases, the digit budget, unequal widths, the gold offset, the closed-form probability under uniform errors, and the Benford integral implementation.

This record did not review the source binding/category decisions of all empirical programs, model outputs, or T1B's full-text constraints; it did not verify that real filing rounding errors are independent and uniform or that their mantissas follow Benford. The full empirical confusion table and the expected fractions must still be supported by the project's main run and recomputation report.

**Review conclusion after fixes: CONVERGED.** Every S1 listed in this record was closed by explicitly weakening the original claim or adding exact conditions; the corrected theorem was not passed off as the task's original unconditional slogan.
