# Pairwise comparison and multi-ranking aggregation on a fixed set of 32 items

This memo specifies the mathematical meaning of the aggregate quantities, for use in this round's comparison of isolated model sessions. The object is one fixed set $`D=\{1,\ldots,N\}`$, $`N=32`$; the two model configurations are written $`M\in\{A,B\}`$, and each method keeps two panels, $`h\in\{1,2\}`$. A higher score means closer to the positive end of the ranking specified in advance for this round; it does not represent a calibrated probability or financial utility.

**The current pairwise implementation uses batched judgments: each model × panel × orientation is split into 4 fixed fresh agents, each reading the 32 texts and 124 specified pairs, returning 496 judgments in total.** The initial single-batch attempt with all 496 pairs did not produce complete output, and an isomorphic split was then made before formal scoring. An agent was not opened for each pair separately. So judgments in the same batch share context and may be jointly affected by the text list, the comparison list and earlier generated content. The aggregation formulas below still hold, but they cannot pose as an implementation with per-pair isolated requests. The specific task criteria, input permutations and failure handling follow the rules already fixed for this round; this document adds no extra experimental gate.

## 1. Pairwise preferences strictly consistent under swapping

Fix the model and the panel. Each unordered pair $`i\lt j`$ appears twice: orientation 1 shows $`(i,j)`$ and orientation 2 shows $`(j,i)`$. First map each output back to **item identity**, and write

```math
d_{ij}^{(o)}=1\ \text{means preference for }i,\qquad
d_{ij}^{(o)}=-1\ \text{means preference for }j,\qquad
d_{ij}^{(o)}=0\ \text{means a tie},\quad o\in\{1,2\}. \qquad (1.1)
```

The strictly consistent result is

```math
a_{ij}=𝟏\{d_{ij}^{(1)}=d_{ij}^{(2)}=1\}
-𝟏\{d_{ij}^{(1)}=d_{ij}^{(2)}=-1\},
\qquad a_{ji}=-a_{ij},\qquad a_{ii}=0. \qquad (1.2)
```

Only if both runs prefer i is $`+1`$ given, only if both prefer j is $`-1`$ given, and everything else gets 0. If the raw output is coded as left/right, **only the answer pair left, right can mean that both runs preferred the same item**; choosing left both times is in fact a conflict after the swap. One tie plus one clear preference also gets 0, with no majority override. Missing or unparseable outputs must keep their failure identity; they cannot be described as the model explicitly judging the items equivalent just because the final aggregation gives 0.

The normalized Copeland score of item i is

```math
C_{M,h}(i)=\frac{1}{N-1}\sum_{j\ne i}
\left(𝟏\{a_{ij}=1\}+\frac12𝟏\{a_{ij}=0\}\right)
=\frac12+\frac{1}{2(N-1)}\sum_{j\ne i}a_{ij}. \qquad (1.3)
```

So $`0\le C\le1`$, and for 32 items the single-panel score is an integer multiple of $`1/62`$. Sort by C in descending order; exactly equal scores stay in the same ordered group, and ties are not broken by ID or input position. If the main result merges the two panels, it explicitly uses $`\overline C_M(i)=(C_{M,1}(i)+C_{M,2}(i))/2`$ while keeping each panel's result; the merged score grid is $`1/124`$.

The 0 here mixes explicit ties, swap conflicts and possible output failures, and cannot be interpreted uniformly as true indifference. Swap consistency also does not guarantee correctness or transitivity: three items can form $`i\succ j\succ k\succ i`$, in which case their Copeland scores are equal. The aggregation gives a total ranking with ties, but does not prove that it matches some latent true total order.

Qin et al. §3.1 uses consistent preferences after swapping the document order, and §3.2 does an all-pair summary with 1 point for a win and half a point for a tie. This document follows these operations and keeps final ties; the paper's practice of falling back to the initial ranking on ties is not part of the formulas here. This document also has the implementation limitation of shared context within batches. [Qin et al., NAACL Findings 2024, §§3.1–3.3](https://aclanthology.org/2024.findings-naacl.97.pdf)

## 2. Midrank with ties and normalized Borda

Each model and panel uses 4 pre-specified random permutations, $`\ell=1,\ldots,4`$, each with its own fresh agent. A valid output is a sequence of ordered groups $`(G_1,\ldots,G_g)`$ covering all 32 IDs with each appearing once; items within a group are tied, and groups run from high to low.

If there are $`H_i`$ items before i's group and i's group has size $`T_i`$, the 1-based midrank and the Borda score are defined as

```math
r_{M,h,\ell}(i)=H_i+\frac{T_i+1}{2},\qquad
b_{M,h,\ell}(i)=\frac{N-r_{M,h,\ell}(i)}{N-1}. \qquad (2.1)
```

This score equals "the number of items ranked after i, plus half the number of other items in i's group", divided by $`N-1`$. So in a single run without ties the first item gets 1 and the last gets 0, and when everything is tied each gets 1/2. It is on the same scale as the win/half-tie scoring in the previous section, but its input is one complete ordered grouping rather than separately generated pairwise judgments.

The equal-weight aggregation within a panel and over the two panels is

```math
B_{M,h}(i)=\frac14\sum_{\ell=1}^4b_{M,h,\ell}(i),\qquad
\overline B_M(i)=\frac12\sum_{h=1}^2 B_{M,h}(i)
=\frac18\sum_{h=1}^2\sum_{\ell=1}^4b_{M,h,\ell}(i). \qquad (2.2)
```

The equal-weight average over all 8 runs is not picking the permutation that best supports a conclusion. The single-panel score grid is $`1/248`$ and the 8-run average $`1/496`$; integer numerators can be kept, tie groups formed first by exact values, and rounding applied only for display. One cannot create ties by truncating decimals first, or break exact ties through floating-point error.

Tang et al. §2.2 supports the idea of fixing the task, shuffling the input and aggregating the output rankings; that paper specifically uses the Kemeny–Young central ranking under Kendall distance, and discusses consistency under particular noise conditions. **What is used here is the midrank Borda mean, not that paper's Kemeny algorithm; its theorems cannot be transplanted directly to this round's 8 outputs with ties.** [Tang et al., NAACL 2024, §§2.2–2.3](https://aclanthology.org/2024.naacl-long.129.pdf)

## 3. Tails and widening quantities on a finite set

The formulas below apply to any explicitly specified method and panel aggregation. For its score S, form descending groups $`G_1^S,\ldots,G_g^S`$ by distinct score values, and define the complete-group boundaries

```math
T_a(S)=\bigcup_{j=1}^{a}G_j^S,\qquad
K_a(S)=\left\vert T_a(S)\right\vert. \qquad (3.1)
```

Take a complete boundary $`A_k`$ of the reference ranking, with $`\left\vert A_k\right\vert=k`$, and write a complete boundary of the candidate ranking as $`B_m`$. The main curve is computed on these actually distinguishable sets:

```math
\widehat R(k,m)=\frac{\left\vert A_k\cap B_m\right\vert}{k},\qquad
\widehat q_\gamma(k/N)=\frac1N\min\{m:\ B_m\text{ is a complete group boundary},\ \left\vert A_k\cap B_m\right\vert\ge\lceil\gamma k\rceil\}. \qquad (3.2)
```

The widening factor relative to the actual reference count is the minimum m divided by k, computed separately for the positive and negative tails; the negative tail uses complete groups in ascending score order. The reference A is the selected model's ranking and is not automatically a true value label, so this is **recall of the reference list**.

The execution protocol also fixes a nominal fraction p: first take floor(Np) items, then include the whole tie group at the boundary, giving the actual count k. The machine results save both m/k (`B_over_actual_A`) and m/(Np) (`q90_over_nominal_p`); **the main pass condition uses the latter, q90/p**, and the denominators are not mixed. With N=128, p=10% and 20% first take 12 and 25 items, while Np is 12.8 and 25.6, so the two are not equal; tie expansion uses floor(Np) as its base. 90% recall requires ceil(0.9k) items; for example, k=12 needs 11 and k=25 needs 23. In stage 1, N=32 and p=25% give exactly Np=8, so this distinction does not change the values already reported.

If a fixed k or m falls inside a tie group, the ambiguity should be kept. Let $`𝒯_k(S)`$ contain all admissible top-k sets: items strictly above the boundary score must be selected, and the remaining slots are filled by any choice from the boundary tie group. Define

```math
R_-(k,m)=\min_{U\in 𝒯_k(S_A),\ V\in 𝒯_m(S_B)}\frac{\left\vert U\cap V\right\vert}{k},\qquad
R_+(k,m)=\max_{U\in 𝒯_k(S_A),\ V\in 𝒯_m(S_B)}\frac{\left\vert U\cap V\right\vert}{k}. \qquad (3.3)
```

This is the exact finite-set range over all admissible ways of breaking ties, not a confidence interval. Correspondingly one can report $`q_- =\min\{m:R_+(k,m)\ge\gamma\}/N`$ and $`q_+ =\min\{m:R_-(k,m)\ge\gamma\}/N`$, which express the pass-through amount reachable by at least one admissible boundary choice, and the amount reached by every admissible boundary choice, respectively. One cannot show only the most favorable tie-breaking result.

With N=32 the smallest non-empty fraction is $`1/32=3.125\%`$, so a 1% or 2% tail cannot be observed exactly. k=4 is a 12.5% tail with a recall step of 25 percentage points; k=8 is a 25% tail with a step of 12.5 percentage points, and the 90% target in fact requires finding all 8. The curve should list k, m and the actual fraction; finer tail evidence cannot be created by interpolation.

## 4. Call counts, dependence, and the questions that can be answered

| Component | Per model | Both models combined |
|---|---:|---:|
| Number of unordered pairs | 496 pairs per panel | The same 496 pairs of the same 32 items |
| Pairwise fresh batch calls | 2 panels × 2 orientations × 4 batches = 16 | 32 |
| Number of raw pairwise judgments | 496 × 2 × 2 = 1984 | 3968 |
| Multi-ranking fresh calls | 2 panels × 4 permutations = 8 | 16 |
| Total scoring session calls | 24 | 48 |

On top of this count there were 2 whole-batch feasibility attempts that produced no output (Luna did not finish, Sol was stopped); they are not included in the scoring data. There were not 3968 independent agent calls, nor 3968 independent financial observations. All pairwise edges share items, and the same batch also shares context; all rankings reuse the same 32-item pool. Random permutations and fresh sessions add repeats of the ranking measurement, not independent text samples. Changing the candidate pool may also change the score and rank of the same text, so these scores are not identified single-item attributes that are invariant to the candidate set.

The two panels can show the difference between this round's repeats, the overlap range and the tie fraction; they cannot directly form a confidence interval. Even when the input permutations are generated randomly and separately, new sessions do not guarantee independent model errors. Each change of input order may also change generation randomness, the comparison context and the inference path of the whole batch, so output differences are a combined repeat sensitivity, and the pure causal effect of position is not separately identified. The strict swap rule keeps consistent preferences but does not prove that these factors have disappeared.

This round can compare the resolution of pairwise aggregation and of the multi-ranking mean, the list overlap at the positive and negative tails, and whether cross-model differences come together with same-model panel fluctuation. Whether the two configurations really differ in cost must be decided by the actual configuration and cost facts. The fixed 32 items and a finite number of repeats do not identify a tail law as $`p\to0`$, do not estimate the structural α, and do not treat a local log–log slope as a conditional-extremes parameter.
