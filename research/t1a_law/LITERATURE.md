# T1A targeted prior-art check and contribution boundary

Search date: 2026-11-16 (America/New_York). This is a targeted search of limited scope, not a systematic review, and it does not claim to have used a full half-day. Only original papers, official standards, official data documentation and official source code are used as the basis for the conclusions below; mirrors, aggregator sites and general tutorials found in the search were used only to discover leads.

## Conclusion

This round found no complete precedent that does all of "filing input rounding box → growth-rate precision threshold → per-question decisions on a financial QA benchmark with zero-parameter validation", so T1A can continue. But "rounding distorts economic growth rates, verified on real economic data" has a clear 1991 precedent; that layer cannot be presented as a new finding. Cancellation, condition numbers, interval arithmetic and uniform error propagation also cannot be presented as new mathematical contributions.

The contribution worth pursuing should be limited to: for fixed FinQA programs and input bindings, proving and testing a displayed-precision rule with stated conditions of validity, making the failure types of the approximate rule explicit, and distinguishing the worst-case frequency from the expected frequency under a specified probability model. Whether this shows that models are unfairly marked wrong requires T1C; whether it still holds after merging full-text disclosures requires T1B.

## Main prior work verified

| Source | What it did | Overlap with and difference from T1A |
|---|---|---|
| Thomas A. Gittings, 1991, *Rounding errors and index numbers*, Federal Reserve Bank of Chicago, Economic Perspectives 15(3), pp. 2–10. [Official abstract](https://www.chicagofed.org/publications/economic-perspectives/1991/06mayjun1991-part1-gittings), [official full text](https://www.chicagofed.org/-/media/publications/economic-perspectives/1991/ep-may-jun1991-part1-gittings-pdf.pdf) | Compares levels and monthly growth rates of the CPI-W before and after rebasing; uses Monte Carlo to study the effect of rounding on time-series estimates; points out that a weaker signal and fewer displayed significant digits make the problem worse. Main text pp. 3–5, 7–10; the footnote on the last page explicitly distinguishes rebasing from fixed displayed precision. | This is the substantive economic-data precedent newly found this round; it covers "loss of rounding precision → growth-rate distortion → empirical/simulated consequences". We did not see a per-question threshold test for financial QA built from the last-digit-unit difference Δ and the relative tolerance τ. It limits broad novelty, but is not a direct duplicate of this narrow benchmark audit. |
| XBRL International, *Calculations 1.1*, 2023-02-22 Recommendation, 2024-02-14 errata version. [Specification](https://www.xbrl.org/Specification/calculation-1.1/REC-2023-02-22%2Bcorrected-errata-2024-02-14/calculation-1.1-REC-2023-02-22%2Bcorrected-errata-2024-02-14.html) | §5.2.3 specifies that a round-to-nearest fact corresponds to a half-a-last-digit-unit interval; §5.5 intersects the intervals of consistent duplicate facts; §5.7 uses interval addition and multiplication by known weights for consistency checks. | Financial input intervals and tightening by duplicate disclosures already have a formal standard. The calculation relationships in the specification are sum relationships; it gives no growth-rate Δ threshold, FinQA frequency or probabilistic version for this task. T1A cannot claim to be "the first to bring interval arithmetic to filings". |
| Silu Panda, 2026-05-28, *FinVerBench: Benchmark Validity and Calibration in Large Language Model Financial Statement Verification*, arXiv:2605.29586v1. [Original](https://arxiv.org/html/2605.29586v1) | §3.4 and §6.5 compare unrounded error injection with a variant rounded to filing precision, and study how display and observability affect error detection. On its observable subset, the rounded variant lowers the reported model's recall from 100% to 79%. | A strong close neighbor already exists for "financial AI benchmark results are affected by displayed precision". Its task is checking financial-statement consistency/injected errors; we did not see answer ranges under input rounding boxes derived from FinQA gold programs, a Δ threshold, or a corresponding zero-parameter confusion table. Not every claim that "rounding affects financial LLM evaluation" can be claimed as original. |
| Bethel Hall, Sachi Shome, William Eiers, 2026-08-10, *VeriFin: A Neurosymbolic Framework for Verifying LLM-Generated Financial Claims*, arXiv:2608.10213v1. [Original §3.6](https://arxiv.org/html/2608.10213v1#S3.SS6) | The verifier binds operands to disclosed fixed values, executes authorized formulas, and then uses half a unit of the disclosed last digit as the tolerance for the candidate output. Its formula explicitly uses equality constraints to fix each operand. | Like T1A it involves verifiable financial numbers and precision, but what it checks is the candidate output under fixed inputs; the output tolerance must not be misread as input interval propagation. We did not see validation of this task's Δ law. |
| Federal Reserve Bank of St. Louis, FRED Help, *What Formulas are Used to Calculate Growth Rates?*. [Official note](https://fred.stlouisfed.org/help/data/understanding-the-data/formulas-calculate-growth-rates) | Official caution: recomputing percentage changes or growth rates from published rounded levels may differ from the original release. | That growth rates are sensitive to rounded data has long been a public data-use caveat; this page gives no threshold or benchmark test for this task. |
| The executor at FinQA's pinned official commit `0f16e2867befa6840783e58be38c9efb9229d742`. [Source code](https://github.com/czyssrs/FinQA/blob/0f16e2867befa6840783e58be38c9efb9229d742/code/evaluate/evaluate.py) | `eval_program` finally applies `round(this_res, 5)` to the value; `evaluate_result` compares it with `qa.exe_ans`. | T1A's relative 1% is a specified sensitivity-audit convention, not the original tolerance of this version of official FinQA. The existence of out-of-tolerance outputs within the input box also does not mean that the task "do arithmetic on the displayed numbers" is undefined. |

The empirical numbers in the literature above belong to their own settings; they are not transplanted as effect sizes for this project. This round did not interpret "not found" as "no precedent exists", and did not do an exhaustive search of paid databases.

## Search log

Below are the complete search queries actually sent (general web search); the official originals above and their relevant sections were then opened. Hits unfavorable to the expected conclusion were not filtered out.

1. `"FinQA" "rounding" "uncertainty"`
2. `"financial statements" "growth rate" "rounding" precision`
3. `"FinQA" "significant digits"`
4. `"financial question answering" "condition number"`
5. `"FinVerBench" rounding`
6. `"VeriFin" "rounding"`
7. `site:xbrl.org "Calculations 1.1" "interval"`
8. `"rounded data" "growth rates" uncertainty`
9. `"financial ratio" "rounding errors" interval`
10. `"growth rate" "significant figures" error rounding`
11. `"FinQA" "interval arithmetic"`
12. `"financial statements" "condition number" rounding`
13. `"rounding" "financial ratios" uncertainty bounds`
14. `"rounding error" "percentage change" bounds`
15. `"growth rate" "rounding" "interval" precision financial`
16. `Thomas Gittings "Rounding errors and index numbers"`
17. `"Rounding errors and index numbers" Chicago Fed`
18. `"FinQA" "rounding interval"`
19. `"financial ratios" "interval arithmetic" rounding`
20. `"rounding errors" "growth rates" "bounds"`
21. `"rounding errors" "financial statements" "precision"`
22. `"FinQA" "rounding" "Benford"`
23. `"growth rate" "rounding" "100" uncertainty`

Other findings and how they were handled: the searches hit an expert opinion in litigation about CPI rounding precision, interval ratios in bank efficiency analysis, notes from commercial financial-reporting tools on rounding sum differences, and many significant-figure textbooks. These can serve as leads for expanded searches, but this conclusion does not rely on mirrored tutorials or insufficiently verified expert opinions; this round also found among these hits no complete validation of a FinQA precision law.

## Usable framing for a paper

"We do not propose a new cancellation theory or a filing interval standard. We study the match between disclosed precision and the audit tolerance of financial QA: given fixed programs and input bindings, we turn classical error propagation into a recomputable precision rule, test its predictive power on FinQA, and report the difference between the worst case and probabilistic results under a uniform rounding model."

This is still a conditional benchmark-audit contribution; based on this search alone it cannot be written up as 'first', 'only' or 'proven to have no precedent'.
