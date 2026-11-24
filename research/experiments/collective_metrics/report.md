# Collective statistic envelope: actual computation results

Source of all numbers: our experiment (constructed vote matrices, not real models). Actual computation time 0.6280 seconds.

| Input | Method | Per-point accuracy | Collective accuracy | Per-point macro-F1 | Collective macro-F1 |
|---|---|---|---|---|---|
| shared_budget_strict_improvement | component | [0, 1] | [1/4, 3/4] | [0, 1] | [1/5, 11/15] |
| shared_budget_strict_improvement | exact | [0, 1] | [1/4, 3/4] | [0, 1] | [1/5, 11/15] |
| component_optima_incompatible | component | [2/3, 2/3] | [2/3, 2/3] | [4/9, 2/3] | [4/9, 2/3] |
| component_optima_incompatible | exact | [2/3, 2/3] | [2/3, 2/3] | [5/9, 5/9] | [5/9, 5/9] |
| no_contamination_perfect | component | [1, 1] | [1, 1] | [1, 1] | [1, 1] |
| no_contamination_perfect | exact | [1, 1] | [1, 1] | [1, 1] | [1, 1] |
| all_heads_change | component | [0, 1] | [0, 1] | [0, 1] | [0, 1] |
| all_heads_change | exact | [0, 1] | [0, 1] | [0, 1] | [0, 1] |

The first example shows that the jointly-affected-heads constraint can strictly tighten the bounds; the second shows that taking per-class F1 extremes separately gives only an outer envelope, and joint reachability cannot be claimed.
"exact" means exact within the relaxation model in which, for a fixed set, the selected heads can freely change all outputs; it does not mean the real training process can realize every endpoint.
The statistic includes all K fixed classes; a class with zero support and zero predictions contributes 0; classes must not be dropped dynamically after each perturbation.
An actual deployment must first prove separately that the trusted core and the shared components are not changed by contamination, and then set the affected-head budget from a valid audit. These input premises were not verified in this experiment.
This round does not pass G0 or G1 on this basis, and does not claim that the collective poisoning certificate or the macro-F1 optimization is new theory.
The program refuses to output when the state budget or the subset budget is exhausted; the exponential/combinatorial complexity of the current implementation limits large-scale use.
