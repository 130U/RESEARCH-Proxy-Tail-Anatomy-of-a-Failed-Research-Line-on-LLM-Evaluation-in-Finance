# T2 numeric perturbation in financial text: prior-art branch record

Search date: 2026-11-16 (America/New_York). This is one independent branch of the main conversation's prior-art check; it is not a systematic review, and no new model scoring was run. The conclusions cover only the material actually read below; no paper code was re-run.

## Charter

- Goal: judge whether T2's measurement of financial number magnitude versus sentiment score already has a substantively identical precedent; separate general number-understanding work from the target response curve.
- Scope / object / unit of comparison: model behaviour on financial text / number magnitude, expression and sentiment output / each paper's input intervention, output variable, curves and control conditions.
- Type: exploratory prior-art check; initial depth of knowledge: preliminary.
- Q1: What does T2 measure? Q2: Which parts already have a direct precedent? Q3: Do the remaining differences support continuing the original topic?
- Source order: the task definition; full texts and appendices of the original papers; formal publication metadata; search results only as leads.

## Canonical sources

| No. | Primary source and date | Actual access in this branch |
|---|---|---|
| S1 | Marks & Vollberg, [The psychophysics of affect in large language models](https://arxiv.org/abs/2610.40985), preprint v1, 2026-10-29 | Opened the [64-page PDF](https://arxiv.org/pdf/2610.40985); read the abstract, the stock-trading design in Methods, the model comparison in Supplement S2 and the prompts in S8; did not read every page of the choice-task appendices; did not run the data or code |
| S2 | Huang et al., [NASH: Numerically Aware Scoring Heuristic for Robust Semantic Similarity](https://aclanthology.org/2026.findings-acl.1119/), ACL Findings 2026, July | Opened the [15-page paper](https://aclanthology.org/2026.findings-acl.1119.pdf); read the numeric augmentation in §4, the evaluation definition in §4.4 and the model objects in §5.1 |
| S3 | Yang et al., [Measuring Consistency in Text-based Financial Forecasting Models](https://aclanthology.org/2023.acl-long.769/), ACL 2023, July | Opened the [15-page paper](https://aclanthology.org/2023.acl-long.769.pdf); read §3 and the definitions of the four types of transformation |
| S4 | Chen et al., [Enhancing Financial Sentiment Analysis with Expert-Designed Hint](https://arxiv.org/html/2409.17448v1), 2024-09-26 | HTML full text §3–5, limitations and references; also found a 2025 workshop version titled Numbers Matter; the two versions are not counted as independent evidence |
| S5 | Zhang et al., [Instruct-FinGPT: Financial Sentiment Analysis by Instruction Tuning of General-Purpose Large Language Models](https://arxiv.org/pdf/2306.12659), 2023-06-22 | Opened the 7-page PDF; read the task definition, the classification output and the description of the numerical sensitivity subset |
| S6 | Chen & Guo, [Shapley in Context: Explaining Financial Language with Domain Expertise](https://arxiv.org/html/2607.00856v1), 2026-07-01 | HTML §2–3, the FinBERT outputs and the definition of monotonicity; the [Duke publication record](https://scholars.duke.edu/publication/1915490) lists a formal journal version dated 2026-08-14 |
| S7 | Jo et al., [Change the Number, Change the Answer: Assessing Rating Scale Sensitivity in LLM-Based Text Scoring](https://arxiv.org/html/2610.22187v1), 2026-10-15 | HTML abstract, experimental design and definition of the rating scales; used only as a reminder about measurement confounds |

The above are authors' papers or formal publication channels, all rank 1 under this round's levels; for S6, only the metadata in the publication catalogue of the author's institution was verified.

## Findings ledger

| ID | Claim after verification | Location | Level / question |
|---|---|---|---|
| F1 | S1 already uses the percentage rise/fall of a stock as the input magnitude and expected feeling as the numeric output, and compares the positive and negative curves and context conditions. | S1 Methods, PDF pp.14–15; S8 p.46 | 1 / Q2 |
| F2 | S1's Study 2 uses the same 20-point grid to cover rises and falls, with outputs from −50 to +50; it compares fits such as linear, power-function and saturating tanh. | S1 Methods, S2 (PDF p.30), S9 (p.48) | 1 / Q2 |
| F3 | S1 reports diminishing marginal sensitivity and amplification on the gain side when items are scored separately; when presented jointly the curve is more linear. This shows that the magnitude curve, the up/down asymmetry and the scoring context are not questions nobody has measured. | S1 abstract, Methods, S2 | 1 / Q2, Q3 |
| F4 | NumFinE changes the magnitude of numbers in fixed financial sentences, but evaluates whether semantic similarity ranks by numeric distance, not financial sentiment intensity. | S2 §4.2, §4.4; PDF pp.5–6 | 1 / Q2 |
| F5 | FinTrust's four types of test are negation, word-order symmetry, adding irrelevant text and entity substitution; it cannot be treated as a study of rewriting equivalent numeric units. | S3 §3.1, PDF p.4 | 1 / Q2 |
| F6 | S4 compares whether numeric hints improve three-way classification of financial social media and groups by number category; S5 also uses numerical sensitivity for classification evaluation. Neither builds a T2-style continuous input response curve. | S4 §3–5; S5 §3–4 | 1 / Q2 |
| F7 | S6 proposes axioms such as monotonicity for Shapley attribution; its examples change the tone of words, and its theoretical axioms cannot be equated with a measured number-magnitude curve. | S6 §3.1–3.2 | 1 / Q2 |
| F8 | S7 manipulates the format, range and sign of the output rating scale, including on a sentiment task; it is not an input-amount experiment, but it shows that the rating scale must be fixed or controlled for separately. | S7 §2.1, §3 | 1 / Q3 |

## Prior-art matrix

"Not seen" refers only to the relevant methods and results checked in this branch; it does not prove that no supplementary analysis exists anywhere in the paper.

| Comparison item | Original T2 | S1 psychophysics | S2 NumFinE | Other finance studies |
|---|---|---|---|---|
| Fixed linguistic frame, changing numbers | Yes | Yes, amounts / stock percentage changes | Yes, counterfactuals of real financial sentences | S4/S5 mainly classify subsets of natural data |
| Number magnitude → continuous affect score | Yes | **Direct overlap** | No, semantic similarity | Not seen |
| Positive/negative direction and comparison of curve shapes | Yes | **Direct overlap**, also studies context | Numeric-distance ranking, not positive/negative sentiment | No identical curve seen |
| Entity sentiment of company news | Yes | No, the shareholder's expected feeling | No | S4/S5 are financial sentiment classification |
| 10 / 50 / 100 local thresholds | Yes | No local-breakpoint design for this question seen | Not seen | Not seen |
| Unit expressions of the same amount/proportion | Yes | No equivalent-unit contrast seen | Magnitude changes, not equivalent-unit invariance | FinTrust does not do this transformation |
| Repeated scoring / presentation-context controls | Yes, mixed filler headlines | **Independent / memory / joint presentation conditions already exist** | Not the same measurement target | S7 warns of output-scale confounds |

## Scope filter

Narrow "financial number understanding or invariance has already been studied" into three different questions: whether the number is read correctly, whether semantic distance preserves order, and how the sentiment output changes with magnitude. Drop the initial impression that "FinTrust has already done numeric unit rewriting"; the full text does not support it (F5). NumFinE cannot be used as evidence that the sentiment curve has been done (F4).

## Object filter

S1's output is the model simulating a shareholder's feeling, not T2's entity sentiment of company news; so it supports "the main experimental logic and the candidate phenomena already have a direct precedent", not "all three sets of T2 experiments have been completed as is". S1's function fits and context effects are very close to T2, but they do not prove that all modern models have the same curve on all financial templates (F1–F3).

## Conclusions

1. **Recommend stopping further investment in the original T2 as a new general behavioural-phenomenon topic.** The most important pieces, the number-magnitude → affect response curve, marginal sensitivity and positive/negative asymmetry, have already been measured in S1 in a financial setting; switching only to profit/fine headlines or shifting the rating scale is not enough to show a new contribution. The original T2 file does not yet specify a scale. This is a research-positioning judgement based on F1–F3, not a factual claim of a "complete item-by-item collision".
2. **Keep the precise residual question "local thresholds × equivalent representations × entity sentiment", but this branch has no evidence certifying its novelty.** It needs to be combined with the other branches' checks on the left-digit effect and unit invariance; one cannot infer from this branch's non-detection that nobody has done it.
3. **If a narrow topic is set up later, the measurement target must be distinguished.** Entity semantic sentiment, simulated investor feeling, price prediction and embedding similarity should not be mixed; at the same time fix the output rating scale and add controls between independent inputs and mixed batches (F4–F8).

## Next steps / Risks

- In this round, following my research priority "stop the same day if substantively similar work is found", we do not recommend entering the formal scoring of the original T2; the main conversation integrates the branches for the final judgement.
- Log-linearity is not a natural standard of correctness. If event risk, a finite upper bound on the score or the prompt scale leads to saturation, failure to follow some curve alone cannot be used to judge that numeric understanding is wrong. This is design analysis in this report, not an existing experimental result.
- Some search leads could not be accessed in full text: Battle of transformers (journal page and SSRN 403); ConFIT (OpenReview verification page). They are not used as decisive evidence for stopping the original topic. The old OpenReview page of NASH was also blocked by verification, but verification was completed with the formal ACL full text.
- Not all theses, paywalled full texts or every author's code repository were searched; no exhaustive forward tracing in citation databases was done. There is no claim that "half a day was actually used up" or that the prior-art check is exhaustive.
- Self-check result: key facts have locations in the original full texts; the conclusion is limited to "overlap of the core logic" rather than complete duplication. Paper code was not re-run; authors' interpretations in the sources were not treated as results we have reproduced.

## Search record

Public web search was used, and among the results arXiv, ACL Anthology and paper publication pages were opened first. Actual queries included:

1. financial sentiment analysis numerical perturbation numbers magnitude large language models
2. "financial" "sentiment" "numerical" "sensitivity"
3. "language models" "sentiment" "magnitude" numbers
4. "9,227" "numerical" "financial"
5. "financial sentences" "controlled numerical"
6. "financial sentiment" "perturbations" numbers
7. "Battle of transformers" Leippold pdf
8. "NumFinE"
9. "Battle of Transformers" "Leippold" (some second-hand catalogues excluded)
10. financial sentiment numerical perturbation magnitude monotonicity benchmark
11. LLM financial sentiment "numbers" "change" "monotonic"
12. language model "profit" "sentiment" "magnitude"
13. financial sentiment "unit" "invariance" language models
14. "NASH: Numerically Aware" ACL 2026
15. "Shapley in Context" financial language
16. "financial sentiment" "numerical perturbation"
17. "sentiment" "magnitude" "psychophysics" language models
18. "financial sentiment" "numbers" "counterfactual"
19. "numerical sensitivity" "sentiment" language models

The specific arXiv identifier of S1 was referred from a parallel branch; this branch then independently opened the PDF to verify the overlap above. The unit-invariance source 2609.25009 was passed to the corresponding branch and is not written up as a conclusion of this branch.
