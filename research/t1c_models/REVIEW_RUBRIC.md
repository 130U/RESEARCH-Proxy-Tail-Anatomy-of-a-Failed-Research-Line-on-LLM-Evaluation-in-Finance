# Independent source review rubric

Review the supplied question, document, reference answer/program, and model response. The packets omit experimental group and numerical interval flags. Do not read the root review or study scores before writing your own judgments. Do not assume either the reference or model is correct.

For each call, report `call_id`, `primary_cause`, `formula_valid` (true/false/null), `alternative_precision_used` (true/false), and a short source-specific `reason`. Explicitly identify the relevant row, years, units, and denominator when disputed. An expression can be valid under a reasonable stated interpretation even if it differs from the reference. Use null where the excerpt is insufficient.

Primary causes:

- `alternative_source_precision`: the model uses a different displayed precision of the same fact (same entity, period, concept and scope), and that substitution explains the reference disagreement without needing another change of meaning, sign, or formula.
- `reasonable_alternative`: the question permits the model's interpretation. Examples include positive decrease magnitude versus signed change, or an actually ambiguous time horizon. Do not automatically excuse an ending-value denominator for an explicitly defined growth rate.
- `reference_error`: source facts and question establish a definite error in the reference, such as the wrong year, missing operation, or missing unit conversion. State why the model formula is supported.
- `true_error`: the model uses the wrong fact or operation, and the question and source support a definite resolution. Do not use this merely because it disagrees with the reference.
- `unresolved`: the problem is incomplete, contradictory, or lacks the source information needed to establish a unique valid resolution. Note any model error that can still be established.
- `invalid_format`: no usable model response without a substantive source-based reason for abstaining.

Flags can overlap. A model can use a finer disclosure and also reverse the sign relative to the reference. In that case preserve the precision flag, but do not call precision the sole cause. Changing money units alone is a unit conversion, not a second disclosure of different precision. Numerical membership in an interval is not part of this source review.

Nonnumeric abstentions and malformed responses are retained as failures in numeric scoring. A justified abstention on a truncated question can nevertheless receive `unresolved` as its semantic cause. Do not invent missing questions or replace raw responses.

These judgments audit rejected expressions. They do not certify all numerically accepted expressions as semantically correct and do not estimate the prevalence of annotation problems across all of FinQA.
