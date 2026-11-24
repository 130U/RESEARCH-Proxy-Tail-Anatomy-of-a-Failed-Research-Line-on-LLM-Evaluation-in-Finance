# T1C — input precision and model scoring

The experiment uses 392 fresh one-question agent sessions: all 196 T1 witnesses and 196 stable controls matched by operation. No paid model API, training, or correctness-dependent retry is used. See [PROTOCOL.md](PROTOCOL.md) for the frozen sample, prompt, metrics, and interpretation rules.

## Artifacts

- `ONE_PAGE.md`: final decision and its limits (written after all responses and reviews).
- `t1c_results.png` / `.pdf`: the requested figure, generated from complete results only.
- `raw/Q001.txt` … `Q392.txt`: original returned final responses; `calls.jsonl`: fresh-session records.
- `inputs/Q001.txt` … `Q392.txt`: exact gold-free prompts; `inputs/LICENSE`: upstream FinQA permission.
- `private/sample.json`: frozen labels and matched pairs, inaccessible by instruction to solving agents. The directory name describes the blind experiment role, not sensitive personal information.
- `scores.jsonl` / `.csv`: both numerical and expression scores, normalization reasons, and exact attainability certificates. `results.json`: counts and document-cluster confidence intervals.
- `review_*.json`: independent source/meaning judgments; `adjudication.json`, if present, retains final resolutions without deleting original judgments.
- `SOURCES_AND_METHOD_REVIEW.md`: official scoring semantics, attribution cautions, and targeted literature check.
- `integrity.json`: SHA-256 evidence manifest and checks of all 392 prompts, sessions, and reference executions.

The artifact directory disables Git newline conversion so original response bytes and evidence hashes survive checkout unchanged. Temporary source-review packets and the duplicated document cache are regenerable and ignored; all source prompts and final independent judgments are included.

## Reproduce calculations

Python 3.12+, NumPy, SymPy, tqdm, matplotlib. Computation does not call a model. It reuses saved original responses and the fixed T1 code/data.

In a checkout with the T1 branch available:

```powershell
git fetch origin task/t1
git worktree add ../proxy-tail-t1-inputs 30acb8d
python ../proxy-tail-t1-inputs/research/t1_rounding/download_inputs.py
python research/t1c_models/prepare.py --t1-dir ../proxy-tail-t1-inputs/research/t1_rounding
python research/t1c_models/prepare_alternatives.py --t1-dir ../proxy-tail-t1-inputs/research/t1_rounding
python research/t1c_models/score.py --t1-dir ../proxy-tail-t1-inputs/research/t1_rounding
python research/t1c_models/analyze.py
python research/t1c_models/plot_results.py
python research/t1c_models/validate_run.py --t1-dir ../proxy-tail-t1-inputs/research/t1_rounding
```

`prepare.py` reproduces the same sample and prompts; it does not replace responses. A new inference replication must use a separate raw directory and a fresh session per question. The serving model version was not exposed by the interface; recorded conditions are the default runtime, no model/effort override, one run. This is a limitation on exact model replication and on cross-model claims.

Official expression scores call the unmodified FinQA evaluator after compiling the response's arithmetic into its DSL. No gold numbers repair a response. Printed-answer scores apply the same numeric equality rule to the emitted number and are explicitly an interface adaptation. Display scoring uses exact rational half-even ties and the written human answer's places, retaining human/execution label disagreements. Percentage encoding and explicit monetary-unit conversions are retained per row.

Two human labels omit `%` even though the question explicitly requests a percentage (`Q021`, `Q046`); their human-label values are interpreted in percent for display scoring. `Q003` averages tax rates already expressed in percentage points. These reference-side unit rules are explicit in `score.py`; no alternative scale is selected by whether a model answer passes. Q018/Q318 use a reference-program conversion from millions to dollars, so a response explicitly in millions receives that conversion. Currency symbols and spelled-out magnitude units are removed only when the whole human label is a simple numeric answer.

`unit_overrides.json` documents Q377: both source operands and the reference subtraction are in billions, while the question and model response request/use millions. The declared currency magnitude is converted to the reference execution unit (factor 1/1000 for millions), independently confirmed by the final code audit. The model's multiplication by 1000 is retained and the unit conversion is appended. Thus these are **unit-normalized expression scores**, not unnormalized raw-DSL scores. This is distinct from a reference ratio that incorrectly combines billion and million inputs, which is not repaired by changing a dimensionless output's scale.

The model sees original source context, so a source-identity review is needed before treating an interval hit as a correct answer. Attainability certificates prove only compatibility with the independent T1 rounding box. They do not impose T1B's additional accounting or duplicate-disclosure constraints. Error-rate differences remain observational after matching by broad operation type.

The alternative-value catalog contains previously verified T1 disclosure substitutions; it is a screening aid, not an exhaustive detector. Every officially rejected expression is also reviewed against its source context. Mixed cases retain a separate `alternative_precision_used` flag even when source precision is not the sole cause of rejection. Nonnumeric abstentions remain failures in every available numeric metric; human-display denominators depend on the reference label, never on whether the model supplied a number.

T1A's exact growth relative radius is used where the saved program is a supported two-input growth form. Its precision budget `p = -log10(relative_radius)` is an error-order measure, not a guarantee of unchanged leading decimal characters. Other programs use the T1 outer interval as a conservative bound. Emitted significant digits count trailing zeros literally; integer trailing zeros can have ambiguous intended precision.

Both signs of a growth expression have the same relative-error budget. The protocol's first-order comparison is reported separately as `t1a_first_order_budget`: `R_first = R_exact * (1 - h_base / abs(base))`, then `p_first = -log10(R_first)`. The existing `t1a_precision_budget` field retains the exact-radius result. Headline overreporting comparisons use the same-source, symbolically equivalent growth subset, so an unrelated model formula is not compared to the reference formula's budget.

The original 196 witnesses are retained exactly as requested. One inherited T1 semantic-binding caveat is `Q003`: the literal count `3` in a three-year average is associated with the same source location as a displayed `3.0` rate, and T1 gives them separate uncertain variables. Its numerical witness is valid for that saved box, but the averaging count should be exact. This is not changed retrospectively in the matched sample and must not be described as a proved full-document ambiguity.
