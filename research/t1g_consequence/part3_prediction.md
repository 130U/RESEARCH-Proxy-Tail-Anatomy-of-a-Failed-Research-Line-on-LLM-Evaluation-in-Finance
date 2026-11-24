# TAT-QA frozen prediction: measurement not yet computed

Source level: our experiment (point values, displayed precision, and answer distribution only; no TAT-QA rounding-box range had been computed when this file was generated).

Input: the official pinned TAT-QA version `870accc41953dcde885aabeb963d94aabdc0fbc3`, train/dev/test_gold. 6,960 arithmetic questions; 5661 conservatively bound; the prediction definition covers 5261.

| Type | Questions | Predicted 1% out-of-tolerance rate |
|---|---:|---:|
| growth | 1349 | 27.464491% |
| difference | 2308 | 31.181029% |
| ratio | 515 | 12.252849% |
| sum | 1089 | 12.433881% |
| Total (population the prediction applies to) | 5261 | 24.494607% |

Growth rates follow T1a: the empirical joint distribution of significant-digit pairs is taken as independent of the growth-magnitude marginal, the base-period mantissa is log-uniform on [1,10), and the exact two-number growth rule is integrated. Ratios use the same mantissa model with the ratio magnitude fixed, integrating the error rule for same-sign absolute quantities. The prediction function does not receive per-question mantissas.

The radius of differences and linear sums is determined by the displayed half last-digit units and the known linear coefficients; the empirical distribution of radii is mixed independently with the empirical distribution of absolute answer values to compute the share with R > 0.01 |y|, without reading the per-question correspondence. The independence in this extension is an assumption; no parameter was fitted.

Another 400 bound non-standard/nonlinear questions have no frozen population prediction; they are still audited later and reported separately. Passing the threshold on the applicable population must not be written up as all arithmetic questions passing.

The main comparison uses the same applicable population, first defining the 1% tolerance on the program center value (the prediction assumes the standard answer equals the value computed from the displayed numbers), and also reports a sensitivity result with the annotated answer as the center. Output magnitude is converted only by percent/explicit units; offsets between the annotation and the center are kept.

Source binding: each number in a formula corresponds to a single table cell; when there is no table match, a single number in the relevant paragraph is used. Identical formula numbers share a variable only when they correspond to a single source; duplicate sources or precision conflicts are excluded. Formula numbers without a source that are 0–10, 12, 100, or decimal unit multiples are treated as explicit structural constants; the rest are excluded. This convention is a conditional rounding audit and does not claim that all integers were actually rounded.

Acceptance, frozen: the population prediction and the measurement differ by no more than 5 percentage points, and the first-order decision agreement rate on the same population is at least 95%. Per-operation-type differences, the fully bound population, and coverage of all arithmetic questions are all reported at the same time.
