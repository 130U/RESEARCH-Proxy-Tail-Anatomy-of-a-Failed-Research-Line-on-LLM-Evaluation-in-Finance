# T1C: independent method review of scoring and attribution

Review date: 2026-11-16 (America/New_York). The main body was written by an independent agent before the blind answers were generated, without seeing any model answer. The "Root-agent follow-up check" at the end is an adjacent literature check added while the experiment was running; this file does not report experimental statistics.

## Core conclusion

The experiment can be run, but three things must be kept apart: **the rounding of how the final answer is expressed, the computed result of the model's formula, and the quantization uncertainty of the original disclosed inputs**. Only the third maps directly onto the T1 hypothesis. A number inside an ordinary interval-arithmetic outer enclosure also cannot be called a "document-consistent correct answer" outright.

## Official rules and this run's interface

An independent reading of the [pinned FinQA evaluate.py](https://github.com/czyssrs/FinQA/blob/0f16e2867befa6840783e58be38c9efb9229d742/code/evaluate/evaluate.py) shows: `eval_program` executes the program the model gives, with no step-by-step rounding, applying `round(this_res, 5)` only at the end; `evaluate_result` compares directly for equality with `qa.exe_ans`. There is also a symbolic program-equivalence metric. The original official task is therefore **program-execution scoring**, not scoring of natural-language answer strings.

Since this run asks for "a final value + a short formula", we recommend keeping two scoring tracks:

1. **Final-value track**: for the value the model actually wrote, normalize the unit and then apply three rules: five decimals, 1%, and gold displayed digits. Call the five-decimal rule "official numeric rule carried over"; do not pass it off as full official execution accuracy.
2. **Formula-execution track**: execute only the formula the model actually gave, keeping its operands and operation structure; using gold to patch a formula is forbidden. Formulas that convert to the official DSL go directly to the official executor. When a formula is incomplete or ambiguous, record it as non-executable; do not reconstruct one from the final value.

For example, the model writes `3.0%`, but its formula is `(137-133)/133*100`. The final displayed value may fail at five decimals, while the correct formula executed as an official program can pass. That difference belongs to **output displayed precision**; it must not be recorded as input rounding causing correct reasoning to be marked wrong by the official scorer.

`qa.answer` and `qa.exe_ans` do not always use the same percentage scale: the original T1 verified `93.5% ↔ 0.935`, and there is also `24.69% ↔ 24.69136`. The scale mapping must be fixed in advance from gold's established encoding and the answer's explicit unit; choosing the 1/100/100x factor "closest to gold" to rescue a score is not allowed. We recommend keeping the original value, original unit, normalized scale, and the reason for the mapping. See [T1 source verification](../t1_rounding/sources.md) and the [pinned data directory](https://github.com/czyssrs/FinQA/tree/0f16e2867befa6840783e58be38c9efb9229d742/dataset).

Scoring by displayed digits should freeze a tie rule; negative numbers, percentages, and trailing zeros must be preserved. When the gold display format cannot be parsed, list it as NA and give the denominator; do not mark it wrong by default. The acceptance region of the 1% rule for a zero target must also be explicit; we recommend that this task keep T1's relative rule and not add an ad hoc absolute tolerance.

## Interval attribution must prove reachability

The documentation of T1's `eval_interval` explicitly calls the result an **OUTER enclosure**; the comments in `classify` also state clearly that a full corner search is not a full range analysis. An input that appears several times in the computation graph causes dependency inflation; for example, the true range of `x-x` is `{0}`, but ordinary interval subtraction may output a nonzero width. Three fields should therefore be kept: hits the outer interval, proved reachable, unresolved.

A sufficient certificate that is easy to implement: keep two input vectors `u,v` strictly inside the rounding box, compute exactly `f(u) ≤ y ≤ f(v)` (or the reverse), and use interval execution along the segment to prove that no denominator crosses zero. Since the box is convex and `f` is continuous along that segment, the intermediate value theorem proves that some valid input produces the model value `y`. No closed-form preimage is needed. When there is only an approximate solution from numerical optimization, or only a hit on the outer interval, the case remains a candidate; do not give it the proved label. The center, existing T1 witnesses, and the remaining inset corners are usually enough to supply these endpoints.

Even when reachability is proved, the case may only be called "**compatible within the T1 independent rounding box**". This is not a sufficient condition for "the model's reasoning is correct", nor does it mean "consistent with all constraints in the full text": a wrong year or formula can land inside the box by chance, and T1B's duplicate-disclosure intersections and accounting constraints may still exclude it. [XBRL Calculations 1.1](https://www.xbrl.org/Specification/calculation-1.1/REC-2023-02-22%2Bcorrected-errata-2024-02-14/calculation-1.1-REC-2023-02-22%2Bcorrected-errata-2024-02-14.html) §5.2, 5.5, and 5.7 already specify reported-precision intervals, intersection of duplicate facts, and interval arithmetic; the full information set cannot be replaced by a standalone input box.

## Recommended attribution record

First store overlapping flags, then decide a mutually exclusive primary attribution, so that the first category does not swallow the other causes:

- `output_rounding_only`: the correct formula passes on execution, but the final answer value fails.
- `alternative_source_precision`: the model really did use a number from elsewhere in the document with the same entity, same period, and same convention; keep the location and the substituted formula. A value that merely happens to be equal is not enough to establish the choice of source.
- `box_compatible_certified`: the original final value or the executed value has the reachability certificate described above, with a separate flag for whether the formula is valid; do not label it "correct" automatically.
- `reasonable_alternative_formula`: the reviewer states explicitly that the question's wording allows this convention. An end-of-period denominator is not reasonable for every growth-rate question; it is acceptable only when there is ambiguity.
- `error` / `unresolved`: keep clear errors and insufficient evidence separately; do not force pending items into correct.

Report both the "in-box compatible share of rejections", computed with the task's literal threshold, and the stricter "share of rejections supported by a valid source / valid reasoning". If only the former exceeds 10%, the conclusion is that numeric scoring disagrees with the loose feasible set; one cannot claim that input rounding **caused** correct model reasoning to be marked wrong. Compute the error denominator separately for each rule.

## Groups, intervals, and significant digits

Keep all 196 witness questions; take stable controls only from T1's `certified_inside`, match without replacement within the same `category`, and freeze the random seed; do not choose controls by model performance. Report the number of categories and document clusters after matching. If one page contains questions from both groups, the bootstrap should resample page IDs of the joint sample and carry all records of both groups on that page together, so that one page is not treated as independent samples. Matching only on operation category does not yet match formula length, answer size, or retrieval difficulty; the error-rate difference is an association, not a causal estimate of rounding causing errors. Public-data contamination may affect the two groups to different degrees; one cannot claim without verification that it cancels out.

Significant digits should be extracted from the original string of the model's final value, recording trailing-zero ambiguity; converting a percentage unit does not change the number of significant digits. The T1A approximate digit budget is a magnitude law with a leading-digit term and a constant term; negative budgets, intervals crossing zero, and exact/near-zero outputs must not be forced into ordinary significant digits. If an independent exact definition of digits is used, write the definition out in full and report it as a separate metric rather than passing it off as the T1A theorem; the outer-enclosure width gives only a conservative budget.

## Targeted prior-art check

On top of the original T1 prior-art check, this run added 7 queries: `FinQA rounding evaluation precision interval`, `FinQA rounding false correct`, `financial question answering input precision benchmark uncertainty`, `FinQA input rounding model evaluation`, `FinQA interval arithmetic model`, `FinVerBench rounding`, and the full paper title `Characterizing Ambiguity in Financial Document Question Answering`. **We found no measurement of the same kind: blind answers on a FinQA rounding-witness group and a matched stable group, followed by a case-by-case proof of input-rounding attribution.** This was a limited targeted search and must not be described as an exhaustive novelty check.

- The [FinVerBench paper](https://arxiv.org/html/2605.29586) studies detection of financial consistency errors, explicitly compares rounded/unrounded presentations, and reports detection performance changed by rounding. It already covers the broad theme "financial displayed precision affects model evaluation", but it is not this task's experiment of QA reference computation with matched groups.
- [Characterizing Ambiguity in Financial Document Question Answering](https://aclanthology.org/2026.finnlp-1.37/) hand-annotates document/question ambiguity in MultiHiertt and evaluates model ambiguity detection; this run confirmed the official page and the abstract. Fetching the PDF timed out this time, so its finer tolerance conclusions are not treated as facts independently verified here.
- The search also located the [RLM author's FinQA audit page](https://queelius.github.io/rlm/research-audit-2026-09-29/decomposition-and-transfer/), whose summary points out the rounding difference between final values and formula execution. Fetching the full text failed; it is listed as a lead to follow up, not as evidence that was read. This lead further shows that simply comparing strict/loose scores cannot be a unique contribution.

This review recommends keeping T1C's planned test while tightening the wording of the conclusion: interval compatibility is a mathematical fact; "the reasoning is correct" and "rounding caused a real misjudgment" need additional formula and source evidence.

## Root-agent follow-up check: annotation problems are not a new finding

While the blind answers were being generated, the source review found cases such as reference programs missing an operation and wrong years, so this adjacent literature was checked; the sample and the prompt were not changed because of it.

- Mavi, Saparov, and Zhao, [Retrieval-Augmented Chain-of-Thought in Semi-structured Domains (2023)](https://aclanthology.org/2023.nllp-1.18/), already hand-checked 40 FinQA samples in Appendix D.2, Table 7, and classed 2 of 10 error cases as annotation error. [PDF read, page 186](https://aclanthology.org/anthology-files/pdf/nllp/2023.nllp-1.18.pdf#page=9). Therefore "FinQA has annotation problems" and "the model is right but the reference answer is wrong" are not suitable as novelty claims for T1C on their own.
- The official repository's [issue #15](https://github.com/czyssrs/FinQA/issues/15), on 2026-08-20, reported that an average of five years of lease payments seemed to be divided by 4 rather than 5. At the time of the check the issue was open with no maintainer reply; it is used here only as an earlier public report, without claiming that maintainers have confirmed or fixed it.
- [Confidently Wrong, v2 §3 (2026-10-13)](https://arxiv.org/html/2607.11414v2) explicitly uses a 2% relative tolerance and several unit-scaling conventions, and discusses auditing the scorer. That work studies error detection from internal states; it is not a matched experiment on source-input rounding boxes. It also shows that loose numeric scoring and unit normalization need a clear convention; this experiment did not choose the scaling factor closest to gold to rescue scores.

This follow-up check does not amount to a duplicate of the same measurement on the same question, but it requires narrowing the new contribution to "the relation between input-precision status and real model scoring, and the distinction between provable reachability and the attribution of actual errors". Reference annotation problems serve only as a control item and an alternative explanation.
