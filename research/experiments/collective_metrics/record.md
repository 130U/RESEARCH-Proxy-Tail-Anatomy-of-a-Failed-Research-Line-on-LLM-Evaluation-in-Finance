# Round 2: collective certificate for fixed test statistics

Date: 2026-11-15. This is P1 theory-envelope and checker work, not Phase 1 model training.

## Pre-run budget

- CPU, 0 GPU memory, 0 training tokens; no network; Python standard library.
- Unit tests and small-example enumeration expected to take under 30 seconds; at most 100,000 states and at most 100,000 shard subsets; when the budget is exceeded the program explicitly refuses to issue a certificate and never returns an optimistic interval for the unsearched part.
- Only hand-made vote matrices, known ground-truth labels and a fixed number of affected shards. Actual training sources, timestamps and true contamination counts are not verified in this computation.

## Claims to verify

1. The constraint from the set of jointly affected shards can narrow the interval compared with a per-point independent contamination budget.
2. macro-F1 cannot reuse the per-point averaging envelope; it needs a joint optimization, or a conservative envelope, over fixed support counts, TP and prediction counts.
3. Integer counts and rational endpoints avoid inward floating-point rounding.

## Program and evidence

Implementation: `research/certificates/collective.py`; independent derivation: `research/theory/collective_metrics.md`.
The inputs and actual results are saved as `constructed_inputs.json`, `results.json` and `report.md`; the audit-chain example is `audit_example.json` and `audit_certificate.json`. Input hashes, checker hashes, the actual hardware and the computation time are in the JSON; all inputs are explicitly marked as hand-constructed mathematical examples.

## Actual execution

- The 7 tests of this module passed; in addition, an independent agent reviewed it with 112 input/budget combinations against an oracle that directly changes vote cells. Details in `research/literature/collective_review.md`.
- Final integration run: 36 tests passed in total, covering the old foundations, XBRL, audit planning and this module; the log for this round is in `research/reproduction_log.json`.
- 4 pre-constructed inputs × 2 methods were executed; computation took about 0.6 seconds, and the exact values agree with the theoretical examples. Peak memory was not measured; no model was trained.
- During the run there was an output error because the Windows console could not encode Chinese: the numeric JSON/Markdown had already been written; the terminal summary was then changed to ASCII JSON and the rerun succeeded. The failing exit code was not treated as success.

## Conclusion

Joint head identity can strictly tighten the fixed test-statistic envelope; the per-class extremes of macro-F1 are in general not attainable at the same time, so the exact DP and the component outer envelope must be distinguished. Both metrics hold simultaneously under the same audit-coverage event. The real-model / real-audit premises are unverified; the G0/G1 status is unchanged.
