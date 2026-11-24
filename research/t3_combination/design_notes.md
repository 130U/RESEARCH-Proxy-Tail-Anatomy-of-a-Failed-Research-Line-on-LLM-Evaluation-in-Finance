# T3: design and limits of interpretation

2026-11-16. Independent design analysis; no new scores generated, no fits run. The mathematical judgements below follow directly from the task's formulas; they are not conclusions of a literature prior-art check, and cannot on their own prove that the topic is a duplicate.

## What can be answered at present

T3 can test **the combination rule on a fixed prompt and a 0–100 output scale**. A better fit of some formula alone cannot prove that the model internally uses that psychological integration mechanism, nor that its financial judgements are more correct or profitable in trading. After a nonlinear monotone transformation of the single scores the ranking is unchanged, but the additive/average relation usually changes; fixed anchors help stabilise the scale, but they are not proof of an interval scale. This is a mathematical interpretation of lines 19–31 of the task statement.

## Record of evidence and inferences

| No. | Basis read or direct inference | Effect on T3 |
|---|---|---|
| D1 | Task statement, lines 9–15: 30 atoms, 100+45+45+200 pairs, two orders. | 390 unordered combinations and 780 ordered headlines in total. Each atom appears repeatedly; the combinations are not 390 independently drawn facts. By count, the 200 neutral combinations should be read as 20 directional facts × 10 neutral facts, excluding neutral + neutral. |
| D2 | Task statement, lines 21–23 only say that negative weights are multiplied by λ, and give no denominator. | A normalised weighted average and an unnormalised amplification of negative terms are two different models; their λ cannot be used interchangeably. |
| D3 | From the additive formula: after adding a neutral N, the untruncated change is d(N); only d(N)=0 strictly predicts "no change". | The actual eight-run mean score of the neutral headline must be plugged in; its baseline cannot be forced to 50 just because the design label calls it neutral. |
| D4 | For 0≤w≤1, an average must lie between the two input scores; same-direction addition, when not truncated, is more extreme than either single score. | Same-direction combinations are a valid second piece of discriminating evidence; the saturation fraction should be listed separately so that endpoint truncation does not hide the difference. |
| D5 | [Lines 15–17 of the previous round's one-page summary](../absolute_scoring/ONE_PAGE.md) report a retest correlation of 0.9748, together with a difference between same-batch and cross-batch correlations. | 0.9748 was measured on a different batch of headlines and a different task, and cannot be taken as T3's known reliability; new sessions and repetition also cannot guarantee independent errors. |
| D6 | Atom baselines come from a limited eight scorings, while the same estimate is used in many combinations. | The λ interval and the fit errors need to propagate baseline uncertainty; treating single-item means as error-free true values would underestimate uncertainty. |

## Minimum conventions to freeze first if the literature gate is passed

1. **Specify the three functions and the order parameter.** Addition is truncated as in the original task; averaging lets w be the position weight of the first item, in the range [0,1]. One usable normalised asymmetric model is

   f(A,B) = [w r(A)d(A) + (1−w)r(B)d(B)] / [w r(A)+(1−w)r(B)], r(i)=λ if i is a pre-specified negative fact, otherwise 1, λ>0.

   λ=1 gives back the average model; w=1/2 means no position preference. The negative category is fixed before scoring, to avoid ad hoc reclassification of neutral headlines that deviate slightly from 50 as negative. If the pre-specified polarity disagrees with the measured baseline, keep it and report it; items cannot be swapped based on results. This λ measures **the extra combination weight relative to the single-item baseline**, not the model's whole negativity bias; the single negative score already contains one value judgement. For same-direction negative + negative, λ cancels between numerator and denominator, so this subgroup cannot be used to estimate λ independently.

2. **Fix the connective.** The main experiment uses a semicolon; if `as` is tested, list it separately as a linguistic condition. `as` can imply a temporal or causal relation, and the meaning of the two facts may change with the combination, so not all differences can be counted as weight or order effects. The texts avoid facts that explain, offset, entail or repeat each other; neutral facts should have no direction for the same entity and should not change the interpretation of the other fact.

3. **Compare predictive ability, not just training residuals.** Models that can tune w and λ are naturally more flexible. At minimum, put both orders of the same unordered pair in the same fold, compare RMSE with combinations held out, and report residuals by category as well. This hold-out only tests unseen combinations of these 30 known atoms; to claim generalisation to new facts requires holding out by atom, and the two must not be conflated. Report the order effect directly as the paired difference between A;B and B;A for the same pair, which can be cross-checked against the fitted parameters.

4. **State the scope of the intervals clearly.** Do not bootstrap the 390 pairs as independent samples. The minimal conclusion can be limited to "the repeated-scoring behaviour of these 30 fixed facts", propagating the uncertainty of atom baselines and combination scores when resampling scores, and keeping the dependence created by shared calls. To generalise to a population of facts, use a clustering/resampling method that respects the two atom members; the 30 hand-picked facts are still not a random sample of the population. Do not use the large number of combinations to inflate the effective sample size.

5. **Define "clear" first.** The task gives directional decisions but no numeric thresholds for "averaging clearly wins" or "a clear order effect". Before scoring, choose the minimum effect in actual score units and the difference in prediction error, and report point estimates and intervals. A λ interval excluding 1 indicates statistical separation, and does not automatically indicate an exploitable economic risk; near the boundary, report the numbers as they are, and do not borrow the old task's tie gate to create a new "inconclusive" ad hoc.

## Grounds for continuing or stopping

**On design grounds there is reason to run a small screen:** neutral combinations and same-direction combinations give different observable predictions for addition vs averaging, and the two orders together with the full crossing of strong and weak combinations help separate position preference from negative weight. The current design gaps can be patched with the small number of frozen conventions above and are not an automatic reason to stop.

**On novelty it must still pass the literature gate independently:** nearby studies of the same theory, negativity bias or order effects do not mean this measurement has already been replicated; conversely, swapping an old measurement into financial vocabulary does not necessarily produce a research contribution. Whether the same question and the same measurement already exist should be decided by item-by-item comparison with the primary literature. This note does not replace that judgement.

**The interpretation must be narrowed:** averaging winning would at most first support "the outputs of this scoring protocol are diluted by neutral text". Response compression due to length, changes in linguistic context and nonlinearity of the output scale remain competing explanations. This alone cannot be used to claim the discovery of an internal averaging mechanism in the model or a confirmed loophole for announcement manipulation.
