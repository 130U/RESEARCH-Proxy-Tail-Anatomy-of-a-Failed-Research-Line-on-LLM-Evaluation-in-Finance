# Independent review of the zero-parameter test

Review date: 2026-11-16 (America/New_York). Objects: `law_core.py`, `analyze.py`, and the generated per-question outputs and summaries; only T1's `results/per_question.jsonl` was read. The implementation under review and the T1 files were not modified.

**Conclusion: no implementation error was found that would invalidate the first-order rule's 5,337/5,337 agreement at the 1% tolerance in this run. That number is an observation on fixed data, not a universal exactness theorem.**

## Why the certificate holds

`interval_ad` propagates derivative intervals through the original computation graph with shared inputs. Division first requires that the whole denominator interval exclude zero; then the endpoint interval of the squared denominator is correct. Only when every partial-derivative interval has a constant sign is coordinate monotonicity used to certify corner extrema. Interval widening caused by correlation among derivatives can make certification fail, but cannot make it pass improperly.

Another 7 questions use the property of linear-fractional functions whose numerator and denominator each have degree at most one in each variable. With the other variables fixed, each coordinate section is a univariate linear-fractional function, monotone or constant on a pole-free interval. Moving each coordinate in turn to the endpoint where the output is non-decreasing/non-increasing attains the global maximum/minimum at a vertex. The implementation still requires the natural interval computation of the original program to pass, which guarantees that all intermediate denominators also stay away from zero; it does not just check the simplified expression. The expressions of the 7 questions are reciprocals, identity maps or ordinary ratios after shared variables cancel; none was seen to violate this condition.

gold uses the `exe_ans` saved by T1; the center is re-executed from the original program and asserted, row by row, to equal T1's exact center. Multiplication by 100 for percentages and unit conversions between millions and thousands stay inside the original computation graph. To replicate the earlier result, the coarse Δ rule deliberately keeps the raw input difference without unit conversion; the corrected analysis uses program derivatives separately. The two were not written up as the same rule.

## Independent execution checks

The independent check did not call `law_core.evaluate`, `gradient_radius` or `range_certificate`: a separate rational program interpreter executes all input corners of each T1 question and compares with the saved output; partial derivatives use direct symbolic differentiation in SymPy, unlike the implementation's forward-mode automatic differentiation.

| Check | Result |
|---|---:|
| T1 `analyzed` rows aligned with T1A per-question output by `(split,id)` | 5,337 pairs, none missing, none duplicated |
| Execute all rational corners independently and check the saved minimum/maximum | 24,674 corners, 0 differences |
| Rebuild the 1% acceptance band from the original gold and check corner labels | 5,337 questions, 0 differences |
| Rebuild the first-order prediction from the saved radius/center/gold and check labels | 5,337 questions, 0 differences |
| Independent symbolic differentiation on a fixed sample of every 23rd question, plus all 7 linear-fractional special cases | 240 rows checked, 506 partial derivatives compared, 0 differences |
| Question sets of the probability file and the deterministic file | Identical |
| Certified stable but probability greater than `1e-9`; closed-form probability zero but strictly out of tolerance | 0 questions each |

The agreement on the 5,322 questions already decided by the original T1 and the agreement on the full recomputation of 5,337 questions are reported separately; the 15 original `unresolved` items are kept and resolved as inside by the new certificate, and were not treated directly as exact labels of the original T1.

The first review found that `const_m1` was not parsed by `law_core.constant`; the implementation agent was notified and fixed it. The full checks above were run after the fix, and all four actual occurrences are included.

## The 31 misclassifications of the coarse rule

The per-item CSV agrees with the program structures: in 24 cases the inputs have the same sign and the same displayed unit and the finite growth cannot be neglected; in 5 cases the raw operands have different units, so the raw difference is not comparable; in 2 cases the broad `growth` label pulled them in, but the actual program is not a two-number growth rate.

After conversion according to the original program, the 5 unit cases have Δ of about 10.59, 15.76, 75.67, 39.11 and 24.43, all back in the region predicted below 100. The 2 non-growth-rate cases are programs that "deduct a percentage and then multiply by a base". The explanation for the remaining 24 errors is the omitted finite growth factor and denominator correction; this does not mean that the two terms make the same marginal contribution in every question.

## A counterexample against overextrapolation

Let `a=100,b=300,h_a=h_b=0.5`; the growth-rate center and the gold are both 2. The first-order radius is 0.02, exactly equal to the 1% tolerance, so the first-order rule predicts inside. Yet the true maximum is

```math
\frac{300.5}{99.5}-1=\frac{402}{199}\approx2.0201005>2.02,
```

so the true decision is outside. A 100% agreement on the data cannot replace the remainder or the exact endpoints; in particular, this approximate rule cannot be advertised as a certifier for arbitrary future financial programs.

The scope of the review does not include fresh manual annotation of the original input semantic bindings, tightening by full-text constraints, empirical measurement of model answers, or extrapolation across datasets.
