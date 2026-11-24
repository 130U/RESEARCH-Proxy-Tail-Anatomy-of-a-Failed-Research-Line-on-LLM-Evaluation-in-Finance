# Sol four-ranking aggregation: validation on 128 new samples

Main result: **FAIL**. Applies only to the selected branch of Sol + four-run aggregation per panel; it does not mean the joint two-model gate passed.

The sample comes from 128 new lexical families, with an intersection of 0 with the previously excluded families; the IDs and texts of the eight inputs are identical. The ranking instruction puts the most positive first, and the integer Borda gives higher scores accordingly. Lexical families do not guarantee fully independent events.

The two panels use order1–4 and order5–8; the m=1, 2, 4 prefixes are all kept, and only m=4 is used for the main working gate. All eight outputs are strictly checked for each ID appearing exactly once, and U items are not filled in with ranks.

## Raw outputs and exact aggregation

| Output | Ranked | U | Groups | True tie groups | Largest tie group |
|---|---:|---:|---:|---:|---:|
| rank_sol_o1.json | 128 | 0 | 43 | 41 | 27 |
| rank_sol_o2.json | 128 | 0 | 77 | 25 | 23 |
| rank_sol_o3.json | 128 | 0 | 48 | 37 | 21 |
| rank_sol_o4.json | 128 | 0 | 28 | 27 | 22 |
| rank_sol_o5.json | 128 | 0 | 30 | 30 | 21 |
| rank_sol_o6.json | 128 | 0 | 42 | 26 | 30 |
| rank_sol_o7.json | 128 | 0 | 98 | 12 | 18 |
| rank_sol_o8.json | 128 | 0 | 98 | 8 | 24 |

Borda computes integer numerators from sums of twice the midrank; identical integer numerators are kept as ties.

## Item-by-item values for the main working gate

| Direction | Tail | p | Nominal/A actual count | Needed for 90%/B pass-through count | Actual recall | Same-budget recall | q90/p | A/B boundary expansion | Passed |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| panel1_to_panel2 | upper | 10% | 12/12 | 11/13 | 0.917 | 0.917 | 1.016 | 0.0%/8.3% | yes |
| panel1_to_panel2 | upper | 20% | 25/25 | 23/25 | 0.920 | 0.920 | 0.977 | 0.0%/0.0% | yes |
| panel1_to_panel2 | lower | 10% | 12/14 | 13/16 | 1.000 | 0.786 | 1.250 | 16.7%/0.0% | no |
| panel1_to_panel2 | lower | 20% | 25/27 | 25/28 | 0.926 | 0.889 | 1.094 | 8.0%/0.0% | yes |
| panel2_to_panel1 | upper | 10% | 12/13 | 12/14 | 0.923 | 0.846 | 1.094 | 8.3%/0.0% | yes |
| panel2_to_panel1 | upper | 20% | 25/25 | 23/25 | 0.920 | 0.920 | 0.977 | 0.0%/0.0% | yes |
| panel2_to_panel1 | lower | 10% | 12/12 | 11/11 | 0.917 | 0.917 | 0.859 | 0.0%/16.7% | yes |
| panel2_to_panel1 | lower | 20% | 25/25 | 23/23 | 0.920 | 0.960 | 0.898 | 0.0%/8.0% | yes |

With N=128, the nominal counts for p=10% and 20% are floor(Np)=12 and 25. The main gate's widening factor is always the B pass-through count/(N×p), not changed to B/floor(Np); the JSON lists the actual B/A counts separately. 90% requires ceil(0.9×A actual count), so the actual recall of a finite list will be above 90%. The same-budget lists also each include their complete boundary groups, so the two actual counts can differ.

The working thresholds require, in both directions and for both tails: same-budget recall ≥80%, q90/p≤1.5, nominal boundary-tie expansion of A and B ≤20%, and no U. This is a pre-set working gate, not a significance test.

## Prefix sensitivity (not post-hoc selection)

| m | midrank Spearman | Minimum same-budget recall over the main p | Maximum q90/p |
|---:|---:|---:|---:|
| 1 | 0.9596 | 0.643 | 2.969 |
| 2 | 0.9853 | 0.714 | 1.875 |
| 4 | 0.9929 | 0.786 | 1.250 |

Spearman is auxiliary only. The 5% lists are diagnostic only; repeated calls do not increase the financial sample size, and the variation between the two directions is not a confidence interval; no bootstrap, alpha fitting or tail-limit inference was done.

[Full numbers](validation_stage2.json) · [Curves](validation_stage2.png) · [PDF](validation_stage2.pdf). Location of the raw blind outputs: `research/private/agent_tail_methods/stage2_n128_sol`.

This read-only analysis: CPU 2.672 s, wall 3.737 s; peak memory not measured. No model calls, training, external API or network.
