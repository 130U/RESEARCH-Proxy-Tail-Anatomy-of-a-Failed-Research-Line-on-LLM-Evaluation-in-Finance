# Exact audit-size frontier: pre-run budget

Date: 2026-11-15. Scope: theoretical numeric checks, not Phase 1 model training.

- Device: local CPU; Python standard library, no network.
- Budget: small-population exhaustion and the discrete frontier expected to take no more than 30 seconds; memory below 128MiB, 0 GPU memory, 0 training tokens.
- Inputs: hand-set N, vote counts and rational alpha; no real SEC corpus counts are filled in.
- Checks: the minimum n is equivalent to the zero-finding gate of the existing audit_upper; small-N exhaustion, monotonicity, full audit, ties and invalid inputs.
- Pre-registered interpretation: the model, population, vote margins and audit design are frozen first; the frontier is conditional on the future sample finding zero errors and does not guarantee that zero errors will be observed. If x>0, the upper bound for the fixed n should be recomputed with the actual x. Resampling until zero findings is not allowed.
