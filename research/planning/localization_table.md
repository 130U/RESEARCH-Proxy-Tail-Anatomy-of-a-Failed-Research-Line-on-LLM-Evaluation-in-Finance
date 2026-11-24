# Round eight complete comparison table

Hand-made mathematical constructions, alpha=1/20, unit audit cost; the 44 rows of exact comparisons are kept separate from the 4 rows with analytic bounds only. The procedure classes and the nature of the research are in the [protocol](LOCALIZATION_PROTOCOL.md).

Current JSON SHA256: 0e990e8ef2790e3b6edde983f399efdd5e667c21bea189fe642f925dd84b7c22

## Original threshold family: 20 rows

| Case | Direct | Box | Total K | Best ex-ante simple combination | Direct saving relative to the combination |
|---|---:|---:|---:|---:|---:|
| threshold-r2-N2 | 4 | 4 | 5 | 4 | 0 |
| threshold-r2-N5 | 10 | 10 | 12 | 10 | 0 |
| threshold-r2-N10 | 20 | 20 | 24 | 20 | 0 |
| threshold-r2-N20 | 38 | 38 | 48 | 38 | 0 |
| threshold-r3-N2 | 6 | 6 | 8 | 6 | 0 |
| threshold-r3-N5 | 15 | 15 | 18 | 15 | 0 |
| threshold-r3-N10 | 30 | 30 | 34 | 30 | 0 |
| threshold-r3-N20 | 57 | 57 | 65 | 57 | 0 |
| threshold-r4-N2 | 8 | 8 | 11 | 8 | 0 |
| threshold-r4-N5 | 20 | 20 | 20 | 20 | 0 |
| threshold-r4-N10 | 39 | 40 | 40 | 40 | 1/40 |
| threshold-r4-N20 | 76 | 76 | 76 | 76 | 0 |
| threshold-r5-N2 | 9 | 10 | 9 | 9 | 0 |
| threshold-r5-N5 | 23 | 25 | 25 | 25 | 2/25 |
| threshold-r5-N10 | 42 | 50 | 44 | 44 | 1/22 |
| threshold-r5-N20 | 84 | 95 | 86 | 86 | 1/43 |
| threshold-r6-N2 | 10 | 12 | 11 | 11 | 1/11 |
| threshold-r6-N5 | 22 | 30 | 22 | 22 | 0 |
| threshold-r6-N10 | 44 | 60 | 44 | 44 | 0 |
| threshold-r6-N20 | 88 | 114 | 88 | 88 | 0 |

## All-strata conjunction: 8 rows

| Case | Direct | Box | Total K | Best ex-ante simple combination | Direct saving relative to the combination |
|---|---:|---:|---:|---:|---:|
| and-d2-N2 | 2 | 2 | 3 | 2 | 0 |
| and-d3-N2 | 2 | 2 | 4 | 2 | 0 |
| and-d4-N2 | 2 | 2 | 5 | 2 | 0 |
| and-d5-N2 | 2 | 2 | 5 | 2 | 0 |
| and-d6-N2 | 2 | 2 | 6 | 2 | 0 |
| and-d8-N2 | 2 | 2 | 7 | 2 | 0 |
| and-d12-N2 | 2 | 2 | 9 | 2 | 0 |
| and-d20-N2 | 2 | 2 | 13 | 2 | 0 |

## Star: 16 rows

| Case | Direct | Box | Total K | Best ex-ante simple combination | Direct saving relative to the combination |
|---|---:|---:|---:|---:|---:|
| star-L1-N2 | 2 | 2 | 3 | 2 | 0 |
| star-L1-N5 | 5 | 5 | 8 | 5 | 0 |
| star-L1-N10 | 10 | 10 | 16 | 10 | 0 |
| star-L1-N20 | 19 | 19 | 32 | 19 | 0 |
| star-L2-N2 | 2 | 2 | 5 | 2 | 0 |
| star-L2-N5 | 5 | 5 | 12 | 5 | 0 |
| star-L2-N10 | 10 | 10 | 24 | 10 | 0 |
| star-L2-N20 | 19 | 19 | 48 | 19 | 0 |
| star-L5-N2 | 2 | 2 | 11 | 2 | 0 |
| star-L5-N5 | 5 | 5 | 24 | 5 | 0 |
| star-L5-N10 | 10 | 10 | 48 | 10 | 0 |
| star-L5-N20 | 19 | 19 | 96 | 19 | 0 |
| star-L10-N2 | 2 | 2 | 21 | 2 | 0 |
| star-L10-N5 | 5 | 5 | 44 | 5 | 0 |
| star-L10-N10 | 10 | 10 | 88 | 10 | 0 |
| star-L10-N20 | 19 | 19 | 176 | 19 | 0 |

## Sharp-constant construction: 4 rows of analytic bounds

The intervals below are proven lower and upper bounds on the optimal cost; no high-dimensional global optimum search was run. The combination baseline is Total K in all four rows; the lower bound on the saving is computed from the direct feasible upper bound and the lower bound on the combination cost.

| N | r=N² | Direct optimal cost range | Combination optimal cost range | Box cost | Lower bound on saving relative to the combination |
|---:|---:|---:|---:|---:|---:|
| 4 | 16 | [16,26] | [28,31] | 64 | 1/14 |
| 8 | 64 | [64,86] | [120,127] | 512 | 17/60 |
| 16 | 256 | [256,302] | [496,511] | 4096 | 97/248 |
| 32 | 1024 | [1024,1118] | [2016,2047] | 31744 | 449/1008 |

In the original N=r² sequence the ratio tends to 1, while here, with r=N², the ratio tends to 2; these are different scales. Broader whole-population random sampling can be cheaper; a single-point check is in [pooled_scope_check.json](pooled_scope_check.json); it is outside the fixed-quota class of this table.
