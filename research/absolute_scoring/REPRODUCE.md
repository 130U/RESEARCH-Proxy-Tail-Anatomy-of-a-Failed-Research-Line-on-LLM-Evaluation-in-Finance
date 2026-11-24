# Recomputing the absolute-scoring experiment

This is the replication and stress test I chose to run after the literature gate. The question, scope and pre-registered decision rules are in [protocol.md](protocol.md). [progress.md](progress.md) records the collection status; do not read the frozen planned counts as completed counts. The analyzer requires all pre-specified raw files to be present before it computes the formal results.

From the repository root, using Python 3.12 and the numerical dependencies recorded in the root [requirements-analysis.txt](../../requirements-analysis.txt), run:

```powershell
python research/absolute_scoring/test_analysis.py
python research/absolute_scoring/analyze_scores.py
```

The Python actually used on this machine is `../130U-FinLLM/.venv/Scripts/python.exe`. If the plotting dependencies are in the adjacent local directory `../tmp/tail_plot_deps`, the program uses that directory; other machines can install the listed versions in their own environment and do not depend on this local directory. The final analysis runs 5,000 headline-paired bootstrap draws by default, with separate fixed seeds for the main analysis and the controls. Outputs go to `results/`: the full JSON, CSVs of directional statistics and boundary data, and the six-panel figure `stability.png` / `stability.pdf`. `--no-figure` recomputes only the statistics. Do not use debugging output with fewer bootstrap draws as the final result of the frozen protocol.

`raw_scores/{call_id}.json` stores the raw ID/integer scores actually returned by each call. The main calls `r01_b01` to `r08_b25` each contain 40 scores; the controls `c1_b01` to `c2_b25` are the two new calls on the complete first-round batches. The analyzer checks each round's ID coverage, duplicate JSON keys, score range and control completeness. `calls.jsonl` records the configuration, agent task identifiers and times; `schedule.csv` freezes the order, `batches.csv` freezes the IDs and positions within each batch, `sample.csv` stores the mapping between source IDs and lexical families, and `control_ids.csv` fixes the 100 control targets.

When everything is complete, the main data should have 8,000 scores and the companion control data 2,000 scores. Of these, only the 200 control scores of the 100 pre-specified targets enter the main control comparison; the other 1,800 companion scores are kept but do not enlarge the main sample. Repeated calls do not increase the number of independent headlines.

Rebuilding the inputs uses `prepare_inputs.py`, [prompt.txt](prompt.txt) and the saved source test split. The program uses only IDs, lexical families, source IDs and text for the fixed-seed selection; it does not filter by existing labels or predictions. The output text is written only to the adjacent directory `proxy-tail-absolute-inputs/` outside the repository. The program refuses to overwrite an existing sample or input directory; a new full replication should be run in a fresh copy. The original input texts were not committed in this round; the synthetic anchors are saved in the prompt.

Scoring again requires opening a fresh-context session for each call, following [agent_task_template.txt](agent_task_template.txt), with fixed `gpt-6-sol`, `reasoning_effort=low`, `fork_turns=none`. The scripts do not generate any model scores themselves and do not call a paid API. The service does not expose temperature, random seed or the exact underlying model snapshot, so the saved results can be fully recomputed, but we cannot promise that a new round of generation will give identical scores.

The call-recording and format-checking helper actually used in this run is saved unchanged in [execution/record_call.py](execution/record_call.py). At run time it sat at the root of the adjacent `proxy-tail-absolute-inputs/` directory, and its relative paths are designed for that location; the copy in the repository preserves the code that was actually run and should not be run directly from here. The file only records calls, keeps the raw bytes and checks outputs; it does not generate scores or open scoring sessions.

`interim_round1.json` is the score-resolution stage result saved after the first round finished; it is not the eight-round retest conclusion. Its boundary statistics can be recovered from the first-round `boundary_diagnostics` of the main analysis. The 13 synthetic tests check ties, directions, pass-through at complete score groups, paired resampling, input completeness and the Gaussian boundaries; the interpolation error is only a numerical check result and is not a rigorous error certificate.

`interim_m1.json` and `interim_m2.json` are the point estimates for the pre-specified comparisons saved when rounds five and six finished, respectively; they contain no formal intervals or formula verdicts. The raw point estimates for the corresponding m in the final analysis's `estimands` should match them. The stage results were not fed back to the scoring sessions and were not used to change the prompt or the decision rules.
