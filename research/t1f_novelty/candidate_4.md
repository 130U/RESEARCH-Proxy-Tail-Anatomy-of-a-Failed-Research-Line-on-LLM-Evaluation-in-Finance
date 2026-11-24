# Candidate 4: the rejections fall on the same questions

Search cutoff: 2026-11-17. The verdict uses the three "or" criteria in the task file and does not narrow the criteria ad hoc to requiring, all at once, the original test set, the latest models, an intersection matrix and a large-scale human audit.

**Conclusion: someone has already done the same thing; suggested ⚪; confidence high.** FINESSE-Bench already reports the shared failure rate of 53 models on the full 1,147-question FinQA test set; there are also a classification of the causes of FinQA rejections, a before/after comparison of revisions to financial derived benchmarks, and a per-question cross-model complementarity analysis on CodeFinQA. The specific "63 questions wrong in all four runs, Jaccard 0.89–0.93, 55/68 attributed to the benchmark side" can still be a new empirical result, but being "the first cross-model shared rejection on the full original test set" can no longer be kept. No equally strong conclusion that independently attributes the majority of shared errors to the benchmark side by human review has been found yet; this is the boundary of the remaining increment.

## The three closest works and short quotations from the originals

### 4A. FinanceReasoning (Tang et al., ACL 2025)

[Formal paper](https://aclanthology.org/2025.acl-long.766/); [formal PDF](https://aclanthology.org/2025.acl-long.766.pdf); [full text and appendix HTML](https://arxiv.org/html/2506.05828v1). Location: §1, §2.1, Table 1, Appendix C.1 (Tables 10–14); in the formal version, Table 1 and the introduction are on printed p.15722, and Appendix A/C.1 on p.15734. Source level: **full text**. The formal PDF was downloaded directly to re-check the key numbers, not relying only on arXiv v1.

> "are saturated due to annotation quality"

Its re-annotation scope is **CodeFinQA test 795**, not the original FinQA test 1,147; the others are CodeTAT-QA test 288, FinCode test 47 and FinanceMath validation 200. In Table 1 the CodeFinQA revisions are 55 answers (6.92%) and 58 disambiguations (7.30%), 113 in total (14.21%). The four revisions together are 208/1,330≈15.6%, with a range of 9.72%–30%. The introduction (p.15722) and Appendix A (p.15734) of the **formal ACL version** still give the number of source questions as 1,420, which is inconsistent with the table total and with 2,238−908=1,330; citations should use the table's denominator and must not copy 1,420. This inconsistency was not corrected in the formal version.

The update actions include disambiguation, adding solution steps and error correction; the appendix also distinguishes unsolvable, ambiguous wording, overly brief steps, wrong answers and lenient scoring. It compares the accuracy of two DeepSeek models before and after revision, but no per-question shared-rejection matrix was seen. It also changed the scoring convention at the same time, so the score increase cannot be attributed entirely to the label revision.

**Judgement on remaining novelty:** fine-grained error causes and independent human adjudication can serve as an incremental audit; "annotation quality limits older financial benchmarks" has been stated explicitly, and shared errors on the full original test set also already have the precedent below.

### 4B. FINESSE-Bench: A Hierarchical Benchmark Suite for Financial Domain Knowledge and Technical Analysis in Large Language Models (Stanishevskii et al., 2026)

[Author's original v2](https://arxiv.org/html/2605.15482v2); [PDF](https://arxiv.org/pdf/2605.15482v2); [author's data](https://github.com/LimexAILab/FINESSE-Bench/blob/main/data/finqa/question.jsonl). Location: §5.1–5.3, §7.4 Table 8 (PDF p.16); v2 dated 2026-05-21. Source level: **full text and original public data**.

> "the share of questions that no model solves (unanimous fail)"

Table 8: FinQA, **53 models, 1,147 questions, unanimous failure 9.33%, unanimous success 22.41%, middle band where 10%–90% of models are correct 24.15%**. This round also compared the authors' question.jsonl line by line with the official FinQA test.json: all 1,147 questions match in the same order, and every author reference answer equals the string of the original qa.exe_ans; so the correspondence to the full test set has been verified, not inferred only from the count. The check summary is in the [data identity check summary](data_identity_check.json). Its format was converted and it uses GPT-5.2 as the judge throughout, so its scores cannot be equated directly with official execution accuracy.

This directly meets the criterion "per-question cross-model comparison on FinQA, shared rejection set". The paper uses this result for discrimination and saturation analysis; **it does not prove that 9.33% is the label error rate**, nor does it provide a human causal audit attributing most shared errors to the benchmark side. Our Jaccard and the specific attribution still leave room for an increment, but the full test set, recent multi-vendor models and the shared-failure phenomenon itself are no longer a gap.

### 4C. Retrieval-Augmented Chain-of-Thought in Semi-structured Domains (Mavi, Saparov, Zhao, NLLP 2023)

[Formal paper](https://aclanthology.org/2023.nllp-1.18/); [formal PDF](https://aclanthology.org/2023.nllp-1.18.pdf); [full text and appendix HTML](https://arxiv.org/html/2310.14435). Location: Appendix D.2, Table 7; the formal PDF was downloaded and page 9, i.e. printed p.186, was verified. Source level: **full text**.

> "Error analysis of the incorrect examples on 40 samples from FinQA."

Of 40 constructed validation samples, 30 are correct; the remaining 10 were classified by hand as arithmetic 3, logic 2, annotation 2 and retrieval 3. So an explicit attribution of FinQA rejections with counts already exists (annotation errors are 2/10 of this batch of errors); the sample is small and is not the full original test set. It meets the task's second precedent criterion, but it does not support "most of the remaining errors come from the benchmark". If our stronger proportion is independently verified by humans, it is an increment in the strength of the conclusion.

## Additional directly related work

### BizBench: A Quantitative Reasoning Benchmark for Business and Finance (Krumdick, Koncel-Kedziorski et al., ACL 2024; preprint 2023)

[Formal record](https://aclanthology.org/2024.acl-long.452/); [formal PDF](https://aclanthology.org/2024.acl-long.452.pdf); [full text HTML](https://arxiv.org/html/2311.06602). Location: §4.1 (the per-question complementarity paragraph is on printed p.8315), Appendix A.2, Appendix B Table 5. Source level: **full text**. The formal venue is indeed ACL 2024, full text pp.8309–8332; the bibliography follows the ACL record, and the order of the two co-first authors differs between the PDF and arXiv.

> "Models pretrained on language-only versus code solve different sets of questions."

On CodeFinQA, Llama-2-70B gets right 33% of the questions CodeLlama-34B gets wrong, 25% in the other direction, and the oracle combination of the two reaches 68%. This is already a per-question cross-model error overlap/complementarity analysis, only on a derived version. Its 50+25+25 wrong outputs are further classified by extraction, formula, generation and question ambiguity; categories may overlap, so the columns cannot be added as independent samples. The full text discusses difficulty with the sign semantics of gain/loss. A.2 converts FinQA equations to Python and checks the executed answers; one cannot conclude from this that it audited the conflict rate between the original answer and exe_ans.

**Judgement on remaining novelty:** changes in the structure of model errors over time can still be compared, but shared failures of recent models also already have the FINESSE precedent; added value must come from a finer audit of causes.

### Other papers read

- **FinQAPT (Singh, Kaur, Smiley, ICAIF 2024)**: [§4.5.1](https://arxiv.org/html/2410.13959). Source level: **full text**. It already gives an error analysis of FinQA by question, context, calculation, etc., with approximate proportions, and discusses percentage/numeric conventions and differences between the execution answer and the given answer. The only short quotation is "disparities between the execution answer and the provided answer". This is also a directly relevant precedent for candidate 5; no overall inconsistency rate between the two fields, and no data pipeline filtering on it, was seen.
- **Do Large Language Model Benchmarks Test Reliability? (Vendrow et al., 2025; Platinum)**: [§2.1–2.2, Appendix B](https://arxiv.org/html/2502.03461). Source level: **full text**. Its 15 benchmarks do not include FinQA. Its cleaning method has several models answer and then manually checks the questions where at least one model is wrong, to separate wrong labels from bad questions. Methodologically very close; it also stresses that model failures remain after repair, so "several models wrong together" alone cannot prove a label is wrong.
- **Confidently Wrong (Wang, 2026, v2 2026-10-13)**: [§3, §5.2, §6](https://arxiv.org/html/2607.11414). Source level: **full text**. Uses the FinQA **training set** distributed by FLARE and TAT-QA; when validating the scorer it reports about 4%–6% residual label noise and convention ambiguity, and it studies cases where eight samples give the same answer and are still marked wrong. It is not an audit of cross-model shared errors on the original test set, and it does not prove that most remaining errors come from the benchmark.
- **Collaborative LLM Numerical Reasoning with Local Data Protection (Zhang et al., preprint 2025 / AAAI 2026)**: [Error Analysis / Table 4](https://arxiv.org/html/2504.00299v2). Source level: **full text**. Search snippets easily give the impression that its 23.3% annotation-error/ambiguity rate refers to FinQA; the full text states clearly that it is **MultiHiertt, Phi3, 30 error cases**, so it is not used as direct evidence for FinQA.

## Item-by-item check of the similar ideas given in the task

| Given claim | Result of the check (all based on full text; exceptions are stated explicitly) |
|---|---|
| FinanceReasoning revised four datasets, 15.6%, 9.72%–30% | Holds; the exact range, the denominator and the fact that it is not the original FinQA test set are in 4A. It explicitly discusses annotation quality and saturation, but this cannot be extended to "the remaining errors on the full original FinQA are mainly attributable to the benchmark". |
| Northcutt et al. 2021, label errors in ten test sets | Holds. [§3 Table 1, §4–5, Appendix A](https://arxiv.org/html/2103.14749) cover ten image, text and audio datasets, with an average of at least 3.3%; no FinQA. It is a precedent for general method and motivation. |
| MMLU-Redux and Platinum cleaning work | Holds. [Gema et al. NAACL 2025 formal record](https://aclanthology.org/2025.naacl-long.262/); [§2–3, Appendix F full text](https://arxiv.org/html/2406.04127) re-annotated 5,700 questions, distinguishing ambiguity, no correct option, multiple correct answers, wrong ground truth, etc. Platinum's scope and method are given above. Neither is a FinQA audit. |
| DocMath-Eval screened/re-annotated FinQA-derived questions | Holds. [§3.2–3.3, appendix](https://arxiv.org/html/2311.09805) explicitly re-annotates FinQA, TAT-QA, etc.: it removes wrong or non-numeric questions, adds scale notes, corrects questions, rewrites Python solutions and verifies evidence. No error rate reported against the original FinQA denominator was seen. |
| BizBench screened/re-annotated FinQA-derived questions | Partly holds; the code rewriting and validation of execution results hold, see the BizBench paragraph above. The paper did not fully re-review all data by hand (Limitations). |
| FinanceMath also cleaned FinQA-derived questions | **Does not hold / not supported by the original.** [§2.2–2.4](https://arxiv.org/html/2311.09797) has experts write new questions based on financial concepts or adapt textbook/web questions, with 674 of 1,200 adapted; FinQA-derived cleaning is not a construction step. |
| FinQA experts about 91%, implying a ceiling | The number is 91.16%, which holds; "so there is a ceiling of about 9% label noise" does not hold. [FinQA §4.3, Table 2](https://aclanthology.org/2021.emnlp-main.300.pdf) is the mean execution accuracy of two external experts on 200 random questions, and cannot separate expert mistakes, annotation errors and ambiguity. |

## Highly relevant leads whose full text has not yet been retrieved

**Li Xi et al. (2025), "An automatic question-answering method for table-text hybrid financial data based on positive and negative chain-of-thought examples" (Chinese-language paper, title translated), *Journal of Chinese Information Processing* 39(7).** [Journal page](http://jcip.cipsc.org.cn/article/id/zwxxxb_3951), [journal PDF](https://jcip.cipsc.org.cn/cn/article/pdf/preview/zwxxxb_3951.pdf). **This round only obtained the abstract index and second-hand descriptions**: [SinoMed](https://www.sinomed.ac.cn/article.do?ui=2025477889), [second-hand lead](https://research.elamur.ai/free/en/papers/li-2025-positive-negative-chain/). The second-hand source says the authors built FinQA-fix, revised nearly 20% of the answers and listed seven error types, including sign; these numbers have not been verified against the original and do not enter any definite judgement. The journal web request timed out, the shell HTTPS connection was reset, and HTTP returned a network-error HTML page. The full text should still be retrieved manually as a priority, in particular to check the revision denominator, the test-set scope and the sign category. Even if this lead ultimately does not hold, the full texts already read are enough to judge candidate 4 as ⚪.

## Implications for this project (this round's judgement, not a literature fact)

Keep this result as a motivation and data-audit attachment; the claim should be narrowed to "on the specified models, prompts and sample, the residual rejections are highly concentrated and, after review, are attributed to a number of reference or convention problems". Shared errors alone cannot be used to infer that the models have no common weakness; the existing 392-question stratified sample, same-provider models and AI judge are not enough to extrapolate to the full test set. Whether it can still independently support a short paper depends on new findings after the full test set, other vendors and human review; for now candidate 4 alone should not serve as the centre of novelty.
