# Source Materials

Material from my earlier work that the Stage A recomputations and the Stage B and C samples read.

**`130U-FinLLM/`** holds the parts of my earlier financial language-model project,
[130U/RESEARCH-Financial-Large-Language-Model](https://github.com/130U/RESEARCH-Financial-Large-Language-Model),
that the analysis here reads: the SEntFiN data in `data/raw/candidates/sentfin/` and the summary of
experiment results in `docs/experiment-results.md`, read by
[`research/evaluation/reconstruct.py`](../research/evaluation/reconstruct.py). The project itself, with
its code, models and full documentation, is public at the link above. `docs/experiment-results.md`
is kept byte for byte, so its two links to other files of that project point outside this folder.

**`source_audit/`** holds the FOMC material read by the Stage A source audit: the 120 FOMC minutes as
JSONL, the 120 matching HTML pages, 12 index snapshots and a manifest. The audit result is
[`research/data/source_audit.json`](../research/data/source_audit.json).

**SEntFiN.** The raw CSV, entity list, README, candidate manifest and the original authors' MIT
licence are in `130U-FinLLM/data/raw/candidates/sentfin/`
([licence](130U-FinLLM/data/raw/candidates/sentfin/LICENSE)). Derived entity rows, lexical families,
fixed splits and per-row predictions are in [`research/private/real_baseline/`](../research/private/real_baseline/).

**FOMC records** state the Federal Reserve Board as the source, the retrieval time and the rights
notes. Pages saved in 2026 do not prove that the same bytes were available in earlier years; the
limits on point-in-time claims still apply.

Source code and source data keep their existing licences. No new common licence is declared for
third-party content. Recomputation commands are in the [root instructions](../REPRODUCE.md).
