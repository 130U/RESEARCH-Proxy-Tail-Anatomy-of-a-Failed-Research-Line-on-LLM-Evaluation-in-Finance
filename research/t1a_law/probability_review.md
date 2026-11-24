# Independent review of the probability implementation

Review date: 2026-11-16 (America/New_York). The object of review is `probability.py`; the independent review script is `test_probability.py`. The implementation under review was not modified, and no T1 code modules were used.

**Conclusion: under the explicit independent continuous uniform rounding model, the checked parts pass.** These are probabilities within a mathematical model, not an empirical distribution of the last digits of actual filings, and not the probability that a model answers wrongly.

## Derivation and boundaries

For a linear-fractional `f=N/D` with a denominator of fixed sign, let `s=sign(D)`; then `f <= t` is equivalent to `s(N-tD) <= 0`. The implementation also multiplies by `s` for negative denominators, so the direction of the inequality is correct. After a linear transformation of two independent uniform variables, their weighted sum has a trapezoidal/triangular distribution; the piecewise quadratic CDF is continuous and normalized, degenerates to a single uniform distribution when one weight is zero, and to a point mass when both weights are zero.

The out-of-tolerance event is written as `P(f < lo) + 1 - P(f <= hi)`, which matches a closed acceptance interval; it is also correct when a constant falls exactly on either endpoint. Repeated references to the same variable use the same symbol and the same batch of samples; shared variables were not wrongly split into independent variables. The gold offset is kept in the acceptance interval. The closed form is refused for denominators whose sign is not fixed.

Symbolic simplification may remove a removable singularity of the original program at a single zero; in the continuous uniform model, the zero set of a denominator that is not identically zero has measure zero, so the probability is unchanged. But this does not support a worst-case statement that the program is defined at that point. In this run the range certificates for the main sample check the whole program's denominators separately; the closed-form probability does not replace the range certificate.

## Independent tests actually run

Command (working directory is the repository root):

```powershell
& ../130U-FinLLM/.venv/Scripts/python.exe research/t1a_law/test_probability.py
```

All 8 tests pass, covering zero weights, constants, cancellation of the same variable, two independent variables with the same center, zero growth, negative denominators, a non-central gold, `const_m1`, and refusal for denominators crossing zero.

The independent oracle is not another copy of the same CDF: it clips half-planes on the unit square with `fractions.Fraction` and integrates exactly via polygon areas.

| Test | Result |
|---|---:|
| 80 synthetic linear-fractional functions × 3 acceptance intervals, against rational areas | 240 bands, maximum absolute difference `2.22e-16` |
| Fixed equally spaced sample of 42 real questions with at most two variables; 38 fit the closed form × 3 tolerances | 114 bands, maximum absolute difference `2.25e-13` |
| For each of the 38 above, 65,536 independently drawn points, against the closed-form probability | Maximum deviation of 1.581 theoretical MC standard errors; all within the preset 6 SE + 2/n range |

The selection rule does not depend on the out-of-tolerance probability or the original decision. The check data come only from T1's `results/per_question.jsonl`.

## Qualifications on exactness in the report

- `closed_form_affine_fraction` denotes a closed-form computation; the implementation ultimately uses double-precision floating point, so it cannot be called a "rational exact probability". The error checks above support the numerical precision for this task, but give no formal error certificate for each floating-point operation.
- The MC Wilson intervals describe only the sampling numerical error under the given rounding model. Independent seeds across questions make the aggregate MC errors additive; the reported aggregate SE is an estimate, not a confidence interval about the true-value distribution of actual filings.
- MC observing no out-of-tolerance cases does not mean the probability is strictly zero; it cannot be used to prove determinacy. Worst-case decisions should rest on the range certificate.
- Excluded questions have no verifiable probability defined; the lower/upper bounds over all questions assign 0/1 to the excluded questions, respectively. These are coverage bounds for missing items, and the lower bound cannot be called a complete probability estimate for all questions.

No error was found that should block delivery of the probability results.
