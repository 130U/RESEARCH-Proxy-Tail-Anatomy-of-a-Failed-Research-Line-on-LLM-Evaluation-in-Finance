# T1 mathematical review: which "out-of-tolerance" cases can be certified

Date: 2026-11-16 (America/New_York). Scope: the task definition, the rounding model, the growth-rate derivation and the execution algorithm; this file contains no FinQA/TAT-QA measurement results. The mathematical proofs were checked assumption by assumption, quantifier by quantifier and constant by constant; the derivations below are an independent check done here, and are not a claim of mathematical novelty.

## Conclusion

T1 can produce a meaningful benchmark sensitivity audit, but "the interval-arithmetic outer envelope exceeds the tolerance" cannot be counted directly as "the answer is not determined by the document". We recommend reporting separately: **certified inside the tolerance, has a consistent out-of-tolerance input witness, not yet resolved**. The strongest first-round conclusion that can be supported is "under the stated rounding-box model, the reference answer is not robust to changes in the hidden last digits of the source numbers". That does not automatically mean an annotation error, insufficient information in the whole report, or that no model could answer.

## 1. Three objects that must be kept apart

Write x for the vector of displayed values, f for the gold program, f(x) for the result of direct computation on the displayed numbers, and y_gold for the stored gold answer. Assume each true source quantity lies in its rounding interval, and that there are no other constraints apart from explicitly merged same-source quantities; this gives the box B. The set of truly reachable answers is R = {f(z): z∈B, the program is defined at z}. Ordinary interval execution gives I, with R⊆I.

For a fixed scoring acceptance set C:

- I⊆C: enough to prove that every defined answer in B passes.
- Finding z∈B with f(z)∉C: enough to prove that an out-of-tolerance answer exists.
- I⊄C but no witness found: can only be recorded as unresolved, and cannot be counted among proven out-of-tolerance cases.

Counterexample: one source quantity X∈[9.5,10.5], with f(X)=X/X identically 1. Naive intervals give [9.5/10.5,10.5/9.5], which crosses the 1% tolerance, but no consistent input witness exists. The same holds for same-source X−X. Keeping the identity of one variable only ensures consistency of scalar witnesses; ordinary interval evaluation can still lose dependencies, so we cannot claim to have removed outer-envelope inflation.

Also, R⊄C_gold only says that this gold center cannot be guaranteed to pass. It is not equivalent to "no single predicted value can satisfy the tolerance for all possible true values". The latter is a different question with stronger quantifiers, and requires intersecting the acceptance intervals over all candidate predictions.

## 2. The rounding box is a conditional model

For a rounded displayed number d with last-digit unit u, take the closure [d−u/2,d+u/2] as a safe outer envelope. The actual tie rule means that one or both endpoints are not in the preimage of that displayed number. So after using endpoints to find an out-of-tolerance case, the witness should be shrunk into the interior of the interval and checked to still be out of tolerance; an out-of-tolerance case that occurs only at an unattainable endpoint does not count as empirical evidence.

u should be recovered from **the original document string and its unit**; precision cannot be inferred back from the parsed float, normalized constants in the program, or exe_ans.

| Case | Handling |
|---|---|
| "12.3 million" | The amount interval is [12.25,12.35] million; converted to dollars, the half-width is 50,000 dollars |
| "1.0%" | The half-width is 0.05 percentage points; if the program uses a ratio, it is 0.0005 |
| Years, the number of years the question asks for, item counts, the program's const_100 | Should be exact quantities according to their semantics; do not automatically add or subtract 0.5 just because there is no decimal |
| The same source quantity referenced several times by the program | All references are bound to one variable and share one value in the witness |
| Two different cells that happen to both display 10 | Cannot be merged into one variable merely because the numbers are equal |
| Parenthesized negatives, dashes, footnotes, missing values | Explicit parsing rules; when zero and missing cannot be distinguished, leave as unparsed |
| Known constraints such as totals, components, non-negativity | If ignored, the box is an outward expansion of the document's feasible region; the report must keep this qualification |

"Independent" here is the assumption of a Cartesian-product feasible region, not random independence. A rounding interval does not by itself give a uniform distribution, and does not allow the possibility of some endpoint to be interpreted as a probability.

When the same quantity is disclosed in several places at different precisions, it can be merged into one source quantity only if the entity, metric, period, currency, consolidation scope and unit all agree. The correct joint information is to convert to a common unit and **take the interval intersection**. An empty intersection should be recorded as a disclosure/mapping inconsistency; one cannot just take the union. A crossing obtained by computing separately with different locations of occurrence is "source-choice sensitivity", not the same as the whole document still being indeterminate. Close values alone are not enough to confirm the same quantity.

## 3. The scoring rule must not be misstated

The official FinQA `eval_program` checked here rounds the final numeric result to five decimal places; `evaluate_result` compares that result directly with `qa.exe_ans`. The code includes add, subtract, multiply, divide, exp, greater and four table operations. It is not scoring by 1% relative error, nor scoring by the displayed digits of the human answer string. [Official code, pinned version](https://github.com/czyssrs/FinQA/blob/dfc5b72c01ee17c442d28d5201b82a1f4e95d5af/code/evaluate/evaluate.py)

So the two rule sets required by T1 should be called this study's two tolerance-sensitivity analyses, not FinQA's native rules:

1. Relative error with the gold as reference: C_rel=[y_gold−0.01|y_gold|,y_gold+0.01|y_gold|]. When y_gold=0 this is the single point {0}; zero answers should be listed as a separate group, and an epsilon cannot be added after the fact to rewrite the threshold.
2. d decimal places according to the gold's original display format: the pass condition is Q_d(y)=Q_d(y_gold), with the tie convention (half-even, half-up, etc.) frozen. If the answer is a percentage, the decision must be made on the displayed percentage scale, or the whole acceptance cell must be transformed to the ratio scale together. A 1.20 that has already been converted to a float cannot recover its two-decimal format.

FinQA's native five-decimal rule can be reported in addition, keeping its distinction from the human answer format. Python binary floating-point rounding and the exact decimal tie rule can differ at the boundary; a claim to reproduce the native rule should be checked against the original implementation, and an exact-rational version should not be called bit-for-bit identical.

Before formally attributing anything to input rounding, first check whether the center f(x) satisfies the corresponding gold rule. Questions whose center is already inconsistent should be listed separately as baseline-inconsistent; otherwise their out-of-tolerance status cannot be attributed to changes in hidden last digits.

## 4. Growth rate: exact result and the half-unit factor

Let g(a,b)=(b−a)/a=b/a−1, a≠0. The true inputs are a+δa and b+δb, with |δa|≤h_a, |δb|≤h_b and h_a<|a|. Putting over a common denominator directly gives

```math
g(a+\delta a,b+\delta b)-g(a,b)
=\frac{a\delta b-b\delta a}{a(a+\delta a)}.
```

On an independent rectangular box, the exact worst-case absolute deviation is

```math
E_{\max}=\frac{\left\vert a\right\vert h_b+\left\vert b\right\vert h_a}{\left\vert a\right\vert(\left\vert a\right\vert-h_a)}.
```

Proof: the triangle inequality and |a+δa|≥|a|−h_a give the upper bound. Take δa=−sign(a)h_a to minimize the absolute value of the denominator; when b≠0 take δb=sign(b)h_b, so that the two numerator terms point in the same direction and the bound is attained; when b=0 choose either δb=±h_b. If the source rounding excludes the endpoints, this is an attainable supremum that interior points approach.

The first-order term is

```math
E_{\mathrm{first}}=\frac{\left\vert a\right\vert h_b+\left\vert b\right\vert h_a}{a^2},\qquad
E_{\max}=\frac{E_{\mathrm{first}}}{1-h_a/\left\vert a\right\vert}.
```

When the two inputs have the same **full rounding unit** u, h_a=h_b=u/2, and therefore

```math
E_{\mathrm{first}}=\frac{u}{2}\frac{\left\vert a\right\vert+\left\vert b\right\vert}{a^2}.
```

If "rounding unit" in the task's expression means the full last-digit unit, the expression is missing a factor of 1/2; if it was meant as the half-width, it is correct. The expression is the absolute sensitivity times the perturbation size, not a dimensionless relative condition number. The first-order error relative to the growth rate itself, with equal half-widths, is

```math
\frac{E_{\mathrm{first}}}{\left\vert g\right\vert}
=h\frac{\left\vert a\right\vert+\left\vert b\right\vert}{\left\vert a\right\vert\,\left\vert b-a\right\vert},\quad b\ne a.
```

If each input is constrained by a relative error ε, the componentwise relative condition number is 2|b|/|b−a|. When growth is close to zero, relative-tolerance failures can be very numerous even if the absolute error is small; the absolute width in percentage points must be reported as well.

The full reachable interval is given by the minimum and maximum of the four vertex values `(b±h_b)/(a±h_a)−1`. Proof: for fixed a the function is monotone in b; for fixed b its derivative with respect to a is −b/a², which does not change sign; the denominator interval does not pass through zero, so the extrema move to the vertices coordinate by coordinate. When a>h_a and b−h_b≥0 this simplifies to

```math
g_{\min}=\frac{b-h_b}{a+h_a}-1,\qquad
g_{\max}=\frac{b+h_b}{a-h_a}-1.
```

Hand-made example (not a data result): a=100, b=110, h_a=h_b=0.5. The displayed growth rate is 10%, and the true growth range is [6/67,22/199]≈[8.9552%,11.0553%]. The example shows the amplification when the difference is small relative to the scale of the values; it provides no evidence about frequency in FinQA. The formula passed checks on 80 exact-rational settings with positive, negative and zero b, with 441 interior points each; this is only an algebraic check, and the proof still rests on the argument above.

## 5. Certification methods that can be implemented within a day

1. Build `Fraction` objects from the original decimal strings, and use rationals for half-widths and acceptance boundaries too. Store input values, source locations and program references separately.
2. Build a DAG; keep identities when the same source variable or intermediate node is reused. Compute the center first and check the baseline result.
3. Use exact rational interval addition, subtraction, multiplication and division to get the outer envelope. If the whole envelope is inside the acceptance set, safety is certified. When the outer envelope of a division's denominator contains zero, we can neither report a finite range directly nor count it directly as unstable: this may be a spurious singularity caused by dependency inflation.
4. For questions with few variables, enumerate near-vertex interior points (for example half-width times 999/1000) within the same source-variable system and execute exactly as scalars. One out-of-tolerance witness is enough to certify existence; save that input vector and output for recomputation. The absence of a witness does not prove safety.
5. For growth rates, use the exact formula of the previous section. For a general rational function, vertex enumeration can be promoted to a complete proof of the extrema only when monotonicity is proven, or when after simplification the numerator and denominator are both of degree one in each variable and the denominator does not change sign on the whole box. A general DAG does not satisfy this condition: for example, the maximum of x(1−x) on [0,1] is in the interior.
6. Questions still unresolved can have their input boxes split and be interval-certified again; when the computation limit is reached, keep them as unresolved. Non-integer powers need a separate reliable interval implementation; ordinary floating-point `pow` cannot pass for a rational certificate. Boolean comparisons and unsupported table operations should be counted separately, and must not be quietly put into the denominator of numeric safety.

Algebraic cancellation must preserve the domain of the original program. For example, x/x can be simplified to 1, but the original program is undefined at x=0; cancellation must not automatically fill in that point. The correspondence of source quantities is still a semantic premise outside the algorithm, and strict arithmetic does not correct a wrong mapping.

## 6. What kind of experiment "changing millions to thousands" is

A pure unit change: multiply the value and its half-width both by 1,000, and the growth rate and its reachable interval are completely unchanged. It adds no information.

Raising disclosure precision: the amount still represents the same true quantity, but with the number of decimals fixed and the disclosure unit changed from millions to thousands, the half-width of the true amount shrinks 1,000-fold; under small perturbations, the absolute uncertainty above shrinks approximately 1,000-fold. In an actual new disclosure the center usually also changes, and old coarse-precision data cannot recover the three discarded digits.

Fixing the old center and only dividing the half-width by 1,000 is an explicit assumption-sensitivity analysis, and cannot be called validation after a real re-disclosure. Validating the prediction requires real, more precise same-source disclosures, or artificial quantization starting from sufficiently precise original values. If the acceptance set is fixed and the boxes shrink in a nested way around the same center, one can prove that the number of non-robust questions is monotonically non-increasing; if the gold and display format are recomputed along with it, this monotonicity does not automatically hold.

## 7. Fractions and decision gates

Let N be the pre-defined total number of target numeric questions, W the number of questions with an in-model witness, S the number already certified safe, and U=N−W−S (including unparsed, unsupported or uncertified). If the model and the mapping are both correct, the non-robust fraction satisfies

```math
W/N\le p\le 1-S/N.
```

Both the fraction on the parsed subset and the bounds over the whole set should be given; reporting only the fraction on successfully parsed questions may have selection bias. An in-model witness is still not an unconditional certificate at the level of document semantics. Subgroups are classified by program structure fixed in advance, with denominators given; multi-label groups may overlap, but must not be dressed up as a mutually exclusive decomposition. For input precision, besides "significant digits" it is advisable to report h/|x|, because cancellation error is also determined by |b−a|.

The task text's "abandon if overall <2%" and "continue if some category ≥15%" can hold at the same time. We recommend freezing, before seeing results: **if any continue condition holds, continue takes priority; otherwise, abandon if the overall upper bound is <2%; in all other cases keep an intermediate or inconclusive status**. This is an explicit interpretation of the overlap in the original text, not a priority the original task already stated. The continue gate should use the lower bound of the proven fraction, and the abandon gate the upper bound of the non-robust fraction; crossing a line only with an inflated outer envelope is not a sound basis for a continue decision.

These numbers are audit fractions for a specific public dataset. Extrapolating to future reports or to financial QA in general requires a separate sampling argument; multiple questions within the same company report also cannot be assumed independent by default.

## Verified and not verified

Verified: the quantifier issue of interval outer envelopes, the growth-rate constants and exact endpoints, unit transformations, and the official FinQA evaluation code. Not yet verified: the accuracy of source-number mapping, all constraints in the original reports, the benchmark frequency, TAT-QA's actual format, novelty, and whether the contribution is enough to publish. This mathematical review cannot substitute for the unverified items above.
