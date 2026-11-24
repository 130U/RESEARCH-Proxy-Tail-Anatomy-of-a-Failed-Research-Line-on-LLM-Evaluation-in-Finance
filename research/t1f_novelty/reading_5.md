# Candidate 5 and root-agent cross-check reading list

Date: 2026-11-17. Each row distinguishes full-text reading, metadata and not obtained; different links to the same work do not count as separate studies.

| Title / source | Year | Link | Scope read | Relevance | Level and use |
|---|---|---|---|---|---|
| Serve only FinQA tasks whose reference agrees with the written answer | 2026 | [PR4](https://github.com/EnvCommons/FinQA/pull/4) | Problem, Fix, Decisions, Tests, all patches of the 3 files, merged code has_consistent_reference and load_finqa_data | 5, 4 | Full text / code; direct precedent |
| Grade FinQA answers at their stated precision and accept percent forms | 2026 | [PR2](https://github.com/EnvCommons/FinQA/pull/2) | Full PR text | 1, 5 | Full text; output scoring rule |
| Grade FinQA answers by a fixed 1% relative tolerance and state the required precision | 2026 | [PR3](https://github.com/EnvCommons/FinQA/pull/3) | Problem, Fix, rule comparison table, Tests | 1, 3, 5 | Full text; not input intervals |
| Credit FinQA amounts written with a scale word in the document's units | 2026 | [PR5](https://github.com/EnvCommons/FinQA/pull/5) | Problem, Fix, Numbers, Tests, Decisions | 5 | Full text; unit parsing |
| Description for the attributes in the data file | 2022 | [issue6](https://github.com/czyssrs/FinQA/issues/6) | Full text; the comments API returned empty | 5 | Full text; the 380/3.8 case |
| Possible incorrect gold answer/program for ANSS/2008/page_89.pdf-1 | 2026 | [issue15](https://github.com/czyssrs/FinQA/issues/15) | Full text | 4, 5 | Full text; a case about the denominator of an average |
| Official FinQA evaluate.py | 2021 project / current file | [Implementation](https://github.com/czyssrs/FinQA/blob/main/code/evaluate/evaluate.py) | str_to_num, eval_program, equal_program, evaluate_result | 1, 5 | Code; official scoring rule |
| GeneralReasoning/FinQA | 2026 | [Environment](https://openreward.ai/GeneralReasoning/FinQA) | Tasks, Reward Structure, Data, Repository | 5 | Full text; documentary corroboration that PR4 is now deployed, not an independent study |
| FinQAPT: Empowering Financial Decisions with End-to-End LLM-driven Question Answering Pipeline | 2024 | [Full text](https://arxiv.org/html/2410.13959) | §§4.1–4.5, focus on §4.5.1 | 4, 5 | Full text; the field conflict is already described in a paper |
| Gauging Overprecision in LLMs: An Empirical Study | 2025 | [Full text](https://arxiv.org/html/2504.12098) | §§3.1, 3.3, 4, 5 Table 4 (re-checked by the root agent) | 3 | Full text; the 3,262 come from the various splits, point ground-truth coverage |
| Optimizing Human–AI Collaboration in Chemistry: A Case Study on Enhancing Generative AI Responses through Prompt Engineering | 2024 | [Full text](https://www.mdpi.com/2624-8549/6/4/43) | §3.2 (re-checked by the root agent), publication metadata | 3 | Full text; small case of prompting for significant figures |
| Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents | 2026 | [Record](https://arxiv.org/abs/2609.00065) | Title, authors, date, version | Method attribution | Abstract / metadata; not used as novelty evidence |


## Additional reading along citation chains

| Title | Year | Link | Location actually read | Level and judgement |
|---|---|---|---|---|
| Evaluating LLMs’ Mathematical Reasoning in Financial Document Question Answering (Srivastava et al.) | 2024 | [ACL](https://aclanthology.org/2024.findings-acl.231.pdf) | §§2, 4/Table3, the relevant analysis in appendix A.3, metadata coverage and citation relations in A.4 | Full text; covers the full FinQA test, ConvFinQA dev and part of TAT-QA dev; precision errors refer to deviations in numeric calculation, which differs from input identifiability |
| Are ChatGPT and GPT-4 General-Purpose Solvers for Financial Text Analytics? A Study on Several Typical Tasks (Li et al.) | 2023 | [ACL](https://aclanthology.org/2023.emnlp-industry.39.pdf) | §3.5/Table8, ConvFinQA and FinQA in Appendix B, references | Full text; later evaluation and model arithmetic/reference errors; does not report input intervals or an inconsistency rate between the original fields |
