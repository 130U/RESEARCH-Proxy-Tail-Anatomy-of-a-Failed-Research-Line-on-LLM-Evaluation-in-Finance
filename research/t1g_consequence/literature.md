# T1g novelty check and verification of two citations

Verification date: 2026-11-17. This file records only the novelty-check conclusion and source evidence; it does not replace this round's experiment.

## Charter

The goal is to decide whether a measurement identical to T1g Parts One and Two already exists, and to verify two papers still awaiting confirmation. The research scope is evaluation of financial and table question answering; the object is answer disagreement caused by the precision of filing disclosures; the specific research units are printed change vs. recomputed change, and the determinability of comparison conclusions. The type is a targeted literature novelty check with an explicit stopping condition. The knowledge starting point is the existing task description and the T1f report; T1f serves only as a search lead, and every substantive judgment below goes back to the original sources.

The questions are: Q1, are there existing statistics on natural change discrepancies in QA benchmarks; Q2, are there existing statistics on the uncertainty of comparison labels determined by input displayed precision; Q3, does FINESSE's common-failure number really appear in the original text; Q4, does 2611.02461 exist, and where are its research boundaries.

## Canonical sources

First rank: the authors' original texts, formal publications, and author-hosted full texts; second rank: the official XBRL specification; third rank: existing research in this repository, used only to find sources. Search-result snippets, aggregator sites, and blogs are used only for locating sources and do not support any technical conclusion on their own. Reading status and evidence level are written row by row in the table below.

This round ran 36 targeted search queries, covering FinQA/TAT-QA, printed/reported/recomputed change, rounding/precision/interval/uncertainty propagation/comparison, financial consistency checking, and table fact verification, and traced back along neighboring literature. What was actually completed is a bounded novelty check within this session; **it did not take half a day of wall-clock time, and it did not complete an exhaustive search of all citing works**. The full text of 2611.02461 and its Appendices A–F were read directly; the reading scope for the other sources is given below.

## Findings ledger

| ID | Verifiable fact and relation to this round | Evidence, reading scope, source level | Answers |
|---|---|---|---|
| F1 | FINESSE-Bench does report that 53 models jointly fail 9.33% and jointly succeed 22.41% on 1,147 FinQA questions. These are values reported by the paper; this round did not rerun the models. | [Authors' v2 full text](https://arxiv.org/html/2605.15482v2), §§5.1–5.3, 7.4 Table 8; also read [PDF page 16](https://arxiv.org/pdf/2605.15482v2#page=16). **Full text** | Q3 |
| F2 | 2611.02461 does exist; it treats rounded, interval, and censored labels as sets of compatible values and trains a digit-token model on event probabilities. | [arXiv original record](https://arxiv.org/abs/2611.02461), [v1 full text](https://arxiv.org/html/2611.02461v1), full text and Appendices A–F. **Full text** | Q4 |
| F3 | Disagreement between ratios printed in a filing and ratios recomputed from its tables already has direct examples and statistics at the level of company documents; "filings contain visible contradictions" cannot itself be claimed as a first finding. | Cao, Li, Luo, Yao, *Towards Automatic Numerical Cross-Checking: Extracting Formulas from Text*, WWW 2018, [author-hosted PDF](https://ping-luo.github.io/files/2018_Towards%20Automatic%20Numerical%20Cross-Checking%20Extracting%20Formulas%20from%20Text.pdf), §1, Figs.1–2, and the method/experiments. **Full text** | Q1 |
| F4 | Existing systems match the same KPI across full text and tables, taking unit, magnitude, and rounding into account during annotation. This is duplicate-disclosure matching, not a natural discrepancy rate for "two level values and a separately printed change" or a QA scoring consequence. | Hillebrand et al., *Towards automating Numerical Consistency Checks in Financial Reports*, 2022, [original](https://arxiv.org/pdf/2211.06112), §§I, III–IV, Fig.1. **Full text** | Q1 |
| F5 | There is existing research on classifying text–table KPI consistency in German financial documents; what it measures is KPI pairing and consistency-classification performance. | Ali et al., *Automatic Consistency Checking of Table and Text in Financial Documents*, 2023, [full text](https://d-nb.info/1280398930/34), §§3–5. **Full text** | Q1 |
| F6 | XBRL already builds rounding intervals of half a last-digit unit and uses interval intersection to judge sum consistency; therefore "point values are unequal" and "incompatible under the rounding model" must be kept apart. | [Calculations 1.1 official specification](https://www.xbrl.org/Specification/calculation-1.1/REC-2023-02-22+corrected-errata-2024-02-14/calculation-1.1-REC-2023-02-22+corrected-errata-2024-02-14.html), §§5.2–5.7. **Full text / specification** | Q1, Q2 |
| F7 | VeriFin binds operands to disclosed point values and then sets an output tolerance by disclosed precision; it does not treat all inputs as pre-rounding variables to find the feasible set of the target. | Hall, Shome, Eiers, *VeriFin: A Neurosymbolic Framework for Verifying LLM-Generated Financial Claims*, 2026, [v3](https://arxiv.org/html/2608.10213v3), §§3.5–3.6, 4, 6. **Full text** | Q1, Q2 |
| F8 | TabVer already proposes a set logic for numbers, quantifiers, and approximation, and runs numeric perturbation/rounding probes on FEVEROUS; its operations take point values and output a single number, and then handle the semantics of the claim. We saw no statistics on the flippability of comparison conclusions propagated from each input's last-digit unit. | Aly, Vlachos, *TabVer: Tabular Fact Verification with Natural Logic*, TACL 2024, [authors' full text](https://arxiv.org/html/2411.01093), §§3, 5, Appendix D. **Full text** | Q2 |
| F9 | CLEARFACTS/GRAYFACTS already list numeric precision and rounding as label ambiguity and compare model rankings before and after cleaning; the example is the judgment convention for 197.9 vs. "about 198". It is not an audit of comparison flips between two derived quantities on the same rounding box. | Seo et al., *Verifying the Verifiers: Unveiling Pitfalls and Potentials in Fact Verifiers*, COLM 2025; [read arXiv v2](https://arxiv.org/html/2506.13342) (2026-02-05), §§2–4, Appendix D.2 Table 17. **Full text** | Q2 |
| F10 | FinVerBench has already measured the performance drop when artificially injected errors are rounded to statement precision; Claude Sonnet 4's recall on 105 observable cases fell from 100% to 79%. What it studies is removing the decimal-format cue of the injected errors. | Panda, *FinVerBench: Benchmark Validity and Calibration in Large Language Model Financial Statement Verification*, 2026, [original](https://arxiv.org/html/2605.29586), §§3.3–3.4, 5.4, 6.4–6.6, Table 11. **Full text** | Q1, Q2 |
| F11 | Earlier numeric language models already integrated a continuous density over a number's rounding interval; "a number represents an interval" did not start with the 2026 paper. | Spithourakis, Riedel, *Numeracy for Language Models: Evaluating and Improving their Ability to Predict Numbers*, ACL 2018, [official PDF](https://aclanthology.org/P18-1196.pdf), p.2107 Fig.2, Eq.(9). **Full text** | Q4 |

## Scope filter

The neighbors above are kept; interpretations that treat "over-rounding in intermediate model steps", "final-answer tolerance", "weight quantization", or "injected numeric errors" as the same measurement are excluded. They show that rounding, numeric ambiguity, or errors in financial documents have been studied, but they cannot directly replace this round's statistics on two pre-registered denominators. In particular, F3 already directly shows in-document arithmetic disagreement, and F8–F9 already study judgment ambiguity caused by numeric approximation; these broad claims must not be passed off as new again.

## Object filter

F1's common-failure data are kept but limited to the authors' GPT-5.2 judge protocol; they cannot be called FinQA official execution accuracy, and the common-failure rate cannot be called a label-error rate. F2's view of set labels is kept, but label-event likelihood training is not equated with this project's propagation of input intervals. F3's result on 1,000 prospectuses is not a share of rounding impact in financial QA samples. F10 is a controlled artificial perturbation, not a statistic on natural rounding residuals in unmodified filings.

## Conclusions

**This round's novelty-check conclusion (one paragraph):** Within the 36 queries above and the original texts of the neighbors, we have not found the same measurement on a financial/table QA benchmark that counts "a change printed separately in the table disagrees with the result recomputed from the displayed level values, linked to that question's scoring"; nor have we found the same measurement that builds jointly feasible inputs from input displayed precision and counts whether derived-quantity comparison labels can flip. Therefore neither Part One nor Part Two triggers the task's stopping condition. This conclusion supports only continuing with the measurement; it is not a proof of being first in the world. Existing literature covers in-document arithmetic discrepancies (F3), filing consistency and rounding intervals (F4–F7), set semantics of approximate numbers and the effect of ambiguity on rankings (F8–F9), consequences of rounded rendering for detection (F10), and set-label learning (F2, F11); the remaining candidate must be narrowed to **the determinability of input precision in the original QA data and its concrete consequences**.

### FINESSE-Bench: verified

The title is *FINESSE-Bench: A Hierarchical Benchmark Suite for Financial Domain Knowledge and Technical Analysis in Large Language Models*. The authors are Dmitry Stanishevskii, Nini Kamkia, Alexey Khoroshilov, Dmitry Zmitrovich, Denis Kokosinskii, Zhirayr Hayrapetyan, and Andrei Kalmykov. arXiv 2605.15482, v1 2026-05-14; the v2 checked is dated 2026-05-21. [Original bibliographic record](https://arxiv.org/abs/2605.15482)

**Location in the original: §7.4 "Discriminative Power and Benchmark Saturation", PDF page 16, Table 8.** The short quotation from the full text on common failure is:

> "the share of questions that no model solves (unanimous fail)"

On the same page, the FinQA row in column order is **53; 1147; 9.33; 22.41; 24.15**: number of models, number of questions, common-failure percentage, common-success percentage, and the middle-band share where 10%–90% of models answer correctly. [Original Table 8](https://arxiv.org/pdf/2605.15482v2#page=16)

§5.3 explicitly uses GPT-5.2 for binary scoring of the question, reference answer, and model reply. So the statement "53 models, 1147 questions, common-failure statistics" holds; neither "these are all gold errors" nor "9.33% is the official rejection rate" follows from it. **Source level: full text.**

### arXiv 2611.02461: exists, and is directly related in concept

The title is *Training Autoregressive Language Models on Rounded, Bounded, and Censored Numerical Labels via Exact Likelihood*. The authors are Jingquan Yan, Yuwei Miao, and Junzhou Huang, University of Texas at Arlington; v1 was submitted on 2026-11-02. [Original record](https://arxiv.org/abs/2611.02461)

A short quotation from §1 states the meaning of a rounded label explicitly:

> "A measurement rounded to one decimal place and reported as 1.2 represents the interval [1.15,1.25)."

§3.2 and Table 1 write an observation as a set of compatible grid points; the objective in §3.3 is the negative log-probability of that set. §4 uses at most two boundary paths of a digit prefix tree to compute the event mass and gradient exactly; §5 also gives quantile, tail-probability, and CRPS computations. The experiments are synthetic distribution recovery, naturally censored hERG molecular measurements, and code latency with constructed timeouts, using two Qwen backbones; no FinQA/TAT-QA audit appears in the full text or appendices. Appendix A and B.3 restrict the setting to a finite grid, an ignorable reporting mechanism, and identifiability: coarse labels do not automatically identify the true distribution inside an interval. [Full text §§3–6, Appendices A–F](https://arxiv.org/html/2611.02461v1)

**Relation (our inference):** "rounded labels should be sets" can no longer be claimed as a unique contribution; that paper does not do this task's propagation of filing-operand intervals, change-discrepancy statistics, comparison-flip witnesses, or measurement of QA scoring consequences. It also gives no empirical guarantee for the independent uniform rounding assumption. **Source level: full text; the boundary with this project is our analysis.**

### The neighbor that most needs to be stated clearly: Cao et al. 2018

Fig.2 already places a table-recomputed share of **91.13%** next to a full-text printed **93.88%**; §1 says their system found numeric inconsistencies in 68.92% of 1,000 published Chinese prospectuses, rechecked by professionals. The paper's core is formula extraction and numeric cross-checking; it does not decompose this overall share into rounding-compatible discrepancies, let alone give a QA gold scoring denominator. [Authors' original §§1, 4–5](https://ping-luo.github.io/files/2018_Towards%20Automatic%20Numerical%20Cross-Checking%20Extracting%20Formulas%20from%20Text.pdf)

This source is enough to refute the broad claim that "no one has previously compared numbers in filing text with values recomputed from tables", **but it does not yet meet the task file's stopping criterion of the same measurement on a financial/table QA benchmark**. Whether there are consequences should still be decided by this round's pre-registered numbers.

## Next steps / Risks

Both parts can continue under the original task, with unchanged thresholds. The search used web search and the full texts of primary sources; it did not do a complete export of Scholar, Semantic Scholar, or the full set of citing works, so later work that was not read could still be prior work. This file does not claim to have used the full "half day". During reading we hit DOI 403 errors, institutional PDF timeouts, and missing PDF screenshot caches, and switched to author HTML or author/library-hosted PDFs; the core evidence for the two papers under verification comes from original texts that were actually opened.
