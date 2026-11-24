# Reproducing T1g

This directory is on the `task/t1g` branch, starting from task commit `ff30d61`. The prediction was committed on its own as `0c68d8a`; do not rewrite it or recalibrate the prediction with the measurement results.

The Python 3.13 environment uses numpy 2.5.5, scipy 1.18.1, sympy 1.14.0, matplotlib 3.11.2, and tqdm 4.70.1. The current interpreter is at `.venv/Scripts/python.exe` in this directory; the environment and the raw downloaded data are not committed.

The read-only dependencies are existing workspaces in the same parent directory: `proxy-tail` (T1 `30acb8d`), `proxy-tail-t1a` (`3b29bfe`), `proxy-tail-t1b` (`3e6e626`), `proxy-tail-t1c` (`c3d2a91`), and `proxy-tail-t1d` (`67569c2`). The code uses their exact interval engine, raw data, and saved results, and did not modify earlier rounds' research files. In this repository those working copies are the stage folders under `research/`; the recomputation of the intersection with existing answers uses T1d's saved results. The computations in the remaining four parts call no paid API or model.

The raw TAT-QA inputs are `tatqa_dataset_train.json`, `tatqa_dataset_dev.json`, and `tatqa_dataset_test_gold.json` from the [pinned official commit](https://github.com/NExTplusplus/TAT-QA/tree/870accc41953dcde885aabeb963d94aabdc0fbc3/dataset_raw), placed at `data/tatqa/train.json`, `dev.json`, and `test.json` in this directory. The raw FinQA data and the official evaluation source are in `research/t1_rounding/data/` of the T1 workspace; its downloader pins the official commit.

Run from the current repository root (let `P` be the Python above and `D` be `research/t1g_consequence`):

```text
P D/tatqa_prepare.py
# A new study must commit its prediction separately at this point; to reproduce this run, check that it matches 0c68d8a.
P D/tatqa_measure.py
P D/tatqa_binding_sensitivity.py
P D/tatqa_validate.py
P D/part1_changes.py --dataset all
P D/part1_questions.py
P D/part1_existing_responses.py
P D/part1_support.py
P D/part1_validate.py
P D/part2_comparisons.py inventory
P D/part2_comparisons.py finqa
P D/part2_comparisons.py tatqa
P D/part2_summarize.py
P D/plot_results.py
```

Part Four runs `part4_duplicates.py` and then `part4_measure.py`; the scan and the semantic labels are described in `part4_report.md`. The widest word-overlap candidate pool is saved as `part4_candidates.jsonl.gz`, about 2 MB, and can be rebuilt by the scan code; the confirmed pairs, actual substitutions, semantic exclusions, and per-item results are saved with the branch. gzip only compresses the per-line candidate data; unreviewed wide candidates are not counted as same-quantity evidence.

The measurement validation covers all 2,839 rows of extrema and corners in Part One, FinQA official scoring, and all 5,661 program centers and 2,339 complete joint witnesses in Part Three; the interior flip witnesses of Part Two are substituted back in by its summary code. Every "manual" check in the reports is explicitly marked as AI semantic reading.
