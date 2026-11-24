# Root resolution of scoring-code audit

The independent audit is retained unmodified in `CODE_AUDIT.md`; its numerical snapshot contains 334 responses, not the final sample.

- Added the protocol's first-order T1A radius/precision budget alongside the exact-radius budget. A sign-invariance test also verifies the independently derived first-order radius (135/532 versus exact 135/530 for the 133-to-137 example).
- Strengthened `validate_run.py` to reject results with missing second source reviews or unadjudicated disagreements. Strict `analyze.py` already enforces both.
- Development results are marked incomplete, including 392-row runs with unfinished semantic reviews. Final statistics and plot were generated after all 392 answers and 68 second source reviews completed and all 7 disagreements were adjudicated.
- Q377's million-dollar response is converted to the reference subtraction's source-grounded billion-dollar unit. `unit_overrides.json` retains the question/reference encoding mismatch; the raw answer and expression are unchanged. The final independent audit confirms this conversion and all full-sample numerical results.
- The updated 12-test suite passes. Final evidence-manifest validation checks prompt reconstruction, calls, reference executions and completion guards.

These changes do not alter any prompt, response, sampling decision or numeric scoring rule.
