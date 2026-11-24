# T3 information integration and dilution effects: targeted prior-art note

Searches up to 2026-11-16 (user's time zone). This note answers only the literature gate; no model scores were generated, and there is no claim of having used half a day or completed a systematic review.

## Charter

- Goal: verify whether the same question and measurement as T3 already exist, distinguishing theoretical precedents, nearby behavioural studies and direct duplicates.
- Scope / object / unit: LLM judgement behaviour / integration of positive, negative and neutral information / the functional relation between single-message baselines and combined-message scores.
- Type: exploratory. The task design is known; literature coverage is to be checked.
- Q1: Has the Anderson adding/averaging framework already been applied to LLMs in the same way? Q2: Has neutral-information dilution been measured directly? Q3: What measurements of negativity dominance exist? Q4: Which results truly cover T3?
- Sources: original papers and full texts from authors/publishers are the first tier; search snippets are only leads, and are not used as proof that "it has not been done".

## Canonical sources

| Source | Scope checked | Use |
| --- | --- | --- |
| Norman H. Anderson (1971), *Integration Theory and Attitude Change*, Psychological Review 78, 171–206: [original PDF](https://fsnagle.org/files/anderson1971integration.pdf) | Full text accessible; focus on pp.175–176, 181–182, 188 | Theoretical precedent for adding/averaging, initial impression, scales and weights |
| Mavillonio et al. (2026), *Measuring sentiment news with transformer-based language models*, ECB WP 3283: [institutional PDF](https://www.ecb.europa.eu/pub/pdf/scpwps/ecb.wp3283~df0633dfd3.de.pdf?495f4d0ec675f3cbda625976eb20dff3=) | §3.2, pp.11–12, Appendix A pp.34–38; 45-page full text accessible | Nearest neighbour for financial sentiment aggregation and neutral dilution |
| Julien Benchek (2025-01-08), *Large Language Models Exhibit Cognitive Biases in Interactive Stock Trading Scenarios*: [university-hosted manuscript](https://bpb-us-w2.wpmucdn.com/voices.uchicago.edu/dist/9/3887/files/2025/01/Benchek_SRF24_Final_Paper.pdf) | §2.1–2.6, §3–4; 10-page full text accessible | Behavioural precedent for negative/positive anchoring in a financial setting; this manuscript is not described as peer-reviewed |
| Acerbi & Stubbersfield (2023), *Large language models show human-like content biases in transmission chain experiments*, PNAS 120(44), e2313790120: [original PDF](https://www.pnas.org/doi/pdf/10.1073/pnas.2313790120) | Results experiments 2 and 4, Methods; 5-page full text accessible | Differences in retention of positive, negative and neutral information in summaries |
| Park, Schoenegger & Zhu (2024), *Diminished diversity-of-thought in a standard large language model*, Behavior Research Methods 56, 5754–5770: [publisher full text](https://link.springer.com/article/10.3758/s13428-023-02307-x) | Methods, Results, the descriptions corresponding to Table 1 | Nearby psychological measurements of less-is-better and order questions |

All of the above are original studies / theoretical papers by the authors; having the full text does not mean every appendix and all code have been reviewed.

## Findings ledger

| No. | Claim supported by the evidence | Exact source | Level / question |
| --- | --- | --- | --- |
| I1 | In human information integration, comparing adding with averaging, and adding more moderate information to reduce extremity, have long been explicit experimental paradigms. | Anderson (1971), p.181, "Averaging versus Adding" | Original theory, Q1 |
| I2 | "The more information of the same value, the more extreme the judgement" can also be explained by an averaging model that includes an initial opinion. A simple two-item average does not represent the full Anderson framework. | Anderson (1971), pp.181–182, "Averaging versus Adding / Averaging Assumptions" | Original theory, Q1/Q4 |
| I3 | Financial news already has sentiment indices built from FinBERT single-sentence classification and then aggregated explicitly by the researchers; an averaged index that includes neutral sentences dilutes polarity, while an index that excludes neutral sentences behaves differently. | ECB WP 3283, §3.2; Appendix A pp.34–38: `index_stat=(pos-neg)/(pos+neg+neu)` | Original study, Q2/Q4 |
| I4 | A GPT-4o mini trading study has already compared changes in sell prices caused by positive/negative market news and by irrelevant weather/mood anchors, and reports that several negative anchors have larger effects. | Benchek (2025), §2.4, §3 pp.7–8 | Original study, Q3/Q4 |
| I5 | In ChatGPT's iterative summaries, it has already been measured that negative content is retained more easily than positive content; there is also a comparison of retention of threat, negative and neutral content. | Acerbi & Stubbersfield (2023), Results experiments 2 and 4; Fig.2B/2E | Original study, Q3/Q4 |
| I6 | GPT-3.5 has been used to replicate the less-is-better psychology experiment, but that experiment compares the generosity of gifts of different categories; it does not merge single positive/negative messages and then predict a sentiment score. | Park et al. (2024), Methods, Results; Table 1 study 12 | Original study, Q1/Q4 |

Open item: this targeted search has not yet verified any LLM paper that has all of "same-entity single-fact baselines + positive/negative / same-direction / neutral pairs + direct scoring of combined headlines + comparison of adding / averaging / negative coefficient". This sentence describes the search result and cannot be upgraded to proven priority.

## Scope filter

Results that conflate Anderson's **information integration theory** with **integrated information theory** from consciousness research were excluded; the latter does not answer this question. Also excluded were works with the same names but different objects, such as attention spreading over long contexts, training-data dilution, copyright market dilution and averaging of multi-model votes.

Human dilution effects provide hypotheses and identification methods, but do not prove that LLMs show the same mechanism. Negative retention in summaries, sell prices and direct sentiment scores are different outcome variables and cannot stand in for each other.

## Object filter

- **I3 is closest in domain, but is not a direct collision.** The ECB paper's combination function is specified by the researchers; T3 aims to infer the model's own combination function when it reads combined text. Seeing that an external averaging formula is diluted by neutral sentences does not mean the LLM's endogenous averaging has been measured.
- **I4 is closest on financial negativity bias, but the measurement differs.** It compares changes in trading decisions under different single anchors; it does not use single-item sentiment scores to predict two-item sentiment scores, and does not estimate T3's combination coefficient λ.
- **I5 already rules out the general statement "LLMs favour negative information is a new finding".** It does not identify combination weights for the sentiment of financial headlines.
- **I6 cannot be used to claim that neutral-message dilution has been done.** Manipulating the evaluability of gift categories is different from adding neutral sentences in this task.

## Conclusions

1. Among the sources checked by this branch, **there is no stopping evidence reaching "the same question and the same measurement"**; the adding/averaging models and the concept of dilution themselves have long existed (I1–I3). This is not a guarantee of novelty.
2. If we continue, the contribution can only be a reproducible measurement on a specific model, prompt and combined financial headlines; it cannot be called "the first discovery of information averaging" or "the first discovery of LLM negativity bias" (I1, I4, I5).
3. The three formulas of T3 should be explicitly called restricted candidate baselines. Even if same-direction combinations are more extreme, this cannot rule out all averaging models; averaging with an initial opinion is a competing explanation that must be acknowledged (I2).
4. A regression towards 50 caused by neutral addition would at most first support a dilution phenomenon under this scoring task. Without a given decision goal and a correct aggregation rule, it cannot be declared a financial loophole directly; external financial indices already have different conventions for handling neutral items (I3; this point is a research judgement).

## Next steps / Risks

Search boundary: public English web searches, using combinations of terms such as `large language models information integration theory Anderson`, `LLM averaging model judgments`, `ChatGPT dilution effect`, `LLM impression formation`, `LLM less-is-better effect`, `language models negativity dominance`, `LLM negative information positive information averaging` and `sentiment neutral sentences dilution`, and tracing to the most recent originals. No systematic review covering all databases was done, not all citation chains were read, and author code was not checked.

Restricted lead: the search index shows that Tak, Bolourani, Shank & Gratch, COLM 2025, [*Impact of LLM Alignment on Impression Formation in Social Interactions*](https://openreview.net/pdf?id=R135tO3SJJ) compares ACT with LLM impressions in social interactions, but reading the OpenReview full text hit a browser verification. This round only saw the abstract of the original source, and does not assert from it that the full text has no relevant experiment. The original abstract's object is gendered social interaction, not financial headlines. The ACL 2026 *HumanLLM* PDF could not be opened because the file was too large, so its list of bias names cannot be treated as verified experiments.

Result of this note's internal evidence check: the narrow claims I1–I6 above are supported by readable originals; "no exact duplicate found yet" must keep its search boundary; whether T3 produces an effect is still to be tested by experiment, and this document does not fill in any estimates or intervals.
