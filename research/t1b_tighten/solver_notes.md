# T1B numeric ranges and certificates

The inputs to `exact_solver.py` are a finite rational box, homogeneous linear equations and the T1 program. Constants or zero-width facts can be put in the box, and equations may be redundant. Each fact is converted by its center and half-width to `z ∈ [-1,1]`, which avoids floating-point scale problems caused by currency units; a zero-width fact corresponds to `z=0`.

## Objectives and solving

The program is first made symbolic. When, after cancellation, the numerator and denominator are both affine and the denominator is constant, a linear program is solved directly. Otherwise, we first prove that the denominator has a strictly constant sign over the whole box, negate both parts if the denominator is negative, and then use the Charnes–Cooper variables `t=1/D(z)`, `y=t z`: `D(y,t)=1`, each equation `A z=b` becomes `A y-bt=0`, and each bound `l≤z≤u` becomes `lt≤y≤ut`. Before the transformation, the denominator is scaled by the mean of its box bounds so that `t` is about 1. The positive lower bound of the denominator also gives a finite safe box for `t` and `y`.

[SciPy's official linprog documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html) defines linear equalities, inequalities, variable bounds and solver statuses; the code uses HiGHS output only as candidates. Symbolic computation uses [SymPy](https://docs.sympy.org/latest/modules/solvers/solvers.html), but every certificate decision is finally made by exact rational comparison with Python `Fraction`.

## Why the outer envelope is reliable

Consider minimizing `cᵀv+c0` subject to `Ev=b`, `Gv≤h`, `l≤v≤u`. Take any rational vector `α` and an elementwise non-positive `β`, and let

`r = c − Eᵀα − Gᵀβ`.

For every feasible point, strictly,

`cᵀv+c0 ≥ c0 + bᵀα + hᵀβ + Σ min(rᵢlᵢ, rᵢuᵢ)`.

The right-hand side is the saved lower-bound certificate. The floating-point dual multipliers are only rationalized; even if they are not the exact optimal multipliers and the residual is not zero, this inequality still holds. The maximum is bounded above by minimizing the negated objective. A floating-point objective is never simply rounded into a "proof".

The active constraints of the floating-point primal solution are solved separately by rational row reduction; after the candidate point is rebuilt, all bounds, inequalities and equations are checked exactly, item by item. If the primal and dual candidates leave a non-zero gap, the dual multipliers are rebuilt by solving the stationarity equations on the exact active constraints, their signs are checked, and they are still verified with the general formula above. If the objective at the exact primal solution equals the certificate bound, `range_exact=true` is recorded; otherwise the interval is still a reliable outer envelope, and exact optimality is explicitly not claimed.

## Existence and empty sets

An out-of-tolerance conclusion requires a complete assignment of facts: it lies strictly inside every non-degenerate rounding interval, satisfies all equations exactly, and the rational execution result of the original program lies outside the acceptance interval. A feasible interior point is found by maximizing a common inward margin, and is then combined convexly with an endpoint in rationals. If the feasible region only touches rounding endpoints, that endpoint is not used to declare out of tolerance. When the certificate interval is out of tolerance but there is no strict interior witness, the result is `unresolved`.

If a feasible point cannot be rebuilt, an independent phase-one problem `min t` is solved, subject to `|Ez-b|≤t`, the original box and `0≤t≤max(1,max|b|)`. This problem always has an obvious feasible point; `infeasible` is returned only when its exact certificate lower bound is strictly greater than zero. An empty feasible region is never counted as "determined".

`verify_result` needs no further optimizer call: it recomputes all bounds from the problem and the saved dual multipliers, and checks the exact primal solution and the strict interior witness. `extrema` saves the minimum/maximum candidate primal assignments and objectives, which may lie on the boundary; these are not automatically valid rounding witnesses. If the whole range does not intersect the gold acceptance interval, the summary program should list it separately as `reference_incompatible`; it cannot be treated as a non-unique answer.

## Nonlinear programs and limitations

For a genuinely nonlinear program (for example the product of two uncertain inputs), the coordinates used by the program are first tightened separately by linear programming, and then rational interval propagation is applied. This is first of all an outer envelope; separately, feasible endpoints of linear objectives and their interior convex combinations are searched to produce out-of-tolerance witnesses. If two exactly feasible assignments attain the two ends of the outer envelope, this independently proves that it is the exact range, and the endpoint certificates are saved; otherwise no exact range is claimed. If the denominator box cannot be proven to have a constant sign, the program also falls into the conservative path; when the interval crosses zero there may be no finite outer envelope. Before symbolic cancellation, the domain of the original program is also checked, to avoid cancelling `0/0` to `1` and then wrongly declaring it determined.

What the solver proves is **a mathematical proposition given the verified semantic constraints**; it does not prove that a candidate sum relation really holds in economic semantics. Semantic screening, same-quantity judgments for duplicate disclosures and document coverage are the responsibility of the per-question audit.

## Independent implementation and pipeline review record

Besides implementing the mathematical core, the solver agent also did a read-only review of `prepare.py` and `run_audit.py`, and of the constraints submitted by reviewers A/B.

- The original 196 rounding boxes were re-solved and passed optimizer-free certificate verification; strict interior out-of-tolerance witnesses were found for all of them. In the first version there were 191 affine or linear-fractional exact ranges and 5 nonlinear outer envelopes. A nonlinear endpoint-attainment check was added later.
- The unit checks cover closed-form growth-rate ranges, sum tightening, negative denominators, empty sets, feasibility only on the boundary, non-exact envelopes of correlated products, redundant equations, zero-width facts, dual residuals, tampered certificates/witnesses, unit scaling, and the `0/0` domain of the original program. Deliberately tampered infeasibility certificates in the tests were also rejected.
- One real integration error was found and reported: for the `4 pt` cell of `UNP/2009/page_35.pdf-1`, the reviewer supplied an additional bound, but the old table parser did not recognize `pt`, and the source link triggered a missing key. I added parsing of the point suffix and an explicit source check, and the rerun passed.
- Cell dashes were not automatically treated as numbers; reviewers had to provide their zero-value interpretation and bounds explicitly. Years in table headers, percentage totals, contractual ratios and negative losses converted to positive magnitudes all require semantic handling and cannot be decided automatically by numeric closeness. We checked MSI's `−1/1000` sign and unit transformation, the fixed 100% composition identity, maturity sums and balance roll-forward relations.
- It was pointed out that "primarily due to" in PM's expense bridge does not guarantee that the listed items are exhaustive, and reviewer B removed that relation from the main constraints; similar non-exhaustive narratives cannot be used as identities just because the displayed centers happen to add up.
- I further reviewed "including" in CME's credit-facility decomposition and confirmed that the two listed items do not guarantee that they exhaust the total facility; that equation is kept only as a sensitivity analysis with an explicit additional assumption and is not counted in the main results.
- Item-by-item confirmation that solving succeeded is not the same as a research conclusion: empty sets are not counted as determined, semantically invalid or pending records are not counted as retained, and questions whose whole range excludes gold are listed separately as reference-incompatible. For retained questions, a feasible assignment inside the acceptance interval should also be saved and paired with the outside assignment; the main pipeline is responsible for that check.

This record is not a proof of completeness with respect to all latent semantic constraints in the documents. The final counts are those in `results/summary.json` and the rerun per-question certificates.

The main pipeline's independent replay from disk also found that the certificates depended on the order in which variables were inserted. Variable names and their boxes are now uniformly sorted by name, and a regression test was added that still verifies after the order of the input dictionary is swapped. After the fix, the final artifacts were re-read from disk and passed rational verification separate from the solving process; they do not depend on set iteration order within one process.
