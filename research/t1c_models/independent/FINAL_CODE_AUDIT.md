# Final numerical implementation audit

Date: 2026-11-17. Reviewer: independent `scoring_audit` agent. This supplements and leaves unchanged [CODE_AUDIT.md](CODE_AUDIT.md).

## Verdict and scope

**No remaining material numerical implementation defect was found in the audited 392-row snapshot.** All 58 newly completed rows, Q335–Q392, were included in the full recheck. The two implementation findings from the initial audit are resolved: first-order precision budgets are now reported separately from exact budgets, and both analysis completion and standalone validation require completed source reviews and adjudication.

This is a sign-off on the numerical scoring, stored certificates, precision calculations, matching, and bootstrap implementation at the hashes below. Independent source reviews/adjudication were still being completed when this note was written. Their final classifications, the final `results.json`, the figure, and the final integrity manifest require the coordinator's subsequent guarded run. This note does not certify unfinished semantic judgments or a not-yet-generated final report.

No model was invoked. The auditor did not modify raw responses, prompts, sampling, implementation, scores, reviews, or prior audit findings. Only this audit note was written.

## Q377: source-grounded output-unit normalization

The source explicitly states net capital of **4.7 billion dollars** and excess capital of **3.3 billion dollars**. The reference program subtracts those operands without conversion, so its execution unit is **billion dollars**. The model's unchanged expression `(4.7 - 3.3) * 1000`, with declared unit **million dollars**, evaluates to 1,400 million dollars, the same quantity.

The new `unit_overrides.json` records a reference monetary magnitude of `1000000000`; `scale_response()` derives the conversion from the model's declared currency magnitude. It therefore applies `1/1000` for millions, `1` for billions, and `1/1000000000` for dollars. These factors follow source dimensions, independently of the answer's numerical correctness. A nonmonetary unit such as `million shares` is rejected by the targeted unit test.

The compiled Q377 program retains both original operations and appends the declared conversion:

```text
subtract(4.7, 3.3)
multiply(#0, 1000)
multiply(#1, 0.001)
```

The raw model expression yields `1400`; the unit-normalized expression yields `1.4` and is accepted by the existing normalized scoring convention. This is consistent with the experiment's other explicit monetary conversions, including Q018/Q318. It must not be described as raw, unnormalized program acceptance. The question asks for millions while the gold/human numeric label `1.4` retains the billion-unit reference representation; that inconsistency is explicitly retained in the override's metadata and reason. It is not evidence of input-precision noise.

This rule does not justify repairing a dimensionless ratio assembled from inconsistent operand units, such as Q249/Q297. Unlike those mixed-unit reference ratios, Q377 has a well-defined currency output unit after subtracting two operands in the same unit.

As a sensitivity check only, the auditor temporarily changed Q377's six score entries to rejection in memory and repeated the bootstrap. **None of the six error-difference decision booleans changed.** This sensitivity result did not select the normalization: the decision was sent to the coordinator first, based on source dimensions alone.

## Full-sample verification

Checks used the existing `130U-FinLLM/.venv/Scripts/python.exe` with bytecode writing disabled. All **12 implementation tests pass**. Additional read-only checks reproduced arithmetic and aggregates in memory rather than invoking scoring/analysis entry points that write artifacts.

| Check | Audited result |
|---|---|
| Original raw responses agree with scored JSON | 392 / 392 |
| New rows included | Q335–Q392, all 58 |
| Numeric expression execution | 391 / 391 reproduce exact values, DSL tokens, and official evaluator results |
| Original expression literals | All 1,266 preserved exactly during DSL serialization |
| Numeric track score vectors | All 782 agree, including independent rational half-even display rounding |
| Original prompts reconstructed | 392 / 392 match document, question, and fixed prompt |
| Gold programs re-executed | 392 / 392 match `exe_ans` under the local pinned official evaluator |
| Attainability certificates | All 641 rechecked against exact endpoint/center arithmetic and box inclusion |
| Growth precision budgets | All 173 exact budgets match four-corner deviations; all 173 first-order budgets match an independent derivative-based calculation |
| Matched sample | 196 witness/control pairs; each pair matches operation category; all 392 IDs distinct |
| Recorded inference sessions | 392 unique IDs and agent paths; all `fork_turns=none`, completed |
| Bootstrap | All six 10,000-draw joint page-cluster intervals reproduced |

There are 196 observations per group. The complete sample has 237 distinct pages: 123 witness pages, 147 control pages, and **33 shared pages**. The same sampled page multiplicity is applied jointly to both groups. No bootstrap draw had an empty denominator for either group under any rule.

### Final numerical aggregates

These values were computed directly from the audited `scores.jsonl`. They can be compared with the coordinator's final regenerated report once semantic reviews are finished.

| Track / rule | Witness errors / n | Control errors / n | Error difference, percentage points | Joint page-bootstrap 95% interval, percentage points |
|---|---:|---:|---:|---:|
| Expression / official | 39 / 196 | 29 / 196 | 5.1020 | [-2.5735, 12.5463] |
| Expression / relative 1% | 38 / 196 | 28 / 196 | 5.1020 | [-2.4827, 12.4467] |
| Expression / human display | 44 / 191 | 25 / 191 | 9.9476 | [2.0798, 17.7295] |
| Printed / official | 49 / 196 | 63 / 196 | -7.1429 | [-16.2183, 2.0044] |
| Printed / relative 1% | 38 / 196 | 28 / 196 | 5.1020 | [-2.4827, 12.4467] |
| Printed / human display | 44 / 191 | 27 / 191 | 8.9005 | [0.8782, 16.7273] |

Official expression scoring accepts **324 / 392** responses. Its witness-minus-control error gap exceeds five percentage points, but the confidence interval includes zero, so the specified error-difference threshold is not met. The display tracks meet their own difference threshold and must remain identified as display scoring, not be substituted for the official-execution finding.

### Display denominators and output quantization

Display scoring has 191 available references per group. The unavailable references are Q020, Q069, Q083, Q092, Q101, Q149, Q186, Q205, Q244, and Q363. Q224's abstention remains a failure in all six available numeric score entries, including both display tracks; it is correctly retained in the control denominator.

There are **44 printed-only official rejections caused by output quantization**, with no flagged printed arithmetic discrepancy. The printed-only failures cannot be attributed to input rounding. Keeping the model's expression and emitted number in separate tracks materially changes the official comparison: expression errors are 39 versus 29, whereas printed-number errors are 49 versus 63.

### Box compatibility and attainable outputs

The exact certificates use either the center or an interior line segment with bracketing endpoint outputs, while interval execution certifies every division is defined throughout the input box. Rechecking all 641 certificates found no false certificate.

Only **3 of the 68 officially rejected expressions (4.41%)** are certified box-compatible: Q027, Q102, and Q114. There are **36 of 112** certified printed-number official rejections. The outer-only printed hits Q052, Q099, and Q162 remain uncertified and are not counted as attainable. These distinctions are preserved in the scorer and must remain separate in interpretation.

These facts establish numerical compatibility with the inherited independent rounding box, not source-supported correctness or input-rounding causation. Q003's inherited uncertain averaging-count issue remains disclosed. Accepted expressions are not a semantic census, and the operation-matched error contrast remains observational.

## Audit findings resolved

**First-order comparison.** The new `t1a_first_order_budget` and `excess_over_t1a_first_order_budget` retain a distinct quantity from the exact-radius budget. An independent calculation used

```text
R_first = (abs(a) * h_b + abs(b) * h_a) / (a^2 * abs(b/a - 1))
p_first = -log10(R_first)
```

All 173 eligible rows agree: 89 witness and 84 control. The maximum difference from exact `p` remains **0.05799194698 digits at Q332**. Exact and first-order fields are carried into analysis summaries. No preexisting answer score or attainability certificate is changed by this addition.

**Final-completion gates.** `analyze.py` now sets final `complete` only when all 392 responses are present and none of the first reviews, second reviews, or adjudications are missing. The development `--allow-incomplete` path can no longer label an unfinished review set complete. `validate_run.py` independently requires empty missing-second-review and unadjudicated-disagreement lists.

The auditor executed the actual parsed completion assignments and validation assertions with four in-memory scenarios: complete review coverage, a missing first review, a missing second review, and a missing adjudication. Only the fully reviewed case passed both gates. The final coordinator run still has to satisfy these guards against the actual finished artifacts.

## Snapshot hashes and remaining limits

| Artifact | SHA-256 |
|---|---|
| `private/sample.json` | `36658b71612465cf888f313da22ec5843ef13f10c49167ab8b45e1916b713249` |
| `scores.jsonl` | `54bca5fa3909812fe266d7ae8e6dd5852d627b382aaaf2a7536f967dde58188f` |
| `score.py` | `e2bc7f8793625aefcec38812513f06cb149060cd6b6579760823912c2a84dade` |
| `analyze.py` | `8a465ddd5e9632ba019ac5c07eea3130a6db42c64ccc86a3cf2812a890a73ccc` |
| `validate_run.py` | `8abe76ccc3a12c1b3d65aeb4fa516f2ab0e917896548a4f162d34912661317b1` |
| `test_score.py` | `c285d77cd79964ac2d181f8ef4f520f6be443c3977b78494c28caf4ba6426c92` |
| `unit_overrides.json` | `091710719653872585889b6f038817487163b337a056f709243650e560e526a5` |
| Unchanged initial `CODE_AUDIT.md` | `68bed5813d7357304df26591fe9e89bc49462c2a24fc4fab81b2f9c07188e086` |

The frozen sample hash is unchanged from the initial audit. Numeric implementation changes after these hashes would require focused revalidation. Semantic review/adjudication files are intentionally not hashed here because those reviews were ongoing; their final versions belong in the final integrity manifest. The one recorded inference condition remains `inherited runtime (exact serving identity unavailable)`. Exact serving-version reproducibility and cross-model replication remain unavailable.
