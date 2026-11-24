# T3 plan fixed before scoring

2026-11-16 (America/New_York). Research question: under a fixed financial-sentiment prompt, how do single-fact scores predict the score after two facts are combined? This is not a test of correctness or investment returns. The prior-art records are in literature_integration.md and literature_sentiment.md; no duplicate of the same question and measurement has been confirmed. Order effects and neutral dilution caused by human averaging both already have precedents and cannot be presented as first discoveries.

The main experiment uses the v2 blind-ID revision: after scoring of the first version began, it was found that the P/N/Z IDs hinted at the design polarity, and it was stopped; b01–b04, 120 scores in total, are kept as they are in superseded_v1/ and do not enter the main analysis. When deciding on the revision I only looked at the number completed and did not read the score values. Only the atom IDs were randomly changed to I0001..I0030, seed 2026111622; the texts, the order-randomisation seed, the model and the decision rules are unchanged. The new version was committed and frozen again before the first main-experiment score. The whole process cannot be described as never having modified the plan; this is a documented revision of an exploratory screen, and the first version is not treated as an independent replication.

## Materials and scoring

prepare.py pre-specifies 10 positive, 10 negative and 10 neutral facts about the same fictional company, Virello Industries; all texts are self-made, and SEntFiN is not used. The facts cover different business dimensions with a spread of strengths. Positive/negative labels are specified in advance by the text design, and items are not swapped based on scores. The facts have no formal contradictions, but interactions in business context may still exist, which is a limitation on interpretation.

Single items 30×8=240 scores; 100 positive-negative pairs, 45 pairs each of positive-positive and negative-negative, 200 pairs of directional fact × neutral; each pair in two orders, four times per order, giving 780×4=3120 scores in total. Overall 3360 valid scores and 88 fresh scoring sessions. The main connective is fixed as `; `; `as`, which carries causal/temporal meaning, is not introduced.

The scoring prompt from absolute_scoring/prompt.txt, with five anchors, 0–100 integers and independent scoring of each item, is reused verbatim. At most 40 items per batch; in the single-item stage each round has 30 items, in the combination stage each round has 19 batches of 40 items and a final batch of 20, and no extra headlines are added to fill batches. Each round is randomly permuted and batched, with seeds in prepare.py; no call repeats the same item. All eight single-item rounds are completed first, then the four combination rounds.

The scoring configuration is fixed at gpt-6-sol / low / fork_turns=none, the same as the previous round's absolute-scoring configuration. The model was chosen and the context isolated by fixed selection criteria; the scorer receives only the current batch file, not hypotheses, polarity labels, literature or other scorers' scores. The session runner does not score. Paid APIs and training are prohibited. A failed call or invalid format may be retried on the original input, with the reason recorded; valid scores are not re-scored or rewritten. raw/ stores the raw JSON, calls.jsonl stores the call records, and scores.csv is the expanded table for recomputation. The exact model snapshot, temperature and internal state are not exposed, so independence of session errors cannot be guaranteed.

## Fixed analysis

Let d_i = eight-run single-item mean − 50, y_ab = four-run combination mean − 50. The main models are:

1. Addition: clip(d_a+d_b,−50,50), no fitted parameters.
2. Averaging: w d_a+(1−w)d_b; w is the first-position weight.
3. Negativity-weighted average: [w r_a d_a+(1−w)r_b d_b]/[w r_a+(1−w)r_b], r_i=λ if pre-labelled N, otherwise 1.

w ranges over [0.001,0.999] and λ over [0.05,20]; if the numerical optimisation hits a bound, this must be disclosed. λ only represents the extra combination weight relative to the single-item calibration score; it is not the model's overall negativity bias. In same-direction N+N, λ cancels. Neutral headlines use their actual single-item baselines, not forced to 50, and are not deleted if their polarity differs from expectation.

A separate interpretive control is listed: clip(k(d_a+d_b),−50,50), k∈[0.5,1]. This family corresponds to averaging equally weighted information with a neutral initial opinion: a single item gives v/(p+1), two items give (v_a+v_b)/(p+2), so k=(p+1)/(p+2). It is a reminder that same-direction combinations being more extreme cannot rule out averaging with an initial opinion. It is used only as a pre-specified diagnostic, not to choose a separate continue gate.

Report the training RMSE/MAE overall and by combination category, and the prediction error with each atom held out. Each fold excludes all combinations containing the held-out atom and then predicts those combinations; the squared/absolute losses of each combination's two held-out predictions are averaged and then aggregated. The held-out atom's single-item baseline is kept, so this tests unseen combinations of calibrated facts, not generalisation to unseen text.

Report λ, w and intervals; neutral dilution is sign(d_directional fact)×(single-item mean − combination mean), where a positive number means shrinkage towards 50; also report the neutral items' own baselines and the additive prediction. The main order effect is the paired difference "positive first − negative first" over the 100 PN pairs; the overall absolute difference across all orders is descriptive. For same-direction combinations report the fraction and magnitude lying between the two single items and exceeding the stronger single item. Report endpoint scores and additive saturation.

1000 bootstrap replicates of stratified atom weights (10 weights with replacement each for P/N/Z); the weight of a pair is the product of the multiplicities of its two atoms; the eight single-item rounds and the four combination rounds are each resampled by whole round, with all items sharing the same round draw, propagating baseline and combination repeat error. Percentile 95% intervals are given. This is a resampling sensitivity for 30 hand-picked atoms and cannot be taken as a coverage guarantee for a population of random financial headlines; four rounds are also not enough to identify all batch correlations. Numerical resampling seed=2026111623. The intervals are per item, not simultaneous intervals after multiple-testing correction.

## Decision gates

If any of the following holds, "continue" to later mechanism validation; otherwise this round "drops / closes"; values at the threshold are decided by the numbers as they are, and the old task's tie gate is not borrowed:

- The 95% interval of λ does not contain 1.
- The absolute value of the mean PN order difference is at least 2 points, and its 95% interval does not contain 0.
- Simple averaging beats addition by at least 2 points in both training and held-out RMSE, and the lower bound of the 95% interval of the mean neutral dilution is greater than 0.

2 points is a practical screening threshold chosen in advance for this round, not something specified by the original task or the literature. A rejection only means that this fixed small sample did not reach the continue gate; it does not prove that there is no effect in the population. Passing a gate also does not guarantee novelty or publishability; if order passes alone, it must be stated that a direct precedent exists, and any later contribution needs separate evidence of mechanism or practical impact.

Deliverables: a one-page summary, one result figure, raw scores and recomputation code; the literature and the short plan are kept as source documentation. No external contact, no paid APIs, no training; the topic is not expanded and no continue conclusion is presupposed.
