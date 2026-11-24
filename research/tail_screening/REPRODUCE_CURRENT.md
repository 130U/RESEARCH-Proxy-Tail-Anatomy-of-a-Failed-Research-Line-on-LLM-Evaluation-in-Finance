# Recomputing the current tail-screening study

Recomputation reads the saved model judgments and does not call agents again. No API keys, costs, training or network access are needed. All paths are relative to the root of the unpacked project, with the research directory structure kept; absolute paths in the original metadata only record the source at the time, and the statistical analysis uses relative locations under the current directory.

The environment actually used for this recomputation was Python 3.12.14, numpy 2.5.3, scipy 1.18.1, matplotlib 3.11.2; these are not a model-version guarantee. In the existing environment matplotlib sits in `../tmp/tail_plot_deps`, so local runs add `--plot-deps ../tmp/tail_plot_deps`; an environment with the dependencies installed normally can omit this argument. Compatibility with other versions was not checked one by one.

```powershell
python research/tail_screening/analyze_agent_methods.py --method all
python research/tail_screening/analyze_agent_methods_validation.py
python research/tail_screening/review_measurements.py
```

The first two rebuild the stage 1 and stage 2 JSON, the PNG/PDF figures and the item-by-item reports, overwriting the derived files of the same names without changing the raw scores. The third is the independent internal review, which separately implements the key integer aggregation, boundary counts and pass conditions and does not call the production analysis functions. Run times vary; the numbers and gates should agree. The raw JSON loader rejects duplicate keys, missing/duplicate IDs and invalid values; all true ties are kept, and no random perturbation is added.

Data locations: `research/private/agent_tail_methods/stage1_n32/` contains the 32 inputs, 32 pair results and 16 rank results; `stage2_n128_sol/` contains the 128 inputs and 8 rank results. Both store the exact prompt, the random orders and the family mapping. The raw whole-batch pairwise input of 496 pairs is kept, but the analysis uses only the formal 4×124 batched results; the two attempts with no output are recorded in methods_protocol.md, and no JSON is fabricated for them.

The sampling preparation scripts are only for research provenance. They refuse to overwrite existing data directories, and resampling is not needed for recomputation. You can verify only the stage 1 batching:

```powershell
python research/tail_screening/prepare_agent_methods.py --verify-batches
```

In the current analysis, every report states the main denominator q90/p = pass-through count/(N×p), and lists the actual B/A separately. The nominal count is floor(Np), all ties at the boundary are included, and the 90% target count is ceil(0.9×actual size of A). The main p is .25 in stage 1 and .1/.2 in stage 2. The 8 repeated rankings are not 8 new sets of texts, and the two directions and the combination ranges are not CIs.

The earlier development and the lexical curves can also be recomputed:

```powershell
python research/tail_screening/analyze_agent_pilot.py --variant v1
python research/tail_screening/analyze_agent_pilot.py --variant v2
python research/tail_screening/analyze_baselines.py
```

The lexical recomputation uses the saved word/char per-item predictions and runs a fixed 200-draw paired lexical-cluster bootstrap; the models are not retrained. The results are conditional on the fixed models, split and lexical-cluster assumption, and the finite-window slope is not the structural α. The source texts and historical predictions in private/real_baseline are kept with the current local deliverable; for license and source notes see research/data and the historical research notes. Keeping them locally is not treated as a new unlimited redistribution license.

The recomputation entry point for the historical nine rounds is research/REPRODUCE.md. This round added no hash manifest or packaging script. For the current work, read [SUMMARY.md](SUMMARY.md) first, then check against the individual source files.

What can be recomputed is the statistical result of the saved judgments. The server version, internal sampling and context process of fresh agents cannot be fully fixed, so rescoring is not guaranteed to give the same rankings. The open problems in the mathematics and literature reports are also not solved automatically by the code running successfully.
