# The `private/` Folder

The name comes from my local workspace, where row-level files were kept out of shared
bundles. Nothing here is confidential; the folder is public with the rest of the repository.

| Folder | Contents |
|---|---|
| [real_baseline/](real_baseline/) | SEntFiN entity rows (MIT licence, see `source_materials/`), the fixed train/development/test splits, quarantined rows, the saved TF-IDF models and per-row predictions. Used in Stages A, B and C |
| [agent_tail_pilot/](agent_tail_pilot/) | Stage B development pilot: two prompt versions × two input orders × two models, raw rankings of 128 headlines |
| [agent_tail_methods/stage1_n32/](agent_tail_methods/stage1_n32/) | Stage B stage 1: every pairwise and ranking input, raw judgement, mapping and seed for 32 fresh headlines |
| [agent_tail_methods/stage2_n128_sol/](agent_tail_methods/stage2_n128_sol/) | Stage B stage 2: eight inputs and eight raw rankings for 128 fresh headlines |

The folder keeps its name because the analysis scripts refer to `research/private/...`.

The saved model `real_baseline/trained/models/entity_only_tfidf_lr.joblib` is a binary scikit-learn
pickle; its vocabulary contains a few non-English entity strings from the source data, left as they
are.
