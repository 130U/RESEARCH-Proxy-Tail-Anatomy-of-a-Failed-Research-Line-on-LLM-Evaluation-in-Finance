# Collective accuracy and macro-F1 envelopes on a fixed test set

Date: 2026-11-15. Status: the finite combinatorial propositions below have complete pen-and-paper proofs; the examples were checked offline by exhaustive enumeration with the Python standard-library `Fraction`. No internet access, no training, no real data; no novelty claim is made. This file extends [T1.3–T1.5](notes.md) and deals specifically with jointly affected shards and with macro-F1, which is not additive.

## 1. Objects, assumptions, and what "tight" means

The fixed test set has J≥1 indexed examples, m≥1 shard heads, and K≥1 classes. The vote matrix is V∈{0,…,K−1}^{J×m}, and the true labels are y_j∈{0,…,K−1}. Every head has equal weight; the winner is the class with the most votes, and ties go to the smallest index. k is a nonnegative integer, and we write b_max=min(k,m). The class list is fixed before computation and does not change depending on whether a candidate prediction contains a given class.

Threat model: a single head set B⊆{1,…,m} acts jointly on all test points, with |B|≤b_max. Votes outside B are fixed; the vote of each head in B at each test point can be set arbitrarily and can vary freely across points. Some votes in B are allowed to keep their original values, so B is the set of heads that are "allowed to be affected"; not every member is required to change.

This is looser than real retraining: a modified deterministic model must produce the same output on the same input, and the output must be realizable by the training process. This model imposes neither restriction; it even allows two indexed test points with the same input to receive different modified votes. Hence "exact" and "tight" below refer only to this explicitly stated outer-relaxation threat model and **do not mean the tightest certificate for the real training process**. Whether deleting at most k documents falls inside this threat model still depends on the premises of T1.3: fixed IDs, deterministic per-shard training, and an uncontaminated shared backbone.

The test examples, true labels, per-class supports, and the denominator J are fixed. We do not re-split the test set, redefine classes, or recompute filtered sets that depend on predictions. This is an envelope on a test-set statistic, not a population generalization interval, and it does not constrain returns or investment performance.

## 2. Exact reachable label set for a fixed B

Let b=|B|, and let the unmodified vote counts be

```math
u_{jc}(B)=\#\{h\notin B:V_{jh}=c\}.
```

Define

```math
R_j(B)=\left\{c:\ \forall d\ne c,\quad
u_{jc}(B)+b\ge u_{jd}(B)+𝟏\{d\lt c\}\right\}.
```

**Proposition CM1.** R_j(B) is exactly the set of winning classes reachable at the j-th point under the threat model with B fixed, and every vector (c₁,…,c_J)∈∏_jR_j(B) can be realized simultaneously.

**Proof.** If c can win under some modification, its total vote count is at most u_jc+b, and every other class d has a total of at least u_jd. Winning requires strictly one more vote than each d<c and at least a tie with each d>c, so the set condition is necessary. Conversely, changing all b votes in B to c gives c a total of u_jc+b and leaves every competitor at u_jd, so the set condition is sufficient. Finally, for each point j, let every head in B output the chosen c_j; the assumption of freedom across points ensures that these choices can be realized jointly. ∎

R_j(B) is always nonempty: keeping all original votes is an allowed modification, so the original winner is reachable. When b=0, R_j(B) is the singleton containing the original winner.

**Why not just use vote margins?** Once B is fixed, one must know which heads voted for which class. A pointwise formula based only on total vote counts erases the correlation of head identities across test points; the common B is exactly the source of information for the collective tightening.

## 3. Enumerating only maximum-budget sets suffices

**Proposition CM2.** B⊆B' implies R_j(B)⊆R_j(B'). Hence, for any fixed test-set statistic S, the maximum/minimum under the threat model with |B|≤b_max equals the maximum/minimum obtained by optimizing only over |B|=b_max.

**Proof.** Keeping the original votes in B'\B reproduces exactly any vote pattern allowed by B. The set inclusion holds pointwise, and the feasible region for the whole vote matrix is nested as well. Any smaller set can be enlarged to b_max heads, so the union of feasible regions over budgets ≤ b_max equals the union over sets of exactly the maximum budget. ∎

This reduction relies on the "at most affected" meaning. If another threat model requires every selected head to actually change its vote at every point, the reduction cannot be used directly.

## 4. Tight collective envelope for accuracy

For fixed B, define

```math
L_{\rm acc}(B)=\frac1J\sum_{j=1}^J𝟏\{R_j(B)=\{y_j\}\},\qquad
U_{\rm acc}(B)=\frac1J\sum_{j=1}^J𝟏\{y_j\in R_j(B)\}.
```

**Proposition CM3.** These two numbers are the exact minimum and maximum of accuracy for fixed B. The exact extremes under the full threat model are

```math
L_{\rm acc}^{\rm coll}=\min_{\left\vert B\right\vert=b_{\max}}L_{\rm acc}(B),\qquad
U_{\rm acc}^{\rm coll}=\max_{\left\vert B\right\vert=b_{\max}}U_{\rm acc}(B).
```

**Proof.** At each point, the worst-case prediction is guaranteed correct only when the reachable set is exactly the singleton of the true label; whenever the true label is reachable, a correct prediction exists. CM1 guarantees that these worst/best labels can be chosen simultaneously across points. Taking extremes over the finitely many B and applying CM2 gives the exact extremes under the full threat model. ∎

For the usual pointwise relaxation, let R_j^union=∪_{|B|≤b_max}R_j(B) and let each point choose its label independently from this union. Because it allows different points to use different B, this feasible region contains the collective feasible region, so

```math
L_{\rm acc}^{\rm union}\le L_{\rm acc}^{\rm coll}\le
U_{\rm acc}^{\rm coll}\le U_{\rm acc}^{\rm union}.
```

The tightening can be strict; see Section 7. Accuracy is additive over points, which is exactly why CM3 decomposes exactly; macro-F1 below cannot be treated this way.

## 5. Macro-F1: a componentwise safe outer envelope

Fix a class c, and let a_c=Σ_j1{y_j=c} be the fixed actual support. For a candidate prediction vector z, the true positives and false positives are

```math
t_c=\sum_j𝟏\{y_j=c,z_j=c\},\qquad
f_c=\sum_j𝟏\{y_j\ne c,z_j=c\}.
```

We use the fixed-K-class macro average with the `zero_division=0` convention:

```math
F_c(t_c,f_c)=
\begin{cases}
2t_c/(a_c+t_c+f_c),&a_c+t_c+f_c>0,\\
0,&a_c+t_c+f_c=0,
\end{cases}
\quad
F_{\rm macro}=K^{-1}\sum_cF_c.
```

When a_c=0, t_c must be 0 and the class F1 is identically 0, including the case where the class is never predicted. Classes without support are not removed from K here. Automatic label inference in different libraries may use different denominators, so the fixed class list must be passed explicitly and the zero-denominator convention must be set.

For the reachable sets with B fixed, define the integer endpoints

```math
\begin{aligned}
t_c^{\min}(B)&=\#\{j:y_j=c,\ R_j(B)=\{c\}\},\\
t_c^{\max}(B)&=\#\{j:y_j=c,\ c\in R_j(B)\},\\
f_c^{\min}(B)&=\#\{j:y_j\ne c,\ R_j(B)=\{c\}\},\\
f_c^{\max}(B)&=\#\{j:y_j\ne c,\ c\in R_j(B)\}.
\end{aligned}
```

Let

```math
\ell_c(B)=F_c(t_c^{\min},f_c^{\max}),\qquad
u_c(B)=F_c(t_c^{\max},f_c^{\min}),
```

and average over classes to obtain L_macro^comp(B)=K⁻¹Σ_cℓ_c(B) and U_macro^comp(B)=K⁻¹Σ_cu_c(B).

**Proposition CM4.** For every reachable prediction vector with B fixed,

```math
L_{\rm macro}^{\rm comp}(B)\le F_{\rm macro}\le U_{\rm macro}^{\rm comp}(B).
```

Taking the smallest lower bound and the largest upper bound over all |B|=b_max still gives a safe envelope for the full threat model, but in general not the exact extremes.

**Proof.** By the definition of the reachable sets, t_c and f_c lie in the listed integer endpoint intervals. When a_c>0, 2t/(a_c+t+f) is nondecreasing in t and nonincreasing in f: the corresponding partial derivatives are 2(a_c+f)/(a_c+t+f)²≥0 and −2t/(a_c+t+f)²≤0. Hence each class lies in [ℓ_c,u_c]. When a_c=0, every feasible t=0, the term is identically 0, and the zero-denominator convention gives the same conclusion. Summing over classes gives the envelope. Every actual common B is contained in its corresponding envelope, so taking the outer extremes over B is still safe. ∎

**Exact per class does not mean exact for the macro average.** For a fixed c, the choice of t involves only points whose true label is c, and the choice of f involves only the other points, so the two use disjoint examples; CM1 guarantees that (t_min,f_max) and (t_max,f_min) can each be realized. Hence ℓ_c and u_c are the exact extremes of the single-class F1. However, the extremes for different c often require the same misclassified example to be predicted as several mutually exclusive classes at once, so they cannot be attained jointly. Section 8 gives an example where the componentwise envelope is strictly wider than the true macro-average range.

If the same componentwise bounds are computed with R_j^union instead, set inclusion shows that for each B, t_min ≥ the union t_min, t_max ≤ the union t_max, f_min ≥ the union f_min, and f_max ≤ the union f_max. Hence the collective componentwise envelope is never wider than the corresponding componentwise envelope built from the union. But do not conflate the width of the componentwise envelope with the width of a separate exact oracle under the label "tightness of collective optimization".

## 6. Exact oracle for small-scale macro-F1

### Confusion-matrix DP

Fix B, and let C∈N^{K×K} be the confusion count matrix, with rows indexed by the true label and columns by the predicted label. Initialize D₀={zero matrix}. Process the points one at a time:

```math
D_j=\{C+E_{y_j,c}:C\in D_{j-1},\ c\in R_j(B)\},
```

where E_rc is 1 only at position (r,c); identical count matrices are deduplicated. Finally, for every C∈D_J compute

```math
F_{\rm macro}(C)=\frac1K\sum_c
\frac{2C_{cc}}{a_c+\sum_rC_{rc}},
```

with terms whose denominator is zero set to 0, and take the minimum and maximum.

**Proposition CM5.** The final states of this DP are exactly all reachable confusion matrices for fixed B, so it computes the exact extremes of macro-F1. Further enumerating B gives the exact collective extremes under the full outer-relaxation threat model.

**Proof.** Induction on j. At zero points there is only the zero matrix. Every feasible prediction vector on the first j points consists of a feasible vector on the first j−1 points and an allowed label c∈R_j(B), and the DP adds exactly its counts. Conversely, every label chosen by a DP transition is allowed and, by CM1, can be realized jointly across points. Hence nothing is missed and nothing extra is added; deduplicating states does not change the reachable counts. The statistic depends only on C, so optimizing over the final states is exact. ∎

### Sufficient-statistic DP (also exact)

When only macro-F1 is needed, the state can be compressed to (t₀,…,t_{K−1},p₀,…,p_{K−1}), where p_c is the number of points predicted as c. Choosing c sets p_c+=1, and if c=y_j also sets t_c+=1. At the end compute K⁻¹Σ_c 2t_c/(a_c+p_c). Any two prefixes with the same state have the same feasible future transitions, because in this threat model R_j(B) does not depend on past predictions, so merging states remains exact.

### Complexity, limits, and numerics

- The number of maximum-budget sets B to enumerate is binom(m,b_max); computing directly under "at most" would take Σ_{b≤b_max}binom(m,b), which CM2 avoids.
- Computing the reachable sets directly for each B takes O(JK²), plus O(Jm) for counting if the unmodified heads are rescanned each time. Accuracy and the macro componentwise statistics then take O(JK).
- Each DP step expands each state by at most K labels. The total number of confusion-matrix states is bounded by ∏_r binom(a_r+K−1,K−1), and in practice is limited by R; this can already be large. The number of compressed (t,p) final states is at most (J+1)^K·binom(J+K−1,K−1), and one still cannot assume a real test set is tractable.
- The "small-scale oracle" is an exact verification reference, not a guarantee of large-scale feasibility on a T4/CPU. If a cap on states or subsets is set, the code must explicitly return an incomplete/outer-envelope mode; the minimum and maximum after enumerating only part of the B sets are in general inner estimates and must not be passed off as a complete certified envelope.
- All counts are integers, and each F1 term and accuracy is rational. Proof-grade numerics should use integer cross-multiplication or `fractions.Fraction` for comparisons and output the reduced numerator/denominator. Decimals are for display only; if floating-point results are used as bounds, they must be rounded outward, not merely truncated to a few decimal places.

## 7. An example where the collective constraint strictly tightens both ends

Let K=2, m=2, k=1, J=4, with ties going to class 0:

| point j | head 1 | head 2 | true label |
|---:|---:|---:|---:|
| 1 | 0 | 1 | 0 |
| 2 | 1 | 0 | 0 |
| 3 | 0 | 1 | 1 |
| 4 | 1 | 0 | 1 |

With B={head 1}, the four R_j are, in order, {0,1}, {0}, {0,1}, {0}. With B={head 2}, they are {0}, {0,1}, {0}, {0,1}. The pointwise union at every point is {0,1}.

The pointwise relaxation can make every point correct, or every point wrong, so the exact pointwise ranges of both accuracy and macro-F1 are [0,1]. But every common B pins down one point with true label 0 and one with true label 1, and both are predicted as 0. The collective accuracy is therefore [1/4,3/4].

Take B={head 1}: only points 1 and 3 have a choice, and they give four prediction vectors:

| full prediction vector | accuracy | macro-F1 |
|---|---:|---:|
| (0,0,0,0) | 1/2 | 1/3 |
| (0,0,1,0) | 3/4 | 11/15 |
| (1,0,0,0) | 1/4 | 1/5 |
| (1,0,1,0) | 1/2 | 1/2 |

The other B gives the same range by symmetry. Hence the exact collective macro-F1 envelope is [1/5,11/15]. In this example the componentwise envelope happens to attain the same two endpoints, but this is not a general property.

A further zero-support check: keep only rows 1 and 2 of the table above, i.e. y=(0,0), with K=2 fixed. The collective accuracy is [1/2,1]; class 1 has no actual support and its F1 is identically 0, so the collective macro-F1 is [1/3,1/2], not the [2/3,1] obtained by dropping the missing class.

## 8. An explicit example where the componentwise macro-F1 bound is not tight

Let K=3, m=5, k=1, y=(0,1,2):

```math
V=\begin{pmatrix}
1&1&1&2&2\\
1&1&1&1&1\\
2&2&2&2&2
\end{pmatrix}.
```

Changing any one of the first three heads gives reachable sets ({1,2},{1},{2}); changing either of the last two heads gives ({1},{1},{2}). So the first point is always wrong and the other two are always right, and accuracy is identically 2/3.

When the first point is predicted as 1, the three class F1 values are (0,2/3,1); when it is predicted as 2, they are (0,1,2/3). Either way, macro-F1 equals 5/9, so the true collective range is [5/9,5/9].

But for a B with R₁={1,2}, the componentwise lower bound makes both classes 1 and 2 absorb the false positive from this misclassified point, giving (0+2/3+2/3)/3=4/9; the componentwise upper bound lets neither absorb it, giving (0+1+1)/3=2/3. The final componentwise collective envelope is [4/9,2/3]. These two fictitious extremes cannot be realized jointly, yet the envelope still safely contains 5/9.

Implementation output must therefore distinguish `component_outer_bound` from `exact_relaxed_oracle`, and must state whether a bound comes from a complete enumeration of B. The whole macro-F1 must not be labelled exact merely because the per-class endpoints are exact.

## 9. Budget saturation, combination with audits, and stopping conditions

- When k≥m, always normalize to b_max=m; there is only one maximum set, B = all heads, and every R_j is the set of all K classes.
- If K≥2, the accuracy range under the full threat model is [0,1]. The macro-F1 range is [0,s/K], where s=#{c:a_c>0}: predicting everything correctly gives F1=1 for every supported class, while unsupported classes are identically 0; changing every point to any wrong label makes all true positives 0. In this case the interval is not always [0,1], because the zero-support convention for fixed classes limits the maximum of the macro average.
- When K=1, all points and predictions are the single class, and J≥1 guarantees accuracy = macro-F1 = 1. J=0, m=0, invalid labels, or a negative budget should be rejected; the zero-denominator convention must not be used to mask the absence of anything to evaluate.
- Given an audit upper bound K_u, applying this envelope with budget min(K_u,m), when the other conditions of T1.5 all hold, gives a clean-comparator test-set envelope at confidence level at least 1−α. Accuracy and macro-F1 are both deterministic consequences of the same event "the true number of affected shards does not exceed the budget", so reporting both does not require paying α again for each metric. Other failure events, for the audit or for population generalization, are still combined according to their valid guarantees.
- Uncertain true labels, selection bias in the evaluation examples, a contaminated shared backbone, and unmeasurable ID/selection rules are not repaired by these combinatorial formulas. Whether only k heads could change in the original training requires separate evidence.

## 10. Review and deliverable criteria

The numbers in the three groups of examples above were checked locally item by item by enumerating head sets with integers, taking the Cartesian product of pointwise reachable labels, and computing with `Fraction`; there is no sampling error, and no confidence intervals are reported. The expected acceptance criteria at the program level are:

1. On small J, m, K, the formula R_j(B) agrees with enumerating all vote changes within B; no implementation may miss a reachable class.
2. The collective formula for accuracy agrees with full enumeration of vote changes/labels.
3. The macro componentwise envelope contains every value of the exact DP/oracle, and reproduces the strict looseness of Section 8.
4. The exact oracle agrees with direct enumeration of small-scale prediction vectors; zero support, k=0, k≥m, and K=1 are all handled according to the conventions of this file.
5. When the subset/state budget is exceeded, no pseudo-exact result is returned; raw rational outputs can be recomputed, and decimal displays are not treated as strict endpoints without rounding control.

This is a set of mathematical interfaces needed by an executable certificate, not evidence that "a non-vacuous certificate has been obtained on a real financial model". The next research question can be stated as: for a fixed data source and audit confidence level, how much can the common-head structure of the actual vote matrix improve the frontier between audit cost and statistical interval width? This file only makes the target quantity and the correctness criteria of that question explicit.
