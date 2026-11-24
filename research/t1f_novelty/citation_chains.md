# Citation chains and exclusion judgements

Search date: 2026-11-17. Below are the relevant chains actually traced in this round. An arrow means the later work cites/uses the earlier work's data, or was traced from its references; **this is not a complete cited-by export**. Requests where native Scholar/S2 access was restricted are recorded in the queries files.

| Seed / chain | Post-2023 work checked and location | Role in the novelty check |
|---|---|---|
| FinQA → BizBench/CodeFinQA → FinanceReasoning | BizBench §4.1, A.2; FinanceReasoning §2.1, Table1, C.1 | Derived cleaning, cross-model complementarity, label quality and saturation; do not confuse 795 with 1147 |
| TAT-QA → BizBench/CodeTAT-QA → FinanceReasoning | Same as above; the 288-question split in FinanceReasoning | Error-correction mechanisms are not unique to FinQA; no input-rounding feasibility proportion seen |
| FinQA/TAT-QA → DocMath-Eval | §3.2–3.3 and appendix | Confirms re-annotation and removal of problem questions; a conflict rate between the two original fields must not be invented from it |
| FinQA/TAT-QA/ConvFinQA → Evaluating LLMs’ Mathematical Reasoning in Financial Document Question Answering (EEDP, 2024) | [§§2, 4, A.3–A.4](https://aclanthology.org/2024.findings-acl.231.pdf) | Meta-annotations and error causes for the full FinQA test, ConvFinQA dev and part of TAT-QA dev; C2 is numeric calculation deviation, not input-rounding uncertainty |
| FinQA/ConvFinQA → Are ChatGPT and GPT-4 General-Purpose Solvers for Financial Text Analytics? (2023) | [§3.5/Table8, Appendix B](https://aclanthology.org/2023.emnlp-industry.39.pdf) | Explicit model arithmetic and context-reference errors; shows that shared errors cannot automatically be attributed to labels |
| FinQA/ConvFinQA/TAT-QA → FINESSE-Bench (2026) | [§5.3, §7.4/Table8](https://arxiv.org/html/2605.15482v2) | Multi-model shared errors on the original 1147 FinQA questions already reported; judge-based scoring must be distinguished from this project's official program scoring |
| FinQA → Mavi et al. 2023; FinQAPT 2024 | The former D.2 Table7; the latter §4.5.1 | Direct precedents for FinQA error attribution and for the difference between the two answers |
| FinQA → Gauging Overprecision 2025 | §§3.3–5, appendix prompts | Numeric-interval answers on the same benchmark have already been evaluated, but the ground truth is a point |
| Significant-figure prompts → Chemistry 2024; Number Cookbook 2025 | §3.2/Fig4; appendix on the NUPA Sig_fig task | "Uses it once reminded" and basic significant-figure evaluation are not firsts |
| Displayed precision → Gittings 1991, XBRL 2023/2024 → VeriFin 2026 | Growth-rate full text; XBRL §§5.2–5.7; VeriFin §3.6 | Distinguishes input error propagation, interval consistency and final-answer tolerance |
| Constraint-based recovery → Dandekar 2010 → Salazar-González 2005 | pp.1161–1163; §§2, 5 | Linear relations + bounds + per-variable extremal programming already have technical precedent |
| Rounded labels → Yan et al. 2026 → Spithourakis/Riedel 2018 | Yan §2–3; the model part of the early numeric LM, see the group 3 reading list | Set labels / rounding-interval likelihood already exist as ideas and cannot be claimed as this project's general thesis |

Highly relevant but not retrieved: the full text of FinQA-fix in a Chinese journal, and the raw responses in the Chemistry supplementary tables; there are also abstract-level leads on MeasureBench and Outsmarting ChatGPT, see attachments 3/4. Not having obtained them does not mean they are irrelevant; the report does not use them to support a definite conclusion that "nobody has done it".
