# Offline reproduction

The round 9 default integration run contains 125 unit tests and 13 subcommands, and all of them finally passed; the 10 source-parsing self-tests are counted separately. The new `python -m research.planning.run_randomization` recomputes the 32 homogeneous threshold constructions according to the [protocol](planning/RANDOMIZATION_PROTOCOL.md). It takes the current round 8 JSON as input and outputs the exact risk, the risk with one document fewer, the minimum sample size and hashes; it involves no training, no private source text and no network. When running it on its own, first make sure the complete round 8 results exist; the unified script already runs things in dependency order. The first table took 0.643217 seconds and the final integration table 0.651663 seconds; peak memory was not measured.

Run from the root of this workspace. Python 3.12.14, NumPy 2.5.3 and PyTorch 2.14.1+cpu are the actual environment used here. The theory checkers mainly use the standard library, evaluation uses NumPy, and synthetic training uses PyTorch; the round 4 real baseline and its construction tests also use SciPy 1.18.1, scikit-learn 1.9.1, joblib 1.6.0 and threadpoolctl 3.7.0. No GPU, API key or download is needed.

Run from the repository root:

```sh
python research/reproduce.py
```

Rerun the four-configuration, three-seed synthetic training:

```sh
python research/reproduce.py --train
```

The script installs nothing, goes online nowhere and downloads no weights. The old-metric reconstruction reads `source_materials/130U-FinLLM/docs/experiment-results.md`; its ready-made JSON is included.

Summary reconstruction of the old public metrics:

```powershell
python -m research.evaluation.reconstruct
```

`python research/reproduce.py` writes `research/reproduction_log.json` with the check commands, their exit codes and their output. The theory JSON files are only examples of mathematical components; the premises of a real model, real parsing and a trusted core are not verified by these commands. The narrative of the synthetic experiment report is pinned to this round's configuration; if the configuration is changed, the conclusions need manual review.

Round 2 added the shared-shard accuracy/macro-F1 checker in `certificates/` and the exact audit-size frontier in `planning/`. The integration command runs the two new test suites, a hand-made vote-pattern example, the planning frontier and an example of the conditional audit chain. The input to `certificates/` is the per-head class predictions; the input to `planning/` is the vote counts per class. Read the respective README for the exact schema; the two are not interchangeable.

The round 3 integration command also includes 8 impact-graph audit tests and 5 threshold-design tests (49 unit tests in total), 10 self-tests of the date-binding parser, and a scan of the 20-cell fixed-threshold family. Rereading the 10 real files for the source audit needs the original repository's local data and is run separately with the `--source-root` command in `data/source_audit.md`; the main integration command runs only its portable self-tests and does not look for or download raw data.

Round 4 added evaluation with native three-class labels, construction tests for the real-baseline preparation/training/joint-prediction interfaces, and a test that private archives are excluded, for 74 integration unit tests in that round; the 10 source-parsing self-tests are counted separately. The default command validates the new trainer only on hand-made rows; it does not read the private real source and does not repeat the 9 real fits. The real run is done separately with the explicit commands below. Before running, read `real_baseline/PROTOCOL.md`; results and limitations are in `experiments/real_baseline/report.md`.

```powershell
python -m research.real_baseline.prepare --source 'source_materials/130U-FinLLM/data/raw/candidates/sentfin/SEntFiN.csv'
python -m research.real_baseline.train_baselines --input research/private/real_baseline/rows.jsonl --private-output research/private/real_baseline/trained --summary research/experiments/real_baseline/baseline_summary.json --manifest research/real_baseline/aggregate_manifest.json
python -m research.real_baseline.bootstrap_results --predictions research/private/real_baseline/trained/predictions_test.jsonl
```

The preparation and training commands write local artifacts with the same names; to keep an old run, copy the whole working directory before running. The original CSV, row-level derived data, vocabularies and models are not in the repository. Without a local raw CSV with a matching hash, one can only run the public construction tests and check the existing summaries, and cannot claim to have independently rerun the real scores. The trainer verifies the input fingerprint. The fallback fix for the Chinese-character DLL path on this Windows machine takes effect only inside the process and does not change installed libraries. The thread evidence is the configuration reported by the libraries themselves; peak memory was not measured.

`theory/notes.tex` has not been compiled; the readable proofs are in `theory/notes.md`, and no compiled PDF is claimed.

Round 5 added 18 PIT construction tests, for a current total of 92 integration unit tests and 10 source-parsing self-tests; the unified script has 10 subcommands, all of which passed. The last one, `python -m research.pit.run_checks`, makes 210 full-chain and 2100 byte comparisons on 30 historical base cases, and also includes 3 classes of deliberately faulty programs, 3 mislabeled-time boundaries, 16 boolean seed mappings and a re-summary of the old public source metadata. This runner depends only on the standard library, reads no private corpus and trains no model. Results are written to `pit/results.json`, with the run environment and timing kept separate from the historically stable artifacts; see `pit/record.md`. The public source_audit.json is included, so this round's metadata table can be recomputed without the raw FOMC files.

Round 6 added 14 semantic-envelope unit tests, for 106 integration unit tests in that round plus 10 source-parsing self-tests; all 11 subcommands of the unified script passed. `python -m research.numeric.run_checks` recomputes the strict rational envelopes, the 25-cell hand-made width gate and each counterexample, and writes the results to `numeric/results.json`. It does not call a natural-text parser, does not train a model, and does not treat model probabilities as real probabilities; see `numeric/record.md`. Even when the source code, configuration and external dependencies are unchanged, the timing fields produced by a rerun can still change; the snapshot hashes in historical review reports are bound only to the version at that time.

Round 8 added 10 tests of the strongest total-count gate and a 12th subcommand, `python -m research.planning.run_localization`. Following the [frozen execution scope](planning/LOCALIZATION_PROTOCOL.md), this command recomputes the 20 original threshold comparisons, 8 conjunctive, 16 star and 4 sharp constructions that have analytic bounds only, with a maximum wall clock of 60 seconds; there is no main-line training, no real audit and no network access. The complete record is written to `planning/localization_results.json`, including source/input hashes, the status of each cell and the strong simple control `min(Box,TotalK)`. The 4 bounds-only rows must not be treated as globally optimal numeric solutions. A unified rerun first refreshes the time fields of the original threshold JSON, and the new record is bound to its current hash; the historical reports still describe only the runs at that time.

This round did not run the original repository's full training or all of its original tests, because the original application code was not modified. Only the checks related to the new research code were run.

In round 8, the atomic result replacement in the 12th command hit a Windows sharing error; the failure snapshot is saved in `planning/localization_io_failure.json`. After the fix, 3 I/O regression tests were added, and the final unified rerun passed all 119 unit tests and 12 commands; the 10 source self-tests are counted separately. Private raw text and model training were not read or rerun in these checks.
