# P2 semantic envelope: mathematical construction run record

2026-11-16, round six. Source level: **our mathematical construction checks**. There was no natural-text parsing, real label audit, model training or network access. The pre-execution questions and budget are in [PROTOCOL](PROTOCOL.md); [SE1–SE6](../theory/semantic_envelopes.md) give the conditions, proofs and counterexamples; [README](README.md) gives the exact numeric algorithm.

## Target quantity and conditions

The input is a finite set of semantic candidates; each candidate refers to the same frozen target and the same ordered class semantics, and has a complete canonical numeric range, a fixed affine logit and thresholds. The target is **the range of this model's probability outputs over all the given candidates**. It is not the true class probability, and it does not automatically contain the correct interpretation of the natural text.

For branch b and class i, first compute the exact theoretical minimum m_bi and maximum M_bi, then take m_i=min_b m_bi and M_i=max_b M_bi. This box is the smallest coordinate-wise envelope of the declared candidate set; the extremes of different coordinates are usually not attainable simultaneously, and the box does not lie entirely in the probability simplex. The checker encloses the true extremes with rationals separately and does not call transcendental endpoints exact rational values.

Numeric error is controlled by positive Taylor terms and a geometric tail bound, with reciprocals for negative arguments; floating-point exp or next-step rounding is not used to guess the error. The numeric uncertainty width of each extreme is ≤1e−12. If the computed lower and upper bounds of D=max_i(M_i−m_i) are [L_D,U_D], the gate w is decided as follows: U_D≤w passes; L_D>w is too wide; everything else is undetermined. When the budget is insufficient the computation is refused; this must not be presented as mathematically too wide.

## Run identity and budget

Branch research/certifiable, base commit 8e4dd0b33c95ac2ac1a6015eba6f2dfafe5c1254; the new source code is still uncommitted. Default precision 1e−12, at most 1,000 Taylor terms, absolute value of a single argument ≤50; only standard-library Fraction is used. The pre-execution total CPU target was ≤60 seconds; the first main run took 0.694393 seconds; the latest rerun time, Python, platform and source/protocol hashes are in [results.json](results.json). No GPU/API/model-training tokens; peak memory not measured.

The check-point budget was originally 256 and was enlarged to 500 before the main runner was executed, for the independent-algorithm cross-check; the independent review had its own pre-execution budget. The review corrected a mix-up between point counts and coordinate counts: the implementation's unit tests use 139 rational grid points and the independent review 216 internal support points (729 coordinate checks), 355 points in total. The main runner adds no dense grid and only runs the frozen 25 cells and the minimal counterexamples. The count revision did not change any case or mathematical result.

## Actual results and strongest counterexamples

The decimals below are display values only; the exact endpoints and the upper and lower bounds of the true extremes are all stored as fraction strings in the JSON. All coefficients are hand-picked mathematical constructions; there are no learned model parameters.

| Construction | Result | Meaning |
|---|---|---|
| Thresholds (−1,1), η∈[−3,3] | Middle-class range about [0.101217,0.462117]; the maximum is at η=0, and both ends are only about 0.101217 | The middle class is not monotone; computing only the two ends misses part of the range |
| Two exact branches η=−4 or +4 | First and last classes each about [0.006693,0.952574]; by symmetry the middle class is about 0.040733, numeric envelope width ≤1e−12 | A numeric radius of 0 does not remove semantic ambiguity; some coordinates can still be identified |
| Merging the discrete branches above, without justification, into η∈[−4,4] | The middle-class upper bound becomes about 0.462117 | Convexification introduces an interior peak that was not attainable; keeping the branch structure is tighter |
| Known x=b∈[100,200] | g=x/b−1=0; the output is a numeric outer envelope of a fixed probability vector | A shared dependence cannot be treated as two independent intervals |
| Dropping the relation x=b and keeping only the same marginal intervals | g∈[−1/2,1]; with slope 2 the last class is about [0.119203,0.731059] | This is the cost of losing a known relation, not intrinsic ambiguity of the original problem |
| Transforming x and b together by five positive rational scales | g and all computed certificates are identical item by item | Only unit scaling of tuples is certified; invariance of natural-text parsing is not tested |
| Each branch q_high=σ(g±4), selector switches at 0 | Input distance 2e−6, lower bound on the output drop about 0.964028; the fixed-branch bound allows only 5e−7 | Each branch is monotone and 1/4-Lipschitz, yet a dynamic branch-selecting system still cannot be certified |

The unit scales are 1/1,000,000, 1/1,000, 1, 1,000 and 1,000,000. Currency changes, time-varying exchange rates and unrecognized unit words are not covered by this guarantee.

The symbolic example uses the given difference candidates directly: when both interpretations satisfy x>b, the rule returns above directly; when x=150 and the base value can be 100 or 200, the feasible labels are above/below and the rule refuses. This is a complete oracle for the sign(x−b) task and needs no learned classification head; this round did not train a learned head on these examples or compare one. Learning the probability of a random ordered target would require a separately given target, true labels and a basis for the direction; this example provides none of that evidence.

## Width gate on the frozen 25 cells

The full table uses r∈{0,0.1,0.5,1,2} and d∈{0,0.25,1,2,4}; each cell has two branches g∈[−r,r], η=g−d or g+d, with fixed thresholds (−1,1). These are 25 equally weighted hand-made candidate problems, reported in full, without picking successful cells.

| Width gate w | Proven pass | Proven too wide | Numerically undetermined | Acceptance fraction on the hand-made task |
|---|---:|---:|---:|---:|
| 0.05 (sensitivity) | 2 | 23 | 0 | 2/25 |
| **0.10 (pre-specified main gate)** | **3** | **22** | **0** | **3/25** |
| 0.20 (sensitivity) | 5 | 20 | 0 | 5/25 |

This table supports "under this candidate specification, many cases cannot be given a narrow probability box". It **is not an acceptance rate on natural text, is not the acceptance test of path 02's real 50% acceptance-rate gate, and cannot be used to reject the whole P2 direction**. The optimal-acceptance-mass conclusion of SE3 is relative to the specified candidate set; if candidates are over-reported, a wider interval may only be caused by a conservative parser.

In addition, the midpoint of a computed width interval was used as an implementation-probe threshold, and the actual return was undetermined. This probe only verifies the three-state boundary; it is not a pre-specified scientific main gate or an extra success.

## Review and error ledger

The implementation's 14 unit tests passed, first in about 0.099 seconds; the independent review ran another 14 tests in about 0.103 seconds and used a different rational scaling–squaring remainder algorithm to cross-check 331 assertions and the coordinate containment of 729 support points. Neither reference takes libm values as exact ground truth. The finite checks support the implementation branches; the general guarantee comes from the remainder and extremal proofs.

The review filled in the common target/schema contract, the boundaries of positive base values and negative x, the quantifiers of the minimax adversary, the α/n=0 boundary of the audit, and the domain of the almost-everywhere derivative. Only the strict inequality sign in the wording of the exp(0) upper bound was corrected; the numeric algorithm was not changed. width_gate consumes trusted, untampered objects produced by this calculator; it is not an independent verifier for foreign JSON certificates.

Parse-coverage risk has still not been measured. If the acceptance event A is fixed and C is the event that the correct full semantic tuple is covered, then the envelope failure rate satisfies P(E|A)≤P(Cᶜ|A), usually not with equality. If only unconditional coverage of 99% is known, the acceptor might still accept only that 1% failure set, so the post-acceptance risk reaches 100%. The audit confidence error α is not the same quantity as this prediction risk; several fragments of the same document also cannot act as several independent audit units.

## What decisions this round can change

There is now an exact numeric interface shared by P2/P05 and a concrete rejection device; "the input numbers are exact" or "each branch has a bounded derivative" can no longer substitute for semantic coverage or overall sensitivity. It has not established a real parse set, the necessity of a natural task, calibrated probabilities or originality. The basic principles of the existing unit-invariant/monotone head still do not count as a new contribution. The decision that matters most: whether the next step should define the language module's task as auditable candidate-set extraction, and allow symbolic computation to replace a redundant learned head.
