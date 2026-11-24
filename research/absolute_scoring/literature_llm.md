# New absolute-scoring question: LLM literature veto check

Search date: 2026-11-16. The question in the repository's TASK.md is: when the same model repeatedly gives absolute scores to financial headlines, is the top-p list of the mean scores stable, and can single-score reliability predict this stability through Spearman–Brown plus a bivariate normal distribution? This file covers only the literature on LLM scoring, retesting, batching and aggregation; it contains no new model scoring.

**Conclusion: we found direct prior work for the theoretical skeleton and for several of the measurements; we have not confirmed that any single original paper completed the full combination of objects and validations in this question. None of "repeated scoring, mean scores, batch effects, LLM screening recall, the reliability formula" can be claimed on its own as a new contribution.** The two closest papers have already studied, respectively, how LLM decisions change under different batches together with Gaussian aggregation predictions, and the screening recall of LLMs for human top candidates. If this question continues, it should be framed as an advance test of a known model on "two-tail top-list self-overlap of the same model", and its value depends on whether a verifiable prediction failure appears; moving to financial headlines is not a theoretical innovation in itself.

This is a targeted quick check with explicit limits for this round; **it does not claim to have completed a half-day search or a systematic review**. Abstracts and search snippets were used only for locating papers; the evidence below comes from the parts noted in opened original papers or author manuscripts. No full citation-network tracing was done, and papers not yet indexed are not excluded.

## Closest prior work

### 1. Xie and Alanwar: Judged in Company (2026)

[Original HTML, arXiv:2610.40241v1](https://arxiv.org/html/2610.40241v1). Read §3, §5.2–5.6, §6, and the prediction tables in appendices H.3–H.5 and I. It re-batches the same items and separates the effects of membership, order and position; under a latent Gaussian score model, it predicts decision flips from the correlation with an exact bivariate normal integral, and studies voting across permutations/batches. Some of the voting predictions were made before the additional runs, and there are also back-fitted results, so not all of them can be called independent validation.

**Degree of overlap: very strong.** Noise reduction from averaging over independent contexts, threshold instability and its Gaussian prediction have all already appeared. In the parts we read we did not see this question's full experiment: means of raw integer scores, two-tail top-p overlap for two groups with m=2/4, and q90/p. Its main measured objects are fixed category thresholds and majority votes, and the latent score is not a directly observed 0–100 score.

There is also an important mathematical correspondence here (the following is an inference from this analysis, not a claim that the authors used this question's terms). In the parallel measurement model

```math
X_{ij}=T_i+\epsilon_{ij},\qquad
r=\frac{\mathrm{Var}(T)}{\mathrm{Var}(T)+\mathrm{Var}(\epsilon)},
```

the correlation between two conditionally independent, homoscedastic m-score means is

```math
r_m=\frac{mr}{1+(m-1)r}.
```

If the standardized means are jointly normal, let h=Φ⁻¹(1−p); for the same marginal fraction p, the flip probability F and the top-list overlap H satisfy

```math
H=\frac{P(Z_1>h,Z_2>h)}p=1-\frac{F}{2p}.
```

So under these assumptions, "SB followed by Gaussian top-list overlap" is a direct combination of existing random-effects/threshold models, and a new law cannot be claimed just by rewriting it in top-list language. Whether exactly the same top-list measurement already exists is a separate question.

### 2. Stockdale, Hickman and Liu: Scoring Employment Interviews With Large Language Models (2026)

[Full author manuscript](https://www.researchgate.net/publication/403780997_Scoring_employment_interviews_with_large_language_models_Evaluation_design_components_validity_investigations_and_best_practice_recommendations), [official DOI](https://doi.org/10.1037/apl0001396). We read the author manuscript's evaluation design, intrarater reliability, test–retest correlations, the ensemble discussion, and Tables 7 and 14 with the corresponding screening text; the author manuscript is not guaranteed to match the published version word for word.

It studies behaviorally anchored scales, examples, single-candidate/nine-candidate batches, temperature and aggregation; **it directly measures the recall with which an LLM keeps human top candidates at different selection ratios**, and examines screening first followed by human review. The authors point out specifically that the test–retest correlation between honest answers and answers given in a job-application setting is not a true same-input retest reliability.

**Degree of overlap: a very strong applied and measurement precedent.** "Does the LLM miss high-scoring candidates" and widened screening have already been measured. In the text we read and in a keyword search of the full text, we found no untuned comparison of single-score r→SB→Gaussian→m=2/4 top-list self-overlap; not finding the keywords cannot substitute for ruling out every equivalent form of the formula.

### 3. Apartsin and Aperstein: CoEval (2026)

[Original PDF, arXiv:2606.03650](https://arxiv.org/pdf/2606.03650). Read §3.4, the panel-size results in §5, and Appendix A. The paper explicitly uses the mean inter-judge correlation and
$`R_k=k\bar r/[1+(k-1)\bar r]`$, and reports that ICC agrees with the SB prediction.

**Degree of overlap: a direct precedent for the formula, but a different object.** It mainly examines different judge compositions and model leaderboards, not headline top lists from repeated scoring by the same model. The numerical agreement between its same-panel ICC and SB also cannot replace this question's use of single-score correlation to predict top-list results that were not used for tuning.

## Other original papers read

| Paper | Parts actually read and what they support | Relation to the new question |
|---|---|---|
| [Yuan et al., BatchEval, arXiv:2401.00437](https://arxiv.org/pdf/2401.00437); [ACL 2024 record](https://aclanthology.org/2024.acl-long.846/) | arXiv author version §2.2, §3, §4.3–4.5: iteratively changing batches and averaging scores, studying the gain from averaging and batch references; gives an ensemble decomposition of squared error. The ACL PDF download timed out, so the author version is not counted as a checked reading of the published PDF. | Re-batching and averaging several scores is not a new design. It actively uses within-batch comparison and also re-batches according to existing scores, which differs from this question's fixed prompt/random re-batching; its target is the overall correlation with human scores. |
| [Messing, Hidden Measurement Error in LLM Pipelines…, arXiv:2604.11581v1](https://arxiv.org/html/2604.11581v1) | §2.4, 2.6, 4.2–4.3 and SI.1.6–1.7: decomposes variance into items, prompts, judges, repeats, etc., and predicts the gain from adding repeats or judges based on a D-study. The small pilot versus full-run comparison uses overlapping data, and the author states that it is not a true out-of-sample validation. | There is already systematic work on measurement-error decomposition and repeat-budget prediction; the top-p two-tail list object of this question was not seen. |
| [Yagubyan, The Coin Flip Judge?, arXiv:2606.13685v1](https://arxiv.org/html/2606.13685v1) | §5.9–5.10: how the probability that repeated votes reach the 50-vote reference conclusion changes with the number of votes, and the ICC/variance decomposition of 50 pointwise scores. | The repeat count–stability curve has precedent; a 50-vote reference consensus is not ground truth, and voting fidelity is not top-list overlap. |
| [Lau, Same Input, Different Scores, arXiv:2603.04417](https://arxiv.org/pdf/2603.04417) | §3–4: numeric scoring repeated ten times under a fixed prompt, comparing models, temperatures and per-item score standard deviations. | There is direct evidence that numeric scoring is unstable; in the results we read we found no experiment predicting top lists after averaging. |
| [Stadler et al., JMIR Medical Education 2026, e94666](https://mededu.jmir.org/2026/1/e94666/) | Methods/Procedure, Data Analysis, RQ1: 122 clinical abstracts, four models, four prompt conditions, five repeats without conversation memory; reports both ICC and category agreement. | Anchored/example scales and retesting already exist. Note in particular that its ICC is computed on the mean of five scores and cannot be used directly as this question's single-score r; no top-list sets or Gaussian prediction were seen. |
| [Liu et al., Evaluating large language models for abstract evaluation tasks, 2026](https://www.frontiersin.org/journals/research-metrics-and-analytics/articles/10.3389/frma.2026.1807672/pdf) | PDF methods and discussion, pages 6–7: abstract scoring, human/LLM agreement; the discussion explicitly uses SB to explain averaging scores from more judges and proposes screening/triage applications. | SB + LLM scoring + screening appear in the same paper; the parts read are explanations and application suggestions, with no advance top-p prediction test of same-model repeated means as in this question. |

## Concrete implications for this question

This round did not confirm any original paper that satisfies all of "same model, repeated absolute scoring of the same items, two groups of means, top-p self-overlap/widening for fixed recall, and an empirical SB–Gaussian validation using only single-score r as input". So we cannot declare a complete duplicate on this basis; equally, we cannot declare novelty. The closest Gaussian batching paper substantially narrows the room for a "new theory".

If the work continues as TASK.md says, the valid framing is: **measure when a known baseline fails under a specified, frozen scoring protocol**. Averaging raw integer scores while computing r from the normal scores of single-round ranks does not automatically satisfy the linear additive assumption of parallel measurement; so the formula should serve as an advance baseline, not as a guarantee that needs no validation. Deviations may come from score nonlinearity, heteroscedasticity, ties, batch dependence or tail dependence, and cannot be attributed only to "tail failure". This is an inference about the method of this question, not an experimental conclusion given by the cited papers.

Likewise, same-model top-list self-overlap only shows retest stability; it cannot be used to assert that financial facts are correct, that recall of human top lists is high, that cross-model screening is reliable, or that economic value is positive. Whether 90% is reached must be reported with the actual sets and the uncertainty; agreement with its own consensus cannot substitute for truth.

The keyword combinations covered by this round's search include: `LLM test-retest reliability scoring`, `LLM Spearman-Brown`, `LLM Spearman-Brown selection/Gaussian`, `LLM top-p Spearman-Brown`, `repeated scoring top-k overlap`, `batch context judge score reliability`, `employment interview LLM selection recall`; we also followed up the methods, formulas and results sections of the directly relevant full texts above. A search that returns no exact combination is not proof that none exists; a complete search of older psychometric and selection formulas is the responsibility of a separate theory-literature work stream.
