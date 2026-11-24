# Candidate 3: the model knows precision but does not use it unprompted

| No. | Conclusion | Suggested colour | Closest work (title, year, link) | What they did | What we add | Confidence |
|---|---|---|---|---|---|---|
| 3 | Someone has already done the same thing (under the task's broad criterion "or has reported the difference between not asking and reminding") | ⚪ | [Optimizing Human–AI Collaboration in Chemistry (2024)](https://doi.org/10.3390/chemistry6040043); [Gauging Overprecision in LLMs (2025)](https://arxiv.org/abs/2504.12098); [Number Cookbook (2025)](https://arxiv.org/abs/2411.03766) | A before/after comparison with an explicit prompt on significant-figure calculations already exists; FinQA numeric-interval outputs and a calibration evaluation already exist; a significant-figure rounding benchmark already exists | The rounding feasible set of filing inputs, using the range exactly propagated through the model's own expression as the reference, and the correlation between natural output digits and supportable digits: this combination was not seen in the full texts read | High: enough to deny novelty to the broad slogan; medium: the judgement that the narrow combination has not been seen. The Chemistry supplement's raw responses and the internal Scholar/S2 results were not obtained |

The ⚪ here does not say that existing papers reproduce all of this project's design. It strictly applies the "or" criterion given in advance by the task. After finding a precedent, one cannot quietly change the criterion to "must be FinQA, must be exact intervals, must be a large sample" to keep the colour. The narrower design can be merged into the main line of candidate 1's paper; "it uses significant figures once reminded" alone should not carry the novelty of a paper.

## The three closest papers: full-text evidence and differences

### 1. Vidhani & Mariappan, 2024 — Optimizing Human–AI Collaboration in Chemistry: A Case Study on Enhancing Generative AI Responses through Prompt Engineering

Source level: **full text**. Published in *Chemistry* 6(4):723–737; §2 experimental design, §3.2 with Fig.4, and §4 read. [Publisher full text](https://www.mdpi.com/2624-8549/6/4/43).

Short excerpt from the original (§3.2, the prompt used in Fig.4E):

> "Round the final answer based on significant figures rules"

The authors report: in a multi-step significant-figure calculation, after switching to another set of values/significant digits (Fig.4D) only 2/10 were correct; after adding the sentence above (E), 10/10 were correct. This must not be confused with a different change: the original expression A gave 0/10, and adding parentheses (B) gave 9/10. After changing the operation, F became unstable again, so this is only a small-case behavioural precedent, not proof that "models generally know precision". §2 states that each revised prompt was tested ten times and discusses same/different context windows; supplementary tables S6–S8 could not be downloaded, so these counts are the authors' reports as checked in the full text, and the raw responses were not independently recomputed. It has no ground-truth rounding interval for filings, but it already covers the broad claim "by default significant figures are not applied; an explicit prompt improves this".

### 2. Bahaj, Rahimi, Chetouani & Ghogho, 2025 — Gauging Overprecision in LLMs: An Empirical Study

Source level: **full text**. §§2–5 and appendices A–D read. [arXiv HTML](https://arxiv.org/html/2504.12098v1).

Short excerpt from the original (§3.3):

> "the percentage of instances where the ground truth answers fall within the generated intervals"

On numeric QA data that includes 3,262 FinQA questions, it asks models to output lower and upper bounds, and tests preset confidence levels, vanilla/CoT, aggregation and self-revision. The ground truth in §3.3 is a point answer, and it measures point coverage; in §5 Table 4 the correlation between interval width and the requested confidence is close to zero. It does not propagate input rounding error, and it is not a correlation between default printed digits and reliable digits. It directly refutes the sweeping claim that "the existing uncertainty literature only studies the probability of being correct and has not studied numeric intervals". It also cannot support "it works as soon as you ask": its models are still clearly overprecise. Full text §4.1 says generation was done five times, while the Table 4 caption says ten times; when citing, one should avoid silently reconciling this reporting discrepancy; this report does not rely on that count for its conclusion. The anonymous ICLR 2026 version that came up in the search was not retrieved, and is not counted as a separate study or as an accepted paper.

### 3. Yang, Hu, Kang, Lin & Zhang, 2025 — Number Cookbook: Number Understanding of Language Models and How to Improve It

Source level: **full text**. ICLR 2025 paper, first arXiv version 2024; §2 and appendices A.1.3–A.1.4, A.2 and A.3 read. [Full text and appendices](https://arxiv.org/html/2411.03766v3).

Short excerpt from the original (formal task prompt in Appendix A.2):

> "Sig_fig: Convert the number to scientific notation: &lt;a&gt; and keep significant figures as &lt;b&gt;."

NUPA's 17 task types include rounding a number to a specified number of significant figures; this is a formal evaluation, not just a general remark that "models are bad with numbers". Here the number of significant figures is specified by the question; the model does not need to judge how many digits the measured/rounded inputs can support, and there is no experiment comparing default output with output after a reminder. So it reduces the claim of "the first evaluation of significant figures", but it cannot directly erase this project's exact-feasible-set design.

## Item-by-item check of known similar ideas

| Known claim | Verification result | Source level and location |
|---|---|---|
| There is a lot on uncertainty expression, calibration and verbal confidence, and the object is usually the probability of being correct | Basically correct, but "only probability of being correct, no numeric ranges" is too strong. In [Just Ask for Calibration (Tian et al., 2023)](https://aclanthology.org/2023.emnlp-main.330.pdf), §2, Table 1 and the prompt templates in Appendix C are indeed about the probability of being correct; Bahaj et al. have directly studied FinQA numeric intervals. | Full text |
| Numeric ability, significant figures and unit handling already have evaluations | Verified. NUPA's Sig_fig is rounding to a specified number of digits; [Learning to Plan by Updating Natural Language (Guo et al., 2024)](https://aclanthology.org/2024.findings-emnlp.589.pdf) Table 2 + Fig.18 (PDF p.24 / printed p.10085) has a significant-figure counting task with 197 examples; [BIG-bench Unit Conversion](https://github.com/google/BIG-bench/blob/main/bigbench/benchmark_tasks/unit_conversion/README.md) tests unit recognition, conversion and arithmetic. | Paper full text/appendix; repository text |
| Significant-figure rule evaluations in scientific QA, no specific reference for now | There is now a clear source: Vidhani & Mariappan 2024 §3.2/Fig.4, with a before/after prompt comparison, which already meets the task's broad criterion. | Full text |
| FinanceReasoning mentions difficulty with numeric precision | Checked by the same group under candidate 4: the example in §4.2 and Appendix B Table 9 is excessive rounding in an intermediate Black–Scholes step (5.44 vs 5.46), not propagation of filing input precision or a test of model-reported intervals. Candidate 3 does not add a separate citation of the same source. | Full text, cross-checked; see the candidate 4 attachment for details |

## 2026 follow-up work and reasons for exclusion

- **Full text**: [Yan, Miao & Huang (2026), Training Autoregressive Language Models on Rounded, Bounded, and Censored Numerical Labels via Exact Likelihood](https://arxiv.org/html/2611.02461v1); §§1–3, §6.1 and the appendix contents/limitations read. It models rounded observations as sets of compatible values and trains a distribution rather than imputing an arbitrary point; the experiments are synthetic distribution recovery, censored molecular measurements and code latency. So the general thesis "numeric labels should be sets" already has a direct precedent, but there is no prompt-behaviour comparison like this project's.
- **Full text**: [Piskorz, Kobalczyk & van der Schaar (2026), Eliciting Numerical Predictive Distributions of LLMs Without Autoregression](https://arxiv.org/html/2603.02913v1); §§2–3 and Appendix A Related Works read. Probes recover quantiles of the model's numeric output distribution from hidden representations; this is not propagating the deterministic rounding range of displayed numbers.
- **Repository text**: [CODATA DRUM-ML](https://github.com/codata/drum-ml); the README explicitly includes GUM uncertainty and significant-figure subtasks, but this is a design/example description of an experimental prototype. The example scorecard in the README was not treated as a verified experimental result; it cannot be used to claim that this project's experiment has been done.
- **Abstract, full text not obtained**: the student question-writing activity in [Outsmarting ChatGPT in Chemistry (2026)](https://doi.org/10.1021/acs.jchemed.5c01611) includes a significant-figures topic; [MeasureBench (CVPR 2026)](https://openaccess.thecvf.com/content/CVPR2026/papers/Lin_Do_Vision-Language_Models_Measure_Up_Benchmarking_Visual_Measurement_Reading_with_CVPR_2026_paper.pdf) involves valid answer intervals for instrument readings. Neither can be used to confirm or rule out the narrow precedent "evaluating model-reported precision against an exact interval ground truth"; both are kept as points for a later check.

## Limits that this project's wording must keep

Tracing back the citation chain: Yan et al. §2 points to [Spithourakis & Riedel (2018), Numeracy for Language Models](https://aclanthology.org/P18-1196.pdf). Its §3.3, Fig.2 and equations (9)–(11) (printed p.2107) were checked: a continuous numeric density is integrated over the range "displayed value ± half a last-digit unit" to obtain the probability of a numeric token, while the probability of the number of decimal places is modelled as well. This shows that probabilistic modelling of rounding intervals in language models did not first appear in 2026; its goal is generative modelling of numbers, not this project's experiment on input-rounding propagation and prompt behaviour. Source level: full text.

**Source level: local draft full text §6 (not an independent replication).** 98.4% corresponds to "interval width within a factor of two of the exact value", and 98.7% to "interval contains the exact range"; neither equals exactly identical endpoints. So the task summary's "98.4% give the correct/exact interval" overstates the result, and the novelty check cannot use that wording to manufacture a difference from prior work. This round only points this out and does not modify the short paper.

The narrow claim that can be pursued is: **use the feasible set derived from the displayed precision of the inputs as the basis for behavioural evaluation, and measure separately the natural output precision, the range coverage/width after an explicit question, and the reliable digits.** To develop this into a main contribution would require multiple datasets, multiple providers and strict endpoint/width metrics; merging it with candidate 1 into one measurement task would be more distinctive than once again claiming that "prompting elicits the capability". This is a research suggestion, not a conclusion proven by the novelty check.

