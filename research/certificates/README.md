# Fixed test-statistic checker

An offline implementation of P1's "jointly contaminated shards → accuracy and macro-F1 intervals". It trains no model and downloads no data.

```powershell
python -m research.certificates.collective research/experiments/collective_metrics/audit_example.json research/experiments/collective_metrics/audit_certificate.json --method exact
python -m research.certificates.run_examples
python -m unittest research.certificates.test_collective -v
```

`audit_example.json` is explicitly a hand-constructed mathematical example; its zero audit findings are not measured data. Probability statements in the output are **conditional on** premises such as random sampling, a correct audit and a historically trustworthy core; the program only computes the bounds under these premises.

## Input

- `input_kind` must be `head_predictions`.
- `votes_by_example_and_head` has one test point per row, and each column holds the **class prediction** of the same shard head; it is not per-class vote counts. Column identity must be the same across all points. The planner in `research/planning/` takes per-class vote counts; the two are not interchangeable.
- `labels` are the fixed test ground truth; `classes` is fixed and at least 2; ties go to the smallest index.
- Choose one: `budget` is the maximum number of heads that can change; or `audit` supplies a finite population size, a fixed sample size, the number of findings and alpha, which are converted into an upper bound on contaminated documents.

Under the conditions of a fully trustworthy core, local training and stable IDs, the number of contaminated documents removed can upper-bound the number of affected heads. This conversion cannot be made directly when the shared backbone is contaminated or when one modification spans two IDs.

## Two computations

`component`: for each set of jointly affected heads, bound TP/FP per class, then take a conservative envelope over the F1 components. It does not guarantee that the per-class endpoints are reachable at the same time.

`exact`: dynamic programming over TP and prediction counts jointly, giving the exact extremes within the declared relaxation model in which "selected heads can freely change all their outputs". It does not prove that some training set can realize the endpoints. Even a fully exact counting model is still an outer relaxation of actual retraining.

Both enumerate the sets of jointly affected heads and keep the constraints shared across test points. When `--max-subsets` or `--max-states` is exceeded they fail; they must not drop the unsearched part and go on issuing a certificate.

Numeric endpoints are given both as exact fractions and as an outward-rounded floating-point display. All K classes take part in macro-F1; a class whose true support and predicted support are both 0 contributes 0. This is not a dynamic average over the observed classes.

## Statistical semantics

The audit wrapper gives coverage with respect to the audit's randomness, on a fixed finite corpus. Accuracy and macro-F1 are obtained simultaneously from the same event `K_true <= K_upper`, so alpha does not need to be split in two. It is not a confidence interval for a future population, and it is not an audit method that stays valid under arbitrary early stopping.

Nothing here proves real corpus rights, timestamps, parsing accuracy, absence of future selection information, training determinism or backbone provenance. The output lists these unverified premises explicitly; the fact that the JSON shows "conditional certificate" is no basis for claiming externally that there is truly no leakage.
