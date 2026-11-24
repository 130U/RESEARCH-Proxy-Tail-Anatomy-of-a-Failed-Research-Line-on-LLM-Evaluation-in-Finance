# T2 prior-art decision: stop the original project, keep an unverified narrow question

Date: 2026-11-16 (America/New_York). **Conclusion: drop the original T2 as an independent novel topic; this round does not enter the scoring experiment.** The reason is that the core response curve and the positive/negative asymmetry already have strong precedents, not that we measured "the model behaves well". We cannot yet claim that all three experiments have each been done.

## Charter

- Goal: check the boundary of T2's contribution and give a continue/drop judgement before entering model scoring.
- Scope / object / unit of comparison: LLM numeric behaviour / the numeric-to-sentiment mapping of financial headlines / for each study, the input intervention, the scoring construct, the response curve, thresholds, units and retest controls.
- Type: exploratory prior-art check. At the start there was only an outline of the topic; after reading my research log, the task statement and the primary literature, a working understanding was reached.
- Q1: What were the original task and the earlier constraints? Q2: What already has substantive precedent? Q3: Is the remaining difference enough to support continuing the original version?
- Acceptance: decisive sources verified down to the full text; distinguish full duplication, core overlap and methodological adjacency; record open questions and actual execution status.
- Boundary: T2 only. Follow this round's requirement "check prior art first, stop as soon as it is found"; do not carry over the exception under which the old topic was later allowed to continue with a replication.

## Canonical sources

| Priority | Source | Use / extent of access |
|---|---|---|
| 1 | My research log for the certifiable financial language model | Read back to the beginning, checking each phase conclusion; historical conclusions do not replace this round's literature check |
| 1 | The T2 task statement | Original task, as frozen before this check |
| 1 | Marks & Vollberg, [The psychophysics of affect in large language models](https://arxiv.org/abs/2610.40985), 2026-10-29, preprint | Full text verified twice independently; I re-checked the methods, results and supplementary model comparison in the [PDF](https://arxiv.org/pdf/2610.40985) |
| 1 | Atta-Duncan, [Same Quantity, Different Answer](https://arxiv.org/html/2609.25009v1), preprint | Full text §§3–5, 8 read; the original web page date is 2026-07-27, which does not match the month in the identifier; not corrected by us |
| 1 | Near neighbours on financial numbers and magnitude representation | Primary sources, extent of access and reasons for exclusion are in the two files [finance prior-art check](finance_prior_art.md) and [psychophysics prior-art check](psychophysics_prior_art.md); these are not additional independent replications |
| 3 | [This round's design audit](design_audit.md) and [the old experiment's conclusion](../absolute_scoring/ONE_PAGE.md) | Local design analysis and historical record; not regarded as new T2 measurements |

## Findings ledger

| ID | Finding / judgement | Evidence location and nature | Answers |
|---|---|---|---|
| F1 | T2 combines the magnitude curve, round-number thresholds, equivalent representations and directional asymmetry; the condition for continuing is that any anomaly exceeds twice the retest noise. | Task sections "method / analysis / decision"; source fact, level 1 | Q1 |
| F2 | The continuous affect curve corresponding to stock price changes and the positive/negative asymmetry have already been measured. | Marks & Vollberg, Fig.3, Table 2, PDF pp.14–15; authors' report, level 1 | Q2 |
| F3 | That study also compares scoring contexts and function shapes; "switch to a financial context and draw the curve again" is not enough to distinguish T2. | Same paper, Methods, supplement §S2; the first half is a source fact, the second half a contribution judgement | Q2–Q3 |
| F4 | First-person feeling is not the same as third-person company-news sentiment; the studies read do not cover T2's fine-grained thresholds and the full set of amount-rewriting experiments. | Task definition of the same paper compared with T2; a difference judgement limited to the material read | Q2 |
| F5 | Equivalent numeric representations and unit invariance have methodological precedents, but math-question accuracy is not the same as a sentiment score difference. | Same Quantity, §§3, 5, 8; source fact and applicability judgement, level 1 | Q2 |
| F6 | Studies of number embeddings, numeric classification and text similarity cannot automatically count as duplicates of T2's continuous sentiment response. | Verification against the originals and object comparison in the two prior-art branches; methodological judgement | Q2 |
| F7 | T2's units, thresholds and economic semantics are not yet fully isolated, and the noise and multiple-testing rules also need to be defined further. | design_audit.md; independent design analysis, level 3 | Q3 |
| F8 | The formal conclusion of the old absolute-scoring experiment was inconclusive, and it cannot be used as evidence that the T2 phenomenon holds. | Last round of the research log and the absolute-scoring one-page summary; historical record, level 1/3 | Q1 |

Open: it has not been confirmed that anyone has fully executed the combination "company headlines × local round-number breakpoints × equivalent units × retest noise"; nor has it been shown that this combination has an independent scientific contribution. Not finding the full combination in searches does not mean it is novel.

## Scope filter

Reject the inference "there is literature on LLM numeric ability, so every numeric-sentiment study is a duplicate" (F5–F6). Arithmetic correctness, embedding geometry, choice preferences and sentiment scoring are different objects. Anomalies reported in papers also do not automatically indicate wrong financial decisions, still less imply tradable returns.

## Object filter

Narrow "a complete collision with existing work" to "the core measurement logic and the proposed finding overlap strongly" (F2–F4). Keep the open space of the third-person news construct and thresholds/units; do not count changing the model, the company names, the number of points or the scoring range as a contribution in itself. The stop recommendation follows my topic-selection standard of screening out duplicated directions first; it is not proof that every sub-question has no value.

## Conclusions

**Decision: stop the original T2 as a novel project and stop the original scoring plan.** If we now measured a nonlinear curve or an up/down asymmetry, that finding alone would not pass the prior-art check; it is no longer a result that sufficiently distinguishes us from existing work (F1–F4). Following this round's stop-loss requirement, we do not launch the full set of calls to reproduce a known phenomenon.

| T2 part | Prior-art judgement | Implication for the current decision |
|---|---|---|
| Magnitude response and curve shape | Strong core overlap; the specific construct and fitted families differ | Curve shape alone is not enough to support the original version as a novel project |
| Positive/negative asymmetry | A directly adjacent measurement already exists in a financial setting | No longer an independent reason to "continue" |
| 10 / 50 / 100 local thresholds | No study with the same structure was confirmed in this round | Open; cannot be used to claim being first |
| Same quantity, different units / representations | The method has strong precedents; the sentiment object still differs | If kept, it must be set up as a separate narrow question |

The task's binary decision also lacks one outcome: when intervals are too wide, noise is too large or the intervention is ineffective, the result should be "inconclusive". Not finding an anomaly cannot be written up directly as "smooth, monotone, symmetric, unit-invariant" (F7). This round is a stop-loss after the prior-art check; it is neither a pass nor a fail of a behavioural test.

## Next steps / Risks

The decision is to archive the original T2 and keep resources for independent topics that pass the prior-art check. Only the conditions for a restart are kept below; they are not packaged as an approved new topic or an executed experiment:

- It must first be explained why "company news sentiment" has a testable mechanism different from existing affect scoring; if the contribution is still only a change of headlines, the stop stands.
- If only the units question is kept, prefer money expressions that are truly equal in quantity, and fix the event, company size and comparison baseline. `profit rises 0.5%` cannot be replaced directly with `rises 50 basis points`; relative percentage growth and an absolute change in a rate must be defined separately.
- If only the round-number thresholds are kept, real economic thresholds, displayed precision and numeric representation must be isolated. A positive profit that falls by more than 100% becomes a loss; a jump there is not necessarily a numeric cognitive bias. Local finite differences also do not automatically prove a mathematical discontinuity.
- Even if the topic is re-launched, the unit for estimating retest noise, same-batch and cross-batch controls, effect intervals, practical thresholds and multiple comparisons still need to be specified. Specific suggestions are in the design audit; none has been executed so far.

Search boundary: up to the date above, public web search, arXiv, ACL Anthology, author materials and the specified repository were used; core sources were opened down to the full text, not relying only on search snippets. A Chicago Booth study on left-digit / agent purchasing was also found, but access to the SSRN full text returned 403, so it is only a lead and is not used to judge that financial sentiment thresholds have been done. This round wrapped up early after finding literature sufficient to change the decision; it does not claim to have used up half a day or to have completed an exhaustive systematic review.

Actually executed: read the research log and the task; two independent literature searches; one independent design audit; my source re-check and synthesis. **New model scoring 0 times, training 0 times, replication of authors' experiments 0 times.** Results in the literature are all authors' reports. The material is saved in the local repository; nothing was pushed, and the authors were not contacted.

Research progress: all six steps (source priority, research conventions, evidence ledger, scope review, object review, conclusions and risks) are complete. The source-audit conclusion is "supported, but the qualification of partial overlap must be kept".
