# Randomized audit designs: the exact minimax risk for homogeneous stratum-occupancy thresholds

Date: 2026-11-16. Offline mathematical derivation from round 9. This file states only conditional mathematical propositions about finite-population audits; it does not modify the existing paper, does no training, uses no internet access, and does not claim to have exhausted prior work or obtained a real financial certificate. The question is: when badness depends on the number of contaminated strata, can allowing a random choice of which strata to audit improve on designs that fix the audit size of each stratum in advance? The answer is yes, and this homogeneous problem has an exact solution.

## Claim and Status

**The non-degenerate output contract comes before optimality.** When the audit finds all zeros, the procedure **must** output the pre-fixed interval $`I`$; once contamination is found, it outputs the full range of the statistic. The interval itself does not change with the sampling result, and abstaining at random after all-zero findings is not allowed. If one only required "outputting $`I`$ must be conditional on all-zero findings", a zero-cost procedure that never outputs $`I`$ would have zero probability of an erroneous certificate, and the nonzero minimax value below would not hold.

Under this contract and the local assumptions below, the candidate formula of the main proposition RA1 holds. The status is **PROVABLE AS STATED**, referring to the proposition as explicitly written in this file; if the initial verbal "zero-only" expresses only a necessary condition, the condition that all-zero findings must produce a certificate has to be added. The proof consists of local finite sums, combinatorial identities, and pairwise compression.

Verification: Conditionally verified. The conditions are the declared finite threat family, ground-truth audits, and the output contract; the pen-and-paper proof is not a Lean verification, an empirical model result, or a novelty confirmation. The results of an internal independent review are recorded separately.

## Invoked assumptions and notation

No shared `assumptions.lock.md` was found in this repository; the numbering below is local to this file, to avoid silently rewriting the earlier fixed-quota assumptions. When this is later merged into a multi-theorem paper, the differences between the two design classes should be registered together.

- **RA-A1 Finite homogeneous population.** $`W=\bigsqcup_{h=1}^dW_h`$, integers $`d,N\ge1`$, each stratum $`\left\vert W_h\right\vert=N`$, and each audited document costs 1; the population, the strata, and all available auxiliary information are fixed before randomization.
- **RA-A2 Exact threat family.** Integer $`1\le r\le d`$; the family of bad configurations is exactly $`ℋ_r=\{C\subseteq W:|\{h:C\cap W_h\ne\varnothing\}|\ge r\}`$. Every such configuration is allowed, in particular configurations with one document in each of any $`r`$ strata. If a financial model can only be shown to have its actual failure configurations contained in this family, then this file is optimal only for this conservative threat family, not automatically for the actual model.
- **RA-A3 Fixed ground truth and exogenous randomness.** $`C`$ is fixed before the audit random numbers are realized. The design may know the fixed objects above but not $`C`$; the audit random tape has no additional association with the unknown contamination ground truth. The adversary may know the design distribution but cannot choose $`C`$ after seeing the sampling result.
- **RA-A4 Exact audits.** The contamination ground truth of queried documents is determined correctly; undetermined cases cannot be recorded as zero findings. The main theorem first considers non-adaptively drawing exactly $`m`$ distinct documents, with integer $`0\le m\le dN`$. The sampling distribution is arbitrary; independence within strata or fixed stratum quotas are not required.
- **RA-A5 Fixed output.** In every run, the pre-specified $`I`$ is reported if and only if all findings are zero, and any finding leads to reporting the full range. The risk in this file is the probability of an erroneous certificate/miss with respect to $`ℋ_r`$; if $`ℋ_r`$ is only an outer relaxation of the model, this probability is an upper bound on the actual probability of an erroneous certificate.

Write $`𝒫_m`$ for the set of all probability distributions on $`m`$-element subsets $`A\subseteq W`$. For a design $`\mu\in 𝒫_m`$ define

```math
R(\mu)=\max_{C\in ℋ_r}\Pr_{A\sim\mu}(A\cap C=\varnothing),\qquad
V_{d,N,r}(m)=\inf_{\mu\in 𝒫_m}R(\mu).
```

All sets are finite, and probability comes only from the audit randomization. Below we construct a distribution attaining the lower bound, so there is no need to invoke an abstract minimax exchange theorem first. Write $`\binom ab=0`$ when the integer $`a\ge0`$ and $`b<0`$ or $`b>a`$; in the normal range the usual definition of binomial coefficients applies, and binomial coefficients with a negative upper index are never used. For a vector $`x`$, $`e_j(x)`$ is the $`j`$-th elementary symmetric polynomial, $`e_0(x)=1`$, and $`e_j(x)=0`$ when $`j<0`$ or $`j`$ exceeds the length of the vector.

## Verification Target and Bottleneck

The verification target is to close both directions simultaneously: the worst-case risk of every randomized design is at least an explicit constant, and some design attains this same constant for every minimal bad configuration. The lower bound must not be only for uniform stratified designs, and the upper bound must not hold only for one random contamination prior.

The key algebraic step is: with $`\sum_h n_h=m`$ fixed, concentrating two interior quotas towards the boundary does not increase $`e_r(1-n_1/N,\ldots,1-n_d/N)`$. The nonnegativity of its coefficient comes from the termwise nonnegativity of elementary symmetric polynomials and does not need independent training samples, asymptotic approximations, or some unverified external theorem. The full compression proof is given below.

## Anchors and Borrowing

Relation to the local [IA1–IA8](impact_audit.md) and [LV1–LV5](localization_value.md): this file inherits the finite-population ground truth, the outer relaxation of impact, and the all-zero certificate semantics, and **changes** "fixing per-stratum quotas in advance" to arbitrary distributions over document subsets. The earlier optimum over fixed quotas cannot be taken directly as the optimum of this larger class.

The proofs in this file are self-contained on paper. The established tools used are finite group averaging, uniform finite comparison distributions, decomposition of elementary symmetric polynomials, and the finite Jensen inequality for convex functions. The background needed is finite probability and combinatorial counting; the comparison-distribution lower bound, symmetrization, pairwise compression, and convexity are all developed in this file. These are not claims of originality. No unverified specific theorem from a paper is imported, and no literature search was done in this round.

## 1. RA1: the exact risk for an exact budget

If $`m\lt dN`$, write $`q=\lfloor m/N\rfloor`$ and $`t=m-qN`$, so that $`0\le q\le d-1`$ and $`0\le t\lt N`$. Then

```math
V_{d,N,r}(m)=F(m)
=\frac{\binom{d-q-1}{r}+(1-t/N)\binom{d-q-1}{r-1}}{\binom dr}. \qquad (1.1)
```

For a full census, define separately $`F(dN)=0`$. A design attaining the optimum is: choose $`q`$ strata uniformly at random and take a census of them; if $`t>0`$, choose one of the remaining strata uniformly at random and audit $`t`$ documents in it uniformly without replacement. These steps jointly determine a subset of exactly $`m`$ elements. When $`t=0`$, no "partial stratum" actually needs to be chosen. The optimal design need not be unique.

### Minimal bad configurations and symmetrization

Let $`ℳ_r`$ be the set of configurations with one document in each of exactly $`r`$ distinct strata. Its size is $`\binom dr N^r`$. Every bad $`C`$ contains some $`M\in ℳ_r`$, and $`\{A:A\cap C=\varnothing\}\subseteq\{A:A\cap M=\varnothing\}`$. Hence, for every design, the maximum risk can be restricted to $`ℳ_r`$.

Consider the finite group $`G`$ generated by arbitrary permutations of strata and permutations of documents within each stratum. It preserves costs and the threat family, and acts transitively on $`ℳ_r`$. Symmetrize an arbitrary design $`\mu`$ as follows: first draw $`A\sim\mu`$, then independently take $`g\in G`$ uniformly, and output $`gA`$. For a fixed bad $`C`$, the new risk is

```math
\frac1{\left\vert G\right\vert}\sum_{g\in G}\Pr_{A\sim\mu}(A\cap g^{-1}C=\varnothing)\le R(\mu). \qquad (1.2)
```

So symmetrization does not increase the worst-case risk. This is a finite averaging computation; it does not assume that the true contamination is random or exchangeable; the true $`C`$ is still fixed.

### A lower bound for every design

Purely as a proof device, take $`M\in ℳ_r`$ uniformly. Fix any audit subset $`A`$, and write $`n_h=\left\vert A\cap W_h\right\vert`$ and $`x_h=1-n_h/N`$. Given the $`r`$ strata occupied by $`M`$, the probability that the document chosen uniformly in each stratum avoids $`A`$ is $`x_h`$; these document choices in the proof device are mutually independent. Hence

```math
\frac1{\left\vert ℳ_r\right\vert}\sum_{M\in ℳ_r}𝟏\{A\cap M=\varnothing\}
=\frac1{\binom dr}\sum_{\left\vert S\right\vert=r}\prod_{h\in S}x_h
=\frac{e_r(x)}{\binom dr}. \qquad (1.3)
```

The maximum is at least the finite average, and exchanging the two finite sums gives, for any $`\mu`$, the lower bound

```math
R(\mu)\ge 𝔼_{A\sim\mu}\frac{e_r(1-n(A)/N)}{\binom dr}
\ge\min_{\substack{0\le n_h\le N\\\sum_h n_h=m}}\frac{e_r(1-n/N)}{\binom dr}. \qquad (1.4)
```

This uniform comparison distribution is not a prior assumption about the actual corpus; it only proves that there is always at least one fixed bad configuration attaining this average risk.

### Compressing quotas closes the lower bound

Outside two coordinates $`a,b\in[0,1]`$, write the remaining vector as $`z`$. Distinguishing term by term whether a product contains these two coordinates gives the identity

```math
e_r(a,b,z)=e_r(z)+(a+b)e_{r-1}(z)+ab\,e_{r-2}(z). \qquad (1.5)
```

All coordinates of $`z`$ are nonnegative, so $`e_{r-2}(z)\ge0`$; when $`r=1`$ this coefficient is 0 by convention. If $`0\lt b\le a\lt1`$, take $`\delta=\min(1-a,b)>0`$ and replace $`(a,b)`$ by $`(a+\delta,b-\delta)`$. The coordinate sum is unchanged, the coordinates stay in $`[0,1]`$, and

```math
(a+\delta)(b-\delta)-ab=\delta(b-a)-\delta^2\le0. \qquad (1.6)
```

So $`e_r`$ does not increase. The original coordinates lie on the integer grid of $`1/N`$, and so does $`\delta`$, so the result still corresponds to valid integer quotas. At least one interior coordinate becomes 0 or 1. Applying this operation repeatedly to two interior coordinates, after finitely many steps at most one interior coordinate remains, and the rest are all 0 or 1. If there is only one coordinate to begin with, no pairing is needed.

With $`\sum_hx_h=d-m/N`$ fixed, the end point necessarily has $`q`$ zeros, $`d-q-1`$ ones, and one entry $`1-t/N`$; when $`t=0`$ the last one is also 1. Its $`e_r`$ value is exactly the numerator in RA1. Since every initial quota can be lowered to this value, and this end point is itself feasible, the value is the global minimum, not merely a local stationary point. In a full census all coordinates are 0, and $`e_r=0`$ when $`r\ge1`$.

### Attaining the same lower bound

Starting from the fixed audit subset corresponding to the end point above and applying independent uniform permutations of strata and within strata gives exactly the design described in RA1: a random census plus one partial stratum. After symmetrization, the risk is the same for all $`M\in ℳ_r`$; its average is still the computed $`F(m)`$, so the risk of every minimal bad configuration equals $`F(m)`$. The risk of any larger bad configuration is no higher. The worst-case risk of this design is exactly $`F(m)`$, matching the lower bound for every design, which proves RA1. Here "attained on the uniform average" is not silently swapped for "attained for every ground truth"; this upgrade relies on the transitivity of the group action.

## 2. Boundary cases and the minimum budget

When $`m=0`$, Pascal's identity makes the numerator of RA1 equal to $`\binom dr`$, so $`F(0)=1`$. When $`m=dN`$, every nonempty bad configuration is found and the risk is 0; listing the full census separately avoids $`\binom{-1}{r}`$.

When $`r=1`$, $`e_1(x)=d-m/N`$ is determined by the total budget alone, so $`F(m)=1-m/(dN)`$. Pairwise compression is not strict in this case, and the optimum is not unique; for example, uniform sampling without replacement from the whole population also attains this risk. One cannot claim from this that concentrating on strata is always strictly better.

When $`N=1`$, $`t=0`$, and RA1 reduces to $`F(m)=\binom{d-m}{r}/\binom dr`$; strata are documents, and there is no additional within-stratum location structure. When $`r=d`$ and $`m\lt N`$, $`F(m)=1-m/N`$, and after a census of any one stratum the risk is 0. More generally, zero risk is first attained at $`m=N(d-r+1)`$: before that, $`q\le d-r`$ and $`t\lt N`$, and the formula has at least one positive term; at this budget fewer than $`r`$ strata are without a census, and every bad configuration must touch a census stratum.

For fixed $`0<\alpha<1`$, the minimum integer budget in this design class is exactly

```math
m_\alpha^*=\min\{m\in\{0,\ldots,dN\}:F(m)\le\alpha\}. \qquad (2.1)
```

$`F`$ is nonincreasing (the next section also gives exact slopes), so it can be inverted monotonically over integer budgets. Binomial coefficients and rationals suffice for rational $`\alpha`$; uncontrolled floating-point rounding must not decide the boundary of equality. A scan or bisection is only an evaluation of the exact formula, not a replacement of its proof by finite tests.

## 3. RA2: at-most budgets and adaptive all-zero paths

**Non-adaptive hard cap.** If $`\left\vert A\right\vert\le m`$ is allowed, but all-zero findings must still produce a certificate, the minimax value is still $`F(m)`$. For any such design, pad samples with fewer than $`m`$ documents up to $`m`$ distinct documents by a pre-specified rule. The miss event of the padded sample is contained in the original event, so the new risk is no higher than the original; and the new design's risk is at least $`F(m)`$. So every original design's risk is also at least $`F(m)`$, and the RA1 design attains it.

**Additional conditions for finite adaptive extensions.** The choice of the next document and the stopping rule may depend on the IDs already queried, their binary contaminated/uncontaminated results, and the exogenous random tape; no extra side channel about the ground truth of other documents may be obtained through the audit. Auxiliary information fixed in advance may be used, but the threat family of RA-A2 must remain valid conditional on that information. For every ground truth and random run, at most $`m`$ distinct documents are queried. No path on which contamination has been found reports $`I`$; a path that stops without finding contamination must report $`I`$.

For a fixed random tape, let $`A_0`$ be the counterfactual set of documents the algorithm queries when every answer it receives is "uncontaminated", i.e. the full path in the clean world $`C=\varnothing`$. It is determined by the random tape before $`C`$ is known, and $`\left\vert A_0\right\vert\le m`$. For any fixed $`C`$, there is the path equivalence

```math
\{\text{the algorithm reports }I\}=\{A_0\cap C=\varnothing\}. \qquad (3.1)
```

If the right-hand side holds, the real run agrees with the all-zero counterfactual at every step and finally reports $`I`$. If the right-hand side fails, take the first query on the all-zero path that belongs to $`C`$; all real responses before it were zero, so the algorithm does reach this query and finds contamination, and by the contract it never reports $`I`$ afterwards. This proves both directions without assuming that the real positive path and the counterfactual all-zero path are the same.

Hence the risk of every such adaptive procedure equals the miss risk of some random set $`A_0`$, and applying the at-most-budget result gives the lower bound $`F(m)`$. The optimal non-adaptive procedure also belongs to the allowed class, so adaptive binary queries cannot improve the minimax risk under this **hard-cap, all-zero-must-certify** contract. This conclusion does not cover procedures that can output a new, narrower interval after non-zero findings.

## 4. RA3: an expected budget must say in which world it is taken

Interpolate $`F`$ linearly between integers, defining it for real $`b\in[0,dN]`$. On each block $`qN\le b\le(q+1)N`$, its slope is

```math
-\frac{\binom{d-q-1}{r-1}}{N\binom dr},\qquad q=0,\ldots,d-1. \qquad (4.1)
```

The numerator is nonincreasing in $`q`$, so the slopes are nonpositive and nondecreasing from block to block; the block endpoints join continuously by Pascal's identity. So $`F`$ is a convex, nonincreasing, piecewise linear function, including the zero plateau at the end.

For a non-adaptive random sample size with $`𝔼\left\vert A\right\vert\le b`$, the lower bound from the uniform minimal bad set and the per-budget RA1 lower bound give

```math
R(\mu)\ge 𝔼 F(\left\vert A\right\vert)\ge F(𝔼\left\vert A\right\vert)\ge F(b). \qquad (4.2)
```

The middle step is Jensen's inequality for a convex function of a random variable with finitely many values; one can take directly any supporting line of $`F`$ at $`𝔼\left\vert A\right\vert`$ and sum over all integer values. Taking the two RA1-optimal designs for $`\lfloor b\rfloor`$ and $`\lceil b\rceil`$ and mixing them independently at random, with weights that make the average sample size $`b`$, the risk of each minimal bad configuration is the same weighted average of the two endpoint values of $`F`$, which equals exactly $`F(b)`$. So the exact value of this expected-budget class is $`F(b)`$; an integer average budget cannot obtain a lower minimax risk than the hard cap at the same integer.

For the adaptive algorithms of the previous section, the sample size in the formula above should be the all-zero path length $`\left\vert A_0\right\vert`$. If the budget constraint is on the **clean world**, $`𝔼_{C=\varnothing}\left\vert A_0\right\vert\le b`$, the same lower bound holds and is attainable. If the expected cost is required to be at most $`b`$ in every ground-truth world, this includes the clean-world constraint; the cost of the non-adaptive mixture above does not depend on the ground truth and satisfies the stronger constraint, so the optimum is still the same.

Requiring only the average cost in bad worlds is not enough. Counterexample: $`d=r=1,N=2`$; query the two documents in random order and stop as soon as contamination is found. Under each single-contamination bad configuration, the expected number of queries is $`3/2`$; when both documents are contaminated it is 1, so the expected cost in every bad world is at most $`3/2`$, yet the miss probability is 0. On the other hand, $`F(3/2)=1/4`$. The difference is that the clean world needs 2 queries, so the clean-world budget is not met. The same notation "expected budget" cannot be used for these two constraints with the same formula applied to both.

## 5. RA4: the upgraded strongest fixed total-count gate baseline

A fair comparison must also let the total-contamination-count gate use an equally large class of randomized designs. Let $`M=dN`$; on all-zero findings the total-count gate reports $`\left\vert C\right\vert\le r-1`$, and otherwise the full count range; what it promises is coverage of the true total, not merely validity of the final interval. Allowing randomized designs over any exactly $`m`$ distinct documents, all $`r`$-element document sets must be ruled out, **without requiring them to come from different strata**.

The minimax risk of this total-count gate is

```math
G(m)=\frac{\binom{M-m}{r}}{\binom Mr}
=\frac{\binom{M-r}{m}}{\binom Mm}. \qquad (5.1)
```

Proof: for any fixed $`m`$-element audit set $`A`$, averaging uniformly over all $`r`$-element bad sets, the fraction that avoids $`A`$ is always $`\binom{M-m}{r}/\binom Mr`$; so the maximum risk of any randomized audit is at least this value. Uniform sampling of $`m`$ documents without replacement from the whole population makes the miss probability of every fixed $`r`$-element bad set equal to the binomial ratio on the right; larger bad sets have no higher miss probability. Hence the average lower bound is attained.

So pooled SRS is not just a convenient baseline: under this total-count coverage contract it is already optimal among all randomized exact-budget designs. The structural risk satisfies $`F(m)\le G(m)`$, because the total-count bad family contains the stratum-occupancy bad family; but this does not prove superiority over every simple audit method. The random-census design of RA1 is itself very simple. Choosing a count rectangle at random and promising its coverage, versus reporting a fixed final interval $`I`$ on all-zero findings, are also different output contracts, and this file does not conflate them.

A hand-computed example is $`d=3,N=2,r=2,m=2`$: a uniformly random census of one stratum has risk $`1/3`$; the strongest total-count gate with SRS from the whole population has risk $`\binom42/\binom62=2/5`$. These are analytic values for explicit finite parameters, not a real corpus or a new experiment.

## 6. Substantive impact on the earlier fixed-quota conclusions

The sharp path of the earlier [LV4](localization_value.md) takes $`r=N^2,d=2r-1`$. For fixed per-stratum quotas, any design with risk less than 1 has its $`r`$-th smallest quota at least 1, so at least $`r`$ strata each audit one document, and the optimal cost of the direct method is at least $`r=N^2`$.

Now fix $`\alpha\in(0,1)`$ and take the integer $`q_\alpha=\lceil\log(1/\alpha)/\log\,2\rceil`$. When $`r\ge q_\alpha`$, a uniformly random census of $`q_\alpha`$ strata has risk

```math
\frac{\binom{d-q_\alpha}{r}}{\binom dr}
=\prod_{j=0}^{q_\alpha-1}\frac{d-r-j}{d-j}
\le 2^{-q_\alpha}\le\alpha. \qquad (6.1)
```

Each fraction is nonnegative and at most $`1/2`$; if some numerator is 0, the risk is 0. The cost is at most $`q_\alpha N=O(N)`$. Hence, on this well-defined sequence of finite problems, once random choice of strata is allowed, the cost ratio of the earlier fixed-quota direct method to the new design is at least $`N/q_\alpha`$ and can grow without bound.

This does not overturn the earlier theorem; it reveals the cost of the earlier restriction on the design class: the earlier result "approaching a factor of two against the strong simple combination" holds only within the class of fixed per-stratum quotas; the same "strongest" label cannot be carried over to the class of arbitrary randomized designs. With $`\alpha=1/20`$, a random census of five strata already gives the cost upper bound $`5N`$, and the exact RA1 allows partial sampling of the last stratum, which may save more. For the total-count gate in the same larger design class, the $`G(m)`$ of the previous section should be used, not the earlier optimum for fixed-stratification total counts.

### Asymptotic constant comparison within the same randomized design class

Still take $`r=N^2,d=2r-1`$, $`\alpha=1/20`$, and let $`m_I^*(N)`$ and $`m_K^*(N)`$ be the minimum integer budgets obtained by inverting $`F`$ and $`G`$ respectively. Then

```math
\frac{m_I^*(N)}N\longrightarrow\frac{22}{5},\qquad
\frac{m_K^*(N)}N\longrightarrow2\log\,20. \qquad (6.2)
```

For the first limit, fix an integer $`q`$, write $`m=qN+t`$ with $`t/N\to\theta\in[0,1]`$. By the limit of finitely many factors, $`F(qN)=\prod_{j\lt q}(d-r-j)/(d-j)\to2^{-q}`$, and

```math
\frac{\binom{d-q-1}{r-1}}{\binom dr}
=F(qN)\frac{r}{d-q}\longrightarrow2^{-q-1}. \qquad (6.3)
```

So $`F(m)\to2^{-q}(1-\theta/2)`$. At the whole-stratum endpoints $`q=4`$ and $`q=5`$, the limits are $`1/16>1/20`$ and $`1/32<1/20`$ respectively, so for sufficiently large $`N`$ the minimum budget lies after the 4th whole stratum and before the 5th. On this block $`F`$ is exactly linear in $`t`$, and solving for the crossing point and rounding up introduces an error in $`t/N`$ of less than $`1/N`$, so $`t/N\to(1/16-1/20)/(1/32)=2/5`$. This gives $`m_I^*/N\to22/5`$.

For the total-count gate, take $`m/N\to\lambda`$ with finite $`\lambda>0`$, write $`M=dN`$ and $`z_j=m/(M-j)`$. For sufficiently large $`N`$ all $`z_j<1`$, and

```math
G(m)=\prod_{j=0}^{r-1}(1-z_j),\qquad
\frac{mr}{M}\le\sum_{j=0}^{r-1}z_j\le\frac{mr}{M-r+1}\longrightarrow\frac\lambda2. \qquad (6.4)
```

At the same time, $`z_{\max}=m/(M-r+1)=O(N^{-2})`$, and

```math
0\le-\log\,G(m)-\sum_{j=0}^{r-1}z_j
\le\frac{r z_{\max}^2}{1-z_{\max}}\longrightarrow0. \qquad (6.5)
```

Hence $`G(m)\to e^{-\lambda/2}`$. Taking any fixed positive distance on either side of $`\lambda=2\log\,20`$, the limiting risks are strictly above and strictly below $`1/20`$ respectively; the monotonicity of $`G`$ squeezes the minimum integer budget between the two, which gives the second limit. Hence, within the same class of arbitrary randomized sampling designs, the budget saving from structural information relative to the total-count coverage gate tends to

```math
1-\frac{m_I^*(N)}{m_K^*(N)}\longrightarrow
1-\frac{11}{5\log\,20}\approx26.56\%. \qquad (6.6)
```

This is an analytic conclusion for one well-defined parameter sequence; it was not selected from a new grid and does not extend the established computation plan. It is a constant gap relative to the total-count coverage contract, not an order-of-magnitude advantage over all audit procedures; both optima are themselves attained by simple sampling.

## 7. Counterexamples, integration boundaries, and research implications

**The adversary sees the sampling result.** In the example $`d=3,N=2,r=2,m=2`$, the procedure takes a random census of one stratum. If the adversary then picks one contaminated document in each of the other two strata, the miss probability is always 1, whereas the RA1 value is $`1/3`$. Fixing the ground truth before randomization is a substantive condition, not rhetoric.

**Abstention allowed after all-zero findings.** The zero-cost procedure that always outputs the full range has probability 0 of an erroneous certificate, so in that output class RA1 cannot be called the minimum error probability; a success-rate/acceptance-rate constraint must be set separately before studying cost. This file does not silently omit that constraint.

**From the outer relaxation to the real model.** A real dependency graph may allow only certain combinations of affected heads, or the realizable training outputs may be fewer than in the outer relaxation where any head can change arbitrarily. In that case the uniform minimal-bad-set comparison distribution of RA-A2 may not be supported by real failure cases, and the "optimality" of RA1 belongs only to the declared conservative threat family. It still upper-bounds the actual probability of an erroneous certificate, but one cannot use it to prove that the real problem cannot be solved with fewer audits.

**Ground truth and historical sources.** This file assumes that sampled contamination is identified correctly. It does not prove that the knowledge-time field is authentic, does not reconstruct missing historical versions, does not infer compliance of historical training from the constant measurability of an already fixed model, and does not guarantee that suspicious documents have a verifiable authoritative source. The finite sampling probability closes only the audit-randomness link in the certificate chain.

**Scope.** The main solution rests on equal stratum sizes, equal per-document costs, and the permutation symmetry of the occupancy threshold family. Unequal sizes, unequal costs, irregular impact graphs, audit misjudgements, side information that depends on the future, data-dependent modification of the interval, and continuing to give non-trivial intervals after non-zero findings are not automatically covered by this theorem. The finite-population frequentist guarantee does not need IID training data, but it does not thereby obtain out-of-distribution semantics or model-utility guarantees either.

## Dependency Map

RA1 depends on the minimal-bad-configuration reduction, the uniform comparison lower bound, quota compression, and symmetric attainment; RA2 depends on RA1 and the all-zero path equivalence; RA3 depends on RA1, convexity from the block slopes, and the correct world for the expected cost; RA4 uses a separate uniform comparison distribution over the larger total-count bad family.

## Obligation Ledger

- O1 Minimal-bad-configuration reduction — CLOSED-LOCAL. Closed at: Section 1, inclusion of events and every bad configuration containing one document in each of $`r`$ strata.
- O2 Symmetrization does not increase worst-case risk — CLOSED-LOCAL. Closed at: Section 1, finite group average over $`g^{-1}C`$.
- O3 Lower bound for every design — CLOSED-LOCAL. Closed at: Section 1, counting over uniform minimal bad sets and exchange of finite sums.
- O4 Integer quota compression — CLOSED-LOCAL. Closed at: Section 1, two-coordinate decomposition of $`e_r`$, change in the product, and preservation of the grid.
- O5 Attainment for every fixed ground truth — CLOSED-LOCAL. Closed at: Section 1, group transitivity makes the risk of every minimal bad configuration equal to the average.
- O6 Boundaries and budget inversion — CLOSED-LOCAL. Closed at: Section 2, handling $`m=0,dN`$, $`r=1,d`$, and $`N=1`$ one by one.
- O7 At-most budgets and adaptive extensions — CLOSED-LOCAL. Closed at: Section 3, padding and the two-direction proof of the all-zero path event.
- O8 Expected budgets — CLOSED-LOCAL. Closed at: Section 4, monotone slopes, finite convex averaging, mixing adjacent budgets; the bad-world budget counterexample is explicitly isolated.
- O9 Total-count gate baseline for the randomized design class — CLOSED-LOCAL. Closed at: Section 5, averaging over all $`r`$-element sets and attainment by pooled SRS.
- O10 Unbounded loss of the earlier fixed design class — CLOSED-LOCAL. Closed at: Section 6, the $`N^2`$ lower bound for fixed quotas and the $`q_\alpha N`$ upper bound for random whole strata.
- O11 Asymptotic constant comparison within the randomized design class — CLOSED-LOCAL. Closed at: Section 6, limits of finite products over whole strata, control of the log remainder for the total-count probability, and the squeeze on the minimum integer budget.

## Verification Checks

| Check | Conclusion |
|---|---|
| Location before expansion | Not applicable: finite polynomial identities are used, with no local approximation |
| Norm/probability mode | The risk is always the miss probability under audit randomness for fixed $`C`$, followed by a finite maximum |
| Good-event bookkeeping | No high-probability event is omitted; all-zero findings are exactly the event counted in the risk |
| Rate leakage | The main conclusion is an exact formula; Section 6 explicitly gives the ratio lower bound for fixed $`\alpha`$ |
| Quantifier upgrade | The upgrade from the uniform average to every fixed minimal bad set explicitly uses group transitivity |
| Citation identity | No external citations used as proof; earlier local results are used only to compare design classes |
| Citation applicability | The main theorem is self-contained; no theorem from unknown literature is invoked |
| Boundaries/singularities | The denominators $`\binom dr,N`$ are positive; the full census is listed separately; $`r=1,N=1,m=0`$ have been handled |
| Closure of ignored terms | No remainder terms are dropped, and asymptotics are not substituted for finite risks; the constant in the $`O(N)`$ cost is the fixed $`q_\alpha`$ |

All 11 proof obligations are closed locally in this file; the unknown source ground truth and the faithfulness of the actual model's threat family are not listed as proved facts. Mechanical structural checks and an independent review are additional quality control; they do not replace these assumptions.
