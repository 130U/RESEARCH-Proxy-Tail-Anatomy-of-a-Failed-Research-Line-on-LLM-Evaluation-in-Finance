# Exact rational envelope checker for finite semantic candidates

This component corresponds to the [pre-run protocol](PROTOCOL.md). It computes the output envelope for given semantic candidates and a fixed affine ordered-logit model, using the Python standard library and Fraction; there is no real text parser, gold-standard audit, model training, network access or deployment error rate. No originality is claimed on this basis for basic interval arithmetic, ordered logits or finite-candidate min/max.

All numeric intervals, slopes, offsets, thresholds and candidate sets in this round are mathematical constructions hand-picked in advance; there are no weights trained from a corpus here. That an example with hand-picked parameters passes does not prove that some real financial model satisfies the same premises.

## Input and target

`SemanticBranch(semantic_id,g_interval,slope,offset,thresholds,target_id=...,class_labels=...)` declares one fixed semantic interpretation: the dimensionless value g lies in a closed interval, `η=slope*g+offset`, and the thresholds are fixed, strictly increasing rationals. There is at least one threshold, i.e. K≥2. The slope may be positive, negative or zero; its sign states the direction of this **given model** and does not prove that the economic semantic direction is correct. Different branches may have different base values, directions and model parameters.

Branches in a union must declare the same `target_id` and `class_labels` in exactly the same order; having the same K is not enough. The default target is an explicit example identifier, and the default labels are `class_0,...`, which carry no financial meaning. The checker can reject differing declarations, but **cannot prove that identical declarations really describe the same semantic target**. `semantic_id` must be unique; it identifies an interpretation and carries no probability for that interpretation.

Interval endpoints, slopes, offsets, thresholds, tolerances, width thresholds and unit scale factors only accept exact int/Fraction; float, bool and unparsed strings are rejected. The budget's max_terms also rejects bool. All intervals must be ordered; when the probability computation exceeds the declared numeric budget, `BudgetExceeded` is raised, and no partial branch or unproven narrow interval is returned.

```python
from fractions import Fraction as F
from research.numeric.semantic_envelope import (
    Interval, Budget, SemanticBranch, relative_change_interval,
    semantic_envelope, width_gate,
)

g = relative_change_interval(Interval(9,11), Interval(8,10))
branch = SemanticBranch("baseline-A", g, F(1), F(0), (F(-1),F(1)),
                        target_id="declared-comparison",
                        class_labels=("below","near","above"))
result = semantic_envelope([branch], Budget())
serializable = result.to_json()  # Rational endpoints are written as strings, not converted to float.
decision = width_gate(result, F(1,10)).to_json()
```

## Ratios, units and the symbolic baseline

`ratio_interval(x,b)` returns the four-corner extremes of x/b; `relative_change_interval(x,b)` returns x/b−1; the two interfaces are not mixed. b.lower>0 is required, and x may be negative. A denominator that contains zero or is entirely negative lies outside this restricted support domain and is rejected directly.

Under the independent rectangle `x∈[l,u],b∈[v,w],v>0`, the four corners give the true extremes; the image of a continuous map is an interval. If the true x and b share a dependence, the rectangle is still a safe outer relaxation but may not be tight. For example, when the true relation is x=b∈[1,2], the ratio is exactly 1, while giving only two independent intervals yields [1/2,2]. Width caused by losing the dependence must not be called natural semantic unidentifiability.

`rescale_interval` only accepts a positive rational scale factor. When x and b are multiplied by the same factor, the Fraction results of ratio and relative_change are exactly unchanged, and the probability envelope with the same parameters afterwards is also the same. This only verifies unit transformations of the given tuples; it does not certify text units, currencies, exchange-rate dates or parser invariance.

`difference_interval(x,b)` gives the interval of x−b. `label_set` returns the possible `below/equal/above` for a numeric interval; the default zero tolerance is 0, where equal means exactly 0; with a nonzero tolerance, equal means lying in the declared closed tolerance band. `robust_label` returns a label only when all candidates jointly allow just that one label; otherwise it returns None. These are comparison relations and must not be renamed as an investment stance or a market direction. If the task is exactly that comparison relation, the symbolic baseline already gives the direct answer, and there is no need to keep a learned head to manufacture a research necessity.

## Exact outer envelopes for transcendental functions

The core does not use `math.exp`, floating-point sigmoid or nextafter, and does not dress up a center value as a proof. For rational x≥0, let `S_n=Σ_{k=0}^n x^k/k!`. When `x<n+2`, from the next term on, the ratio between successive terms is at most `r=x/(n+2)<1`, so:

```text
S_n ≤ exp(x) ≤ S_n + [x^(n+1)/(n+1)!] / [1−x/(n+2)].
```

The program recurses with exact Fraction and returns only once the tail bound is within the requested tolerance. `max_terms` counts the k=0 term, default 1,000; the default maximum absolute argument is 50. This is an implementation budget, not the mathematical domain; reaching the limit without meeting the tail bound is a failure. A negative argument uses the reciprocal `[1/U,1/L]` of the positive exp interval, and L≥1, so the reciprocal does not enlarge that absolute width.

sigmoid uses an exact envelope of `E=exp(|z|)`. For z≥0 it uses `E/(1+E)`, and for z<0 it uses `1/(1+E)`; the derivative magnitude of both functions on E≥1 is at most 1/4, so the returned width is at most the requested tolerance. The cache only reuses proven results for the same exact argument and the same budget, and does not change values; there is no approximate fallback when the budget is exhausted.

## True per-branch extremes and numeric error are stored separately

The η interval of the affine map is obtained from the two endpoints, which are swapped automatically for a negative slope. The first class `q₀=σ(θ₀−η)` decreases in η, and the last class `q_last=σ(η−θ_last)` increases in η. A middle class is:

```text
q_i(η) = σ(θ_i−η) − σ(θ_(i−1)−η).
```

Its peak is at the midpoint of adjacent thresholds `(θ_i+θ_(i−1))/2`; its minimum is at an endpoint of the η interval. The program therefore computes both endpoints for each class, and for interior classes also adds the midpoint if it falls inside the interval; checking only the two endpoints is not enough. This characterization of the extremes over the true continuous range comes from the model structure; a finite grid is only an implementation check.

Each sigmoid request uses 1/4 of the public tolerance. The difference of two sigmoids uses `[L_hi−U_lo,U_hi−L_lo]`, intersected with [0,1]; its numeric uncertainty width is at most tolerance/2. Each candidate's true value is strictly contained. Taking the minimum over several candidate values gives the envelope `[min L,min U]`, and taking the maximum gives `[max L,max U]`; these operations do not add up the largest numeric widths of the candidates. Hence the numeric uncertainty width of each true extreme is at most the public tolerance, and the one-sided error is also at most tolerance.

`branch_probability_extrema` returns `RangeCertificate(minimum,maximum)` for each class, which encloses the true minimum and the true maximum respectively; `branch_probability_ranges` returns `[minimum.lower,maximum.upper]`. This is a strict **numeric outer envelope**; it does not claim that the transcendental endpoints themselves have become exact rationals. The total outward widening of the true range can reach the sum of the numeric errors of the two endpoints, so tolerance must not be taken as the width of the true semantic range.

## Finite semantic union and the three-state width gate

`semantic_envelope` takes the min of all candidates' minima and the max of their maxima, and does not assume or estimate branch weights. `Envelope.class_intervals` is the final coordinate-wise outer envelope; `extrema` keeps the numeric uncertainty of the joint true extremes, and `branch_intervals` keeps the computed range of each branch. The theoretical coordinate-wise hull is the tightest for the declared candidate set, and the machine computation is a rational outer envelope of it.

This does not mean that every point in the box is attainable: the extremes of different coordinates may come from different η or different branches, and some corners of the box may even sum to more than 1, so they are not probability vectors. It also does not prove that the true parsed interpretation is in the candidate set, let alone that all candidates are realistically feasible; a missing candidate breaks coverage, and a falsely reported candidate adds conservativeness.

`width_gate` decides whether the true maximum coordinate range width `D=max_i(max q_i−min q_i)` is at most the threshold w. If the true minimum lies in [a,b] and the true maximum lies in [c,d], then the true width of that coordinate lies in `[max(0,c−b),d−a]`. Taking the maximum lower bound / maximum upper bound over the coordinates gives the interval [L_D,U_D] for D:

- `pass`: U_D≤w, the width is proven to pass.
- `fail`: L_D>w, proven too wide for the current candidate set that must be fully covered.
- `undetermined`: all other cases; the current numeric precision cannot distinguish them, so the budget should be refined or the result left undetermined.

An outer width>w alone does not constitute fail; this is the key misuse this component must avoid. Even a fail applies only to the current candidate set and model; it is not a proof of impossibility for natural text without a semantic audit, and still less an acceptance of financial deployment risk.

The entry contract of `width_gate` is that it consumes an unmodified Envelope object successfully produced by this checker's `semantic_envelope`. Python type checks cannot prove that a hand-constructed object has correct extremes; this function **is not a verifier that reads foreign JSON and independently checks a mathematical certificate or signature**. Likewise, `target_id/class_labels` only checks that the declarations agree and cannot verify the natural-language semantics behind them; external JSON, parsers or transmission chains need a separate verification interface, which this round did not implement.

## Finite checks executed

```powershell
& '..\130U-FinLLM\.venv\Scripts\python.exe' -X utf8 -m unittest research.numeric.test_semantic_envelope -v
```

On 2026-11-16 the first 14 tests passed, in about 0.099 seconds. The tests cover positive and negative exp and sigmoid, budget failure, exact unit invariance under positive scaling, rejection of zero/negative base values, negative slopes, interior peaks, per-branch envelopes, common target/schema, symbolic refusal, the three width states and strict types. The grid checks use 100 ratio points and 39 η points, all hand-built rational constructions, not natural-text data.

The tests also use an independent rational Lagrange-remainder oracle: 96 Taylor partial sums together with the upper bound `exp(x)≤3^ceil(x)` (x≥0, with equality at x=0) form a narrower reference interval; this differs from the geometric tail bound used by the implementation and does not use floating-point exponentials as ground truth. The reference intervals are contained in the implementation's envelopes; this only gives a numeric cross-check at these finite points; validity over the whole domain comes from the remainder derivation and the extremal proofs. The broader construction records of the parent-task runner and of the independent review are saved separately; this document does not pre-fill their results.
