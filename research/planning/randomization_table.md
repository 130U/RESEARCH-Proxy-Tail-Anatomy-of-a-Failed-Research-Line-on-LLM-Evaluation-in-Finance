# Arbitrary random quotas: complete 32-cell results

All inputs are hand-made homogeneous threshold structures, α=1/20; all zero findings must output the fixed interval, and the true bad set is fixed in advance.
The randomized method is minimax optimal within the restricted output class; pooled is optimal within the whole-population SRS class. The fixed-quota sharp rows keep their bounds.
Sources: [JSON](randomization_results.json), [protocol](RANDOMIZATION_PROTOCOL.md), [proof](../theory/randomized_audit.md).
JSON SHA256: `90c3feb577533f39d69be92b687f0f77db3ff3cd38eb6f617a7785899c690616`.

| Case | d | r | N | Randomized optimum | pooled optimum | Fixed direct optimum or bounds | Fixed simple-combination optimum or bounds | Randomized-method risk (approx.) |
|---|---:|---:|---:|---:|---:|---|---|---:|
| threshold-r2-N2 | 3 | 2 | 2 | 4 | 5 | 4 | 4 | 0.00000000 |
| threshold-r2-N5 | 3 | 2 | 5 | 10 | 12 | 10 | 10 | 0.00000000 |
| threshold-r2-N10 | 3 | 2 | 10 | 19 | 23 | 20 | 20 | 0.03333333 |
| threshold-r2-N20 | 3 | 2 | 20 | 37 | 47 | 38 | 38 | 0.05000000 |
| threshold-r3-N2 | 5 | 3 | 2 | 5 | 6 | 6 | 6 | 0.05000000 |
| threshold-r3-N5 | 5 | 3 | 5 | 13 | 16 | 15 | 15 | 0.04000000 |
| threshold-r3-N10 | 5 | 3 | 10 | 25 | 31 | 30 | 30 | 0.05000000 |
| threshold-r3-N20 | 5 | 3 | 20 | 50 | 63 | 57 | 57 | 0.05000000 |
| threshold-r4-N2 | 7 | 4 | 2 | 6 | 7 | 8 | 8 | 0.02857143 |
| threshold-r4-N5 | 7 | 4 | 5 | 15 | 18 | 20 | 20 | 0.02857143 |
| threshold-r4-N10 | 7 | 4 | 10 | 29 | 37 | 39 | 40 | 0.04000000 |
| threshold-r4-N20 | 7 | 4 | 20 | 57 | 73 | 76 | 76 | 0.04571429 |
| threshold-r5-N2 | 9 | 5 | 2 | 6 | 8 | 9 | 9 | 0.04761905 |
| threshold-r5-N5 | 9 | 5 | 5 | 15 | 20 | 23 | 25 | 0.04761905 |
| threshold-r5-N10 | 9 | 5 | 10 | 30 | 40 | 42 | 44 | 0.04761905 |
| threshold-r5-N20 | 9 | 5 | 20 | 60 | 81 | 84 | 86 | 0.04761905 |
| threshold-r6-N2 | 11 | 6 | 2 | 7 | 8 | 10 | 11 | 0.03787879 |
| threshold-r6-N5 | 11 | 6 | 5 | 17 | 21 | 22 | 22 | 0.04242424 |
| threshold-r6-N10 | 11 | 6 | 10 | 33 | 43 | 44 | 44 | 0.04696970 |
| threshold-r6-N20 | 11 | 6 | 20 | 65 | 86 | 88 | 88 | 0.04924242 |
| and-d2-N2 | 2 | 2 | 2 | 2 | 3 | 2 | 2 | 0.00000000 |
| and-d3-N2 | 3 | 3 | 2 | 2 | 3 | 2 | 2 | 0.00000000 |
| and-d4-N2 | 4 | 4 | 2 | 2 | 4 | 2 | 2 | 0.00000000 |
| and-d5-N2 | 5 | 5 | 2 | 2 | 4 | 2 | 2 | 0.00000000 |
| and-d6-N2 | 6 | 6 | 2 | 2 | 4 | 2 | 2 | 0.00000000 |
| and-d8-N2 | 8 | 8 | 2 | 2 | 4 | 2 | 2 | 0.00000000 |
| and-d12-N2 | 12 | 12 | 2 | 2 | 4 | 2 | 2 | 0.00000000 |
| and-d20-N2 | 20 | 20 | 2 | 2 | 5 | 2 | 2 | 0.00000000 |
| sharpness-N4 | 31 | 16 | 4 | 16 | 20 | [16,26] | [28,31] | 0.04338154 |
| sharpness-N8 | 127 | 64 | 8 | 35 | 46 | [64,86] | [120,127] | 0.04639140 |
| sharpness-N16 | 511 | 256 | 16 | 70 | 94 | [256,302] | [496,511] | 0.04967710 |
| sharpness-N32 | 2047 | 1024 | 32 | 141 | 190 | [1024,1118] | [2016,2047] | 0.04953064 |

Exact risks and the risks with one document fewer are in the JSON; decimals are for display only and are not used for decisions. The 16 star structures are asymmetric and are explicitly outside the scope of this theorem.
Relative gains only describe the hand-made structures and the specified output convention; they are not a natural-model certificate, originality, or a G0/G1 pass.
