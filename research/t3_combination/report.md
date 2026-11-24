# T3: combined scoring of two messages

**Pre-registered decision: continue behavioural validation.** Completed 88 calls and 3,360 valid scores: 30 single facts 8 times each, 780 ordered combinations 4 times each.

| Model | Full-sample RMSE | Leave-one-atom-out RMSE | Full-sample MAE | Held-out MAE |
|---|---:|---:|---:|---:|
| additive | 5.235 | 5.235 | 3.441 | 3.441 |
| average | 12.144 | 12.144 | 10.191 | 10.191 |
| asymmetric | 10.300 | 10.564 | 8.653 | 8.847 |
| prior_average | 4.966 | 5.027 | 3.264 | 3.311 |

**Interpretation warning: the asymmetric average model that estimates λ has a larger hold-out error than the additive model. The λ interval excluding 1 only triggers the pre-registered screening gate; it cannot be used to conclude that the real integration mechanism has a corresponding negative weight. Model misspecification should be ruled out first; the coefficient cannot be treated directly as a multiplier of the influence of bad news.**

The main intervals are percentile 95% intervals from 1,000 resamples of stratified atom weights + shared scoring rounds; their interpretation is limited by the fixed hand-made item bank. The number of replicates and the seeds are in results.json.

- Negative combination weight λ: 2.691 [1.219, 5.304]; first-position weight w: 0.498 [0.487, 0.510].
- Directional shrinkage from adding a neutral fact: 1.036 [-0.030, 2.014] points; additive residual after subtracting the actual neutral baseline: 1.036 [-0.030, 2.014] points.
- Positive first minus negative first: -0.168 [-1.643, 1.160] points.
- Absolute order difference over all combinations: 1.458 [1.367, 2.654] points.
- Fraction of same-direction combinations beyond the stronger single item: PP 73.3%, NN 64.4%; corresponding mean excess 2.844, 1.167 points.
- Fraction of same-direction combinations lying between the two single scores (endpoints included): PP 26.7%, NN 35.6%.
- Fraction of additive predictions that hit endpoint truncation: 8.5%; prior-average diagnostic k: 0.929 [0.853, 0.996].

Gate-by-gate results: {"lambda_interval_excludes_one": true, "PN_order_at_least_two_and_interval_excludes_zero": false, "averaging_improves_full_and_cv_by_two_with_neutral_contraction": false}. Optimisation boundary: {"w": false, "lambda": false}. When a boundary is hit the binary decision is kept, but the magnitude of λ or w is not yet sufficiently identified.

The hold-out analysis still uses the held-out atom's single-item calibration score; the two hold-out losses of each combination are averaged first and cannot be treated as two independent observations. Cross-validation has no bootstrap intervals. Sensitivity intervals for the fixed item bank, resampling only scoring rounds, are stored separately in results.json.

These results describe the output behaviour of a fixed model, prompt and 0–100 scale. λ is a combination weight beyond the single-item baseline and cannot be interpreted as the whole negativity bias; averaging or dilution phenomena alone cannot prove an internal mechanism, financial correctness, economic loss or novelty.

[Figure](combination.png) · [Full metrics](results.json) · [Raw scores](scores.csv) · [Analysis code](analyze.py)
