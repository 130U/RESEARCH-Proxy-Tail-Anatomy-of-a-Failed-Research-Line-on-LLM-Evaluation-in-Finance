# Reproducing the Results

Every result can be recomputed from the saved model outputs. Recomputation calls no model, needs no
API key and trains nothing. Calling the models again will not reproduce the outputs byte for byte.

Run commands from the repository root. The analysis was run with Python 3.12.14; the numerical
packages and versions are in [`requirements-analysis.txt`](requirements-analysis.txt) (numpy, scipy,
matplotlib). Some stages need more; each stage's own notes say what.

## Where Each Stage's Instructions Are

| Stage | Instructions |
|---|---|
| A. Certifiable FinLM | [research/REPRODUCE.md](research/REPRODUCE.md); runner `python research/reproduce.py` |
| B. Proxy tail | [research/tail_screening/REPRODUCE_CURRENT.md](research/tail_screening/REPRODUCE_CURRENT.md) |
| C. Absolute scoring | [research/absolute_scoring/REPRODUCE.md](research/absolute_scoring/REPRODUCE.md) |
| D. T3 | [research/t3_combination/execution_notes.md](research/t3_combination/execution_notes.md) |
| E. T1–T1g | Each `research/t1*/` folder; T1g: [research/t1g_consequence/RUN.md](research/t1g_consequence/RUN.md) |

## Stage B Quick Start

```sh
python research/tail_screening/review_measurements.py
python research/tail_screening/analyze_agent_methods.py --method all
python research/tail_screening/analyze_agent_methods_validation.py
```

The first command re-checks the raw outputs against the saved results with an independent
implementation and changes nothing. The other two rewrite the corresponding JSON, PNG and PDF figures
and per-item reports; run times vary, but the statistics and decisions should be identical. To check
the paired batches:

```sh
python research/tail_screening/prepare_agent_methods.py --verify-batches
```

The data-preparation script accepts
`--source source_materials/130U-FinLLM/data/raw/candidates/sentfin/SEntFiN.csv` and refuses to
overwrite existing samples or aggregates.

## Stage A Source Audit

```sh
python research/data/fomc_source_audit.py --self-test
```

The self-test checks the audit's parser on the saved FOMC pages. The saved audit result is
`research/data/source_audit.json`.

## Known Limits

- **Paths.** Some T1-series scripts default to sibling working directories that existed on my
  working machine (for example `proxy-tail-t1a/`). Pass the documented `--t1-dir`-style arguments,
  or point them at the matching folder under `research/`. Run records show local paths as
  placeholders such as `<workspace>`.
- **Hashes.** Several records pin other files by SHA-256 (protocols, proof notes, prompts). The
  hashes were computed on the working-language files, which were written in Chinese.
- **Data.** FinQA and TAT-QA are downloaded by `research/t1_rounding/download_inputs.py` and the T1g
  scripts; they are not stored in the repository.
- **Reports.** The Markdown files are the source of the stage reports.
