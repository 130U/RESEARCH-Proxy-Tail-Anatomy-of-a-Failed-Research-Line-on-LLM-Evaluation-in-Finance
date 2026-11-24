# Independent T1C scoring and statistics audit

Audit date: 2026-11-17. Reviewer: independent `scoring_audit` agent, separate from the response-generating agents and the analysis implementation author.

## Scope and conclusion

This is an audit of the **frozen partial 334-row scoring snapshot**, not a sign-off on the final 392-response experiment. The audited snapshot contains 160 witnesses and 174 controls. Additional raw responses were being generated separately; they were not scored or incorporated in this audit. No model was invoked, no raw response or sample was changed, and no implementation or result file was modified by this reviewer.

No material numerical-scoring, attainable-output certificate, exact growth-radius, or joint page-bootstrap error was found in the 334 scored rows. The official-expression and printed-number tracks are correctly separate. Two implementation/reporting issues remain for finalization: the promised first-order precision budget is absent alongside the correct exact budget, and the standalone integrity validator does not itself enforce second-review/adjudication completion. The coordinator has acknowledged both and plans changes after this audit; those future changes are outside this snapshot's validation.

The existing `results.json` is an explicitly developmental **323-row** report. It must not be combined with the 334-row scores or presented as final evidence. Final reporting requires all 392 rows, regenerated scoring/statistics/figures, complete source reviews and adjudication, and a fresh integrity manifest.

## Findings that require finalization

1. **First-order budget promised by the protocol is not yet reported.** `score.py:172–208` correctly calculates the exact relative growth radius and labels it `T1A exact growth relative radius`; it does not also retain the protocol's first-order approximation. For a supported growth formula with baseline `a` and half-width `ha`, `R_first = R_exact * (1 - ha/abs(a))`, so `p_first = -log10(R_first)` is at least `p_exact`. Across the 150 eligible scored rows (76 witness, 74 control), independent exact corner evaluation agrees with every stored exact radius. The largest first-order versus exact budget difference is **0.05799194698 digits**, at Q332: exact `p = 0.47712125472`, first-order `p = 0.53511320170`. This omission does not alter any answer score, certificate, or error-rate threshold. Add the first-order quantity alongside the exact one rather than relabeling or replacing the exact result.

2. **Standalone final integrity validation has a review-completion gap.** `analyze.py:139–140` correctly refuses a normal final analysis if second reviews or adjudications are missing. However, `analyze.py:75` sets `complete` solely from `n == 392`, even when `--allow-incomplete` bypasses the review guard. `validate_run.py:65` checks only `complete`, `n`, and missing first reviews. Thus a 392-row report generated using `--allow-incomplete`, with all first reviews but missing second reviews or adjudications, could pass that particular integrity gate. This is a latent validation weakness, not evidence that a deficient final run has occurred. Require empty `missing_second_source_review` and `unadjudicated_disagreements` in final validation; the final analysis must run without the development flag.

3. **The current review and result artifacts are unfinished.** At the audited review snapshot, 58 expressions were officially rejected. There were 57 first reviews, 27 second source reviews, and 3 adjudications. Q329 lacked a first review; 31 rejected expressions lacked second review. All three currently detected disagreements (Q125, Q182, Q297) had retained original/independent judgments and explicit adjudications. These counts are audit-time development status and may change as ongoing review finishes. The reviewed records contain zero strict `alternative_source_precision` cases, but that cannot be reported as a complete-run conclusion yet.

## Checks performed and evidence

All checks used the existing `130U-FinLLM/.venv/Scripts/python.exe`; bytecode writing was disabled. The 11 existing `test_score.py` tests passed. Additional in-memory checks independently verified the stored evidence and statistics without running `score.py` or `analyze.py` entry points.

| Check | Result |
|---|---|
| Frozen sample reconstructed from the T1 data and seed | All 392 IDs, group labels, pair IDs, and order match |
| Matched sample structure | 196 unique pairs; one witness and one control per pair; same operation category |
| Category counts in each complete group | Growth 90, ratio 52, difference 35, sum 14, other 5 |
| Original prompt reconstruction | All 392 prompt files exactly match original document/question plus fixed template |
| Official gold-program execution | All 392 reproduce stored `exe_ans` using the local pinned FinQA evaluator |
| Saved response preservation | All 334 scored response objects match their original raw JSON |
| Numeric literal preservation | All 1,085 expression literals survive DSL serialization exactly as rational numbers |
| Model-expression re-execution | All 333 numeric responses reproduce stored exact values, DSL tokens, and official execution values |
| Score reproduction | All 666 numeric track/rule vectors agree; exact half-even display rounding independently checked |
| Attainability evidence | All 546 stored certificates have valid inputs and exact endpoint/center arithmetic |
| Exact growth budget | All 150 eligible budgets match the actual extreme deviations at the four rational corners |
| Bootstrap reproduction | All six 10,000-draw joint page-cluster confidence intervals reproduced |
| Recorded inference conditions for scored rows | 334 distinct call IDs and agent paths, `fork_turns=none`, completed status, one inherited runtime condition |

The full sample reconstruction uses the saved T1 output at local commit `30acb8dc6450ae1982b0270aafb18c74e6540bc7`. At 334 scored rows, only 144 matched pairs are complete, 46 pairs contribute a single scored member, and 6 pairs have no scored member. The partial sample is not a balanced 196/196 result.

### Official execution, normalization, and printed answers

The DSL compiler preserves the model's operands and operation order. It does not substitute gold operands. Its only additional arithmetic is the declared unit conversion. All audited finite numeric literals round-trip exactly through the compiler; executing the compiled DSL reproduces direct floating arithmetic under FinQA's final five-decimal rounding rule. Printed answers instead receive a separately labeled numeric adaptation of that equality rule.

The percentage rules and explicit million-to-dollar conversions are selected from reference/source encoding and the declared response unit, not by testing which scaling makes the model pass. The special cases Q003, Q021, Q046, Q018/Q318, and Q245 were inspected. Q194's basis-point response remains a reference-program disagreement rather than being rescaled to force agreement. The normalization implementation is tailored to this experiment's units; remaining responses still need their declared-unit handling checked during final scoring.

There are **40 printed-only official rejections** that are explained by rounding the model's otherwise accepted expression. No audited row has `printed_arithmetic_discrepancy = true`. These 40 losses are output quantization and must not be called input-rounding-caused failures.

### Human-display denominators and Q224

Display availability is determined from the reference label before attempting to parse the model number. There are 156 available witness references and 169 available control references in this snapshot. Four witness and five control labels are missing or nonnumeric. Q224's human label is `8%`, so its abstention remains a **failure in all six numeric score slots**, including both display tracks. It is not dropped from the display denominator. Its source review may separately classify the truncated question as unresolved; this does not change the observed answer/abstention score.

Reference human/execution disagreements are retained as a separate flag. Currency symbols and magnitude words are removed only when the entire reference label is a simple numeric answer. Exact half-even display rounding is used independently of binary floating-point execution scoring.

### Attainability versus outer hits

`attainable()` first checks the rational interval enclosure, then certifies an exact center or a continuous segment between rational interior endpoints whose outputs bracket the target. Every division is certified pole-free over the whole input box. Rechecking all stored endpoint inputs and values found no invalid certificate.

Q052, Q099, and Q162 have printed-number outer interval hits without attainability certificates and are correctly not counted as certified. Only **three officially rejected expressions** are certified box-compatible in this snapshot: Q027, Q102, and Q114. There are 33 certified printed-number official rejections. These sets cannot be substituted for each other.

The certificates establish numerical compatibility with the inherited independent rounding box. They do not establish source identity, semantic correctness, or causation. In particular, the disclosed Q003 issue remains: T1 gives an uncertain input to an averaging count that should be exact. The frozen sample is preserved, but Q003's box sensitivity cannot be promoted to proof of a document ambiguity. Algebraic `same_source_symbolic_formula` is also not an independent source-binding proof; the analysis correctly limits the source-review census to officially rejected expressions.

### Joint document/page bootstrap

All 334 rows map to 218 pages: 112 witness pages and 134 control pages, with 28 shared pages. One multinomial page multiplicity is applied jointly to both groups, so a shared page's questions are retained together. Rule-specific denominator matrices omit only unavailable reference-display scores. None of the 10,000 audited draws had an empty group denominator.

The following are **audit-time partial-run cross-checks**, computed in memory. They are not replacements for final `results.json`.

| Track / rule | Witness errors / n | Control errors / n | Error difference, percentage points | Joint page-bootstrap 95% interval, percentage points |
|---|---:|---:|---:|---:|
| Expression / official | 31 / 160 | 27 / 174 | 3.8578 | [-4.8333, 12.3591] |
| Expression / relative 1% | 30 / 160 | 26 / 174 | 3.8075 | [-4.7031, 12.0928] |
| Expression / human display | 36 / 156 | 21 / 169 | 10.6509 | [1.9849, 19.3969] |
| Printed / official | 40 / 160 | 58 / 174 | -8.3333 | [-18.5293, 1.7250] |
| Printed / relative 1% | 30 / 160 | 26 / 174 | 3.8075 | [-4.7031, 12.0928] |
| Printed / human display | 36 / 156 | 23 / 169 | 9.4675 | [0.7276, 18.3786] |

These contrasts remain observational. Operation matching, shared-page resampling, and box membership cannot establish that input rounding caused a model-scoring discrepancy. A literal threshold crossing on a display or printed-number track must not be substituted for the official executed-expression finding or for source-supported causal attribution.

## Snapshot identity and limits

SHA-256 values identify the audited versions; later implementation changes require focused revalidation.

| Artifact | SHA-256 |
|---|---|
| `private/sample.json` | `36658b71612465cf888f313da22ec5843ef13f10c49167ab8b45e1916b713249` |
| `scores.jsonl` | `5470ed7db5382f565d7c8bb70f073d7d10267ff1e113e4951bcf732ceaab1a1a` |
| `score.py` | `fcbc8f301659e2064649fa0873730536bf3b59df9e8fffe5daead8cae03b1515` |
| `analyze.py` | `59c4e504ad5713faabeb76ca8869af7ccacc7ef1705e1a78e2866934ea8b4aaa` |
| `validate_run.py` | `38caa06b0cc65734dee2749487b9e65bde23292cdafc2f1c5b4fdf23a78e5557` |
| Developmental `results.json` (323 rows) | `7e05fdb061da8a68a02e979ce5e9dabab55337a0b2a1679b3f4939f66287cd41` |
| Local pinned FinQA `evaluate.py` | `845cd131cab843eceff256cf6d392978cc470a7da4a80107beb56027fdca5c13` |

This audit validates the arithmetic and stored evidence against the local pinned evaluator; it does not independently attest remote-serving identity or every semantic source judgment. The recorded serving version is unavailable. There is one inherited runtime condition, so this experiment does not supply an identified cross-model replication.
