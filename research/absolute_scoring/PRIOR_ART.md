# Literature gate for the absolute-scoring question

Later decision: I chose to continue scoring as a replication and stress test, and all 250 scoring calls were completed. The original judgment from the literature-gate stage and the zero-scoring status at that time are kept below. For the final results see the [one-page summary](ONE_PAGE.md) and the [full report](REPORT.md); the basis for execution is the [frozen protocol](protocol.md).

2026-11-16. Based on the frozen task statement for this stage. In this round I checked the LLM literature, the reliability mathematics and the execution design separately.

**Conclusion: the mathematical skeleton of the new question and several key measurements already have direct prior work; we have not confirmed that any one paper has done the full combination of experiments in this question. The finding had to be weighed before deciding whether to spend about 200–250 scoring calls.** There is currently no evidence for listing this formula, or "an LLM's own top list is unstable", as a new contribution. If the work continues, the reasonable framing is a replication of a known baseline under a specific scoring protocol, plus a test of its failure mechanisms.

This deliverable is a pre-execution result: **0 new scoring calls, 0 new scores; no sampling, no frozen final prompt, no experimental result figures.** The results of the earlier pairwise comparison and rank aggregation remain old experiments and cannot be used as measurements for this question. This round completed a targeted search and a check of the key original texts; it does not claim to have completed a half-day or systematic review.

## Closest evidence

| Source read closely | What it already did | Parts not yet confirmed as covered |
| --- | --- | --- |
| [Xie, Alanwar, Judged in Company, §3, §5.4, H.4, Tables 12/17](https://arxiv.org/html/2610.40241v1) | Dependence of LLM scoring on the batch; a formula from Gaussian correlation to threshold flips; the gain from repeated aggregation; a prediction made from the main experiment and then validated with additional voting runs. It also reports probability means, so we cannot say it only uses votes. | The full combination in this question: raw 0–100 integer means, two groups with m=1/2/4, two-tail self-overlap at fixed p, and widening factors. |
| [Zhang, Yang, LLM-as-a-Judge Version Shift, §7, Appendix J](https://arxiv.org/html/2610.32986v1) | Changes in the top-30% list under repeated scoring with the same version, as a comparison baseline for version changes. | Predicting the top-list curve of raw-score means from single-score reliability. |
| [Wan, Brennan, Lee, 2007, §1.1–1.2](https://education.uiowa.edu/sites/education.uiowa.edu/files/2022-10/casma-research-report-22.pdf) | Classical measurement theory already uses Spearman–Brown-adjusted reliability as a bivariate normal correlation to compute classification consistency. | This specific measurement on LLM scoring of financial headlines. We did not obtain the full text of the 1989 original paper it traces back to, and do not pretend to have read it. |

More adjacent empirical work includes behaviorally anchored scoring, repeated numeric scoring, averaging after changing batches, and measuring LLM recall of human top candidates by selection fraction. Paper-by-paper scope and links to the originals are in the [LLM literature analysis](literature_llm.md); the classical basis and the full derivation are in the [reliability and mathematical analysis](literature_reliability.md).

## Why "switching to top lists" is not enough to be a new theory

The following are mathematical consequences drawn during this check. They do not claim that the papers in the table above have carried out all experiments in this question.

Under the parallel measurement model S_j=T+ε_j, with errors uncorrelated with T, equal error variances across rounds and errors mutually uncorrelated, the correlation between two disjoint m-round means is

```math
r_m=\frac{mr}{1+(m-1)r}.
```

If the two standardized means are jointly normal, the threshold flip rate F can be obtained by integration from r_m. For two sets with the same marginal selection fraction p, the top-list self-overlap H satisfies

```math
H=1-\frac{F}{2p}.
```

The second formula is only a set identity. Rewriting an existing reliability formula and a Gaussian threshold model as top-list overlap is not enough to make a new theorem. When ties make the two lists different in size, this equal-size formula also cannot be applied directly.

## Interpretation limits that must be kept even if the work continues

**Scale.** The r obtained after a normal-rank transformation of each single round is not the same object as the correlation that corresponds to raw integer score means. A monotone transformation preserves each round's ordering but can change the ordering of the cross-round means. So the formula in this question can serve as a fixed, falsifiable baseline, not as a necessary prediction under satisfied assumptions. A mismatch with the formula may come from scale nonlinearity, ties, the covariance structure or the joint distribution; it cannot be named directly as a new tail regularity.

**Scope of the research question.** Same-model self-overlap measures stability, not correctness. Choosing wrongly both times and choosing correctly both times can give exactly the same self-overlap. So this experiment alone cannot decide whether "ask several times" or "cast a wider net" brings higher true recall or economic value. That budget choice needs an extra reference target and a definition of cost, and the current design does not identify it.

**Statistical interpretation.** r and the mean-score lists come from the same eight rounds. This is an internal test without extra tuning, not an independent held-out prediction. The difference between same-batch and different-batch correlations is also not an identified "percentage of batch noise". The headline bootstrap should carry all eight rounds of scores; it does not automatically cover all the uncertainty from regenerating batches or from shared context.

**Execution details.** The 100 random control targets are usually spread over nearly all 25 batches. If their complete 40-item first-round contexts are reused and repeated twice more, the controls add at most 50 calls, for a total of about 250. The new ties gate compares the whole boundary tie group with 20% of the nominal count, not the number of extra items added. The new headline inputs must be stored outside the repository. The exact conventions are in the [frozen protocol](protocol.md).

## Decision at this stage and open questions

The final requirement of the TASK is: if someone has specifically done top lists together with the same formula comparison, stop before running. **The current evidence is not yet enough to declare strictly that "the same full experiment has already been done", so the question is not judged a literature FAIL here.** Holding off on batch scoring is a research judgment based on very close prior work, so that the evidence that would change the value of the investment is weighed first. It is not a tool, API or permission obstacle.

My recommendation is to drop the framing "this formula is a new theory". Whether to continue the original experiment should depend on whether it is accepted as a replication and stress test, with the remaining increment stated clearly before scoring. Open questions:

1. Given the prior work above, is the two-tail, fixed-selection-fraction validation on financial headlines still worth a short experiment? If so, to which falsifiable mechanism should the contribution be limited, rather than just a change of dataset?
2. Is the scale difference between raw-score means and rank-normal reliability a baseline misspecification that we deliberately want to test? If so, do we accept the interpretation that "a mismatch may come first from scale", rather than attributing a mismatch directly to a tail anomaly?
3. Is the current goal only to answer retest stability? If the budget choice between repetition and widening is still to be answered, what independent reference must be added so that stability and validity can be told apart?

This report did not request API keys, did not contact outside people, and did not generate or replace scoring data. Only after the research framing is received does the next stage start: freezing the prompt and rules, drawing the new sample and completing the eight measured rounds. At this stage we cannot report overlap rates, the number of repeats needed to reach 90%, or the measured error of the formula.
