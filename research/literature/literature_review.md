# Literature verification and research differences

Date: 2026-11-15 (America/New_York) · Internet access: yes · Search cutoff: 2026-11-15 · Status: first-round verification of key items, not a complete systematic review.

## Charter

Goal: check whether the mathematical components of P1/P2 already exist, and whether the remaining differences are enough to justify research investment. Scope / object / specific unit: certifiable financial language models / information sets and numeric sensitivity / theorems, threat models, input representations and audit assumptions of the original papers. Mode: exploratory; look for veto evidence first, and do not conclude originality from "found nothing".

Questions: Q03 and Q29 concern how residual mislabelling propagates to models and statistics; Q10, Q13 and Q31 concern hard structural guarantees; Q30 concerns sampling audits; Q32 concerns parsing certificates. Q01, Q02, Q12 and Q14 provide necessary background; the other questions remain open in this round.

## Canonical sources

Ranking: full text of the original paper / material formally released by the authors (rank 1); official XBRL International specification guides (rank 2); the initial plan (hypotheses to be verified). Only primary sources that were actually opened are used to support the table below. Search snippets serve only to locate sources. No data were requested from sec.gov; SEC counts, fields, licences and historical availability times were not verified in this round.

## Findings ledger

| ID | Verified claim | Source, version and location | Level | Related |
|---|---|---|---|---|
| L01 | Look-ahead freedom can be stated as temporal non-interference; the author explicitly treats model weights as a black box, and bringing the model's pre-training cutoff date into the certificate is still a next step | [Fonseca, 2607.04958v1](https://arxiv.org/html/2607.04958v1), 2026-07-06, §9 limitations | Full text, rank 1; preprint | Q03 |
| L02 | Deterministic partitioned training, stable hashing and vote margins give poisoning-robustness certificates; the original threat budget is counted as a symmetric difference of sets | [Levine & Feizi, DPA, 2006.14768v2](https://arxiv.org/html/2006.14768v2), 2021-03-18, §3.2, Theorem 1, Appendix A; ICLR 2021 | Full text, rank 1 | Q03/Q29 |
| L03 | Finite Aggregation extends DPA with overlapping subsets; the effect of a single contaminated item on several base classifiers must be counted according to its design | [Wang et al., 2202.02628v1](https://arxiv.org/html/2202.02628v1), §3; published version ICML 2022 | Full text read is v1, rank 1 | Q29 |
| L04 | Joint poisoning of bagging can be written as a BILP that bounds the number of predictions changed at the same time; there is also hash bagging | [Chen et al., 2205.13176v2](https://arxiv.org/html/2205.13176v2), 2022-09-06, §3–4, Appendix B; ICML 2022 | Full text, rank 1 | Q29 |
| L05 | A Lipschitz network plus a linear residual enforces monotonicity in specified coordinates; this is an existing architecture | [Kitouni et al., 2112.00038v2](https://arxiv.org/html/2112.00038v2), 2023-03-15, §2.1–2.2 | Full text, rank 1 | Q10 |
| L06 | More general expressive monotone networks use weight constraints and a single residual; ICLR 2023 | [Kitouni et al., 2307.07512](https://arxiv.org/abs/2307.07512), 2023-07-14 | Abstract, rank 1 | Q10 |
| L07 | Dimensionless features achieve exact unit equivariance; the basic method is constructed from dimension-zero monomials | [Villar et al., 2204.00887v2](https://arxiv.org/html/2204.00887v2), §4, Appendix; [JMLR 24(109)](https://www.jmlr.org/papers/v24/22-0680.html), 2023 | Full text, rank 1 | Q13 |
| L08 | Hypergeometric confidence sequences for sampling without replacement already have an anytime-valid construction | [Waudby-Smith & Ramdas, 2006.04347v4](https://arxiv.org/html/2006.04347v4), §2; NeurIPS 2020 | Full text, rank 1 | Q30 |
| L09 | Weighted financial audits without replacement can use a test martingale and can incorporate unreliable side information | [Shekhar et al., 2305.06884v1](https://arxiv.org/html/2305.06884v1), 2023-05-08, §2–4 | Full text, rank 1 | Q30 |
| L10 | Distributions that change in stochastic order with covariates are an existing statistical object | [Henzi, Ziegel & Gneiting, 1909.03725v3](https://arxiv.org/html/1909.03725v3), 2021-09-28, §2; JRSSB 2021 | Full text, rank 1 | Q31 |
| L11 | xVal multiplies a placeholder embedding by the numeric value and then feeds it into the transformer trunk | [Golkar et al., 2310.02989v2](https://arxiv.org/html/2310.02989v2), 2024-12-15, §2.1 | Full text, rank 1 | Q10/Q12 |
| L12 | In iXBRL, scale is a power-of-ten scaling; the negative sign is expressed through sign, and displayed parentheses cannot be the only basis | [Inline XBRL Part 0: Primer 1.1](https://www.xbrl.org/WGN/inlineXBRL-part0/WGN-2026-07-14/inlineXBRL-part0-WGN-2026-07-14.html), 2026-07-14, §4, §5.9–5.10 | Full text of the official working group guide, rank 2; not a complete implementation specification | Q14/Q32 |
| L13 | FiNER's numeric labels depend on context; fragmentation of numbers into subwords affects performance | [Loukas et al., 2203.06482v2](https://arxiv.org/abs/2203.06482), 2022-04-19; ACL 2022 | Abstract, rank 1 | Q14/Q32 |
| L14 | TAT-QA combines extraction from tables and text with symbolic computation | [Zhu et al., ACL 2021](https://aclanthology.org/2021.acl-long.254/) | Abstract, rank 1; QA scores not treated as parsing accuracy | Q32 |
| L15 | DatedGPT uses year-by-year crawl-date filtering; its instruction generation also uses modern models and vocabulary restrictions | [Yan et al., 2603.11838v2](https://arxiv.org/html/2603.11838v2), 2026-07-23, §2–3 | Full text, rank 1; preprint | Q01/Q02/Q03 |
| L16 | Chronologically Consistent LLMs are an existing direction of time-restricted training | [He et al., 2502.21206v3](https://arxiv.org/abs/2502.21206), 2025-07-06 | Abstract, rank 1 | Q01 |
| L17 | Scale-equivariance-based fine-tuning already exists for VLMs; its abstract reports approximate equivariance and does not give the hard certificate for financial text that this work needs | [Tan et al., 2609.00658v3](https://arxiv.org/abs/2609.00658), 2026-10-04 | Abstract, rank 1; preprint | Q13/Q24 |

## Scope filter

Delete the inference "moving it to a financial application constitutes a theoretical innovation": L02–L10 already cover each main mathematical component. Delete the inference "zero findings mean no contamination": an audit only produces a confidence conclusion under the specified sampling model. Delete the inference "probability calibration proves that a given prediction is correct". Keep the certificate chain as a way of organizing the work, but the union-bound composition itself is not a new theorem.

## Object filter

Correct "P2 must be trained from scratch": as long as the input numbers do not bypass the constrained channel, the text encoder can be an existing frozen model; its pre-training history does not affect mathematical monotonicity with respect to the current input. If the historical-information constraint of P1 is also required, the training sources must be audited separately. Correct "xVal can be plugged directly into T2.2": the trunk in L11 depends on the numbers, so using it directly cannot satisfy c being independent of g. Correct "an authoritative timestamp means correctness with probability zero of failure": it needs binding to the content version, the semantics of availability time, withdrawals/revisions, and the extraction and crawl process; it is currently still a conditional assumption.

## Conclusions

1. **P1 is a promising combination study whose novelty is not yet proven.** L01 does not address contamination of model weights; L02–L04 already address the basic components of poisoning and collective robustness; L08–L09 already address the statistical foundations of auditing. The remaining candidate is the computable connection, and its tightness, of "temporal source assumptions—audit budget—contamination influence—fixed backtest statistic interval", not the first proposal of any one component.
2. **The basic theorems of P2 cannot be packaged as original.** L05–L07 and L10–L11 already cover monotonicity, dimensional analysis, stochastic order and continuous number representations. The researchable questions are when financial semantic specifications are reasonable, how to strictly isolate the numeric side channel, how parsing errors enter end-to-end guarantees, and whether it is still needed compared with symbolic/ordinal-regression baselines.
3. **The G1 novelty evidence only reaches "partly existing, differences not exhausted".** There is no evidence supporting a high-confidence conclusion of "no similar work found". Nor can it be used to judge both main lines as complete failures; forward/backward citation tracking for narrower differences still has to be completed.
4. **Finite-corpus auditing is a transfer of mature statistical techniques.** L08–L09 already provide sequential and side-information tools; the scaling of the rule of three cannot stand alone as a new theoretical contribution.

## Next steps / Risks

- First check, for Q03/Q29, the 2023–2026 poisoning certificates for generative models and language models, and the unlearning/stability routes; this round did not exhaust them.
- Define the clean comparator with an explicit bounded statistic, to avoid passing off a counterfactual empirical interval as a guarantee for the future population.
- Add "frozen text model + hard head" and "purely symbolic/ordinal regression" baselines to P2; if both are enough, withdraw the narrative that training from scratch is necessary.
- Under the offline boundary of this round, real-source verification is not carried out; it can continue with lawful local materials or a changed boundary. No conclusions are currently given on annual EDGAR counts, accepted semantics or licences.
- Run a whole-tuple error audit of the parser on independent real samples clustered by company/report; FiNER label accuracy or TAT-QA QA scores cannot substitute for it.
- All 2026 papers are judged by the version read; a preprint's journal template is not taken as a claim of formal acceptance.

## Search record and boundaries

**Stop record:** during this round I decided not to contact outside parties and to do the research locally. From that point all new network requests were stopped immediately; answers after that point cite only primary materials retrieved before the stop and local derivations. No authors were contacted, no emails sent, nothing posted, and no research materials sent to third parties. Unverified subquestions remain marked as incomplete and are not filled in by additional internet access.

Searches were run on 2026-11-15; keywords included `Deep Partition Aggregation Levine Feizi`, `Look-Ahead-Freedom as Temporal Non-Interference`, `financial language certified monotonic numeric`, `language model units equivariance`, `ordinal regression stochastic dominance cumulative link monotonic`, `Collective Robustness Certificates`, `confidence sequences sampling without replacement`, `FiNER-139`, `TAT-QA`. The original papers in the table above were opened from the relevant results; the newly found L04, L09, L10 and L17 expand the original candidate set. No forums or automatically generated reviews were used to support conclusions.

Access limits: the NeurIPS 2020 PDF timed out once, so the arXiv full text was read instead; the JRSSB IDR page could not be read, so the authors' arXiv full text was read instead; McCullagh's author PDF opens but its text could not be extracted, so this round does not list it as a closely read full text. The JMLR 22-0689 tried first is an unrelated article and was excluded; the correct source is 22-0680.

"Partly complete" on the key answers already written means that unverified sub-items remain within the question, not that the whole question is complete.
