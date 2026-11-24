# Real-source task baseline built from scratch

2026-11-16, round four. **This round has actual training and paired evaluation: on the fixed SEntFiN entity-sentiment test split, word TF-IDF/LR has macro-F1 0.7920 and char TF-IDF/LR has 0.7548. The pre-specified char−word difference is −0.03723, with a nominal 95% lexical-cluster bootstrap interval of [−0.05306, −0.02156].** This is a simple-method reference for later research, not a certificate of novelty, of a historical information set, or of financial deployment.

All data, libraries and computation come from this machine; there were no downloads, external requests, messages or publications. The models are linear classifiers newly fitted in this round; no old checkpoint was used, and this is not pretraining a language model from scratch. The raw text, per-row labels, splits, predictions, vocabularies and weights all stay in `research/private/`, which is excluded by gitignore and by the archiver. The public evidence is the [pre-run protocol](../../real_baseline/PROTOCOL.md), the [preparation manifest](../../real_baseline/aggregate_manifest.json), the [training summary](baseline_summary.json) and the [paired summary](bootstrap_summary.json).

## What this round answered

The target is the **source sentiment toward the specified entity** in a headline, with three classes negative / neutral / positive. These are not equivalent to bearish/neutral/bullish on a security. When one headline involves several entities, different entities can have different sentiment labels; the input therefore keeps the target, and the target is marked in the headline with a literal whole-word rule written in advance.

Both formal models fit the vocabulary, IDF and LR coefficients on the training set only. Each selects C from {0.1,1,10} by three-class macro-F1 on the development set, with exact ties going to the smaller C; after selection there is no retraining on train+dev. The primary comparison was fixed before the real run as char−word test macro-F1, and the test set is exactly the same for all four systems. The majority class and entity-only are pre-specified diagnostics. Test scores were not used to choose C, re-split the data, or change the entity input rule.

An independent design suggestion proposed "development-set winner − majority class" as the primary comparison; the root agent did not adopt it and kept char−word from the pre-run protocol. Either design answers a well-defined question, but one cannot switch after seeing the test results. "How much performance entity identity explains" in the protocol is to be read only as a shortcut diagnostic: F1 cannot be decomposed, and this round does not estimate the causal contribution or explained share of entity identity.

## Data preparation and sampling scope

The source is the locally available SEntFiN.csv, SHA256 `570af7ba58f724f3fcc414dd5ba80da5b1a3b342134d76c6ebdf53a32c54a92f`. A strict AST check rejects duplicate keys before literal_eval; anomalies are not repaired by guessing. The unit of conflict is same normalized headline + same entity, not different entities in the same headline.

| Stage | Count and unit |
|---|---:|
| Raw source rows | 10,753 |
| Whole-row syntax anomalies quarantined / source rows parsed successfully | 13 / 10,740 |
| Entity occurrences expanded from successfully parsed rows | 14,371 |
| Conflict keys / entity occurrences involved | 7 / 14 |
| Extra entity occurrences merged as non-conflicting duplicates | 73 |
| Final entity samples / lexical clusters | 14,284 / 10,591 |

The closing relations are 10,753=13+10,740 and 14,371=14+73+14,284. The number of intended labels in the anomalous source rows is unknown, so 14,371 is not the known total number of labels in the whole original file. The supplementary accounting only reads the source and did not change the frozen data or manifest; see the [count reconciliation](../../real_baseline/PREPARATION_ACCOUNTING.md).

Headlines with the same normalized form or with token-set Jaccard≥4/5 are joined by an edge; transitive connected components are taken and then partitioned by a hash with fixed seed=130. Duplicate detection uses all headlines; anomaly/conflict handling uses the source labels. This is a publicly described dataset construction process, and the test data cannot be called completely unseen. The source material may also have been seen in an earlier project, and a new hash split does not erase that history.

| Partition | Entity rows | Lexical clusters | negative | neutral | positive |
|---|---:|---:|---:|---:|---:|
| train | 10,041 | 7,438 | 2,658 | 3,831 | 3,552 |
| development | 2,136 | 1,583 | 572 | 838 | 726 |
| test | 2,107 | 1,570 | 558 | 787 | 762 |

The largest kept cluster has 7 entity samples and at most 3 normalized headlines. The number of within-definition families, identical normalized headlines and near-duplicate edges that cross partitions is 0 in each case. The clusters here are only lexical components; unaudited same-event rewrites, shared entity identity and cross-cluster dependence may still exist. There is no evidence for a time split or for generalization to unseen entities.

In the preparation stage, 19 rows had no literal substring match; the model uses whole-word boundaries, under which 112 samples could not be marked (train 81/dev 10/test 21). The two numbers use different rules and are not interchangeable. When a target cannot be marked, the original headline and the target prefix are kept as the protocol specifies; no NER was called to add aliases, and no samples were deleted based on test errors.

## Fixed test results

All intervals in the table below are nominal 95% percentile lexical-cluster bootstraps with 10,000 replicates and seed=130; the per-system / per-class marginal intervals are descriptive only, with no multiple-comparison correction. When a cluster is drawn, all of its entity rows enter together; point estimates are weighted by entity row, not equal-weighted by cluster.

| System | C selected on development set | Test macro-F1 | Descriptive interval | Test accuracy |
|---|---:|---:|---|---:|
| Training majority class | — | 0.18129 | [0.17325, 0.18952] | 0.37352 |
| word TF-IDF/LR | 10 | 0.79202 | [0.77249, 0.81089] | 0.79402 |
| char TF-IDF/LR | 1 | 0.75478 | [0.73497, 0.77371] | 0.75368 |
| entity-only TF-IDF/LR | 0.1 | 0.53359 | [0.51063, 0.55593] | 0.53726 |

**The only pre-specified primary comparison: char−word macro-F1 = −0.0372334, interval [−0.0530595, −0.0215595].** The paired difference of the two models is computed on the same set of resampling indices, not by subtracting two marginal intervals. The current design resolves the higher score of the word baseline; it does not prove that the word model is generally better on other tasks or over the population distribution.

The 0.5336 of entity-only shows that the entity field alone can support informative predictions on this split, so identity/label-prior shortcuts are worth controlling in later research. This must not be written as "explains about 67% of the word model's performance", and the remaining difference cannot be attributed directly to compositional reasoning. The training majority class has macro-F1 below its accuracy because of the fixed three-class average; this is not a computation error.

The current intervals are conditional on the fixed training results, the development selection and the test predictions. That lexical clusters are independent and representative has not been proven; the intervals also do not include training randomness, research search, unknown event dependence or distribution drift. 10,000 replicates only reduce the numerical resampling error; they do not turn these gaps into a finite-sample guarantee. None of these numbers may be compared with the old project's 0.6549/0.6087 as a same-test-set difference.

## Execution and traceability

| Step | Actual wall time | Run status |
|---|---:|---|
| Raw preparation and exact lexical deduplication | 0.766725 s | Frozen data and manifest written to disk |
| 9 LR fits, model selection and predictions for four systems | 13.809371 s | No convergence warning in any of the 9 |
| Paired and descriptive bootstrap on fixed predictions | 2.306168 s | 10,000 replicates; all test rows aligned |

The pre-execution budgets were 2/5/2 minutes respectively; all the actual values above are within budget. Training CPU time 13.15625 seconds; GPU not used. Peak memory was not measured, so the ≤2GB target cannot be declared met on this basis.

Python 3.12.14, NumPy 2.5.3, SciPy 1.18.1, scikit-learn 1.9.1, joblib 1.6.0, threadpoolctl 3.7.0. On Windows the initial construction tests failed because threadpoolctl corrupted a DLL path containing Chinese characters; no real fit had happened before that. The fix only uses the existing Unicode module to enumerate fallback paths inside the process context and sets the startup thread environment; no global library was modified and no model was changed. The three numeric libraries found before and after training all self-reported 2 threads; the evidence is in the summary. This is a library-configuration check, not an operating-system measurement of peak threads.

The frozen rows SHA256 is `8ab314ebd74680466f3a24055433f3a44d442107773607204cd3983122d87567`; the joint test-prediction SHA256 is `d18a8a43c8ee10c5ce248ae7d0e96207ce759cbdf238dc36436f911e7f10adab`. The training summary binds the source code, configuration, preparation manifest, inputs and the digests of all private artifacts; the bootstrap re-checks the rows manifest and the integrity of test IDs/labels/groups, and records the prediction digest. The public package does not include these per-row private artifacts; a third party rerunning the real training needs its own lawful local source; the hand-constructed tests in the package can run independently.

## Review and next decisions

A separate review pass checked the development-set selection, 21 summary confusion matrices and the exact scores, and verified the paired evaluation with all 27 resamplings of three unequal-sized clusters. The review found that the trainer's long model names did not match the evaluator's short names; this was fixed with an explicit mapping, and a constructed integration test of the real training schema was added. The fix happened before the first real bootstrap run of this round and did not change models/scores or reselect parameters. The current 74 integration unit tests pass; source parsing has another 10 self-tests, and the other finite mathematical checks are in the unified reproduction log.

This round closes part of the gap "there is no real task baseline for this round". Row-level records for the old 24M model are still missing, the FinBERT/small-LLM baselines were not run, the original G0 is not passed, and G1 flagship training was not started on this basis. The research value of the next step should be defined around **falsifiable mathematical propositions and a complete certificate chain**; piling on more ordinary sentiment classifiers, even ones that exceed 0.7920, will not automatically solve the toy problem identified in the initial plan.

The judgment at this point: the simple reference now runs; what needs scrutiny is how a new task replaces the old G0, why learning or training from scratch is necessary, and which structural conclusion existing methods do not provide.
