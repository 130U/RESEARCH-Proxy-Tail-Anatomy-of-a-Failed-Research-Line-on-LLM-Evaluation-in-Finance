# Document impact structure and fixed stratified zero-finding audits: a rigorous interface and a rectangle cost separation

**Comparison-boundary addendum from round seven:** the theorems IA1–IA8 are unchanged. The round-seven draft and a new adversarial review added two stronger comparisons: a safe non-rectangular count region can fully reproduce the direct risk, and a balanced gate on the total contamination count already attains the 88 audits of the IA7 main example and the same Ω(r) separation from rectangles. Hence this separation cannot prove that modelling impact locations is necessary. The gain from location information is isolated separately with a three-stratum, N=20 example: cost 38 versus 48 for a fixed total-K≤1 gate. This is still an exploratory construction, not a prior-work check or a check of real-world validity.

Date: 2026-11-16. Status: IA1–IA8 below come with complete finite combinatorial proofs, **pen-and-paper proofs, not Lean-verified**. This file used no internet access, no training, and no real audit labels. Numerical examples are marked as analytic constructions; program run results are carried by separate implementation records, and the derivations here must not be taken as evidence that anything was run. It accompanies the [collective statistic envelopes](collective_metrics.md).

The actual progress in this file is: writing a direct test of a fixed conclusion as an executable mathematical contract; proving that the two-level antichain reduction and the finite optimization are exact; and giving a generalizable cost-separation family that remains strict against the **strongest joint zero-finding rectangle procedure**. These are self-contained combinations of finite-population testing, monotone sets, and finite combinatorial optimization; **differences from prior work have not been verified so far, and no original theorem or real financial certificate is claimed**.

## 1. Claims, assumptions, and proof dependencies

The population is a finite set of document versions $`W=\bigsqcup_{h=1}^{d}W_h`$, with each stratum of size $`N_h\ge1`$. Empty strata are removed first. The true contaminated set $`C^*\subseteq W`$ is fixed, and no prior is placed on contamination locations. Each stratum independently draws a fixed number $`n_h\in\{0,\ldots,N_h\}`$ uniformly without replacement; the audit correctly determines whether each sampled version belongs to $`C^*`$. Undeterminable cases must be handled separately and cannot be treated as clean. Each document costs $`c_h>0`$ to audit, and the fixed cost is $`c\cdot n`$.

**A1: Freezing.** Before sampling, fix the population, the strata, the impact map, the training implementation and random seeds, the observed votes $`V`$, the test labels $`y`$, the statistic $`S`$, the target interval $`I=[\ell,u]`$, $`\alpha\in(0,1)`$, and all $`n_h`$. These may depend on observational information available before the audit, but the sampling mechanism below must still hold conditional on that information. Changing any of these objects after selecting a favourable sampling outcome cannot be justified by the fixed-design proofs in this file.

**A2: Structural impact upper bound.** Each document has a fixed set of possibly affected heads $`H_i\subseteq\{1,\ldots,m\}`$. For **every** allowed deletion set $`C`$, after retraining with the randomness fixed, every head outside $`B(C)=\bigcup_{i\in C}H_i`$ is identical to the observed head. This is a structural property that holds simultaneously for all deletion sets, not a document-by-document deletion test. A shared tokenizer, normalization, model selection, encoders, ID migration, and label processing are all dependencies that must be covered.

**A3: Outer relaxation.** Heads in $`B`$ may output anything at each test point, freely across points; heads outside $`B`$ are fixed. Heads marked as affected are allowed to keep their original outputs. The test set, true labels, denominator, and class conventions do not change. This model contains the actual deletion comparator but is usually wider.

**A4: Sampling and ground truth.** Uniform without replacement within strata, independent across strata, fixed $`n`$, correct audit ground truth. Shared human misjudgements or undeterminable historical versions do not disappear automatically from the combinatorial formulas. Uncovered assumptions about sources/historical selection still leave the final conclusion conditional.

Define $`𝒵(B)`$ as the set of allowed prediction vectors above, and $`𝒜(B)=\{S(z):z\in 𝒵(B)\}`$. When only an interval is needed, use its exact envelope $`A(B)=[\min 𝒜(B),\max 𝒜(B)]`$; finiteness and nonemptiness guarantee the endpoints exist. Because $`I`$ is a closed interval, $`𝒜(B)\subseteq I`$ is equivalent to $`A(B)\subseteq I`$.

The proof chain is: A2 → IA1 dependency correctness; A3 → IA2 monotonicity and bad configurations; A4 → IA3 miss probability and coverage; IA2, IA3 → IA4 two-level reduction; IA4 → IA5 global fixed-design search; IA3 → IA6 strongest rectangle comparison; IA2, IA6 → IA7 threshold-family separation; IA7 → IA8 exact symmetric optimization.

## 2. IA1: when a dependency graph suffices to support the impact upper bound

**Proposition.** If the pipeline is a fixed directed acyclic computation graph, every node is a deterministic function of its parents' values and of already-fixed exogenous randomness, document $`i`$ enters the graph only through its listed input nodes, and $`H_i`$ contains every output head reachable from those inputs, then A2 holds.

**Proof.** Delete an arbitrary $`C`$ all at once, replacing the corresponding inputs with fixed missing values; the missing values and any retraining nodes must be operations represented in the graph. For any node not in the descendant set of these inputs, none of its parents is in the descendant set either. Along a topological order, the unchanged exogenous inputs are the same; if all parent values of such a node are the same, its fixed function and randomness give the same output. Induction gives that every non-descendant output head is unchanged. The union of descendant heads of all deleted inputs is covered exactly by $`\bigcup_{i\in C}H_i`$, so A2 holds. When $`C=\varnothing`$ the union is empty, and the original output is likewise obtained. ∎

Fixed shard IDs, per-shard training, and a trusted shared encoder form an easily checked special case. If deletion triggers a global re-sharding, the graph must contain that control dependency, and the relevant $`H_i`$ often become all heads.

**Counterexample for joint effects.** Two document input bits are originally $`(1,1)`$, and the output is their OR; deleting either one alone leaves the output at 1, while deleting both makes it 0. Hence "single-document deletion does not change the head" does not imply $`H_i=\varnothing`$. The dependency graph tracks possible effects, not the empirical sensitivity to one observed input.

## 3. IA2: monotonicity, the exact accuracy interface, and bad configurations

**Proposition.** $`C\subseteq D`$ implies $`𝒵(B(C))\subseteq 𝒵(B(D))`$, and hence $`A(B(C))\subseteq A(B(D))`$. Therefore

```math
ℋ_I=\{C\subseteq W:A(B(C))\not\subseteq I\} \qquad (3.1)
```

is an upward-closed family of sets.

**Proof.** The definition as a union gives $`B(C)\subseteq B(D)`$. Keeping the original votes on the additional heads $`B(D)\setminus B(C)`$ reproduces every prediction vector of $`𝒵(B(C))`$. Hence the feasible regions are nested, the minimum does not increase, and the maximum does not decrease. If the smaller region already has $`S(z)\notin I`$, the same $`z`$ is still feasible in the larger region, so the latter is also bad. ∎

For majority voting with ties going to the smallest class index, let $`b=\left\vert B\right\vert`$ and let $`u_{jc}(B)`$ be the number of votes for class $`c`$ outside $`B`$. Then

```math
R_j(B)=\{c:\ u_{jc}(B)+b\ge u_{ja}(B)+𝟏\{a\lt c\}\quad\forall a\ne c\}. \qquad (3.2)
```

The exact accuracy endpoints for fixed $`B`$ are

```math
L(B)=J^{-1}\sum_j𝟏\{R_j(B)=\{y_j\}\},\qquad U(B)=J^{-1}\sum_j𝟏\{y_j\in R_j(B)\}. \qquad (3.3)
```

The reason is that casting all changeable heads at point $`j`$ for a candidate class makes that class reachable; A3 allows each point to realize its own worst/best choice simultaneously. The full proof is in CM1 and CM3. An implementation can decide $`L<\ell`$ or $`U>u`$ directly with integer counts and rational endpoints, without floating-point approximation.

**Caveat on outer envelopes.** A sound approximate interval may fail to be nested, so upward-closed pruning cannot be used merely because the interval is "sound". One can instead use $`\widetilde A^\uparrow(B)=\mathrm{hull}\bigcup_{D\subseteq B}\widetilde A(D)`$, which is still sound and nested; the cost may be large. Or use the exact accuracy interface above directly. A non-monotone approximation is not necessarily invalid in itself, but it must state clearly which reductions it supports.

## 4. IA3: miss probability and zero-finding coverage

Write $`q_h(C)=\left\vert C\cap W_h\right\vert`$, with the convention $`\binom ab=0`$ when $`b>a`$ and $`\binom a0=1`$. For integers $`0\le q\le N_h`$ define

```math
p_h(q;n_h)=\frac{\binom{N_h-q}{n_h}}{\binom{N_h}{n_h}},\qquad p_n(q)=\prod_{h=1}^{d}p_h(q_h;n_h). \qquad (4.1)
```

**Proposition.** For fixed $`C`$, the probability of the all-zero-finding event $`Z`$ is exactly $`p_n(q(C))`$. This function is coordinatewise nonincreasing in $`q`$ and in $`n`$. If

```math
R_I(n):=\max_{C\in ℋ_I}p_n(q(C))\le\alpha, \qquad (4.2)
```

then the procedure "report $`I`$ on $`Z`$, otherwise report the full range of $`S`$ or abstain" covers the actual deletion-comparator statistic with probability at least $`1-\alpha`$ for every fixed $`C^*`$. The maximum over an empty bad family is taken to be 0.

**Proof.** Stratum $`h`$ has $`\binom{N_h}{n_h}`$ equally likely samples, of which $`\binom{N_h-q_h}{n_h}`$ avoid $`C`$ entirely; independence gives the product. Increasing $`q`$ shrinks the set that can be avoided; increasing $`n`$ can be coupled by taking uniform samples as longer prefixes of a random permutation, so the zero-finding event can only shrink, which gives both monotonicities. If the actual statistic is not in $`I`$, A2–A3 guarantee that it belongs to $`A(B(C^*))`$, so $`C^*\in ℋ_I`$. An erroneous certificate can be issued only when $`Z`$ occurs, with probability at most $`R_I(n)`$. If the actual statistic is in $`I`$, the procedure cannot lose coverage because of it. This holds for every fixed ground truth, which gives the stated frequentist coverage. ∎

This is not "the probability of contamination after observing zero findings is ≤α", it is not a proof of historical measurability, and it does not guarantee a high probability that zero findings succeed. If $`\varnothing\in ℋ_I`$, empty contamination gives zero findings with probability 1, and no $`n`$ can make $`R_I(n)\le\alpha<1`$; when the pre-specified interval does not even contain the observed statistic, the design should be explicitly declared infeasible.

## 5. IA4: minimal bad configurations and the stratum-count antichain reduction

Let $`ℳ_I`$ be the members of $`ℋ_I`$ that are minimal under set inclusion. Let $`Q=\{q(M):M\in ℳ_I\}`$ with duplicates removed, and let $`Q_{\min}`$ be the vectors in it that are minimal in the coordinatewise partial order. These are two different antichains and must not be conflated.

**Proposition.** For every fixed $`n`$,

```math
R_I(n)=\max_{M\in ℳ_I}p_n(q(M))=\max_{q\in Q_{\min}}p_n(q). \qquad (5.1)
```

Moreover, for any budget rectangle $`[0,b]=\{q:0\le q_h\le b_h\}`$, the rectangle contains no bad configuration if and only if there is no $`q\in Q_{\min}`$ with $`q\le b`$.

**Proof.** The bad subsets of any bad $`C`$ form a finite nonempty family, so there is a minimal bad $`M\subseteq C`$. The stratum counts satisfy $`q(M)\le q(C)`$, and IA3 gives $`p_n(q(M))\ge p_n(q(C))`$; the reverse inclusion $`ℳ_I\subseteq ℋ_I`$ gives the first equality. Every vector in the finite $`Q`$ dominates a minimal vector, and the probability is coordinatewise nonincreasing, which gives the second equality. If the rectangle contains a bad $`C`$, it also contains the $`q(M)`$ above and the element of $`Q_{\min}`$ it dominates; conversely, every member of $`Q_{\min}`$ is realized by an actual bad configuration, so $`q\le b`$ supplies a bad configuration. ∎

**Quantifier details.** Strictly speaking, the two maximum reductions use only finiteness and the monotonicity of the miss probability; they do not need the whole bad family to be upward closed. The additional value of upward closure is that it supports the semantics "once a bad subset is found, remove all its supersets", and that checking minimality requires only checking all single-element deletions: if every single deletion is good, every proper subset is good; otherwise some superset of that single deletion is also bad. A non-monotone approximation cannot use this local test as is.

What the stratum-count antichain retains is "there exists a bad location configuration with this count", not the claim that every location configuration with the same count is bad. Because the miss probability under stratified uniform sampling depends only on counts, the maximum risk is still exactly equal. This reduction fails for non-uniform sampling within strata, unless enough state to determine the probability is retained again.

**Compression for identical impact sets.** If all $`H_i`$ within each stratum are identical, then $`B(C)`$ depends only on $`𝟏\{q_h(C)>0\}`$. A minimal bad document configuration has at most one document per stratum; otherwise removing one document from that stratum keeps $`B`$ unchanged, so it could not be minimal. Hence it suffices to enumerate the $`2^d`$ stratum presence patterns and treat them as a 0/1 count antichain. Document identities within a stratum need not be enumerated one by one. If a stratum has several impact types, one can first split by type $`(h,H_i)`$; the sampling probabilities are still computed from the original stratum totals, and the sampling design must not be silently changed to fixed quotas per type.

## 6. IA5: correctness of the finite global minimum cost over fixed quotas

**Proposition.** Enumerate all $`\prod_h(N_h+1)`$ fixed quota vectors, check $`R_I(n)\le\alpha`$ using IA4 and rational arithmetic, and take the minimum $`c\cdot n`$ among the qualifying ones. This gives the global minimum cost, under A1–A4, for the class of procedures with this fixed interval, fixed stratification, uniform sampling, and certificate on all-zero findings. If the set is empty, the procedure correctly returns infeasible.

**Proof.** Every allowed fixed design is represented by a unique grid vector; for each vector, IA3–IA4 compute the exact worst-case miss probability over the corresponding relaxed bad family. The search misses no qualifying design, and the minimum over a finite nonempty set is attained, so the returned value is minimal. If no vector qualifies, no design in this class exists. Qualifying here is a criterion that guarantees the whole relaxed threat model; the real training process may be more robust than the relaxation, and one cannot claim this is also the minimum cost among all certificates for real training. ∎

The bad family requires at most $`2^{\left\vert W\right\vert}`$ envelope calls; writing the cost of one call as $`T_S`$, this part is $`O(2^{\left\vert W\right\vert}T_S)`$. Deciding minimal members also requires single-deletion queries, and naive Pareto filtering of stratum counts takes at most $`O(d\left\vert Q\right\vert^2)`$; these costs cannot be left out of the total budget. Planning once the antichain is available takes $`O(\prod_h(N_h+1)\,d\,\left\vert Q_{\min}\right\vert)`$. The antichain can be exponentially large, for example all subsets of half the size, so general polynomial complexity cannot be claimed. When the search exceeds its budget, a qualifying quota already found gives only a **feasible cost upper bound**; an incomplete search cannot return "optimal", and failing to find one cannot return "infeasible" either.

## 7. IA6: a fair strongest joint zero-finding rectangle baseline

The additional commitment of the rectangle procedure is: on all-zero findings, report the whole count box $`[0,b]`$; otherwise report the whole count space; and every document location configuration inside the box must satisfy $`A(B(C))\subseteq I`$. The budget $`b_h\in\{0,\ldots,N_h\}`$ is fixed before sampling. It first gives a count confidence set and then propagates it to the final statistic.

**Proposition.** The exact worst-case miscoverage probability of this rectangle is

```math
R_{\rm box}(n,b)=\max_{h:b_h\lt N_h}p_h(b_h+1;n_h), \qquad (7.1)
```

and 0 if no such $`h`$ exists. Hence the strongest baseline of this kind should enumerate all safe $`b`$ and $`n`$ simultaneously, minimizing cost subject to $`R_{\rm box}\le\alpha`$.

**Proof.** For a fixed true configuration outside the rectangle, at least one stratum has $`q_h\ge b_h+1`$; the all-zero probability is at most $`p_h(b_h+1;n_h)`$ for that stratum, and hence at most the displayed maximum. Choosing a stratum attaining the maximum and placing $`b_h+1`$ contaminated documents only in that stratum, with zero in the others, attains exactly this probability. This configuration lies outside the box and need not belong to the bad family of the final statistic, because what this baseline commits to is **coverage of the whole count box**. Safety inside the box is checked exactly by the rectangle test of IA4. ∎

An ordinary Bonferroni rectangle requires $`\sum_{h:b_h\lt N_h}p_h(b_h+1;n_h)\le\alpha`$, which is sound but may be more conservative; optimizing per-stratum failure budgets still amounts to this sum constraint. The comparison in this file must include the $`\max`$ version above; one cannot omit it and call Bonferroni the "strongest".

The limitation must also be stated clearly: if one does not require the count box itself to be covered, only the final $`I`$, and calibrates against the final bad family, one is back to the direct test of IA3, which is no longer in the rectangle procedure class of this section. The "rectangle cost" is the cost of the additional commitment to an intermediate confidence set; it must not be misstated as beating every possible confidence procedure.

**Weak dominance of the direct method.** Every safe box places all final bad configurations outside the box, so $`R_I(n)\le R_{\rm box}(n,b)`$. The minimum cost of the direct method is no larger than that of the strongest box baseline under the same conditions; whether it is strictly smaller requires an instance. Uniform fixed quotas must also be checked with the same $`ℋ_I`$ and the same $`I,\alpha`$; the uniform baseline must not be switched to the harder goal of stability of all predictions.

## 8. IA7: a generalizable threshold family and a strict cost separation

Take an integer $`r\ge2`$, $`d=m=2r-1`$, with exactly $`N\ge1`$ documents per stratum, each affecting only the corresponding head $`h`$. Fix any $`J\ge1`$ test points; every head votes for the true label $`y_j`$ at point $`j`$. When $`J\ge2`$ the labels may include two classes, and the proof is exactly the same. Let $`S`$ be the fixed-test accuracy, $`I=[9/10,1]`$, and cost $`c_h=1`$. This is an artificial oracle voting structure, not a trained model or a real financial task; the $`J=1`$ version chosen for the run budget does not test task utility.

**Proposition.** In this family, the bad configurations are exactly those with contamination in at least $`r`$ strata, and the minimal count antichain is the set of all 0/1 vectors with exactly $`r`$ ones. Hence

```math
R_I(n)=\max_{\left\vert T\right\vert=r}\prod_{h\in T}(1-n_h/N). \qquad (8.1)
```

The balanced quota $`n_h=n_\star`$ is feasible as soon as $`(1-n_\star/N)^r\le\alpha`$. In continuous form, $`n_\star=\lceil N(1-\alpha^{1/r})\rceil`$, but an implementation should solve for it through integer powers / rational inequalities to avoid boundary rounding. Its cost upper bound is $`(2r-1)n_\star`$. The exact minimum cost of the strongest joint zero-finding safe rectangle is

```math
C_{\rm box}^*=r\,\lceil N(1-\alpha)\rceil. \qquad (8.2)
```

**Proof.** With at most $`r-1`$ affected heads, at least $`r`$ heads are unaffected and all vote for the true class; any other class has at most $`r-1`$ votes, so every point is still correct. When at least $`r`$ heads can change, they can jointly vote for one wrong class at every point, outvoting at most $`r-1`$ true votes; they can also all keep their original votes. Hence in this case the accuracy envelope is $`[0,1]`$, whereas before it was $`\{1\}`$, and badness with respect to $`I`$ is determined exactly by the number of affected strata. A minimal bad configuration has one document in each selected stratum, and IA4 gives the risk formula.

For balanced quotas, every product of size $`r`$ is the same, so the displayed inequality gives feasibility. A safe rectangle can allow budget $`b_h\ge1`$ in at most $`r-1`$ strata; otherwise, contaminating one document in each of any $`r`$ of those strata would land inside the safe box while pushing the statistic out of $`I`$. So at least $`r`$ strata must have $`b_h=0`$. IA6 requires $`1-n_h/N\le\alpha`$ for each such stratum, so each needs at least $`\lceil N(1-\alpha)\rceil`$ audits, which gives the cost lower bound. Choosing exactly $`r`$ strata with budget 0 and budget $`N`$ for the rest, and auditing only the former, attains this number; the box then contains at most $`r-1`$ affected heads, and the IA6 risk meets the target, so the lower bound is attained. ∎

**Optimal ordinary Bonferroni box for the same family.** If one instead requires the sum of the risks of all strata outside the box to be ≤$`\alpha`$, the exact minimum cost is

```math
C_{\rm Bonf}^*=\lceil N(r-\alpha)\rceil=rN-\lfloor N\alpha\rfloor. \qquad (8.3)
```

Proof: every safe box has at least $`r`$ zero-budget strata; their individual risks are $`(N-n_h)/N`$, and requiring the sum of these risks to be ≤$`\alpha`$ requires the sum of their audit counts to be ≥$`N(r-\alpha)`$, so the integer total cost is at least the displayed value. Choose exactly $`r`$ zero-budget strata, take a census in $`r-1`$ of them and audit $`N-\lfloor N\alpha\rfloor`$ in the remaining one, and give the other strata budget $`N`$ with no audits; the sum of risks is exactly $`\lfloor N\alpha\rfloor/N\le\alpha`$, which attains the lower bound. If there are more zero-budget strata, the cost lower bound can only increase. ∎ This comparison shows the extra conservatism of sum allocation; the main separation in this file still uses the stronger IA6 max box as the baseline.

**Analytic example, not a new experimental result.** With $`r=6,d=11,N=20,\alpha=1/20`$, auditing 8 documents in each stratum under balanced quotas gives risk $`(3/5)^6=729/15625=0.046656\le0.05`$, at cost 88. The exact minimum cost of the safe box is $`6\times19=114`$, and the optimal ordinary Bonferroni box is $`120-1=119`$. Hence the direct optimal cost satisfies $`C_I^*\le88<114`$, a saving of at least $`26/114=13/57\approx22.807\%`$ relative to the stronger optimal box. **This derivation does not claim that 88 is the direct optimum**; if a program proves a lower value, it should be reported separately. Also, for $`r=5,d=9,N=2`$, the balanced scheme has risk $`1/32`$ and cost 9, while the optimal box cost is 10.

**Order-of-magnitude separation.** Fix $`\alpha\in(0,1)`$, let $`a=\log(1/\alpha)`$ and $`N=r^2`$. By $`1-e^{-a/r}\le a/r`$ and $`\lceil x\rceil\le x+1`$,

```math
C_I^*\le(2r-1)(Na/r+1)\le2Na+2r, \qquad (8.4)
```

while $`C_{\rm box}^*\ge rN(1-\alpha)`$. Since zero cost gives every bad configuration miss probability 1, $`C_I^*>0`$; hence

```math
\frac{C_{\rm box}^*}{C_I^*}\ge\frac{rN(1-\alpha)}{2Na+2r}=\Omega(r). \qquad (8.5)
```

This gives a rectangle lower bound within the matching procedure class and a feasible upper bound for the direct method; it does not prove minimax optimality of the direct method for general impact graphs. The growing population is $`(2r-1)r^2`$, and one cannot hide the change in scale to claim savings by an arbitrary factor on a fixed corpus.

**Interpretation.** In this family the source sizes, costs, and marginal contamination assumptions are fully symmetric; the strict difference does not come merely from allocating more audits to high-risk strata, but from not having to rule out simultaneously every configuration where "a single stratum is contaminated but the final result is still safe". It is a joint test against a composite bad family; the rectangle pays an extra cost because it first proves more intermediate facts. This phenomenon may fall entirely within existing theory on risk-limiting audits and joint testing; without a literature check of the increment, the contribution is positioned as a clear combinatorial interface and boundary examples.

## 9. IA8: exact symmetric optimization for the threshold family

**Proposition.** For the equal-cost, equal-size structure of IA7, the direct global optimal cost equals the minimum of $`\sum_{i=1}^{r-1}a_i+r a_r`$ over all nondecreasing integer tuples $`0\le a_1\le\cdots\le a_r\le N`$ satisfying

```math
\prod_{i=1}^r(N-a_i)\le\alpha N^r; \qquad (9.1)
```

the corresponding quota over all strata is $`(a_1,\ldots,a_r,a_r,\ldots,a_r)`$, padded with $`r-1`$ further copies of $`a_r`$. This requires enumerating $`\binom{N+r}{r}`$ tuples.

**Proof.** Permuting strata changes neither risk nor cost, so any feasible quota can first be sorted as $`n_1\le\cdots\le n_{2r-1}`$. The largest risk comes from the first $`r`$ strata with the fewest audits, because their zero-finding factors are largest. Lowering the audit counts of the remaining $`r-1`$ strata to $`n_r`$ does not change the multiset of the $`r`$ largest factors, so the quota stays feasible and the cost weakly decreases. Hence some global optimum has the stated shape. Conversely, every such tuple explicitly gives a valid full quota, so the reduction in both directions loses no optimum. Nondecreasing tuples of length $`r`$ are choices of $`r`$ values with repetition from $`N+1`$ values, of which there are $`\binom{N+r}{r}`$. ∎

For the general "bad only if at least $`r`$ strata" structure with $`d\ge r`$, the same argument gives the objective $`\sum_{i=1}^{r-1}a_i+(d-r+1)a_r`$; IA7 takes $`d=2r-1`$, giving coefficient $`r`$. The symmetric reduction cannot be applied directly with unequal costs or unequal stratum sizes.

## 10. Complete families, budgets, and fair comparisons that can be frozen before computation

This section gives the input contract for the mathematical sweep; the identities frozen before actual execution are governed by [impact_budget.md](../planning/impact_budget.md), and existing hand-computed examples are not retroactively recognized as blind-test findings. The author of this file does not change planning code and does not start training. The initially suggested multi-test-point version is an optional extension of IA7 and must not be described as having been executed in this round; the concrete run choices below agree with the budget file.

1. **Main threshold family:** all 20 combinations of $`r\in\{2,3,4,5,6\}`$ and $`N\in\{2,5,10,20\}`$; $`d=m=2r-1`$; the frozen run takes $`J=1,y_1=0`$, with every head voting for the true class; $`\alpha=1/20`$, $`I=[9/10,1]`$, unit costs. All members, with and without gains, are published; one cannot report only $`r=6,N=20`$. The main target is still the same accuracy interval; that in this family the interval can be narrow only if all points are stable is a special feature of its structure and is not generalized into a general requirement. The multi-point two-class oracle version, though covered by IA7, is still not actual training.
2. **Control with no strict gain:** two strata with the same $`N`$, each affecting only one head; of three all-correct heads, the other one is trusted and fixed, and the configuration is bad only if both strata are contaminated. The direct risk is $`(1-n_1/N)(1-n_2/N)`$. For a given total $`s\le N`$, this product $`=1-s/N+n_1n_2/N^2\ge1-s/N`$, with the minimum attained by concentrating on one stratum; hence both the direct method and the strongest box need, and can meet the target with, $`\lceil N(1-\alpha)\rceil`$. If $`s>N`$, the cost is already higher than this feasible cost, so no improvement is possible. This refutes "exploiting joint structure always saves optimal cost".
3. **Baseline set:** balanced fixed quotas on the same input (directly calibrated); the strongest joint zero-finding safe rectangle; the ordinary Bonferroni safe rectangle; the direct global optimum. Balanced quotas are themselves a fixed design and belong to the direct method class; the advantage of this family over rectangles must not be packaged as an advantage over "all fixed audits". Ordinary uniform sampling without replacement from the whole population and fixed per-stratum quotas are different designs; if the former is also compared, its true combinatorial probability should be written out, and these formulas must not be mixed in.
4. **Actual execution budget:** governed by the frozen budget file: Python standard library, CPU, no GPU; the full threshold grid is expected to take under 30 seconds with memory <256 MB; general checks and tests have a total cap of 60 seconds and memory <512 MB. The largest single tuple domain is $`\binom{26}{6}=230230`$, and each check needs at most 6 integer factors. General document configurations are capped at 65536, discrete count states at 50000, and design/rectangle grids at 100000; identical impact within a stratum can be compressed to at most $`2^{11}=2048`$ presence patterns. The search must not expand without limit. The earlier, looser 5-minute estimate in this file was not taken as execution authorization; exceeding the budget returns incomplete according to IA5, not a pseudo-optimum.
5. **Verification and resource fairness:** the same $`\alpha,I,V,y,H_i,c`$ and rational comparisons; all optimizers obey the same total task budget and the state limits declared in advance; analytic formulas and proven symmetric reductions may be used, but must also be verified on small domains. Record the time spent building antichains, optimizing, and reviewing certificates, and do not hide planning computation from audit cost. If some baseline is not solved, report a feasible upper bound and a safe lower bound/gap; an unoptimized value cannot be used to claim a proportional improvement. The analytic box lower bound above is already exact and is unaffected by any failure of numerical optimization.

The main family is an artificial check of a mathematical mechanism; it does not meet the requirements of a real historical-version audit, real task utility, or an independent confirmation set. Reaching 20% would only trigger a discussion of continuing PATH_03 and could not be taken directly as PATH_01/G1 passing. Because the analytic separation example was known before the sweep, the sweep checks the shape and implementation of the whole pre-specified family, not an independent finding in the statistical sense.

**Cross-reference to post-implementation results.** [threshold_results.json](../planning/threshold_results.json) records the exact search over all 20 cells, taking about 0.695 seconds; 9 cells have strict savings and 11 have no gain, and the median saving over the whole frozen family is 0. The program optimum for $`r=6,N=20`$ is 88, the same as the feasible upper bound above; the largest saving, $`4/15`$, occurs at $`r=6,N=5,10`$. These are "our mathematical design experiments", not original results from a paper or real audits. **The complete pre-specified family did not reach the proposal gate of median saving ≥20%**, and one cannot afterwards cut out only $`r=6`$ and claim the gate was passed. The general-graph code and its exhaustive evidence are reported separately in the corresponding implementation records.

## 11. Proof obligations and verification checks

| Obligation | Status | Where closed locally |
|---|---|---|
| O1 The structural graph covers any joint deletion | CLOSED-LOCAL | IA1 topological induction; the faithfulness of the dependency graph is the empirical obligation of A2 |
| O2 Nested feasible regions and exact accuracy | CLOSED-LOCAL | IA2; the key construction from the CM1/CM3 derivation is restated in that section |
| O3 Sampling probability, quantifiers, and coverage | CLOSED-LOCAL | IA3 counting and per-ground-truth test |
| O4 Two-level antichains and the safe-box test | CLOSED-LOCAL | IA4 finite minimal elements, monotone probability |
| O5 Global optimality of the search | CLOSED-LOCAL | IA5 full finite design grid; for the specified procedure class only |
| O6 Risk of the strongest joint zero-finding box | CLOSED-LOCAL | IA6 upper bound and the single-stratum contamination example attaining it |
| O7 Strict difference and asymptotic separation | CLOSED-LOCAL | IA7 threshold, attainable box lower bound, and exponential inequality |
| O8 Symmetric search misses no optimum | CLOSED-LOCAL | IA8 sorting and lowering the tail entries |

All eight mathematical obligations have been closed locally; the unknown faithfulness of real dependency graphs and of historical audit ground truth has not been treated as a closed proof. Novelty, real-world efficiency, and adaptive/non-zero-finding extensions are not among the propositions proved. An independent internal review checked the threshold family, the rectangle risk, joint deletion, and the simple AND counterexample with no cost separation; it is not external peer review.

Boundary checks: an empty bad family has risk 0; if the empty configuration is bad, the design is infeasible; $`n_h=0`$ gives factor 1; $`n_h=N_h`$ with $`q_h>0`$ gives factor 0; $`b_h=N_h`$ produces no constraint outside the box; H_i is allowed to be empty; multi-label and tie semantics are fixed; denominators are nonzero; every comparison uses the same final statistic; probability refers to sampling randomness, not a prior on contamination; finite checks do not replace a general proof. This file is Markdown; no TeX reference indexer or Lean was run, and no formal tool verification is claimed.
