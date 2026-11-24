# New Phase 0 real baseline: pre-execution protocol and budget

2026-11-16. Status: written before this round's real preparation, training and test prediction. I decided to build from scratch and to keep the research local; this experiment uses only existing files and local libraries, downloads no weights and contacts no one outside. The old 24M predictions cannot be recovered; this experiment forms **new evidence on the original source task**; it does not back-fill old scores and does not claim that the original G0 is fully passed.

## Goal and identity

The task is the **sentiment toward a specified entity in a headline**, as defined by the original SEntFiN authors. The labels are fixed as negative, neutral, positive, with indices 0, 1, 2 in that order; they are not renamed as investment stances on securities. The model input is the headline and the specified entity; several entities in the same headline can have different labels. The main question is: under a fixed lexical-cluster split, how large is the difference between strong character and word linear baselines, and how much of the apparent performance does entity identity by itself explain? This is not an innovative contribution for a paper; it is the real foundation for later judgments on whether a model is necessary.

Original file: `data/raw/candidates/sentfin/SEntFiN.csv` in the old repository; the existing inventory SHA256 is `570af7ba58f724f3fcc414dd5ba80da5b1a3b342134d76c6ebdf53a32c54a92f`, 10753 rows; re-verified during this round's preparation. Hashes of the source code, configuration, data and split files are saved separately. Licence and task scope are in the [source judgment](../data/source_audit.md); the use stays private research.

## Data rules

1. Accept only the frozen column structure and usable Title/Decisions. First parse the AST and reject duplicate dictionary keys, then read the restricted entity→label dictionary with literal_eval; do not use eval, and do not guess repairs for anomalous labels. Empty/non-string entities, normalized entity collisions or illegal labels quarantine the row. Anomaly reasons and raw rows stay only in the private quarantine file; the report gives only counts.
2. Unicode normalization, casefold and whitespace normalization of headlines are used for duplicate detection; identical labels for the same normalized headline and the same normalized entity are merged, and conflicts within the same key are quarantined. Different labels for different entities are kept. The exact normalization is fixed by prepare.py and its hash, and is not adjusted after seeing model scores.
3. All entities of the same headline are first bound into the same group; then all pairs of headlines with token-set Jaccard≥.8 are connected transitively. Similarity uses integer comparison, and candidate filtering must be equivalent to all-pairs search; unverified approximate MinHash must not be used. Empty token sets are not treated as similar via 0/0; they are merged only if their normalized forms are identical.
4. Compute a hash from the stable group identity and seed=130, and assign 70%/15%/15% to train/development/test; no re-splitting driven by scores or labels. Record sample/headline/group counts, the largest group and the distribution, and that duplicate/near-duplicate cross edges are 0. This grouping is lexical clusters, **not reviewed semantic events, and not a time split**.
5. All text and per-row labels/splits/predictions/training weights live only in `research/private/real_baseline/`. This directory is excluded by both gitignore and the archiving code; the public record contains only code, anonymous summaries and hashes. When the root package is rebuilt, acceptance checks that the archive has no private members.

The text of the whole corpus is used for pre-split deduplication, and conflicting labels are used for data cleaning; these are explicit dataset-construction operations, and we do not claim that the test material is completely unseen or that the historical information set is measurable. Test scores and per-row errors are not used before model/hyperparameter selection is frozen; lexical duplicate detection is not treated as removing all event leakage.

## Fixed baselines and selection

| System | Features/training | Purpose |
|---|---|---|
| Majority class | Train label frequencies only; ties by the fixed label order | sanity baseline |
| word LR | train-only TF-IDF, word(1,2), at most 50000 features; multiclass LR | Primary comparison baseline |
| char LR | train-only TF-IDF, char_wb(3,5), at most 50000 features; multiclass LR | Primary comparison target |
| entity-only LR | Reads only the target entity, word(1,2), at most 50000 features; same LR selection | Pre-specified identity-shortcut diagnostic, not presented as a language-understanding result |

The two primary systems share a fixed text transformation: keep the original target-entity prefix; replace case-insensitive, whole-word-boundary literal matches of the target entity in the headline with `TARGET_ENTITY`. When there is no literal match, keep the headline and count coverage, without calling NER or a model to add aliases. The entity lexical marker only helps the same rule-based baseline bind the target; it does not prove that all semantic binding is correct. The raw input_text in the data file and the actual feature transformation are recorded separately and must not be quietly mixed.

The C candidates for LR are fixed at {.1,1,10}, with class_weight=balanced, max_iter=1000, tol=1e-4, random_state=130 and a CPU thread limit of 2. Each system selects C only by the fixed three-class macro-F1 on development, with exact ties going to the smaller C. The TF-IDF vocabulary and IDF are fitted on train only; the selected system is not refitted on train+development. Convergence warnings and actual iteration counts must be recorded; they must not be silently ignored, and the solver must not be changed after looking at test.

Word-level tokenization is fixed as `(?u)\b\w+\b`, keeping single-character entities/digits; TF-IDF explicitly uses lowercase=True, norm=l2, use_idf=True, smooth_idf=True, sublinear_tf=False, min_df=1, max_df=1.0. This addition was fixed before the real preparation/training was executed. The difference between the entity marking and the source input_text must be recorded in the model configuration.

The primary comparison is pre-specified as **the paired char−word difference in test macro-F1**; it is not picking the best system after looking at test and then claiming its CI is valid. Other accuracies, per-class P/R/F1 and the entity-only comparison are descriptive/diagnostic, explicitly without multiple-comparison correction. The conditions for running FinBERT/a small LLM locally are not in place; without running them the table is not filled in, and the three local simple baselines cannot be said to replace the original three-baseline requirement.

## Evaluation and statistical scope

Fixed three-class macro-F1 (zero denominators contribute 0) and accuracy, with a paired percentile bootstrap sampling the same lexical groups, 10000 replicates, seed 130, nominal 95%. The main estimand is weighted by entity-sample row; multi-entity headlines therefore have more influence than single-entity headlines; this choice is reported and not mislabelled as equal weight per group. The difference between the two fixed predictors is computed using the same sampled group indices.

The interval only describes the approximate sampling uncertainty given the fixed training/selection results; it is not an exact certificate and does not include training randomness, model selection, unknown event dependence or temporal drift. Lexical groups do not guarantee independence/representativeness. A CI that contains 0 only says that no difference was resolved under this design and cannot prove the methods equivalent; one that excludes 0 cannot prove that a new architecture is necessary or a causal gain.

The frozen test is run only for the finally selected systems; C is not tuned, groups are not changed, the seed is not re-chosen, features are not swapped and anomalies are not back-filled based on test. If an implementation error is found, record the invalid result and the fix, and do not present the rerun as the first confirmation.

## Compute budget and execution order

Local Python 3.12.14, NumPy 2.5.3, SciPy 1.18.1, scikit-learn 1.9.1; no GPU/API/external models. Preparation and deduplication expected ≤2 minutes, the 9 sparse LR fits and predictions of the baselines expected ≤5 minutes, the bootstrap expected ≤2 minutes; total run suggested ≤10 minutes, RAM target ≤2GB. These are pre-execution estimates; evidence of actual time/available memory is saved separately; if the budget is exceeded, first record which step, and do not change the frozen target by picking a subset.

Order: package private-boundary check → prepare and an independent small-domain deduplication oracle → check summaries/split identity → freeze the train/dev selection → one test prediction → paired bootstrap → independent code and evidence review → summary report. Pure construction unit tests can be run first; any trial run with real parameters is logged, and no trial run is done on test.

Stop/fix conditions: source hash mismatch; uncertain parsing/conflict rules; any group crossing splits; the vocabulary touching dev/test; private products entering the archive; a class without training support; non-convergence beyond budget; a change in output label semantics. When such a problem occurs, fix the corresponding step first and keep the error record. Reporting is not stopped because accuracy is not good enough; a strong simple baseline winning would itself affect the later judgment on whether a model is necessary.
