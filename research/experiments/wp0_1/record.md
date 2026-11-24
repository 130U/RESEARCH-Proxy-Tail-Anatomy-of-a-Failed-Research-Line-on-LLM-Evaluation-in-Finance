# WP0.1: reconstruction of the public development-set summary and an interface for later cluster evaluation

Date: 2026-11-15. Status: **partly complete**; the public-summary reconstruction and the evaluation tools are done; the three real-data baselines and the cluster confidence interval for the original model are not done.

## Question to test

The initial plan asked whether "the gap of 0.655 versus 0.609 is within sampling error". The strict answer is: **the existing summary cannot identify the uncertainty of the paired difference, so it cannot be judged significant or non-significant**. We first reconstruct the sampling sensitivity of the model itself under an IID assumption, and state clearly what data would be needed in future to test the difference.

## Budget and configuration

The pre-run budget is in [budget.md](budget.md). The input is the public summary in `docs/experiment-results.md`; source baseline `8e4dd0b33c95ac2ac1a6015eba6f2dfafe5c1254`. The new source code for this round is in `research/evaluation/` and had not been committed at run time; file hashes are recorded by the deliverable manifest.

- Data size: a 101-row summary; real row-level labels, predictions and event links are not available. I decided not to rely on old checkpoints/predictions and to build from scratch.
- Actual hardware: Windows AMD64 CPU; Python 3.12.14, NumPy 2.5.3. The processor and the input-file SHA256 are in [reconstruction.json](reconstruction.json).
- Seed: 130; matrix indices are derived through `SeedSequence([130,index])`; 100,000 multinomial samples per matrix.
- Actual computation time: first run 1.109 seconds; unit tests 0.367 seconds, 7/7 passed. Source: our experiment `wp0_1`, not a retraining of the historical model.
- Tokens, GPU memory: 0. No new models or data were downloaded.

## Derivation and complete enumeration

The class order is bearish / neutral / bullish, the true class supports are `(10,76,15)`, and the diagonal is `(5,62,12)`. From the four-decimal precision values, within integer denominators of at most 101, the corresponding prediction counts are uniquely `(11,66,24)`. All consistent matrices can be written as

```math
C(a)=\begin{pmatrix}5&a&5-a\\7-a&62&7+a\\a-1&4-a&12\end{pmatrix},\quad a\in\{1,2,3,4\}.
```

Non-negativity gives `1 <= a <= 4`, so no other matrix is missed. The four have the same accuracy and the same per-class P/R/F1, but different joint structure of misclassifications. Each matrix is expanded into an empirical joint distribution, from which 101 truth–prediction pairs are drawn with replacement; multinomial sampling is exactly equivalent to the row bootstrap. For each sample the fixed three-class macro-F1 is computed, with the F1 of a missing class counted as 0 following the existing evaluation convention, and the 2.5% and 97.5% quantiles are taken.

## Results

Source of all intervals and enumerated numbers below: **our experiment wp0_1**; source of the input numbers: the repository's public summary, whose original provenance is my Kaggle training log, not an independent reproduction in this round.

| a | Accuracy | Macro-F1 | 95% IID percentile bootstrap interval for Macro-F1 | n |
|---:|---:|---:|---|---:|
| 1 | 0.782178 | 0.654938 | [0.520936, 0.769613] | 101 |
| 2 | 0.782178 | 0.654938 | [0.521071, 0.768393] | 101 |
| 3 | 0.782178 | 0.654938 | [0.520883, 0.769282] | 101 |
| 4 | 0.782178 | 0.654938 | [0.520957, 0.769178] | 101 |

The accuracy and all per-class precision/recall/F1 intervals for each matrix are in the JSON. We report the range of the lower endpoints `[0.520883,0.521071]` and the range of the upper endpoints `[0.768393,0.769613]`, rather than picking the single most favourable matrix. The small endpoint differences caused by different RNG samples are included in these ranges and should not be read as exact matrix effects.

TF-IDF's 0.6087 falls inside the model interval above; this is only a description and **not a test of the difference**. The difference needs joint predictions of the two systems on the same samples, and in particular information on whether errors occur in the same cluster. Even given two independent marginal CIs, whether they overlap cannot replace a paired CI. The four model confusion matrices still cannot reconstruct the joint model × baseline × true label table, let alone recover the family/event structure.

## Evaluation tools provided

`research/evaluation/evaluate.py` implements:

1. Cluster bootstrap for accuracy, macro-F1 and per-class P/R/F1; metrics are row-weighted, and whole clusters are the sampling unit.
2. Intervals for the model−baseline difference on the same rows with the same resampled clusters; a partially missing baseline is not allowed.
3. Transitive closure over both family and event links, so that one event is not wrongly treated as independent because it sits in different families.
4. Preset time thresholds, with partitioning by the latest `available_at` of each linked group; a late-arriving member does not enter an earlier training partition.
5. A deduplication policy that keeps the earliest view per audited event_id and target, and refuses automatic merging when a label conflict for the same event target is found.

These tools cannot automatically find all semantic duplicates, and cannot turn source timestamps into true availability times. Independent/representative clusters are an assumption; a small number of clusters, non-stationarity and post-hoc model selection still distort the percentile bootstrap. It is not a P1 finite-sample certificate.

## Baseline status

| System | Current traceable status | New 95% cluster interval | Missing |
|---|---|---|---|
| Original 24M balanced SFT | Public log summary; development-set point estimate | Not obtained | Original per-row predictions and reliable event clusters; the old weights are not used as a dependency |
| TF-IDF + logistic regression | Implemented in `src/finllm/baselines.py`, historical dev 0.6087 | Not obtained | The same independent new test samples and paired predictions |
| FinBERT | Not run | None | Local model weights, semantically matched data, fixed version |
| Small LLM zero-shot | Not run | None | Local model weights, fixed prompt/version, measured compute |

I kept this round offline, so it adds no downloads or remote calls for these missing items. The synthetic foundations experiment is reported separately and cannot fill the gap left by the real-data baselines.

## Conclusion and limits

Under the IID row-sampling assumption the model itself shows a fairly wide uncertainty interval. Whether it beats TF-IDF is **not determined**; neither "the difference is just noise" nor "the difference is significant" is supported by the existing evidence. The original development set was used for model selection, and the 101 rows are not a confirmed sample of independent events, so this reconstruction cannot be treated as the final generalization interval. The example conclusion in the initial template, "the gap of 0.655 vs 0.609 is within the 95% interval", needs to be replaced by the more accurate statement above.

Next step: freeze a new task, an event/time split, a budget and selection rules, and produce independent test predictions from scratch; the three baselines must use the same test rows and the same bootstrap clusters. The full G0 cannot be judged passed on the basis of this summary reconstruction.
