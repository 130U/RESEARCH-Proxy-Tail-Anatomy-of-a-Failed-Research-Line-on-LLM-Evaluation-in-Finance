# T2: pre-execution design audit

2026-11-16 (America/New_York). Internal independent AI design audit; no T2 scores or experimental results have been produced yet. This page only audits the interpretation of the measurements and does not make the literature-novelty judgement. The experimental revisions below apply only if the prior-art check does not trigger the stop condition.

## Charter

- Goal: identify design gaps that would change T2's "continue / drop" conclusion, and give the minimal revisions.
- Scope / object / unit: behavioural measurement on financial text / change in the model's sentiment score caused by a numeric change / paired differences between the same semantic template, values and equivalent representations.
- Type: descriptive design audit, following on from the main task's exploratory prior-art check; all recommendations are unexecuted plans.
- Questions: Q1 Do the numeric changes keep the economic semantics comparable? Q2 Can the observed differences be separated from representation, batch and retest fluctuation? Q3 Can the decision gate support the claimed conclusion?
- Acceptance: each key issue corresponds to a concrete counterexample or a source that was read; the recommendations do not treat a non-significant difference as evidence of "well-behaved".

## Canonical sources

| Priority | Source read | Use / boundary |
|---|---|---|
| 1 | The T2 task statement, read on 2026-11-16 | A/B/C design and the original decision rule; the examples in the text are not treated as a frozen complete protocol |
| 1 | [One-page summary of the previous experiment](../absolute_scoring/ONE_PAGE.md) | The same project observed batch sensitivity and boundary problems with discrete scores; cannot be extrapolated directly to T2 |
| 1 | [Frozen protocol of the previous experiment](../absolute_scoring/protocol.md) | Existing conventions: fixed model, prompt, fresh context, raw outputs, failure records |
| 2 | [SEC Investor.gov: Basis Point](https://www.investor.gov/introduction-investing/investing-basics/glossary/basis-point), full text opened | 1 bp = 0.01 percentage points; the conversion examples on this page are computed from it |

## Findings ledger

| No. | Finding / judgement | Basis | Type | Question |
|---|---|---|---|---|
| D1 | The original task does not specify the scoring scale, the perspective of the target entity, the noise estimator, the test family or an inconclusive branch | T2 "method / analysis / decision" | Textual observation | Q2, Q3 |
| D2 | A profit that falls by more than 100% from a positive base crosses into a loss; there is an economic-semantic boundary near 100 | If the initial profit is P>0, then after a fall of x% it is P(1−x/100); direct algebra | Design inference | Q1 |
| D3 | "0.5%" and "50 bp" can represent the same rate numerically, but when substituting into a change in a rate, the distinction between a percentage change and a percentage-point change must be kept | SEC definition of bp and the conversion examples on this page | Definition + design inference | Q1 |
| D4 | In the old experiment the normal-score rank correlation within the same batch differed from that across batches; the report already states clearly that this is not a pure noise share | Old one-page summary and frozen protocol | Existing experimental report; not recomputed on this page | Q2 |
| D5 | Rotating a few fixed company names does not automatically make company name orthogonal to value; four repeats are also not four independent financial events | T2's design of 5 fixed names, rotation, ≥4 repeats | Design inference | Q2 |
| D6 | "Difference > twice the noise" cannot give a unique statistical decision unless the noise and its uncertainty are defined; failing to detect a difference does not equal equivalence | T2's decision rule still lacks an estimator; the old protocol already distinguishes practical equivalence from failure to reject | Methodological review | Q3 |
| D7 | An asymmetry on a continuous bounded sentiment scale does not automatically equal loss aversion, and a local jump does not automatically equal a left-digit mechanism | T2's operation only changes the headline and measures the score; it does not measure decision utility or isolate the encoding mechanism | Inference about identification limits | Q1, Q3 |

## Scope filter

Do not expand T2 into a study of investment effects, personality psychology or model correctness. Monotonicity is a response property to be observed; in headlines lacking scale, expectations and baseline, it is not a universally valid correct financial answer. The batch sensitivity of the old study only gives a reason to set up controls; it cannot prove that T2 will necessarily be affected to the same degree. D1–D7 are kept and interpreted within these boundaries.

## Object filter

Downgrade "numeric magnitude causes model errors" to "score changes under a fixed prompt, template and model". Restrict "unit invariance" to pairs whose economic semantics are equivalent after item-by-item verification. Keep "left-digit effect" and "loss aversion" as candidate explanations for later, not as mechanisms the current design can identify. Company name, template and call batch must all be kept as levels in the analysis.

## Conclusions

**Even setting aside the collision with existing work, the current version can only support exploratory screening; it cannot directly upgrade any anomaly to a psychological law, or write up an undetected anomaly as proof of being well-behaved.** The three representations of the same amount have a fairly clear paired meaning, but this design merit does not equal research novelty and is not a reason to continue the original topic; the prior-art conclusion is in the main report. (D1–D7)

1. **The positive and negative curves must share an interpretable baseline.** `quarterly profit falls 500%` is not mathematically invalid in every case: from a positive profit base, it means the new profit is −4 times the original. The problem is that it crosses from profit to loss and cannot be treated as the purely symmetric counterpart of the ordinary growth `rises 500%`. Restrict the main symmetric range to values that do not cross zero, such as 0.1%–50%, and specify the same base period; list profit falls >100% separately as a semantic stress test. Headcounts must be integers and not exceed an explicit total number of employees; the meaning of layoffs for the company's prospects may also differ from their meaning for employees. When the absolute amount of a fine lacks the company's size, its curvature should not be interpreted as a psychological scale. (D1, D2)

2. **Proportional units require checking the sentence, not just the number.** For the same rate level, `default rate is 0.5%` and `default rate is 50 basis points` are numerically equivalent. When discussing a change, `operating margin rises from 10% to 10.5%` is equivalent to `rises by 0.5 percentage points` or `rises by 50 basis points`; "the profit margin grows by 0.5% in relative terms", however, turns 10% into 10.05%. So one cannot mechanically substitute bp into `profit rises 0.5%` and claim equivalence. The three representations of amounts can be kept, but the overall effect of commas, number of decimal places and word units should be called a "representation effect", and not used to identify tokenisation as the cause on its own. (D3, D7)

3. **100 is a possible location of an economic boundary, not a clean left-digit test.** A 100% profit fall crosses from profit to loss, and 100% layoffs involve all employees; such jumps have a semantic explanation. To test a numeric-representation boundary, prefer observing contrasts such as 9.9/10.1 in amount ranges with an explicit scale that do not trigger an economic event; also keep a round threshold like 50 that does not add a digit. For each threshold use left and right neighbourhood controls with the same spacing, allowing smooth curvature; call the result "local extra change", and do not declare a mathematical discontinuity from a two-point difference alone. (D2, D7)

4. **Positive/negative asymmetry is first of all a scale phenomenon.** A fixed scale midpoint does not guarantee that a template's empirical neutral point is exactly the midpoint. First add zero-change headlines with the same template and report `s(+x)−s(0)` and `s(0)−s(−x)`; avoid mechanical asymmetry caused by one side being close to the scale's upper/lower limit. Even if the difference is repeatable, it is still only a scoring asymmetry under that prompt and cannot directly imply loss aversion in economic utility. (D1, D7)

5. **The original binary decision must allow "inconclusive".** A model that outputs the same integer every time makes the estimated noise zero, and a one-point difference must not therefore be upgraded automatically to a large effect. Conversely, failing to detect a difference with four repeats cannot prove that the curve is smooth, unit-invariant or symmetric. Unparseable numeric input, a scale that barely discriminates, an interval that crosses the decision boundary and obvious context dependence should all go to "inconclusive", with the results kept. (D1, D6)

## Next steps / Risks

Both prior-art branches received by the main coordinator report that A and the core of the positive/negative response are already covered by existing research, so this page does not launch an experiment on the basis of the residual design recommendations. Only the conditions that would have to be met if B/C were evaluated separately later are kept below; **this is not a new execution plan**:

- Specify one model, prompt, target entity and scale; fully cross company names with values, present semantic pairs separately, fix the filler and position rules, and record the complete call inputs. The number of repeats is not an independent financial sample size. (D1, D5)
- Report separately the single-run standard deviation of same-representation retests, the mean difference between representations and its interval. "Twice the noise" is a practical threshold, not a significance theorem; controls with a fixed complete batch and re-randomised batches must not both be called pure generation noise. (D4, D6)
- The raw adjacent-inversion rate is descriptive only; a flat curve plus noise also produces inversions. Thresholds use neighbourhood controls with the same spacing; curve comparisons freeze the parameterisation and hold out value ranges, and cannot be won by the training residuals of a more flexible model. (D1, D7)
- For several pre-specified thresholds, representations or templates, report everything and control for multiple comparisons, or list an independent confirmation separately. Only a difference interval that falls inside a pre-specified practical-equivalence range supports "no important representation effect seen"; mere non-significance should be written as inconclusive. (D6)

Evidence review for this page: the sources and direct algebra support the design gaps listed; there are no T2 measurements. General model behaviour, literature novelty, the required sample size and the relative merits of the curves are not verified on this page.
