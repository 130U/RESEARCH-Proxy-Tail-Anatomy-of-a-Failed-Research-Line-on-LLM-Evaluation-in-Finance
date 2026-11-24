# T1C: one-page summary

**Under official execution scoring, the result did not reach the preset "has practical impact" threshold; this run did not confirm any model misjudgment caused by input rounding alone.** The witness group's error rate is higher by **5.10 percentage points**, but the 95% interval **[−2.57, 12.55]** contains zero. Of 68 rejections, only **3 (4.4%)** can be proved compatible within the T1 rounding box, and all three involve a denominator or reference-program problem. This result means "not yet detected"; it does not prove the effect is zero.

All 196 T1 witness questions were matched without replacement, by operation type, to 196 stable questions; 392 independent fresh sessions, a fixed prompt, and a single inherited runtime condition. Confidence intervals use a joint cluster bootstrap over 237 filing pages, 10,000 draws, keeping the cross-group dependence within a page.

| Scoring track / rule | Witness-group accuracy | Control-group accuracy | Error-rate difference, percentage points (95% CI) |
|---|---:|---:|---:|
| Formula execution / official five decimals | 80.10% | 85.20% | +5.10 [−2.57, 12.55] |
| Formula execution / relative 1% | 80.61% | 85.71% | +5.10 [−2.48, 12.45] |
| Formula execution / human-answer displayed digits | 76.96% | 86.91% | +9.95 [2.08, 17.73] |
| Final value / official numeric rule carried over | 75.00% | 67.86% | −7.14 [−16.22, 2.00] |
| Final value / relative 1% | 80.61% | 85.71% | +5.10 [−2.48, 12.45] |
| Final value / human-answer displayed digits | 76.96% | 85.86% | +8.90 [0.88, 16.73] |

The denominator is 196 per group; the display rule uses only the 191 parsable human labels per group. Every track first normalizes by the declared unit; formulas go to the unmodified official executor, keeping the original operands and operations. The million/billion conversion for Q377 has its own source record; it is not a direct comparison of raw, unnormalized DSL.

**Attribution.** All 68 official rejections received two source reviews: 33 reference answer/program problems, 24 defensible alternative conventions, and 11 cases of insufficient information or mixed problems; the last group includes 3 identifiable model formula problems, so one cannot claim from this that the model was right in every case. 7 disagreements were adjudicated, with the original opinions kept. Rejections explained solely by different displayed precision of the same fact: **0/68**. Q236 has both a finer disclosure and a sign difference, and was not counted as a pure precision cause. Formulas that already passed numeric scoring did not all receive semantic review.

**Rule sensitivity is real.** The display rule meets the between-group difference threshold, but 32 human labels disagree with the display of the standard program's center value. Scoring the final value directly adds 44 more answers rejected only because of output rounding, whose correct formulas had passed; the in-box compatibility fraction on that track is 36/112 (32.1%). The formula compatibility fraction under the display rule is 16/69 (23.2%). Passing these broad-convention thresholds cannot serve as causal evidence about input rounding.

**Over-reported digits.** In the subset of growth questions with the same source and the same formula (witness 69 / control 75 questions), the median number of reported significant digits is 16/12, the median T1A first-order error-magnitude budget is 1.39/3.03, and the median per-question excess over the budget is **14.42/8.36 digits**. The exact budget is saved as well; across all applicable questions the two budgets differ by at most 0.058 digits. This is a magnitude diagnostic that assumes the disclosure is a rounded measurement. It does not guarantee identical leading digits, and it does not mean that computing from the displayed digits is wrong.

**Scope limits.** Only one model condition; the tool does not expose the exact service version; public-data contamination may affect the two groups unequally. Operation matching is not causal identification; a balanced sample cannot estimate the misjudgment rate for all of FinQA. The in-box certificates do not include the T1B full-text constraints. We recommend keeping T1 as a diagnostic of input precision and benchmark semantics, and not claiming on this basis that large-scale rounding misjudgment has been confirmed.

[Results figure (PNG)](t1c_results.png) · [Vector figure (PDF)](t1c_results.pdf) · [Per-question scoring and attribution](judgments.csv) · [Recomputation and raw records](README.md) · [Independent numeric audit](independent/FINAL_CODE_AUDIT.md)
