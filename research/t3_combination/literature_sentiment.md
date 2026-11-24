# T3 sentiment-combination prior-art check: financial sentiment and order-effect branch

Search date: 2026-11-16 (America/New_York). This is a bounded, targeted prior-art check, not a systematic review, and it does not claim to have taken half a day. No model scoring was executed.

## Charter

- Goal: check whether there is already a study of the same question with the same measurement, "single-fact scores → pairwise concatenation → addition, averaging, negative weighting and order reversal"; if found, recommend stopping the duplicate experiment.
- Scope / object / unit: LLM sentiment measurement / combinations of good and bad facts about the same entity / single-item and combined numeric scores, irrelevant neutral information, order effects.
- Type: exploratory; the measurement definition is understood, and no novelty is presumed about literature coverage.
- Q1: Has the same sentiment-integration measurement already appeared? Q2: What are the precedents for neutral dilution, negative asymmetry and order effects respectively? Q3: Which precedents can serve only as background?
- Sources: original paper full texts and appendices (1), full texts uploaded by authors (1, but with publication status marked separately); search snippets serve only as leads.

## Canonical sources

| Source | Parts checked | Use |
|---|---|---|
| Socher et al. (2013), [Recursive Deep Models for Semantic Compositionality Over a Sentiment Treebank](https://aclanthology.org/D13-1170.pdf) | §5.3, Figure 7, page 8 of the paper | Classic sentiment composition of contrasting clauses |
| Temkit (2026), [AMEL: Accumulated Message Effects on LLM Judgments](https://arxiv.org/html/2605.22714v1) | §3.1–3.4, §4.5, §9 | Negative asymmetry from LLM evaluation history; preprint |
| Alessa et al., [Quantifying Cognitive Bias Induction in LLM-Generated Content](https://www.jskirzynski.com/static/cognitive_bias_llm.pdf) | §4, §7.2, §7.4, Appendix A.6 | Sentiment drift in summaries and weighting towards early content; author full text |
| Mavillonio et al. (2026), [Measuring sentiment news with transformer-based language models](https://www.ecb.europa.eu/pub/pdf/scpwps/ecb.wp3283~df0633dfd3.de.pdf?495f4d0ec675f3cbda625976eb20dff3=) | Cover, abstract, Appendix A / Table A.1 | Explicit aggregation of sentence scores in financial news; ECB WP 3283, September 2026 |
| Liu et al. (2024 online; 2025 volume), [Longitudinal Sentiment Analysis with Conversation Textual Data](https://link.springer.com/article/10.1007/s40647-024-00417-0) | §4.2, §4.3.2–4.3.3 | Neutral dilution in arithmetic means and down-weighting of zeros |
| Rawat, Kang & Vardham (2026), [Beyond Accuracy: Adversarial Robustness and LLM Benchmarking for Financial Sentiment Analysis in Social Media](https://www.researchgate.net/publication/403468872_Beyond_Accuracy_Adversarial_Robustness_and_LLM_Benchmarking_for_Financial_Sentiment_Analysis_in_Social_Media) | §3, §5.1; full text uploaded by the authors on 2026-04-03 | Rules out a false collision caused by the title and the keyword "signal dilution" |

## Findings ledger

| # | Verifiable finding | Evidence, level | Answers |
|---|---|---|---|
| S1 | Socher et al. jointly examine clause and whole-sentence sentiment on 131 X-but-Y test cases, explicitly with the second clause carrying the main point. That study is trained sentiment classification and does not have T3's independent numeric baselines, averaging/adding comparison or paired double orders. | Socher §5.3 / Fig.7; 1 | Q1, Q3 |
| S2 | AMEL compares binary judgements of the same target under no history, 90% affirmative, 90% negative and 50/50 histories; the negative-history effect is stronger than the positive one. But its "neutral" is a history of half positive and half negative evaluations, not at all the addition of one sentiment-free fact. The author explicitly limits it to yes/no, code review / content moderation / diet judgements. | Temkit §3.1–3.4, §4.5, §9; 1 | Q2, Q3 |
| S3 | Alessa et al. compare whether three sentiment classes agree between the original text and the summary, and quantify content weighting with the embedding similarity between the summary and the first, middle and last thirds of the original. This is not scoring two separate facts and then estimating their numeric combination function. | Alessa §4, §7.2, Appendix A.6; 1 | Q2, Q3 |
| S4 | The ECB working paper first uses FinBERT to classify sentences in financial news, and then the researchers define several article-level indices. (pos−neg)/(pos+neg+neu), which includes neutral sentences, dilutes; indices that exclude neutral sentences do not. This comparison is an externally imposed aggregation rule, not a finding that a generative LLM averages on its own. | Mavillonio et al., Appendix A / Table A.1; 1 | Q2, Q3 |
| S5 | Liu et al. use sentimentr's lexicon-based sentiment extraction, state explicitly that including neutral zero scores in an arithmetic mean dilutes the overall score, and compare schemes that down-weight zeros. This is not an LLM behavioural experiment. | Liu et al. §4.2, §4.3.2–4.3.3; 1 | Q2, Q3 |
| S6 | What Rawat et al. call "signal dilution" is FinBERT/VADER scores staying unchanged after direction words are altered in long, multi-topic tweets; the LLM part is mainly a three-class classification comparison. No single/paired numeric scoring and no averaging/adding model selection were found. | Rawat et al. §3, §5.1; 1 (course-project author manuscript, not confirmed as peer-reviewed) | Q1, Q3 |

The core queries actually used include: `LLM sentiment analysis neutral information dilution effect negative positive order bias`; `large language models sentiment composition averaging positive negative information integration`; `"large language models" "dilution effect"`; `"sentiment" "order" "positive and negative" "large language models"`; `"LLM" "averaging" "sentiment" "neutral"`; `"LLM" "sentiment" "primacy" "recency"`; `"large language models" "negativity bias" "sentiment"`; `"sentiment" "compositionality" "LLMs" contrast`; `"sentiment" "dilution" "ChatGPT"`; `LLM "mixed sentiment" order effect`; `"sentiment" "neutral sentences" "language models"`; `LLM "positive and negative information" judgment`; `"financial" "sentiment" "compositional" LLM`; `"LLM" "sentiment" "conjunction" "but"`; `"sentiment" "concatenation" "large language models" bias`; `"sentiment" "mixed" "order reversal" model`; and exact-title searches for each candidate paper.

## Scope filter

Exclude "sentiment directions in neural activations are linear" as evidence that scores can be added; a linear representation and the combination function of a behavioural scale are not the same proposition. Also exclude multi-model ensemble averaging, changes in proportions in financial tweet streams and changes in model-generated sentiment as direct duplicates of T3.

## Object filter

S2's cross-item evaluation history is not the integration of facts within one headline; S3's summary selection is not numeric scoring; S4–S5 are aggregations defined by researchers; S6 is antonym substitution. None of them can on its own meet the stopping condition of "same question, same measurement". S1, on the other hand, is a direct reminder: semantic relations introduced by a connective change the overall sentiment, so dominance of the clause after `but` cannot all be called order bias. T3's `as` may also express cause or simultaneity; results with a fixed semicolon are easier to interpret.

## Conclusions

This branch did not confirm that T3's full set of measurements has been done; this cannot be used to declare that the literature gate failed, nor to declare that the topic is novel. (S1–S6)

"Averaging with neutral items dilutes" is itself a known methodological property; if T3 continues, the empirical addition may only be: whether a generative model under a fixed prompt spontaneously shows this regularity, and whether the regularity can explain combinations of independent facts. Negativity bias, order effects and dilution cannot be claimed in general terms as first discoveries. (S1–S5)

Hämäläinen (2025), [NLP4DH paper](https://aclanthology.org/2025.nlp4dh-1.18.pdf), checked separately by the root task, should be included in the root report: it has order reversal of lists of positive and negative adjectives and independent 1–5 scoring, and is a more direct precedent for T3's order branch. This note does not treat the root task's account as an independent check by this branch.

## Next steps / Risks

Enter the planned small experiment only if, after integrating the other branches, no identical measurement has been found; do not wrongly kill the not-yet-covered numeric-integration question because of the broad "order bias has long been known". The interpretation of the experiment should distinguish in advance within-sentence combination, batch influence, connective semantics and scale compression.

The original Zenodo full text of `Algorithmic Hesitation: Evaluating Confidence Drops in LLM Sentiment Analysis on Mixed-Emotion Text` has not yet been obtained; there is only an author-release lead, and no collision is judged from it. The FLUKE PDF timed out once; only the abstract was checked, and it was not used for the conclusions in the table above. Some search-engine dates are clearly wrong (the ECB page once showed ten years earlier); the September 2026 on the cover of the original is used.

Internal evidence check: the conclusions above are limited to the specific measurements checked in the full texts, and do not include re-running or independently reproducing the papers' experiments.
