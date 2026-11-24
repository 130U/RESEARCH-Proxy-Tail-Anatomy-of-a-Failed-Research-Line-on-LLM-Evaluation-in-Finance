# T1 conventions fixed before the first count

Date: 2026-11-16 (America/New_York). The entry point is `tasks/T1_rounding.md`; this directory is independent of the earlier absolute-scoring experiment.

## Prior-art check and object of study

The first round of targeted search and full-text verification of close neighbors found no complete duplicate; details are in `literature.md`. This does not mean the literature was exhausted, and we do not claim to have used the full half-day prior-art budget. Interval arithmetic, rounding error propagation and interval intersection of XBRL duplicate facts are all existing methods. This study only measures the sensitivity of public QA data under an explicit rounding model.

The quantity studied is **whether, given the gold program, the bound reported numbers and independent rounding boxes, the answer stays within the preset scoring interval**. It is not the same as a benchmark annotation error or a model error, and it does not automatically prove that the whole original filing lacks sufficient information. If the question was meant to be computed from the displayed numbers, the benchmark task itself is still determined.

## Data, denominators and execution

- Main result: all questions in the official FinQA public test; dev and train are reported separately, plus the total of all three. No training, no paid APIs, no picking questions based on results.
- Precision is taken from `table_ori` and the text number strings provided by the benchmark, never from program floats or `exe_ans`. Trailing zeros are kept. Locate first using gold-supported facts, then use the source table/text; questions without a reliable binding are listed separately. Multi-level table headers are aligned by row label and cannot be indexed directly by physical row number.
- For each reported value that can be included, the half-width is half a unit of the displayed last digit. The data check found that `const_*` tokens can also encode actual reported values, so any question with a const operand whose value matches a value in the source support is excluded entirely; the rest are treated as program constants. Years, counts, contractual amounts, fixed investment basis points and the like should not all be treated as continuous rounded values; when unclear, exclude.
- Repeated references to the same bound input use one variable. When the candidate source/precision is not unique, we do not arbitrarily pick the coarsest value to enlarge the phenomenon.
- Exact rational interval arithmetic gives the outer envelope; consistent interior input corners give actual out-of-tolerance witnesses. Cases where only the envelope is out of tolerance and there is no witness are marked unresolved. Questions whose center does not satisfy the reference answer to begin with are listed separately as center mismatches and are not attributed to rounding.
- Denominators are listed for all questions, numeric questions, and questions that are executable and successfully bound. Unparsed questions are not treated as stable; with all questions as the denominator we report the lower bound of the witnessed fraction and the unresolved fraction.

## Scoring rules

1. Relative 1%: closed interval around `qa.exe_ans`; zero answers use a zero-width interval, with no absolute tolerance quietly added.
2. Displayed precision: build the rounding cell from the displayed digits and percentage scale of the original `qa.answer` string. Questions whose precision/scale cannot be recovered are listed separately; digits are not invented with `str(float)`.
3. The official rule as a supplement: the FinQA program result is compared with `qa.exe_ans` after rounding to five decimal places. 1% and displayed digits are this study's audit rules and are not written up as the official rule. When exact decimal rounding cells are used for sensitivity analysis, we state how their boundaries differ from Python binary floats.

The two task-specified rule sets are reported separately, and the main gate uses the looser 1% rule, so that a continue verdict does not rest only on very narrow answer display cells. Any continue condition (overall ≥5%, or an operation group ≥15%) takes priority over the abandon condition of overall <2%; the original task did not specify a priority when a group and the overall rate conflict, so we make it explicit in advance. Question counts are given within each group, and small groups are not treated as stable general patterns. If the overall rate is 2%–5% and no group reaches 15%, I decide case by case.

## Operations, precision and additional analyses

Operations are determined by program structure: growth rate first (a difference divided by the same base), then ratio, difference, sum, other. Input significant digits are computed from the original decimal representation, and results are reported grouped by each question's minimum significant digits.

Same quantity at different displayed precisions requires evidence of entity, metric, period and unit; close values alone do not make the same fact. Candidates are screened automatically and then verified manually; we report candidate coverage and confirmed counts, and do not pass off the candidate rate as the true overall fraction. We report whether center computations at different locations of occurrence cross the scoring boundary, and discuss the interval intersection after conversion to a common unit.

Precision improvement is only a **synthetic counterfactual**: within the same physical unit, shrink input half-widths by factors of 10, 100 and 1000. Merely rewriting millions as thousands, scaling the numbers and the rounding error together, adds no information; without original disclosures at higher precision we do not claim that real data has validated this improvement.

## Log of implementation fixes

The first trial parse of 200 questions was used only to check source parsing; the decision thresholds were not changed. Then source reading of 20 random questions found problems with constant tokens, integer share counts and multi-level table headers; non-unique source precision, non-unique source identity and obviously exact quantities were excluded. The first full source check (fixed seed 20261116, sampling 25 of the 199 out-of-tolerance test questions at the time) further found missed integer counts of stores/call centers and missed `per common share` dividend wording; semantic exclusions were added and everything was rerun. The number of out-of-tolerance test questions fell from 199 to 196. The duplicate-precision review found that "both years were 2.6" can appear as a single text span while referring to two facts, so any question with two identical raw-number arguments in the same step is excluded entirely; x-x cannot be assumed to be identically 0. We also fixed leading-dot decimals and duplicated parenthesized percentages added by text preprocessing. All of the above are parsing and type fixes; the 5%/15%/2% gates were not changed based on results. The exclusion rules lean conservative and do not amount to a complete semantic parser.
