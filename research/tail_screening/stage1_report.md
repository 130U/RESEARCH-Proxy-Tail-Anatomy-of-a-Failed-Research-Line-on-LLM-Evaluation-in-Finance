# 32 new samples: stage results of the ranking methods

Scope of this analysis: `all`. Only saved outputs were read; no model calls, training or network access.

Every nominal tail includes all ties at the boundary. The gate uses nominal p=25%; the JSON also records the actual A count, the actual fraction and the B/A factor. 12.5% is only a diagnostic with a nominal four items.

## pair

Full overall working gate: **FAIL**; all outputs judgeable: True.

- luna, combined verdict over both directions and both tails: FAIL.
- sol, combined verdict over both directions and both tails: FAIL.

Work items not met:

- luna_p1__to__luna_p2, upper: q90_over_nominal_p_at_most_1_5, B_tie_expansion_at_most_0_2.
- luna_p1__to__luna_p2, lower: same_budget_recall_at_least_0_8, q90_over_nominal_p_at_most_1_5.
- luna_p2__to__luna_p1, upper: same_budget_recall_at_least_0_8, q90_over_nominal_p_at_most_1_5, A_tie_expansion_at_most_0_2.
- luna_p2__to__luna_p1, lower: same_budget_recall_at_least_0_8, q90_over_nominal_p_at_most_1_5.
- sol_p1__to__sol_p2, upper: q90_over_nominal_p_at_most_1_5.
- sol_p2__to__sol_p1, upper: q90_over_nominal_p_at_most_1_5.

| Model/panel | Swap disagreements/comparable pairs | Merged zero edges/496 | Strict three-edge cycles/strict triangles | U judgments |
|---|---:|---:|---:|---:|
| luna_p1 | 248/496 | 272/496 | 8/508 | 0 |
| luna_p2 | 230/496 | 266/496 | 7/543 | 0 |
| sol_p1 | 56/496 | 149/496 | 0/1964 | 0 |
| sol_p2 | 63/496 | 135/496 | 0/2125 | 0 |

## rank

Full overall working gate: **FAIL**; all outputs judgeable: True.

- luna, combined verdict over both directions and both tails: FAIL.
- sol, combined verdict over both directions and both tails: PASS.

Work items not met:

- luna_p1__to__luna_p2, upper: q90_over_nominal_p_at_most_1_5.
- luna_p2__to__luna_p1, upper: q90_over_nominal_p_at_most_1_5.

All prefix results for m=1, 2, 4 are kept in the JSON; only m=4 decides this method's gate, and the most favorable m was not picked.

Combination ranges are not confidence intervals; judgments in the same batch share context, and repeated rankings do not add independent financial samples. If a pair U enters the zero-edge diagnostic, it always keeps its failure identity; a rank U is not filled in with a made-up complete rank.

Results: [methods_stage1_all.json](methods_stage1_all.json); [figure](methods_stage1_all.png). Raw inputs/outputs are in `research/private/agent_tail_methods/stage1_n32/`.

Actual CPU 2.547 s; wall 3.264 s; peak memory not measured.
