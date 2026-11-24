# T3 one-page summary: continue per the pre-registered gate, but check for model misspecification first

2026-11-16 | **Formal decision: continue; the only gate passed is the λ gate. Research recommendation: do only one model-specification check, and for now do not expand scoring or claim a new mechanism.** Fixed gpt-6-sol / low, 30 self-made single facts eight times each, 390 pairs in both orders four times each: **88 main calls, 3,360 scores, all completed**.

**The clearest observation: combined scores are closer to addition, and simple averaging performs poorly.** All error units are points on the 0–100 scale; the hold-out still uses the held-out fact's single-item calibration score.

| Candidate rule | Fit RMSE | Leave-one-atom-out RMSE |
|---|---:|---:|
| Truncated addition | 5.235 | 5.235 |
| Simple weighted average | 12.144 | 12.144 |
| Negativity-weighted average | 10.300 | 10.564 |
| Control family with a neutral initial opinion (pre-specified diagnostic) | 4.966 | 5.027 |

The diagnostic control is only slightly better than addition, and cannot be used to confirm an internal averaging mechanism. The main measurements are as follows; brackets give the main 95% resampling intervals:

- **λ: 2.691 [1.219, 5.304]**, passes the pre-registered gate; it comes from the negativity-weighted average model, which fits poorly.
- **Shrinkage from adding a neutral item: 1.036 [−0.030, 2.014] points**. All ten neutral single scores are 50; looking only at bad news + neutral gives 1.176 [−0.153, 2.359] points, so the evidence for dilution is unclear.
- **Positive first minus negative first: −0.168 [−1.643, 1.160] points**, the order gate failed; position weight w=0.498 [0.487, 0.510].
- **Same-direction combinations:** positive-positive 73.3% and negative-negative 64.4% are more extreme than the stronger single item, exceeding it by 2.844 and 1.167 points on average.

**Risk in interpreting λ:** for positive + neutral, the normalised average predicts about dP/2, which λ cannot correct; for negative + neutral, however, increasing λ can pull λ/(1+λ)·dN back to the single item. So near-additive behaviour can also push λ up. This model's hold-out error is about twice that of addition, so 2.69 cannot be interpreted as a real "bad-news influence multiplier". The only next step worth taking is an additive test with separate positive and negative coefficients on the existing data, **clearly labelled as post hoc exploration**, to rule out model misspecification first and then decide whether to expand the study; this round's frozen decision stays unchanged.

The prior-art check did not confirm a complete duplicate, but [scoring in reversed positive/negative order](https://aclanthology.org/2025.nlp4dh-1.18.pdf) and [human aggregation rules for neutral dilution in finance](https://www.ecb.europa.eu/pub/pdf/scpwps/ecb.wp3283~df0633dfd3.de.pdf?495f4d0ec675f3cbda625976eb20dff3=) already have precedents. One cannot claim the first discovery of averaging, order bias or a financial manipulation loophole. [Literature gate](literature_gate.md)

The intervals come from 1000 resamples stratified by atom + whole-round score resampling, and are limited to the hand-made item bank. The first version's P/N/Z IDs may have hinted at polarity; those 4 calls / 120 scores are kept as is and excluded; when the revision was decided I had not read the score values, and the main experiment switched to random blind IDs. 92 calls were actually made; the main experiment had no failures or retries. [Execution and recomputation](execution_notes.md)

[Result figure](combination.png) · [Figure PDF](combination.pdf) · [Raw scores CSV](scores.csv) · [Raw JSON](raw/) · [Analysis code](analyze.py) · [Full metrics and intervals](results.json) · [Frozen plan](protocol.md)
