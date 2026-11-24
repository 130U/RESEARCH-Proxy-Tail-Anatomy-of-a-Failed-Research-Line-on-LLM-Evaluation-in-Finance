# Candidate 3 full-text reading ledger

Date: 2026-11-17. Only sections actually read are listed as "read"; supplementary material that was not obtained does not count as read. The source level "full text" includes formal paper full texts, appendices or author repository texts; the latter two are stated explicitly.

| Title | Year | Link | Parts actually read | Relevance and handling |
|---|---|---|---|---|
| Optimizing Human–AI Collaboration in Chemistry: A Case Study on Enhancing Generative AI Responses through Prompt Engineering | 2024 | https://doi.org/10.3390/chemistry6040043 | §2, §3.2, Fig.4, §4; supplement S6–S8 not obtained | 3, decisive precedent under the broad criterion |
| Gauging Overprecision in LLMs: An Empirical Study | 2025 | https://arxiv.org/html/2504.12098v1 | §§2–5; appendices A–D, focus on the ground truth in §3.3, the data in §4, Table4 | 3, FinQA numeric-interval outputs; point ground truth rather than a rounding feasible set |
| Number Cookbook: Number Understanding of Language Models and How to Improve It | 2024 first version / 2025 ICLR | https://arxiv.org/html/2411.03766v3 | §2; appendices A.1.3–A.1.4, A.2, A.3 | 3, formal significant-figure rounding task |
| Learning to Plan by Updating Natural Language | 2024 | https://aclanthology.org/2024.findings-emnlp.589.pdf | Method paragraphs in §3, §4/Table2; appendix Fig.18 (p.10085) | 3, significant-figure counting and the effect of prompt plans; no interval ground truth |
| Just Ask for Calibration: Strategies for Eliciting Calibrated Confidence Scores from Language Models Fine-Tuned with Human Feedback | 2023 | https://aclanthology.org/2023.emnlp-main.330.pdf | §§1–2, Table1, appendix B temperature fitting and C prompt templates | 3, background on verbal calibration of the probability of being correct |
| Training Autoregressive Language Models on Rounded, Bounded, and Censored Numerical Labels via Exact Likelihood | 2026 | https://arxiv.org/html/2611.02461v1 | §§1–3, §6.1; appendix structure/limitations, experimental appendix not checked item by item | 1/3, interval numeric labels and training; not a FinQA behaviour audit |
| Eliciting Numerical Predictive Distributions of LLMs Without Autoregression | 2026 | https://arxiv.org/html/2603.02913v1 | §§2–3; appendix A Related Works | 3, probes for numeric uncertainty of the model's output distribution |
| BIG-bench Unit Conversion | Project documentation, accessed 2026-11-17 | https://github.com/google/BIG-bench/blob/main/bigbench/benchmark_tasks/unit_conversion/README.md | Full repository README, focus on Subtasks, Behavior, Limitations | 3, evaluation of unit handling, not rounding-interval propagation |
| CODATA DRUM-ML | Project documentation, accessed 2026-11-17 | https://github.com/codata/drum-ml | Repository README, benchmark/uncertainty and scorecard context | 3, design of an experimental prototype; its example scorecard was not verified as measured |
| Numeracy for Language Models: Evaluating and Improving their Ability to Predict Numbers | 2018 | https://aclanthology.org/P18-1196.pdf | §3.3, Fig.2, equations (9)–(11), relevant passages of §3.5–4 and §5.2–6 | 3, followed the Yan 2026 citation chain to verify rounding-interval integration and modelling of decimal places; not a prompt-behaviour audit |

Full texts not obtained (not counted in the full-text reading above): Outsmarting ChatGPT in Chemistry (2026), doi:10.1021/acs.jchemed.5c01611; MeasureBench (CVPR 2026); the anonymous OpenReview version of Gauging Overprecision that came up in the search (404).

Among the known ideas, the FinanceReasoning precision example was checked in full text by the candidate 4 group; this ledger does not take credit for that full-text reading.

