# Candidate 5: the human answer disagrees with the program's executed value

**Verdict: someone has already done the same thing; suggested ⚪; confidence high.** As of 2026-11-17. The judgement here uses the task's criterion "reported an inconsistency rate, or filtered the data on it"; the precedent does not need to have obtained exactly the same 508/7,952.

## Decisive evidence (full text: public PR, code, release documentation)

izarov, 2026-10-08, [Serve only FinQA tasks whose reference agrees with the written answer, EnvCommons/FinQA PR #4](https://github.com/EnvCommons/FinQA/pull/4), merged the same day at 14:38:46 UTC. The PR's Problem, Fix, Decisions and Tests sections and the full patches of the three files were read; the merged version [`finqa.py` L27–74](https://github.com/EnvCommons/FinQA/blob/b0e5f907abda069f0915e93e006c4ba55658360e/finqa.py#L27) was checked.

The author compares `qa.answer` and `qa.exe_ans` directly and reports:

| Split | Original questions | yes/no | Numeric field mismatch | Kept |
|---|---:|---:|---:|---:|
| train | 6,251 | 124 | 455 | 5,672 |
| dev | 883 | 10 | 58 | 815 |
| test | 1,147 | 20 | 80 | 1,047 |

Of the 455 conflicts in the training set, the author lists 64 sign flips, 51 other units and 340 other. The three splits have 593 numeric conflicts in total; 593/8,127 = 7.30% is computed by this report from their numbers, with the denominator being the questions excluding yes/no; **it is not an inconsistency rate under our convention reported by the author**. The PR explicitly enables the filter on all three splits; the [current release page, Tasks](https://openreward.ai/GeneralReasoning/FinQA) also shows these kept counts.

The filter judges a pair consistent if any of the following holds: 1% relative difference; falling within the half-unit rounding band of the human answer's last digit; a same-sign truncation error smaller than one last-digit unit; and it tries the program value as is, multiplied by 100 and divided by 100. Questions with no parseable human number are kept. This differs from this project's count, which uses only displayed precision, lists sign conflicts separately and restricts the denominator to parseable questions. So 593 and 508 do not contradict each other; **nor can a different number be used to claim the method is new**.

The PR gives the example STT/2006/page_92.pdf-4: the human answer is 35.72%, the program divides in the reverse direction and gets 0.73684; 16 training sessions all gave about 35.72 and all scored 0. This is at the same time an existing public case of the benchmark causing a stable rejection. It is not a multi-model, full-test-set study, and cannot be extended to all of candidate 4's conclusions.

## The three closest primary sources and short quotations

The direct precedent for this item is software maintenance work. The type of each source is stated explicitly below; the three sources are not passed off as three independent academic papers.

1. **PR #4 (2026, direct precedent).** Original Fix text: > "a task is served only if `exe_ans` is a number that agrees with the written answer."
   It already reports per-split counts and a sign-flip subcategory and implements the filter, which meets the task's precedent criterion. Source level: **full text / code**. The remaining increment is stricter parsing rules, an exact denominator and per-question linkage to model rejections; these can serve as replication and evidence, but can hardly carry a paper on their own.
2. **[Description for the attributes in the data file, czyssrs/FinQA issue #6](https://github.com/czyssrs/FinQA/issues/6) (2022-05-17, public discussion in the official repository).** Item 3 of the original question: > "`answer` and `exe_ans` are different for Sample 1"
   It gives 380 and 3.8; the full text was read, and the API confirmed that the comments visible at the time were empty. Source level: **full text (issue)**. It is only a single case and the difference is exactly a factor of 100, which under this project's rule allowing percentage scaling may not count as a contradiction; it cannot by itself justify downgrading to white or support saying that 6.4% is already known.
3. **[FinQAPT: Empowering Financial Decisions with End-to-End LLM-driven Question Answering Pipeline](https://arxiv.org/html/2410.13959) (Singh, Kaur, Smiley, ICAIF 2024).** §4.5.1, FinReader paragraph: > "disparities between the execution answer and the provided answer"
   §§4.1–4.5 read, especially 4.5.1; the paper directly points out differences between the execution answer and the given answer, and the convention problem of a question asking for a number but the answer giving a percentage. Source level: **full text**. It does not give a separate overall inconsistency rate between the two fields, nor does it describe filtering questions by field consistency, so this paper alone is not yet enough to fully meet the task's criterion for candidate 5; PR #4 clearly does meet it. FinQAPT reports proportions for other error categories in 4.5.1, but those proportions cannot be turned into a field-contradiction rate.

## Check of known claims

- "Not found in the initial searches": the 2022 issue lead and the PR merged in 2026-10 have now been added; this can no longer be used as a first-discovery claim.
- "The official scoring uses `exe_ans`": read str_to_num, eval_program and evaluate_result in the [official evaluate.py](https://github.com/czyssrs/FinQA/blob/main/code/evaluate/evaluate.py); L188 rounds the predicted executed value to 5 places, L418 takes exe_ans, L444 compares for equality; the official scorer does not use a uniform 1% free-text tolerance.
- [PR #2](https://github.com/EnvCommons/FinQA/pull/2) and [PR #3](https://github.com/EnvCommons/FinQA/pull/3) were both merged on 2026-10-07: the former sets a 1% cap according to the output's displayed digits, the latter changes to a fixed 1% and asks for at least 3 significant figures. The discussion and experiments concern **output comparison rules**, not the feasible interval induced by rounding of filing inputs, and cannot be used to refute candidate 1 directly.
- [PR #5](https://github.com/EnvCommons/FinQA/pull/5) was merged on 2026-10-09 and adds handling of magnitude words aware of document units. It shows that units and formatting still affect scoring; it does not mean this project's independent recomputation has been done.

## Limitations

All visible issues/PRs of the official repository (15, including PRs) and all 6 PRs of EnvCommons were read directly, and the highly relevant patches were checked. The GitHub search interface once returned 0 for an EnvCommons empty query, but the listing REST endpoint successfully returned 6 items; so this report uses the enumeration result and does not treat zero search hits as zero precedent. The direct search endpoints of Google Scholar and Semantic Scholar could not be accessed with this round's browsing tools; see the search log. The PR's count of 593 was not re-run; this document reports the author's original public results and the implementation as read, and the 508 in the task statement was not recomputed in this round either.
