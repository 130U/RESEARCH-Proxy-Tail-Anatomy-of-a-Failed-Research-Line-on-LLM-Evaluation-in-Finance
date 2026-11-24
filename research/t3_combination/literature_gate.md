# T3 literature gate: allowed into a small experiment, cannot claim to be first

2026-11-16 (America/New_York). My research log for the certifiable financial language model has been read, from the initial certificate direction to the final absolute-scoring replication, and the repository's pinned task version 8b89b7d has been checked. The current task keeps the latest requirements "no training, no paid APIs, check prior art first, one-day screening"; the earlier certifiable-model route is not something this topic must complete.

## Charter

Goal: judge whether T3 is already covered by primary research on the same question with the same measurement; if covered, stop, otherwise only carry out a behavioural screen of the specified size. Scope / object / unit: financial LLM sentiment judgement / the combination of two pieces of information about the same entity / single-item calibration score, combination score, neutral addition and order reversal. The type is exploratory; the task design is understood, and literature coverage needs external verification. Q1 Has the same combination function already been measured? Q2 What is the precedent for neutral dilution? Q3 Are negative weighting and order effects new? Q4 What can the remaining empirical work answer?

## Canonical sources

Primary paper full texts and appendices come first, then author code and institutional documents; search snippets are used only to locate sources. Two branch notes record the specific queries and the boundaries paper by paper: [information integration](literature_integration.md), [financial sentiment](literature_sentiment.md). There is also a direct mathematical analysis, [design_notes.md](design_notes.md), which cannot replace the prior-art check.

## Findings ledger

| No. | Verified claim | Primary evidence | Question |
|---|---|---|---|
| F1 | Addition/averaging, moderate information reducing extremity, and averaging with an initial opinion are all existing theory and experimental paradigms. | Anderson (1971), [pp.181–182](https://fsnagle.org/files/anderson1971integration.pdf), original theory, level 1 | Q1/Q4 |
| F2 | There are already LLM experiments that reverse the order of positive and negative features and score each independently on a numeric scale; order effects themselves are not new. | Hämäläinen (2025), [§3–5, Tables 4/6](https://aclanthology.org/2025.nlp4dh-1.18.pdf), 200 sets of descriptions, 1–5 points, level 1 | Q3 |
| F3 | Financial news already has a dilution measure that includes neutral sentences, but the combination rule is specified explicitly by the researchers and cannot be used as evidence that a generative model averages spontaneously. | Mavillonio et al., ECB WP3283 (2026), [§3.2, Appendix A, Table A.1](https://www.ecb.europa.eu/pub/pdf/scpwps/ecb.wp3283~df0633dfd3.de.pdf?495f4d0ec675f3cbda625976eb20dff3=), level 1 | Q2/Q4 |
| F4 | Preferential retention of negative content, anchoring in financial trading, and negative asymmetry in cross-item evaluation history have been studied, but the outcome variable is not T3's combined sentiment score. | Original full texts listed in I4/I5 of the information-integration note and S2 of the sentiment note, level 1 | Q3/Q4 |
| F5 | Sentiment composition of contrasting clauses has classic experiments; the semantics of the connective changes the interpretation. | Socher et al. (2013), [§5.3, Fig.7](https://aclanthology.org/D13-1170.pdf), level 1 | Q1/Q4 |
| F6 | FLUKE compares classification robustness after small lexical/syntactic/discourse modifications; its sentiment task is SST-2 positive/negative binary classification, not estimating a pairwise combination function from single-item numeric scores. | Otmakhova et al., [§2, Appendix A.8](https://arxiv.org/html/2504.17311v3), level 1 | Q1/Q4 |

I checked the key passages of the originals for F1–F3 and F6; F4–F5 were checked by an independent search, with sources kept. No experiments from the literature were re-run.

## Scope filter

Exclude same-name results such as integrated information theory in consciousness research, attention dilution in long contexts, model weight averaging and copyright dilution. Human psychology experiments only provide existing theory and experimental paradigms; they do not directly prove that LLMs have the same mechanism.

## Object filter

Distinguish combination within a headline, other headlines in the same batch, preceding conversation, summary retention and human aggregation. F2 covers T3's order branch; F3 covers the mathematical properties of averaging with neutral items. Neither covers the core measurement "predicting, from independent single-item baselines, the score the model gives when it reads a two-item headline directly". F1 also shows that a simple two-item average is only a restricted baseline, and its failure cannot be used to reject all averaging theories.

## Conclusions

**Literature gate: continue with the small experiment of the specified size.** Among the sources checked, no duplicate of "the same core question and the same measurement" was confirmed; this cannot be used to prove that we are first. (F1–F6) The reason to continue is that there is still one clearly measurable increment, not that existing order/negativity biases have suddenly become a new finding.

The testable increment is limited to: the output combination rule of a fixed model, prompt and synthetic financial headlines; the focus is whether neutral addition spontaneously changes the score of a directional fact, and how large the prediction error of the restricted formulas is. A significant λ or a significant order effect alone is not enough to guarantee a paper contribution. (F2–F5)

Even if averaging fits better than addition, one cannot assert from this that a psychological averaging mechanism is used internally or that a profitable announcement-manipulation loophole has been found. Nonlinearity of the scale, contextual interaction between facts and other integration models remain competing explanations. (F1/F3/F5)

## Next steps / Risks

Complete the fixed small experiment of 3360 scores and 88 fresh sessions per [protocol.md](protocol.md); the main decision and figure are recomputed from the raw scores. The literature-gate decision precedes the new scoring, and the novelty standard is not modified in light of the effects that appear.

This was a multi-branch targeted prior-art check, with searches up to 2026-11-16; there is no claim of having spent half a day or of exhausting all databases. Full-text verification of the COLM impression-formation paper was blocked, Algorithmic Hesitation has only an author-release lead, and the PDF of the audit-dilution study timed out; none of these is used as a basis for a verified duplicate or for the absence of one. Where a search engine's date is wrong, the cover of the original is used. If an original that truly covers the core measurement is obtained later, the novelty positioning should be withdrawn and expansion stopped.
