# Can single-score reliability predict the averaged top list? Literature and mathematical review

Review date: 2026-11-16. Object: the absolute-scoring experiment in this repository's `TASK.md`. This report contains no new scoring and does not change the task; its judgments hold as of this targeted search and full-text check.

## Conclusion and recommendation for the experiment gate

**The recommendation was to stop before batch scoring and weigh the highly similar prior work against the research increment.** Existing research not only establishes the relation between Gaussian correlation and decision flips, but also, in LLM batch scoring, uses parameters estimated from a main experiment to predict in advance the stability after repeated voting, and then tests this with new runs. Other LLM research directly measures retest changes in the top list for the same version. Connecting Spearman–Brown to Gaussian classification consistency also has precedent in classical measurement theory.

This is not the assertion that "exactly the same experiment, with financial headlines, 0–100 means, m=2/4 and two-tail fixed top-p, has been published": **in the original papers read this time, we did not find this item-by-item identical experiment.** But these implementation differences are not enough to restore a theoretical contribution automatically. The reasonable framing at present is at most a replication and stress test of an existing measurement model on a specific screening task; whether it is worth doing depends on first stating an incremental question that existing research cannot answer. Stopping batch scoring is a research judgment, and it cannot be rewritten as the literature having covered `TASK.md` word for word.

## Decisive adjacent literature

### Judged in Company: closest to the current plan

In [Judged in Company: In-Context Batching Makes LLM Verdicts Depend on Other Items, v1](https://arxiv.org/html/2610.40241v1), §3 Proposition 3 gives the Gaussian flip integral at an arbitrary threshold; H.4 discusses means and votes; Tables 12 and 17 clearly separate the predictions made before the new voting experiment from the measurements after it. §5.4 also reports actual results from averaging level probabilities. So we cannot claim that the paper only uses votes and has no averaging at all. Its main empirical work uses fixed ordinal cutoffs; we did not see this question's fixed-p two-tail mean-score list curves.

The most important difference here is **the observed quantity and the aggregation rule**, not the financial context or the sample size: the existing research mainly checks fixed-category threshold decisions and majority votes; this question mainly checks the ranked sets of raw integer score means. This difference may affect the results, but at present there is no evidence that it can produce a sufficient research contribution. Nor can "testing an untuned stability prediction on new data" be treated as original to this question.

### Other coverage limits

| Original source | What it already covers | What cannot be counted as first proposed by this question |
| --- | --- | --- |
| [LLM-as-a-Judge Version Shift, v1, §7, Appendix J](https://arxiv.org/html/2610.32986v1) | Changes in ranking and in the top-30% set when rescoring with the same version, as a baseline for version changes; discusses false stability caused by ties | That an LLM's own top list is unstable; using same-version retests to build a top-list stability baseline |
| [JudgeProfile, v1, §C.1](https://arxiv.org/html/2609.36705v1) | Split-half on fitted attribute weights, then Spearman–Brown to convert to full-sample reliability | Using Spearman–Brown in LLM judge research; but its object is not this question's top sets of headline mean scores |
| [Right Order, Wrong Scale, v1, Appendix M](https://arxiv.org/html/2610.02492v1) | Split-half and Spearman–Brown for means of human occupational ratings; distinguishes ordinal and cardinal evaluation | "Reliable correlation but a different scale" cannot be treated as a new finding; its reliability target is not repeated means of the same LLM |
| [Just Ask the Model, author manuscript, p.3](https://valentinklotzbuecher.github.io/llm-uj-research-eval/Just-Ask-the-Model--One-Shot-LLM-Research-Evaluation-and-Structured-Expert-Review.pdf) | Explicitly warns that applying Spearman–Brown to rank correlations and to unequal panel sizes is only an approximate adjustment | Treating a rank correlation directly as an exact reliability input for an arbitrary averaging operation |

The classical foundations must also be attributed explicitly. The [original Taylor–Russell (1939) paper](https://gwern.net/doc/statistics/decision/1939-taylor.pdf) already links bivariate normal correlation, selection ratio and outcome ratio. More directly, [Wan, Brennan, Lee (2007), CASMA Research Report 22, §1.1–1.2](https://education.uiowa.edu/sites/education.uiowa.edu/files/2022-10/casma-research-report-22.pdf): their comparative study of classification consistency describes using the Spearman–Brown-lengthened reliability as a bivariate normal correlation and then computing classification consistency; the paper traces these practices back to Woodruff–Sawyer (1989) and others. What we read directly this time is the 2007 original comparative study; the 1989 paper, whose full text we did not obtain, is not reported as read.

[Ellis and Sijtsma (2024)](https://link.springer.com/article/10.1007/s11336-024-09956-7) study the asymptotic convergence rate of Spearman–Brown under random item sampling, uncorrelated errors and regularity conditions, and discuss prediction bias for short scales. It cannot be used as a basis for m=2, 4 in this question holding exactly under an arbitrary scoring mechanism.

## The two mathematical steps must be kept apart

The derivation below is for checking the task; it makes no new theorem claim. The first step is about second moments; only the second step is the distributional assumption that determines tail events.

Let the score of a random headline in round j be S_j=T+ε_j. If Var(T)=τ², the errors are uncorrelated with T, and the errors in each round have mean zero, variance σ² and are mutually uncorrelated, then the single-score correlation is r=τ²/(τ²+σ²). The correlation between two disjoint m-round means is

```math
\mathrm{Corr}(\bar S_{1:m},\bar S_{m+1:2m})
=\frac{\tau^2}{\tau^2+\sigma^2/m}
=\frac{mr}{1+(m-1)r}.
```

This formula does not need normality. More generally, if every repeat has variance v and every pair of distinct repeats has covariance κ, the same identity holds with r=κ/v. So one cannot say in general that "heteroscedasticity or correlated errors necessarily break the formula": conditional heteroscedasticity can still preserve these unconditional moments, and a bias permanently shared across repeats can be absorbed into the stable component. The latter makes self-consistency very high, but says nothing about accuracy relative to the truth.

If the within-group covariance is κ_W, the between-group covariance is κ_B, and each round has variance v, the correlation between the two m-round means is

```math
\frac{m\kappa_B}{v+(m-1)\kappa_W}.
```

A single average of all 28 correlations cannot identify this expression in general. Non-exchangeable structure caused by sessions, time drift, shared batches and so on must be judged from the design and the data; independence cannot be claimed just because "a new session was opened".

Second step: let X, Y be standard bivariate normal with correlation ρ; let z_p=Φ⁻¹(1−p), and write

```math
J_\rho(p,q)=\int_{z_p}^{\infty}\phi(x)
\bar\Phi\!\left(\frac{z_q-\rho x}{\sqrt{1-\rho^2}}\right)dx.
```

Under a continuous distribution, the equal-fraction top-list overlap is O_ρ(p)=J_ρ(p,p)/p. The pass-through fraction needed for a fixed recall γ is q_γ(p)=inf{q:J_ρ(p,q)≥γp}, and the widening factor is q_γ/p. The positive and negative tails are the same under this model; an asymmetry between the upper and lower tails would reject this common Gaussian baseline, but on its own it cannot determine which mechanism causes it.

The boundaries can be checked: at ρ=0, O=p and q_γ=γ; at ρ=1, O=1 and q_γ=γp. The last case shows that the so-called widening factor can be below 1; if q≥p is forced artificially, the result is already a different definition.

Let F be the symmetric-difference fraction of two equal-size sets with population fraction p; then the identity is

```math
O=1-\frac{F}{2p}.
```

**This step is a set identity transformation given by this report; it does not claim that the LLM papers above have measured top-p curves.** Combining it with the normal flip formula and the moment identity for means gives the curve the task intends to use. So rewriting it as overlap or switching to fixed quantiles cannot be treated as a new theory. If the two sets differ in size because of ties, their actual sizes must be used; this equal-size formula cannot be applied directly.

## The most critical scale gap in the current task

The task first applies a rank-normal transformation to each round of scores and then computes r; the actual decision, however, first takes the arithmetic mean of the raw 0–100 scores and then takes the top list. **Rank transformation and averaging do not commute.** Even if Spearman–Brown held exactly on the first scale, that would not imply that the list prediction holds exactly on the second scale.

A purely algebraic counterexample is enough: for two rounds, suppose the pre-transformation coordinates are (3,0) for headline A and (2,2) for headline B; the means put B first. Apply the same strictly increasing transformation g(z)=100(e^z−1)/(e³−1) at these points: A's mean is 50 and B's mean is about 33.5, so the order reverses. The original ordering within each round is unchanged, yet the ordering after averaging changes. The counterexample only proves that the operations do not commute; it does not assume that these two headlines come from a normal population.

So if the main analysis is run as the task says, the curve should be called a **fixed falsifiable baseline**, not a theoretical necessity under satisfied assumptions. Deviations may come at least from the shape of the raw scale, discrete ties in the scores, the covariance structure, a non-Gaussian joint distribution and the finite sample. One cannot first ignore the earlier items and then name the deviation a new tail regularity. Supplementary diagnostics also should not rewrite the main aggregation rule after the results have been seen.

Pearson r on normal scores is neither the raw-score ICC nor the Spearman rank correlation. Mapping midranks to Φ⁻¹((rank−0.5)/N) is only an explicit computational definition; with many ties it does not produce a continuous normal margin. Integer averaging refines the grid, but does not guarantee removing ties at the top-list boundary.

## What can be reported, and what the current design cannot give directly

"Not tuning with the m=2, 4 overlap rates" can hold; but r comes from the same 8 repeats, and m=2, 4 are also built from these repeats, so this is not a prediction on independent held-out data. It should be called an internal test of a fixed formula, and in the bootstrap the difference should be recomputed together with r and the prediction curve, keeping their dependence.

Resampling by headline should carry all repeat scores of that headline together. If errors within a batch are correlated, the interval from an ordinary headline bootstrap covers only the resampling assumption used, and does not necessarily cover all the variation from regenerating batches. Several intervals intersecting the curve cannot be taken directly as proof that the model fits everywhere.

The difference between same-batch and different-batch correlations can describe batch sensitivity, but a difference of two correlation coefficients is not "the percentage of noise due to the batch effect". Without an explicit variance model and identification conditions, this task's one-page summary should report the visible difference and its uncertainty, and not give an unidentified variance share. Fixing 100 control items also cannot automatically separate all session, position, shared-context and time effects.

## Search coverage and open issues

This check targeted several intersecting directions: Spearman–Brown, normal classification consistency, LLM retest top lists, LLM averaging/voting gains, and batch effects. The reading focused on the formulas, methods and appendices of the original papers above, rather than matching terms from abstracts only. Search terms included "Spearman Brown LLM", "test retest top selection", "classification consistency bivariate normal", "Gaussian top-k overlap measurement noise reliability".

The web index of Stanford *AI Measurement Science* shows relevant chapters, but direct full-text access returned 404 this time, so it is not used as decisive evidence. In [LLM Judge Validation Under Sparse Overlap](https://arxiv.org/html/2609.31857v1), overlap refers to coverage by shared human annotation and top-1 refers to selecting the best judge; these terms do not refer to the same objects as in this question, and no collision was judged on that basis.

This report did not do a full-database systematic review and does not prove that no earlier study of exactly the same type exists. The evidence obtained is enough to reject both "a reliability formula connected to Gaussian top-list probabilities is new mathematics" and "this is the first measurement of an LLM's own top-list stability". Whether to carry out this experiment anyway should rest on a clearly stated remaining research question; not having found word-for-word identical implementation details cannot be a reason to continue.
