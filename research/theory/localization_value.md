# The strongest fixed total-contamination gate and the limits of the value of location information

Date: 2026-11-16. Offline conditional derivation from round 8. This file only adds mathematical interfaces, proofs, and comparison boundaries that can be refuted; it does not modify the existing paper, does no training, uses no internet access, and does not fill in citations from memory. The classification is **finite population, fixed ground truth, frequentist audit, finite combinatorial optimization**; IID training samples are not needed, and no asymptotic normal approximation is used. The asymptotics in this file only compare the costs of a sequence of well-defined finite design problems.

The core conclusions are both positive and negative: the miss risk of the strongest fixed total-count gate can be computed exactly by a greedy procedure; for the earlier $`d=2r-1`$ threshold family, the cost ratio against it is less than 2 and the constant 2 can be approached, while under the original paper's setting $`N=r^2`$ the cost ratio tends to 1. Another structure, an all-strata conjunction, does have a linear gap, but the simple rectangle gate of taking a census of one stratum already attains the optimum of the direct method. **An advantage over one particular count aggregation must not be restated as a complex graph optimizer being indispensable, or as an original theoretical result having been obtained.**

## 1. The fixed problem and a truly fair total-count gate

We follow [IA1–IA8](impact_audit.md): $`W=\bigsqcup_{h=1}^dW_h`$, $`N_h=\left\vert W_h\right\vert\ge1`$; the true contaminated set $`C`$ is fixed. Integer audit sizes $`0\le n_h\le N_h`$ are chosen in advance; strata are sampled independently, uniformly without replacement within each stratum, and the audit ground truth is correct. The votes, labels, impact map, statistic $`S`$, target interval $`I`$, error budget $`0<\alpha<1`$, and costs $`c_h>0`$ are all frozen before sampling. Source ground truth that has not been determined cannot count as a zero finding.

Let $`ℋ\subseteq2^W`$ be the family of bad configurations, for which the envelope of allowed statistics cannot be contained in $`I`$; by IA2 it is upward closed. Write $`q_h(C)=\left\vert C\cap W_h\right\vert`$ and $`p_n(q)=\prod_h\binom{N_h-q_h}{n_h}/\binom{N_h}{n_h}`$; a binomial coefficient is 0 when its upper index is smaller than its lower index. Denote the direct certificate risk and optimal cost by

```math
R_I(n)=\max_{C\in ℋ}p_n(q(C)),\qquad
C_I^*=\min_{n:R_I(n)\le\alpha}\sum_hc_hn_h. \qquad (1.1)
```

On all-zero findings the direct procedure reports $`I`$; otherwise it reports the full range of the statistic. By contrast, the total-count procedure of this round makes an additional commitment: on all-zero findings it reports $`\left\vert C\right\vert\le k_0`$, otherwise the full count range; this count gate must be safe for the final target. It is still allowed the **best fixed stratified quotas**; it is not compared only against uniform quotas.

First the boundary cases. If $`ℋ=\varnothing`$, take $`k_0=\left\vert W\right\vert`$; neither procedure needs any audit. If $`\varnothing\in ℋ`$, empty contamination has all-zero probability 1, and no all-zero certificate design of the above kind satisfies $`\alpha<1`$. In the remaining cases define

```math
s=\min_{C\in ℋ}\left\vert C\right\vert\in\{1,\ldots,\left\vert W\right\vert\},\qquad k_0=s-1. \qquad (1.2)
```

**Proposition LV1 (strongest safe total-count gate).** $`k_0`$ is the largest safe fixed integer upper bound on contamination. For fixed $`n`$, the exact count miscoverage risk of this gate is

```math
R_K(n;s)=\max_{\substack{0\le q_h\le N_h\\\sum_hq_h=s}}
\prod_h\frac{\binom{N_h-q_h}{n_h}}{\binom{N_h}{n_h}}. \qquad (1.3)
```

Its optimal cost is $`C_K^*=\min_{n:R_K(n;s)\le\alpha}\sum_hc_hn_h`$, and $`C_I^*\le C_K^*`$.

**Proof.** No configuration of size less than $`s`$ is bad, so the gate is safe; some bad configuration of size $`s`$ exists, and every larger integer upper bound contains it, so such bounds are unsafe. The miscoverage event of the gate is all-zero findings when the true $`\left\vert C\right\vert\ge s`$. The miss probability depends only on the stratum counts and is coordinatewise nonincreasing; every larger configuration contains a subset of size $`s`$ whose miss probability is no smaller, so the maximum can be restricted to the displayed count level. Every integer count vector can be realized within the finite strata, so this maximum is exact. All bad configurations lie outside the total-count gate, so $`R_I(n)\le R_K(n;s)`$, which gives the cost relation. Choosing an upper bound smaller than $`k_0`$ requires ruling out more configurations and cannot lower the risk of the same design, so it does not improve the optimal cost either. ∎

The risk parameter $`s`$ is "the smallest contamination count that must be ruled out", not the allowed upper bound $`k_0`$; implementation interfaces must avoid this off-by-one error. These probabilities are miss probabilities under repeated sampling, not prior/posterior probabilities of contamination locations after observing zero findings.

## 2. LV2: exact prefix-greedy risk with unequal stratum sizes

For each stratum define a marginal chain of length $`N_h`$:

```math
a_{h,j}=\max\left(0,\frac{N_h-n_h-j}{N_h-j}\right),
\qquad j=0,\ldots,N_h-1. \qquad (2.1)
```

These lie in $`[0,1]`$ and are nonincreasing in $`j`$. The hypergeometric zero-finding probability of each stratum equals

```math
p_h(q;n_h)=\prod_{j=0}^{q-1}a_{h,j},\qquad p_h(0;n_h)=1. \qquad (2.2)
```

**Proof.** When $`q\le N_h-n_h`$, the ratio of binomial coefficients can be written as the ratio of falling factorials $`(N_h-n_h)_q/(N_h)_q`$, which gives the product. When $`q>N_h-n_h`$, the numerator binomial coefficient is 0, and the product also contains a 0. On the nonzero segment, $`a_{h,j}=1-n_h/(N_h-j)`$ is nonincreasing in $`j`$, and the truncated zero tail is still nonincreasing. When $`n_h=0`$ the whole chain is 1; when $`n_h=N_h`$ the whole chain is 0. ∎

**Proposition LV2 (global top-$`s`$ is compatible with the prefix constraint).** Merge the marginal chains of all strata into one multiset; the product of its $`s`$ largest numbers is exactly $`R_K(n;s)`$. A count vector attaining the worst-case risk can be obtained by the following procedure: start with 0 factors from every stratum; at each step, among the current head factors of the chains not yet exhausted, pick the largest, increase that stratum's count by 1, and repeat $`s`$ times.

**Proof.** Every valid count vector takes exactly one prefix from each chain, for a total of $`s`$ factors. Ignoring the prefix constraint, any such product is at most the product of the $`s`$ globally largest factors, because all factors are nonnegative. On the other hand, the maximum of the remaining part of each chain is at its current head; hence each choice of the largest current head is also a choice of a maximum among all unchosen factors. Induction shows that the $`s`$ steps select exactly a global top-$`s`$ multiset, while always satisfying the prefix constraint. This attains the unconstrained upper bound and also gives a valid worst-case configuration. Ties may be broken by taking any current head without breaking feasibility; if the top-$`s`$ contains a 0, the optimal product is 0. ∎

Maintaining at most $`d`$ current heads in a max-heap, a risk evaluation takes $`O(d+s\log\,d)`$ bookkeeping/comparison operations; the bit complexity of rational comparisons and products is counted separately. This result does not require equal $`N_h`$, equal $`n_h`$, or equal audit costs. Costs do not enter the risk computation for fixed quotas.

Boundary conventions: when $`s=0`$ the empty product is 1; when $`s>\sum_hN_h`$ there is no configuration to rule out, and the risk is defined as 0. For a valid nonempty bad-configuration problem, the $`s`$ given by LV1 does not cross these boundaries. A positive product must not be mistaken for 0 after probability underflow; implementations should use exact fractions/integer comparisons.

## 3. LV3: a finite algorithm for the optimal fixed quota, and an optional symmetric reduction

Enumerate the $`\prod_h(N_h+1)`$ fixed quotas, compute the risk of each exactly with LV2, and take the lowest cost among all with $`R_K\le\alpha`$. This gives the global optimum for the class of procedures with fixed stratification, uniform sampling without replacement, and a certificate on all-zero findings: every valid design appears exactly once in the grid, the risk test is exact, and the minimum over a finite set is attained. This proof does not make the search a generally polynomial algorithm; when limits are exceeded, one can only report incomplete / the feasible cost upper bound found so far, and cannot claim optimal or infeasible.

If $`s\le N_h`$, placing all $`s`$ contaminations in stratum $`h`$ is a valid counterexample, so $`p_h(s;n_h)\le\alpha`$ is a necessary condition for each stratum and can be used to prune quotas that are too small. But these single-stratum conditions are in general not sufficient: contamination spread across strata may have a higher miss probability. If $`s>N_h`$, this unrealizable single-stratum counterexample must not be forced.

When all strata have size $`N`$ and equal costs, one can sort quotas in nondecreasing order and enumerate combinations with repetition; the sorted grid in all $`d`$ dimensions has $`\binom{N+d}{d}`$ points, and the optimum is unchanged. The symmetric formulas in this section normalize the common per-document cost to 1; when the common cost $`c`$ is restored, all cost expressions are multiplied by $`c`$, and the optimal quotas and risks are unchanged.

**Proposition LV3 (the total-count gate also allows lowering the tail, but with a different risk formula).** With equal sizes, equal costs, and $`s\le d`$, there is an optimal design of the form

```math
0\le n_1\le\cdots\le n_s\le N,\qquad
n_{s+1}=\cdots=n_d=n_s. \qquad (3.1)
```

Its cost is $`\sum_{i=1}^{s-1}n_i+(d-s+1)n_s`$; the risk can be computed by taking the top-$`s`$ factors from the first $`s`$ **complete marginal chains**. Hence it suffices to enumerate $`\binom{N+s}{s}`$ prefixes rather than the full $`d`$ dimensions.

**Proof.** After sorting, the head factors of the first $`s`$ chains are all at least $`x_s=1-n_s/N`$, so the original $`s`$-th largest global factor is at least $`x_s`$. Every factor of the later chains is at most that chain's head factor, which is at most $`x_s`$. Lowering all later quotas to $`n_s`$, every factor of these new chains is still at most $`x_s`$. They cannot displace any top factor strictly greater than $`x_s`$; they can only replace tied values at positions equal to $`x_s`$, so the top-$`s`$ values and their product are unchanged, and the cost weakly decreases. The first $`s`$ chains already supply at least $`s`$ factors no lower than this threshold, so the tail chains can also be omitted from the risk evaluation. Conversely, every prefix explicitly gives a valid full quota, so no optimum is lost. ∎

This resembles the quota shape of IA8, but **IA8's risk "product of the first $`s`$ head factors" must not be carried over**: a total-count adversary may place several contaminations in the same stratum, so the complete chains must be kept. When $`s>d`$, the prefix length can be taken to be $`d`$, and no such dimension reduction occurs. With unequal sizes/unequal costs, the symmetric argument cannot be applied directly. The new reduction in this section is a mathematical interface; whether it has been used in an implementation should be determined from the actual code and records of the comparison script.

## 4. Conditions under which location necessarily has no value

**Single-stratum conclusion.** If $`d=1`$, then whatever the document impact graph, as long as the smallest size of a nonempty bad configuration is $`s`$,

```math
R_I(n)=p_1(s;n)=R_K(n;s),\qquad C_I^*=C_K^*. \qquad (4.1)
```

Proof: every bad configuration has size at least $`s`$, and the miss probability is nonincreasing in size; some bad configuration of size $`s`$ exists and attains this upper bound. Uniform sampling within a single stratum does not distinguish where the contamination is located, so it cannot gain anything extra from a finer impact graph. ∎ Location information can change the cost of zero-finding designs of this kind only when combined with sampling designs/stratifications that can tell locations apart.

**General sufficient condition.** If every valid stratum count vector with $`\sum_hq_h=s`$ can be realized by some bad configuration, then $`R_I(n)=R_K(n;s)`$ for every $`n`$. The reason is that the maximizing vector of the total-count risk can itself be realized by a bad configuration, and combining this with the reverse inequality from LV1 gives equality. It is not necessary that every location configuration with the same counts be bad. More weakly, for a fixed $`n`$, equality holds as soon as one worst-case total-count vector can be realized by a bad configuration.

This is not a complete characterization by a necessary condition. Strata with zero sampling create risk plateaus, and larger bad configurations may also attain the same maximum risk. This file does not misstate an easily checked sufficient condition as an if-and-only-if.

In addition, if general non-rectangular count sets are allowed, the safe downset "no member of the bad count antichain is dominated by the current count" already reproduces the direct test exactly; see the IA addendum and Section 6 of the paper. What this round compares is the information lost by **a single fixed total-count upper bound**, not a claim to beat every count confidence method.

## 5. LV4: a universal constant upper bound for homogeneous $`r`$-of-$`d`$

Let $`1\le r\le d`$, with exactly $`N\ge1`$ documents per stratum and the same unit cost, and let a configuration be bad if and only if at least $`r`$ strata contain contamination. Then $`s=r`$, and the direct risk is the product of the $`r`$ largest head factors. With equal quotas $`n`$, the total-count risk is also exactly $`(1-n/N)^r`$: each stratum's marginal factors are at most its head factor, the product for any configuration with total $`r`$ is at most this value, and placing one document in each of $`r`$ strata attains it.

This structure can be realized concretely by majority voting: when $`r\le d\le2r-1`$, take $`m=2r-1`$ heads that are all originally correct, of which $`d`$ changeable heads correspond one to each stratum, and the remaining $`2r-1-d`$ are fixed trusted heads. The result can change only if at least $`r`$ changeable heads change. The algebraic bounds that follow use only the declared $`r`$-of-$`d`$ badness and cover more general homogeneous threshold constructions.

**Proposition LV4.** For the nonempty problem above,

```math
1\le\frac{C_K^*}{C_I^*}\le\frac{d}{d-r+1}. \qquad (5.1)
```

**Proof.** Take a direct optimal quota and sort it as $`n_1\le\cdots\le n_d`$. Its maximum miss probability is $`\prod_{i=1}^r(1-n_i/N)\le\alpha`$. Since each of the first $`r`$ factors is at least $`1-n_r/N`$, we have $`(1-n_r/N)^r\le\alpha`$, so auditing $`n_r`$ in every stratum is a feasible total-count design, with cost $`dn_r`$. The original design has at least $`d-r+1`$ strata with quota at least $`n_r`$, so $`C_I^*\ge(d-r+1)n_r`$. The all-zero quota has risk 1, so a feasible design has $`n_r>0`$ and positive cost, and we can divide. Combining with $`C_I^*\le C_K^*`$ gives the result. ∎

This yields a necessary geometric condition: if $`(d-r+1)/d`$ is bounded below by a positive constant along a sequence of problems, the ratio of the gain from location relative to the optimal total-count gate has a constant upper bound. To obtain an unbounded ratio in this homogeneous family, the slack $`d-r+1`$ in the number of strata allowed to be uncontaminated must become smaller and smaller relative to $`d`$. It is not a sufficient condition; later we give an all-strata conjunction family that does attain a linear gap.

### The original $`d=2r-1`$ family: less than 2, and the constant 2 can be approached

Substituting directly into LV4 gives

```math
1\le C_K^*/C_I^*\le (2r-1)/r<2. \qquad (5.2)
```

Hence the earlier $`\Omega(r)`$ separation against rectangle gates cannot be carried over as an order-of-magnitude gain against the optimal total-count gate. This constant upper bound is sharp when $`r,N`$ vary jointly. Fix $`\alpha`$, let $`N\to\infty`$, $`r=N^2`$, and take

```math
k_N=\left\lceil\frac{\log(1/\alpha)}{-\log(1-1/N)}\right\rceil=O(N). \qquad (5.3)
```

Here $`N\ge2`$; for sufficiently large $`N`$, $`1\le k_N\le r`$. Under this explicit condition, leave $`r-k_N`$ strata unaudited and audit one document in each of the remaining $`r+k_N-1`$ strata; then the product of the $`r`$ largest head factors is $`(1-1/N)^{k_N}\le\alpha`$, so $`C_I^*\le r+k_N-1`$. A finite parameter check must first verify $`k_N\le r`$; for example, with $`\alpha=1/20,N=2`$, $`k_N=5>r=4`$, this particular quota cannot be used, and one must not generate a negative number of unaudited strata or report an invalid upper bound as a result.

The number $`u`$ of unaudited strata in any feasible total-count design must satisfy $`uN\lt r`$; otherwise the adversary can place all $`r`$ contaminations in the unaudited strata, with miss probability 1. Each remaining stratum audits at least one document, so

```math
C_K^*\ge 2r-1-\left\lfloor\frac{r-1}{N}\right\rfloor=2N^2-N. \qquad (5.4)
```

Combining $`k_N=O(N)`$ with LV4,

```math
\frac{2N^2-N}{N^2+k_N-1}\le\frac{C_K^*}{C_I^*}<2,
\qquad C_K^*/C_I^*\longrightarrow2. \qquad (5.5)
```

The reason for $`k_N=O(N)`$ is that $`-\log(1-1/N)\ge1/N`$, so $`k_N\le N\log(1/\alpha)+1`$. This is an exact squeeze between upper and lower bounds on the cost sequence, not a random large-sample approximation.

### The original paper's $`N=r^2`$ sequence: the ratio tends to 1, a stronger statement

The previous sharp construction uses $`r=N^2`$, whereas the original paper's rectangle separation uses the reverse scaling $`N=r^2`$. The two must not be confused. For $`d=2r-1`$, let $`a=\log(1/\alpha)>0`$; the following lower bound is valid for all $`N,r`$:

```math
C_I^*\ge \frac{Nadr}{r^2+ad}. \qquad (5.6)
```

**Proof.** Write the direct optimal total cost as $`M`$; after sorting, $`n_r\le M/r`$. If $`M\ge rN`$, the displayed lower bound is less than $`rN`$, and the result holds automatically. Otherwise the first $`r`$ values $`x_i=n_i/N`$ are all less than 1, and $`x_i\le M/(rN)`$. Using $`-\log(1-x)\le x/(1-x)`$ and, under the sorting, $`\sum_{i=1}^r n_i\le rM/d`$, we get

```math
a\le\sum_{i=1}^r-\log(1-x_i)
\le\frac{rM/(dN)}{1-M/(rN)}. \qquad (5.7)
```

Rearranging with the positive denominator gives the lower bound. ∎ On the other hand, the balanced total-count design gives $`C_K^*\le d[N(1-e^{-a/r})+1]\le d(Na/r+1)`$. Hence

```math
1\le\frac{C_K^*}{C_I^*}
\le\left(1+\frac{r}{Na}\right)\left(1+\frac{ad}{r^2}\right). \qquad (5.8)
```

Fix $`\alpha`$, take $`N=r^2`$, and let $`r\to\infty`$; the right-hand side tends to 1. **On the same sequence that earlier showed the $`\Omega(r)`$ gap against rectangles, the direct method and the optimal total-count gate are asymptotically equivalent.** This is one of the most useful negative results of this round for the original claim; it must not be omitted while keeping only favourable constants such as 38 versus 48.

## 6. LV5: an all-strata conjunction has a linear gap, but a single rectangle is already optimal

Next take $`r=d\ge2`$ with $`N=2`$ per stratum, and let a configuration be bad if and only if every stratum contains contamination. A concrete voting realization uses $`d`$ changeable heads plus $`d-1`$ fixed correct heads, $`2d-1`$ heads in total; each document affects only its corresponding changeable head. Within this outer-relaxation model, where affected heads may change their outputs arbitrarily, every document belongs to some minimal bad configuration, and there is no padding with documents that have no effect; this is not a measured conclusion about actual retraining sensitivity.

Fix $`0<\alpha<1/2`$ and write

```math
\kappa=\min\{k\ge1:2^{-k}\le\alpha\}\ge2. \qquad (6.1)
```

**Proposition LV5.** The direct optimal cost and the optimal cost of the strongest safe rectangle are both 2. The optimal cost of the strongest total-count gate $`\left\vert C\right\vert\le d-1`$ is

```math
C_K^*=d+1\quad(d<\kappa),\qquad
C_K^*=\left\lceil\frac{d+\kappa}{2}\right\rceil\quad(d\ge\kappa). \qquad (6.2)
```

**Proof: direct and rectangle.** Taking a census of the two documents in any one stratum, all-zero findings prove that stratum is uncontaminated, so the all-strata conjunction cannot hold; cost 2 is feasible. This is itself a safe rectangle that sets only that stratum's count upper bound to 0 and the other strata's upper bounds to 2. Cost 0 has risk 1, and cost 1 can only audit one document in one stratum; the bad configuration with one document in each stratum then has miss probability 1/2, which exceeds $`\alpha`$. So no lower cost exists, and both optima are 2.

**Proof: total-count gate.** Write $`u,v,w`$ for the numbers of strata with quota 0, 1, 2, so $`u+v+w=d`$. The marginal factors are, in order: $`2u`$ ones, $`v`$ halves, and zeros for the rest. The total-count gate takes the top-$`d`$ factors.

If $`2u\ge d`$, the risk is 1 and the design is infeasible. If $`2u\lt d\le2u+v`$, the risk is $`2^{-(d-2u)}`$; feasibility requires $`d-2u\ge\kappa`$. The cost $`v+2w=d-u+w`$ is then at least $`d-\lfloor(d-\kappa)/2\rfloor=\lceil(d+\kappa)/2\rceil`$, attained by $`w=0`$, $`u=\lfloor(d-\kappa)/2\rfloor`$. This branch exists if and only if $`d\ge\kappa`$.

In the remaining case $`2u+v\lt d`$, the risk is 0. From $`d=u+v+w`$ we get $`w>u`$, so the cost $`d-u+w\ge d+1`$; $`u=0,w=1,v=d-1`$ attains it. If $`d\ge\kappa`$, the previous cost is at most $`d`$ and so beats the zero-risk scheme; otherwise only this zero-risk scheme is feasible. ∎

With $`\alpha=1/20`$, $`\kappa=5`$, so the cost is $`d+1`$ for $`d<5`$ and $`\lceil(d+5)/2\rceil`$ for $`d\ge5`$, while the direct cost is always 2, giving a ratio of $`\Theta(d)`$. All stratum sizes, audit costs, and numbers of heads affected per document are identical; the gap comes from the geometric structure "every stratum is touched" and from the inability of total-count aggregation to distinguish concentrated from spread-out contamination.

However, this example also proves that **a complex direct optimizer is unnecessary**: the single rectangle gate that takes a census of any one stratum already attains the optimum. In the original family, the total-count gate beats rectangles; in this family, rectangles beat the total count. Neither baseline dominates the other in general.

## 7. A star family with heterogeneous impact: another localization mechanism

As a supplement, take a center stratum 0 and $`L\ge1`$ leaf strata, $`d=L+1`$, with $`N\ge2`$ per stratum. The model has $`2L+1`$ heads that are all originally correct: center documents affect $`L`$ center heads, each leaf-stratum document affects one corresponding leaf head, and there is one more fixed correct head. Badness is exactly "the center contains contamination and at least one leaf stratum contains contamination". Within the same outer-relaxation impact model, every document belongs to a minimal bad pair, and the smallest bad size is 2; this is not taken as a claim that a real trainer can realize arbitrary corresponding outputs.

The direct optimal cost is $`\lceil N(1-\alpha)\rceil`$: auditing only the center up to this number suffices; conversely, every center–leaf pair must satisfy $`(1-n_0/N)(1-n_i/N)\le\alpha`$, and the product is at least $`1-(n_0+n_i)/N`$, which forces total cost at least $`\lceil N(1-\alpha)\rceil`$. The single rectangle gate "the center is uncontaminated" again attains this direct optimum.

The risk of the total-count gate $`\left\vert C\right\vert\le1`$ is the maximum over two types: "two documents in the same stratum" and "one document in each of two strata". After sorting quotas $`a=n_1\le b=n_2\le\cdots`$, the same-stratum risk is largest for the first stratum, and the cross-stratum risk is largest for the first two strata. Hence its exact optimum equals

```math
\min_{0\le a\le b\le N}\{a+(d-1)b:
p_h(2;a)\le\alpha, (1-a/N)(1-b/N)\le\alpha\}. \qquad (7.1)
```

The proof lowers all subsequent quotas to $`b`$, which leaves both worst-case risks unchanged and weakly lowers the cost, and then enumerates all integers $`a,b`$. Let $`u=\min\{n:p_h(2;n)\le\alpha\}`$ and $`v=\lceil N(1-\sqrt\alpha)\rceil`$. Because $`p_h(2;v)\le(1-v/N)^2\le\alpha`$, we have $`u\le v`$. The first entry of any feasible sorted quota is at least $`u`$, and the second must be at least $`v`$ (the product of the two head factors is at least the square of the second head factor). Hence

```math
u+(d-1)v\le C_K^*\le dv. \qquad (7.2)
```

With $`N\ge2,\alpha`$ fixed, the total-count gate cost is $`\Theta(L)`$ while the direct cost is constant, giving an order-of-magnitude gap without padding by documents that have no effect. But knowing "the center is uncontaminated" is the optimal simple strategy, and badness can even be described exactly by the occupancy-weighted score $`L𝟏\{q_0>0\}+\sum_{i=1}^L𝟏\{q_i>0\}\ge L+1`$; this example should not be packaged as showing that a general advanced graph algorithm is necessary.

## 8. Combined baselines, finite checks, and research status

The exact comparisons above lead to a stricter comparison standard: for the same problem, report at least the direct method, the strongest fixed total-count gate, the strongest safe joint zero-finding rectangle, and the cheaper of the two simple methods. One must not choose only the rectangle in the original threshold example and only the total count in the conjunction example, and then merge their respective advantages into "generally beats simple methods". This file does not prove a general order-of-magnitude advantage of the direct method over this combined baseline.

Nor does the combined baseline equal the direct method in every finite example. Take, for example, the original family with $`r=6,d=11,N=2,\alpha=1/20`$: one unaudited stratum plus ten strata each auditing one document gives direct risk $`1/32`$ at cost 10. A cost below 10 is infeasible: if the sixth-smallest quota is 1, at least five of the first six quotas must be 1, so at most one stratum can be unaudited; if the sixth-smallest quota is 2, at least six strata take a census, which already costs 12; if the sixth-smallest is 0, the risk is 1. Hence the direct optimum is 10.

In this example the total-count gate optimum is 11: if at least one stratum is unaudited, the top-6 contains at least two 1s; as long as the rest can be filled with 1/2, the risk is at least $`1/16>1/20`$, so feasibility can only rely on a 0 appearing in the top-6, i.e. the total number of positive factors $`2u+v\le5`$. The cost $`v+2w=22-(2u+v)\ge17`$. With no unaudited stratum, auditing one document in each of all 11 strata gives risk $`1/64`$ and cost 11; adding any census only increases the cost, so the optimum is 11. The rectangle optimum is 12. So the direct method has a finite strict gap even against this combined baseline, but **10 versus 11 is still only a structural diagnostic, not evidence of additional innovation or practical value**.

**A sharp constant gain over the combined baseline still exists.** Write $`C_S^*=\min(C_K^*,C_{\rm box}^*)`$. On the $`r=N^2,d=2r-1`$ path of Section 5, the cost of the strongest safe joint zero-finding rectangle is $`C_{\rm box}^*=r\lceil N(1-\alpha)\rceil=\Theta(N^3)`$: a safe rectangle sets the count upper bound of at least $`r`$ strata to 0, and each of these strata must be audited up to this number; leaving the other strata unaudited attains this value. On the other hand, for sufficiently large $`N`$, auditing one document in each of all $`d`$ strata makes the total-count risk $`(1-1/N)^r\le e^{-N}\le\alpha`$, so $`C_K^*\le d=\Theta(N^2)`$. Hence, for sufficiently large $`N`$, the combined baseline necessarily picks the total-count gate, and the squeeze above directly gives

```math
\frac{C_S^*}{C_I^*}=\frac{C_K^*}{C_I^*}\longrightarrow2,
\qquad 1-\frac{C_I^*}{C_S^*}\longrightarrow\frac12. \qquad (8.1)
```

This proves that, relative to the combination of two strong simple methods, there is still a **sharp constant gain**, with the cost ratio approaching two and the saving approaching 50%; it does not prove an unbounded order-of-magnitude gain. Nor does it contradict the ratio tending to 1 under the reverse scaling $`N=r^2`$ of the original draft.

A finite bound checked by [this round's rational check record](../planning/localization_results.json) is $`\alpha=1/20,N=32,r=1024,d=2047`$: $`C_I^*\in[1024,1118]`$, $`C_K^*=C_S^*\in[2016,2047]`$, and the rectangle cost is 31744. Hence

```math
1-\frac{C_I^*}{C_S^*}\ge1-\frac{1118}{2016}=\frac{449}{1008}\approx44.54\%. \qquad (8.2)
```

This lower bound compares global optimal costs and comes from a feasible upper bound for the direct method and a necessary lower bound for the combined baseline; it is **not** a claim that the exact optima of both sides were computed, nor a measured audit saving. The record marks such points as `bounds_only`, separately from the 44 points where exact fixed-design optimization was completed. On the exact small grid, most points show no gain over the combined baseline, which cannot be extrapolated to no gain for all structures; conversely, this exploratory favourable sequence cannot retroactively count as passing a pre-set gate.

All proofs here are conditional on the contract of a fixed impact graph, statistic envelope, sampling, and ground truth. No new real audits were added, and no constructed input is called a natural model. The pen-and-paper derivations in this file do not depend on numerical sweeps; the independent implementation and execution records are in the JSON above. An independent binomial-coefficient DP and checks on small complete grids are used for code verification and do not replace the proofs. This round's use of the 20 cells already seen in round 7 is a review of the extended baselines, not a new blind confirmation set; the conjunction/star structures must likewise keep their complete parameter families and execution budgets set in advance, and favourable points must not be cherry-picked.

The judgement from this round most worth keeping is: **the value of location information is determined jointly by the geometry of bad configurations and the available audit designs.** With a single stratum it has no value; the original majority-threshold family has an advantage of at most a factor of two, which vanishes at the original asymptotic scaling; the critical all-strata conjunction can have an order-of-magnitude gap, but it is attained by a simple local census. Further research that aims to go beyond established finite-population combinatorics must explain what real impact structures, auditable ground truth, and broader simple strategies still cannot solve the target. The current conclusions do not establish originality, a non-vacuous certificate for a realistic model, or G0/G1 passing.

## 9. Record of proof obligations and applicability

| Obligation | Status | How closed |
|---|---|---|
| Largest safe total-count gate and exact risk | CLOSED-LOCAL | LV1 smallest bad size and zero-finding counts |
| Worst-case configuration from prefix greedy | CLOSED-LOCAL | LV2 global top factors and reachability on nonincreasing chains |
| Fixed optimal quotas and lowering the tail | CLOSED-LOCAL | LV3 finite enumeration, threshold argument for homogeneous chains |
| Sufficient conditions for no location value | CLOSED-LOCAL | Section 4 single stratum and realizability of the worst-case count |
| Original homogeneous family below 2, and sharp 2 | CLOSED-LOCAL | LV4 order statistics and lower bound from unaudited capacity |
| Asymptotic equivalence on the original $`N=r^2`$ sequence | CLOSED-LOCAL | Finite log lower bound plus balanced total-count upper bound |
| Sharp constant 2 over the strong simple combination | CLOSED-LOCAL | On the $`r=N^2`$ path the rectangle cost has a higher order, so the combination eventually picks the total-count gate |
| Exact total-count cost for the conjunction family | CLOSED-LOCAL | LV5 exhaustive case split by the number of strata auditing 0/1/2 |
| Star family and finite combined-baseline examples | CLOSED-LOCAL | Sections 7–8 feasible solutions and matching integer lower bounds |

"CLOSED-LOCAL" refers only to pen-and-paper derivations under the given assumptions. Equal stratum sizes/equal costs are used only for the explicitly marked symmetric and ratio conclusions; the general risk greedy does not need them. The strongest total-count gate is still bound by the contract of fixed stratification, uniform sampling without replacement, and reporting on all-zero findings; it does not cover adaptivity, reselecting the population, model co-design, or arbitrary non-rectangular confidence sets. An internal review is not an external referee's opinion; no unverified literature citations or claims of exhaustive prior-work search are made.
