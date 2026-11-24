# P2 semantic-set envelope: pre-run questions, scope and budget

2026-11-16, round six. This round studies how parsing ambiguity propagates into numeric certificates, and when the system must refuse; no new model is trained, no private source text is read, and there is no network access. All numbers from the runs belong to "our mathematical construction checks". G0/G1 are not passed, and this round does not replace a real parser, a gold-standard audit or a complete financial certificate.

## Mathematical questions to answer

Given finitely many semantic candidates, each with a fixed context/direction, a positive range for the base value, and an explicit ordered logit map, what is the smallest coordinate-wise envelope of the model output? How wide must the candidate set be before guaranteeing coverage of all candidates within a prescribed width is possible only by refusing? For a simple numeric comparison, does a direct symbolic rule already achieve the same guarantee?

Every candidate refers to **the same frozen target and the same class-label semantics and order**; probabilities from different tasks cannot be put on the same coordinate for a min/max. The code can check that the target/schema declarations agree; it cannot prove that those declarations are semantically correct. The numeric envelope contains the model's outputs on the listed candidates, not the actual labels, true probabilities or economic Greeks.

## Fixed scope

- Numbers are exact rationals via Fraction; the base-value interval for b is strictly positive, and x may be negative. Under an independent rectangle, the extremes of x/b and x/b−1 are attained at the four corners. If x and b share a dependence, this is only an outer relaxation by the rectangle; it must not be presented as still tight for the original semantic set.
- Each branch is a fixed affine logit η=a·g+c with fixed strictly increasing thresholds. For an η interval, the probabilities of the first and last classes are monotone, but the maximum of a middle-class probability can be at the midpoint between adjacent thresholds, so taking only the two ends is not enough.
- exp/sigmoid use provable rational upper and lower bounds; a libm output plus one nextafter step is not passed off as a certified transcendental-function error. When the number of terms or the numeric range exceeds the budget, the check fails explicitly and does not output an unfinished narrow interval.
- The smallest coordinate-wise box over the union of branches does not mean that the box corners lie in the probability simplex or can be attained simultaneously. Discrete semantic ambiguity cannot be hidden by a numeric radius of 0.
- The width gate distinguishes "proven acceptable / proven too wide / numeric precision insufficient to decide". An upper envelope wider than the threshold is not enough on its own to prove that the true minimum width exceeds the threshold.
- When finitely many branches persist in correspondence, a common monotone direction and Lipschitz bound carry over to the upper and lower envelopes; branch switching/disappearance can cause jumps, and local Greeks cannot cover such changes.
- The robust width lower bound and the maximum acceptance rate are first of all conclusions relative to **the candidate set that must be covered in full**. If candidates are over-reported, this only shows that the current abstraction is conservative; it does not prove that the natural text is intrinsically unidentifiable.
- The parse-set coverage failure rate is kept separate from the audit confidence error α; only after the width acceptance rule is fixed can the accepted subpopulation be audited. There is no real semantic audit, so this round does not fill in a deployment error rate.

## Pre-specified controls and checks

1. A counterexample where the middle-class peak falls inside the interval.
2. Numbers fully exact, semantic branches different, and the joint probability interval still wide.
3. The exact relation x=b for the same quantity, compared with the envelope of the independent rectangle after the dependence is lost.
4. When x and b in the same unit are scaled together by a positive rational factor, the canonical features and all computed envelopes are unchanged; this only checks the tuple transformation and does not claim invariance of natural-text parsing.
5. A counterexample where every branch is monotone but the selector jumps downward as the input switches branches.
6. A candidate set on which the symbol sign(x−b) decides consistently, and a conflicting candidate set that must be refused; the task is not changed in order to keep a learned head.
7. A width–acceptance-rate table for the finite frozen candidate task, keeping numerically undecided cells, without picking the best-looking cells as success.

These are pre-specified mathematical controls, not a model contest on a natural corpus. Numeric exactness, coverage of the candidate truth, and empirical usefulness are each accepted separately.

## Budget

Pure standard library on CPU, target ≤60 seconds for all construction checks; at most 200 semantic branches and 256 extra rational grid points. No GPU/API/model-training tokens. Expected memory ≤100MB, recorded only as a budget unless measured. Default endpoint tolerance 1e−12, at most 1,000 Taylor terms, absolute value of a single exp argument at most 50; these limits are implementation budgets of the checker, not the domain of validity of the mathematical theorems. The implementation may guarantee loosening of the reported endpoints under a smaller internal tolerance, with a clear proof.

Stop/fix conditions: any parsed support point falls outside the computed interval; a middle peak is missed; success is still returned after the numeric budget is exceeded; float/bool is implicitly turned into an exact rational; tasks/schemas are spliced together; the computed upper-envelope width is mistaken for an unavoidable exact width. When a problem is found, keep the counterexample and the fix and narrow the claim if needed; do not silently delete test points.

The deliverables are conditional proofs, an executable rational-envelope checker, a frozen construction record, an independent review, and the open questions. No originality is claimed on this basis for basic tools such as monotonicity, interval arithmetic or the minimax radius.

## Main-run frozen details and check-budget supplement

The main run uses the full 25-cell grid r∈{0,1/10,1/2,1,2}, d∈{0,1/4,1,2,4}: each cell has two semantic branches g∈[−r,r] with logits g−d and g+d, and fixed three-class thresholds (−1,1). All cells have equal weight; only the relative candidate acceptance rate of the hand-made task is summarized, and no distribution over a natural corpus is inferred. The main width gate is 0.10; 0.05/0.20 are only sensitivity columns listed alongside it, and the best of them is never picked to announce success. The seven kinds of minimal counterexamples and controls listed above are also kept.

The independent review uses a different rational scaling–squaring implementation to check the main numeric algorithm, and the implementation's unit tests check another 139 ratio/η grid points. To keep cross-evidence from an independent algorithm, the combined check budget of 256 points in the first draft was explicitly enlarged to 500 points before execution; the main runner adds no extra dense grid; the mathematical task and the 25 cells are unchanged, and the total CPU target is still ≤60 seconds. This budget enlargement was recorded before the main runner and the final unit suite were executed, and no case was chosen based on any financial performance.

Count erratum after review: the independent review actually used 24 branches × 9 points = 216 internal support points; because the branches have different K, there were 729 coordinate-containment checks in total. Earlier, 729/3 was wrongly counted as 243 points; this is now corrected; 216+139=355 points is within the enlarged 500-point budget. Only the count is corrected; no case is deleted or added, and the content of the first main run is unchanged.
