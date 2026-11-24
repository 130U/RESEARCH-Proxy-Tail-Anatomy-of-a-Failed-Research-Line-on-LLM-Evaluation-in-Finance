# Reproducible evaluation entry point

Run from the repository root; requires Python >=3.10 and NumPy. The research code does not read the network, does not need old checkpoints, and does not modify the old Trial.

```powershell
python -m research.evaluation.reconstruct
python -m unittest research.evaluation.test_evaluate -v
```

The first command rebuilds the public summary and overwrites `research/experiments/wp0_1/reconstruction.json`. Random-number results are reproducible under the same NumPy version/seed; the runtime and hardware fields will naturally differ.

For future new experiments, first freeze the model and the test set, then export the per-row predictions to a **local private directory**, one JSON object per line. For example (illustration only, not an existing real sample):

```json
{"id":"row-1","family_id":"family-1","event_id":"event-1","target":"A","available_at":"2024-01-01T12:00:00Z","label":"neutral","prediction":"neutral","baseline_prediction":"bullish"}
```

At minimum you need id, label, prediction, and one of family_id/event_id. When comparing systems, baseline_prediction must be present on every row and come from the same row. `available_at` and target are used by the split/deduplication helper functions; do not invent missing times, and do not automatically treat a missing event_id as an independent event.

```powershell
python -m research.evaluation.evaluate runs/private/new_predictions.jsonl runs/private/new_metrics.json --repetitions 10000 --seed 130
```

This command outputs aggregate statistics and the input SHA256; it does not output text, per-row labels or predictions. You should still check whether the output is fit to publish. It can run from the same repository root on Kaggle/Colab and calls no cloud service; it only summarizes predictions that already exist locally.

Use `chronological_split(records, train_end, development_end)` to get the preset time split; `deduplicate_events(records)` keeps the earliest view of each reviewed event-target unit. Choosing "one row per event target" changes the estimand and must be fixed before looking at the test labels. Split by complete event family first, then take representative records within each partition by the pre-registered rule; do not first delete late-arriving views and then treat the family as available early.

The cluster bootstrap estimates row-weighted performance: each replicate draws, with replacement, the same number of whole clusters as the original; when cluster sizes differ, the number of resampled rows can differ. If the target is equal weight per event, a different statistic must be defined; the two must not be mixed silently.

Baseline execution order: TF-IDF fits the vocabulary and classifier on the training partition; FinBERT and the small LLM fix the local weight version, the input task/label mapping and the prompt; the same independent new test set is used to generate predictions. This deliverable has no actual FinBERT/LLM results and provides no fabricated baseline table. The original SEntFiN sentiment labels and this project's author stance also cannot be used directly as the same gold.
