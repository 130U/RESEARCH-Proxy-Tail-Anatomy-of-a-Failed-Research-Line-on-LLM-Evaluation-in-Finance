# T1A computation conventions (fixed before execution)

This is a review and extension done after the T1 results were observed, not a new pre-registered confirmatory test.
The only input is T1's `results/per_question.jsonl`; sources are not rebound and its exclusion rules are not changed.

- Main rule: differentiate the original program with respect to its shared input variables at the displayed center; the first-order radius is `sum(abs(gradient_i)*halfwidth_i)`; add the offset from the center to the gold and compare with `tau*abs(gold)`. No fitted constants.
- The simple growth-rate rule is reported separately: `delta=abs(b-a)/(h_a+h_b)`, and `delta < 1/tau` predicts out of tolerance; the corrected rule does not replace this rule's misclassification rate.
- All analyzed rows are kept. When comparing with T1, only `certified_inside` and `witnessed_outside` are treated as decided labels; the 15 unresolved items are listed separately.
- New ranges use exact rational arithmetic: for linear-fractional functions of degree at most one in each variable separately, with all program denominators away from zero within the box, exact extrema are obtained at the four corners/multidimensional corners; or monotonicity is proven from sign-definite derivative intervals to obtain exact extrema. Otherwise, interval envelopes certify stability and real interior points certify out of tolerance, and unresolved is kept.
- Tolerances are fixed at 0.1%, 0.5%, 1%, 2%, 5%. The same gold is used for all tolerances. Only strict crossing is judged outside; a boundary point in the closed interval does not count as out of tolerance.
- Per-question output of first-order rule misclassifications and simple delta rule misclassifications, with reasons identified from formula structure, unequal precision, gold offset and the remainder; thresholds are not tuned to make results pass.
