# T2 prior-art check on psychophysics and numeric representation

Search date: 2026-11-16 (America/New_York). This file is an independent literature branch; no model scoring was executed, no authors' experiments were reproduced and nothing was uploaded.

## Charter

- Goal: answer Q2 "does T2 already have a substantively identical study?" and Q3 "are the remaining differences enough to support continuing the original topic?"
- Scope / object / unit: LLM numeric behaviour / score curves induced by amounts and proportions / magnitude, positive/negative direction, thresholds, equivalent units and repeated measurement.
- Type: exploratory prior-art check; authors' reports are kept strictly separate from any measurements reproduced in this round.
- Criterion: compare the manipulated variables, output construct, functional form and control conditions; similar paper titles do not mean the same topic.

## Canonical sources

| Priority | Primary source | Date and extent of reading |
|---|---|---|
| 1 | Marks & Vollberg, [The psychophysics of affect in large language models](https://arxiv.org/abs/2610.40985); [PDF](https://arxiv.org/pdf/2610.40985) | Preprint of 2026-10-29; the methods, results, Fig. 3, Table 2 and supplementary tables S1 and S4 in the full text were verified, not just the abstract |
| 1 | Atta-Duncan, [Same Quantity, Different Answer: Numerical Representation Invariance in Language Models](https://arxiv.org/html/2609.25009v1) | The original page is dated 2026-07-27, yet the identifier is 2609; the metadata discrepancy is kept and not corrected by us. Full text §§3–5, 8–9 verified |
| 1 | Cacioli, [Weber's Law in Transformer Magnitude Representations](https://arxiv.org/html/2603.20642v1) | Preprint of 2026-03-21; §§3.3–3.4, 4.2–4.3 verified |
| 1 | Shah et al., [Numeric Magnitude Comparison Effects in Large Language Models](https://aclanthology.org/2023.findings-acl.383/); [PDF](https://aclanthology.org/2023.findings-acl.383.pdf) | Findings of ACL 2023, 2023-07; the object of study and methods in the full text verified |
| 3 | [Marks & Vollberg author repository](https://github.com/joeamarks/Psychophysics_of_Affect_in_LLMs) | Verified that the repository exists, is public and has default branch main; code not executed, data not independently recomputed |

## Findings ledger

| ID | Verifiable finding | Location | Relation |
|---|---|---|---|
| P1 | Marks & Vollberg's Study 2 already measures the positive and negative curves from stock price percentage changes to affect scores. Its question is first-person expected feeling, scored from −50 to +50; related to company-news sentiment but a different construct. | PDF pp.14–15, Tasks and stimuli; Fig.3 p.9 | Q2: strong overlap on the curve / positive-negative direction |
| P2 | A fixed set of 20 magnitude points covers 0.2–12; Study 1 uses pounds sterling and Study 2 uses percentages. 30 independent call sequences per model × condition; compares independent prompts, previous scores placed in context, and joint scoring in the same prompt. The stock experiment covers only gpt-5-nano and kimi-k2.5. | PDF pp.12–16 | Q2: repetition and context controls already have precedent |
| P3 | The stock experiment reports diminishing sensitivity and a stronger gain side, with joint scoring close to linear; its power-function fit is not T2's three-way choice of linear / log / saturating. The paper does not give T2's 9.9/10.1 local thresholds or an experiment changing units at equal quantity. | PDF Fig.3, Table 2, pp.17–18 | Q2: partial substantive coverage; not all experiments match |
| P4 | Same Quantity tests five families of equivalent transformations, including units, percentages and scientific notation, with 3,600 exact-rational math word problems and 8,600 prompts; it evaluates five open-weight systems. | HTML §§3–4 | Q2: the unit-invariance method already has a strong precedent |
| P5 | That paper distinguishes parser rejections from numeric errors; unit errors are concentrated in particular models and templates. The main experiment makes one greedy request per prompt, which cannot stand in for T2's comparison of sentiment score differences against retest noise. | HTML §§5, 8 | Q3: identifies alternative explanations, limits extrapolation |
| P6 | The Weber paper fits linear, log and power-law hidden-layer geometry, and does number comparison and digit/unit-boundary controls; the author states explicitly that log geometry does not guarantee the same behavioural performance. | HTML §§3.3–3.4, 4.2–4.3 | Q2: not a sentiment curve; cannot be used to judge a complete collision |
| P7 | The ACL 2023 paper studies distance, size and ratio effects in embeddings of number words / Arabic numerals, mapped to human reaction times through a linking hypothesis. | PDF pp.1–3 | Q2: prehistory at the representation level, not a financial sentiment measurement |

## Scope filter

Exclude the inference from "numeric representations are logarithmic" to "financial sentiment scores must be logarithmic" (P6–P7); representation geometry, task choice and affect scoring are different outputs. Exclude replacing the positive/negative asymmetry of sentiment scores with the loss-aversion parameter from gain/loss choices. Web abstracts were used only for locating sources; the conclusions use the original full texts that were opened.

## Object filter

Rephrase P1–P3 as "a strong precedent for the core curve and the asymmetry", not as T2 being fully done: first-person feeling differs from third-person news sentiment, a fixed set of 20 points differs from 25 log-spaced points, and the original paper did not test T2's thresholds and unit conditions. Rephrase P4–P5 as "a precedent for invariance to equivalent representations", and do not pass off math word-problem accuracy as a sentiment effect. Keep P6–P7 only as design input.

## Conclusions

1. **The broad contribution of the original T2 is not enough to continue the project as "the first discovery of a magnitude response curve / gain-loss asymmetry".** The preprint of 2026-10-29 has already drawn the relevant curves in a stock-percentage context and manipulated the comparison context (P1–P3). This is the most important stop-loss evidence.
2. **There is no evidence to declare that "the three experiments are each completely identical".** This branch did not confirm that local jumps in financial news near 9.9/10.1, or the effect of million/billion and percent/basis-point rewrites relative to retest noise, have been completed in the same study (P3–P5).
3. If the main task adopts the strategy "stop once the core is found to have been done", the original experiment should be stopped, and the company-news construct, thresholds and units should only be listed as differences for a possible re-launched topic; these differences by themselves are not yet verified novelty. To keep a new topic, one must first explain why third-person financial evaluation differs from existing affect scoring, and propose a falsifiable mechanism that goes beyond "change the template and draw the plot again" (P1–P7).

## Next steps / Risks

- Complete the overall verdict with the financial-text search results; this branch's "not found" does not establish absence across the whole field.
- The authors' stock results come from only two models; they should not be generalised across models, prompts or versions. Their gateway model snapshots and effective temperature have reproducibility limits that the authors state explicitly (Marks & Vollberg, Methods).
- Monotonicity can only be interpreted after fixing the entity's scale, the financial baseline and a reasonable value domain; extending a profit fall beyond 100%, or treating the number of layoffs directly as the intensity of shareholder loss, changes the economic meaning. These are design judgements, not yet experimental findings.
- Comparisons of equivalent representations should verify the input, the parsing and the actual semantics separately. A parse failure caused by unit conversion and a change in sentiment response are not the same phenomenon (P5).

## Search boundary and record

Web search was used, followed by going back to the original papers:

1. `large language models numerical magnitude psychophysics Weber Fechner law sentiment`
2. `large language models left digit bias price numerical magnitude`
3. `large language models unit invariance numerical framing financial sentiment`
4. `"large language models" "left-digit"`
5. `"large language models" "unit" "invariance" numbers`
6. `"language models" "loss aversion" magnitude`
7. `"language models" "numerical" "sentiment" "curve"`
8. `"LLM" "left-digit bias"`
9. `"language models" "unit invariance"`
10. `"LLM" "round numbers" bias pricing`

In addition, arXiv:2610.40985, 2609.25009, 2603.20642 and ACL:2023.findings-acl.383 were verified directly. News retellings, aggregator sites and studies of rounding-output preferences found in the search were not used as empirical evidence for jumps at input thresholds. There is no claim of having used half a day or of an exhaustive systematic review; the search was wrapped up after finding a near neighbour sufficient to change the project decision.
