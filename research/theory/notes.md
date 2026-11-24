# WP0.3: Theory notes on the certificate chain, and corrections to the initial draft

Date: 2026-11-15. Basis: the initial theory notes, version of 2026-11-15. "Proved" in the status column means that this file gives a pen-and-paper mathematical proof; nothing has been certified by a proof assistant such as Lean. Numerical checks are in `../checks/record.md` and do not serve as proofs over the whole domain. This file contains no certificate on real financial data and makes no novelty claim.

## Status and dependencies

| ID | Status | Dependencies and main corrections |
|---|---|---|
| T0 | Proved (conditional) | union bound; passing tests is not a zero failure probability for program reliability |
| T1.1 | Original statement too strong; holds after correction | adds point-in-time-measurable selection and metadata rules; separates non-interference under a fixed seed from measurability of random parameters |
| T1.2 | Proved (given the privacy guarantee) | exact group δ; a bound in expectation is not an interval for a single checkpoint |
| T1.3 | Proved (local training on fixed shards) | the adjacency budgets differ for deletion/modification with a fixed ID versus replacement across IDs |
| T1.4 | Audit upper bound proved; the original necessary condition has a counterexample | the m=2k exception with ties going to the smallest-index class; usefulness of population intervals separated from pointwise robustness |
| T1.5 | Proved (A1–A7) | clean comparator for deletion of contamination; errors in the trusted core cannot be added like ordinary shard contamination |
| T2.1 | Definitions and counterexamples | UP does not imply LBL; a REL margin does not guarantee an actual label change |
| T2.2 | Proved after correction | only coordinates in M change, with c fixed; derivatives almost everywhere; the finite-increment guarantee holds everywhere |
| T2.3 | Proved after correction | the full-model context must be invariant; "no loss of expressiveness" needs a complete set of invariants and a specified domain |
| T2.4 | Proved (conditional) | for renamings satisfying canonicalization consistency; correctness of alias recognition does not hold automatically |
| T3.1 | Proved (known marginals, independence across clusters) | calibrated probabilities are not the true per-example marginals; a Bernoulli proof that does not rely on external lemmas is given |

Dependency graph: the point-in-time premises of T1.1 + the deterministic envelope of T1.3 + the coverage of T1.4 → T1.5; T0 combines the additional failure events. T2.2 and T2.3 are two different properties, requiring a fixed context and unit normalization respectively; neither proves that parsing is correct. T3.1 does not depend on the performance conclusions of P1/P2.

## T0: Certificate semantics and combination

### Statement and assumptions

A certificate records the proposition φ, all assumptions A, the evidence E, and the checker version V; a statistical certificate additionally records the sampling mechanism and α. Deterministic soundness is the mathematical proposition `V(E)=accept ⇒ (A⇒φ)` over all allowed inputs and cannot be inferred from a few successful tests alone. A statistical certificate is the repeated-sampling coverage of the whole pre-specified procedure and is not in general equal to the conditional probability given that this particular run accepted.

Let event E_i mean that the i-th link is valid, with P(E_iᶜ)≤α_i on an explicit common probability space, and suppose that under A, ∩E_i implies φ. Then P(φ)≥1−min(1,Σα_i). Independence of the events is not required. Setting α_i=0 applies only to proved mathematical implications and premises that actually hold; code bugs, data trustworthiness, and human audit errors do not disappear because of it.

### Proof

φᶜ⊆∪E_iᶜ, so P(φᶜ)≤ΣP(E_iᶜ)≤Σα_i. If the failure events are pairwise disjoint, the bound can hold with equality, so it cannot be improved in general when the dependence structure is unknown. Only relations that have been proved, such as independence or nesting, allow replacement by a tighter combination. Choosing α in a data-dependent way, choosing the best-looking certificate, or repeatedly looking at fixed-time intervals changes the coverage and must be included in the same procedure.

## T1.1: Point-in-time information sets, the deletion comparator, and selection leakage

### Corrected definition

The atomic record is a content version. F_t contains the content, versions, IDs, collection/ingestion records actually available up to t, and all point-in-time information needed by the selection rule. To argue that the random seed Ω adds no future information, it is required to be independent of the whole data-generating world, or more generally to be conditionally independent of the future given F_t. Marginal independence from the future alone is not sufficient.

If the parameters can be written as θ=F(H_t,Ω), where H_t is the point-in-time snapshot and F is measurable, then θ is measurable with respect to F_t∨σ(Ω). For fixed ω, all worlds with the same point-in-time snapshot produce the same output; this is called pathwise point-in-time non-interference. Independent randomness does not make a random θ literally F_t-measurable; one can include the randomness in F_0 in advance, or use the enlarged information set above.

Addendum from the independent review of 2026-11-16: the composition of measurable functions and the fixed-seed statement above do not themselves require independence; independence is the condition for "the seed carries no extra future information". Let the past H and the future B be independent uniform bits, and let Ω=H xor B; then Ω and B are marginally independent, but (H,Ω) recovers B. Hence the original blanket phrase "independent of future data" must be tightened, and an enlargement for measurability cannot be directly called no extra information. [Full conditions and proof](pit_noninterference.md).

The same round further separated informational measurability from actual source admissibility: text that is constant in the chosen probability space, and a checkpoint fixed as a constant after the fact, may both be measurable, which does not prove that the corresponding bytes were public at the time or that the model could have been built from inputs allowed at the time. The ex ante algorithm, the cross-world data semantics, and the contract for version availability and selection must be fixed; a "point-in-time certificate" cannot be obtained by treating realized outputs as constants. The "point-in-time-measurable comparator" below is a conditional informational conclusion; compliance of real historical sources still needs separate verification; see PNI4–PNI6 for details.

The training set filtered by record time is D_obs={i:τ_i≤t}, and the contamination is C_t={i:τ_i≤t<τ_i*}. Define the deletion comparator D_del=D_obs\C_t. If the selection of this subset, the metadata, and all shared components depend only on H_t, then Π(D_del,t,Ω) is a point-in-time-measurable comparator; it is not necessarily equal to the model "retrained on all truly point-in-time data".

### Proof, and a counterexample to the original proposition

The corrected proposition follows directly from the composition of measurable functions. D_del contains no future content, but "all inputs are old documents" is not by itself enough to prove point-in-time validity: let old documents d_0,d_1 both exist before t, and let a future bit B determine that the record time of d_B is t−1 and that of the other is t+1. Filtering by record time keeps only d_B, and the training program outputs its index. C_t=∅, yet the output equals the future B. The leak comes from the selection metadata. Hence "late timestamps only lose information and cannot leak" needs the additional condition of a point-in-time-measurable retention mechanism.

A constructive implementation should prevent the future corpus from affecting the tokenizer, vocabulary, deduplication clusters, sample weights, hyperparameters, early stopping, task labels, distillation models, and any external lookup. That the run result is unchanged after adding records later than t is a necessary regression test; finite tests do not exhaust all hidden inputs.

### Differences from the draft

"Exactly only the effect of C_t" is downgraded to a conditional proposition; the deletion comparator is distinguished from full point-in-time retraining; the σ-algebra of the randomness is made explicit. Authoritative timestamps can support the trusted-core assumption, but machine generation does not mean that all storage, revision, time-zone, and public-availability times have been proved correct.

## T1.2: The DP bound on the expected shift

### Statement

The training algorithm M satisfies (ε,δ)-DP with respect to adding or removing a whole document, including all data-dependent preprocessing, model selection, and output. D and D' are separated by at most k such adjacency operations. Fix one and the same measurable scoring function S∈[0,1]; the scoring function is not allowed to read the two raw training sets separately. The expectation is over the training algorithm's randomness; the evaluation set can be fixed.

Write a=kε and b=δΣ_{j=0}^{k−1}e^{jε} (b=0 when k=0). Then

```math
\left\vert E S(M(D))-E S(M(D'))\right\vert
\le \min\{1,(e^a-1+2b)/(e^a+1)\}.
```

A looser but valid bound is min{1,e^a−1+b}, and b≤k e^{(k−1)ε}δ (k≥1). When ε=0, b=kδ. The original draft's δ upper bound has the right direction but omits the truncation at 1; it is not the tightest TV bound.

### Proof

Iterating the DP inequality along k adjacency edges gives P(A)≤e^a Q(A)+b, and the reverse also holds. Let A be such that d=P(A)−Q(A)≥0, and q=Q(A). Applying the forward bound to A and the reverse bound to Aᶜ gives

```math
d\le(e^a-1)q+b,\qquad e^a d\le(e^a-1)(1-q)+b.
```

Adding the two gives (e^a+1)d≤e^a−1+2b. Swapping P,Q and taking the supremum over events gives the TV bound; the layer-cake representation E S=∫₀¹P(S>u)du for S∈[0,1] gives the bound in expectation.

### GDP version and limits

If the testing trade-off between adjacent outputs is at least G_μ(α)=Φ(Φ⁻¹(1−α)−μ), chaining for group privacy gives G_{kμ}: with `f⊙g=f∘(1−g)`, G_u⊙G_v=G_{u+v}. Hence the sum of the two error types of any test is at least min_α[α+G_{kμ}(α)]=2Φ(−kμ/2), so TV≤2Φ(kμ/2)−1.

More directly, for any event A (or randomized test), the guarantee for adjacent distributions P_j, P_{j+1} gives P_{j+1}(A)≤Φ(Φ⁻¹(P_j(A))+μ). Recursing k times along the adjacency path gives the kμ in the same formula, so the sqrt(k) composition for independent mechanisms is not misapplied here to data-group privacy.

Requiring this bound to be ≤0.05 is equivalent to kμ≤2Φ⁻¹(0.525)≈0.1254 (a pure mathematical computation, not a model experiment). This does not imply that "the 24M model necessarily learns nothing"; utility requires real training evidence. A DP certificate constrains the expectation over the random training distribution, and the same number cannot be taken directly as a deterministic shift interval for one realized checkpoint. Token-level DP also cannot be called document-level DP without composition.

## T1.3: Voting and statistic envelopes under fixed shards

### Assumptions

1. m≥1 heads; classes are {1,…,K}, K≥2, and ties go to the smallest index.
2. The shared backbone, tokenizer, label map, hyperparameters, and feature transformations are frozen and determined only by the trusted core / point-in-time exogenous information.
3. IDs and the shard map h do not change between comparators; head l is a deterministic function of its own shard's data and a fixed exogenous seed. No cross-shard early stopping, global normalization, rebalancing hash, or data-dependent shared state.
4. Deleting k records affects at most k shards; the same holds for content modifications that keep the ID. Replacing an old ID with a new ID can touch two shards at once and must be budgeted as at most 2k shard changes. Deletion is the adjacency needed for the P1 clean comparator.

### Voting proposition and proof

Write n_c(z) for the vote count of class c, and a for the observed winner. When at most b heads change arbitrarily, the vote margin between the winner and a competitor c decreases by at most 2b. Hence if, for all c≠a,

```math
n_a-n_c\ge 2b+𝟏\{c\lt a\},
```

then after the change the margin is still at least 1 against competitors with smaller index and at least 0 against those with larger index, and a still wins. This is a sufficient condition for arbitrary changes in shard outputs and does not require the hash to distribute uniformly. An empty shard also needs a fixed default classifier.

### Collective statistics

Fix J evaluation points and pre-specified s_j:{1,…,K}→[0,1]. Let R_j(b) be the set of all winning labels reachable with at most b vote changes. If an approximate set is computed, it must be an outer envelope and must not miss any truly reachable label. Define

```math
L(b)=J^{-1}\sum_j\min_{c\in R_j(b)}s_j(c),\quad
U(b)=J^{-1}\sum_j\max_{c\in R_j(b)}s_j(c).
```

Any common change of at most b shards puts each point's label in R_j(b), and summing term by term gives L≤S≤U. Optimizing each point separately relaxes the restriction to "a common set of affected shards", so it can be conservative but cannot fail in the other direction. Optimizing over common shards must also allow the output vectors of these shards across different test points; assigning outputs independently is a further relaxation of training realizability.

**Scope restriction:** accuracy or a bounded pointwise loss has the form above; macro-F1, the Sharpe ratio, and path-dependent drawdowns do not have this additive form, and the formula cannot be applied directly. Macro-F1 can be optimized over all reachable confusion counts; other statistics need separate derivations and the necessary lower bounds on denominators.

## T1.4: Exact finite-population audit and resolution

### Full setup and coverage

Fix N suspicious documents, with true contamination count K*∈{0,…,N}. The audit size n∈{0,…,N} is fixed before sampling; n IDs are drawn uniformly without replacement; audit decisions are correct with no misses. Observe X=x. Define

```math
F_K(x)=\sum_{j=\max(0,n-N+K)}^{\min(x,n,K)}
\frac{\binom Kj\binom{N-K}{n-j}}{\binom Nn},\qquad
K_u(x)=\max\{K\in\{0,…,N\}:F_K(x)>\alpha\},
```

where 0<α<1 and an empty sum is 0. When n=0, K_u=N; when n=N, K_u=x. Then for every fixed K*, P_{K*}(K*≤K_u(X))≥1−α.

**Proof.** Within the same random sample, relabelling good records in the population as bad one at a time couples the X_K monotonically, so F_K(x) is nonincreasing in K. If K_u(X)<K*, then necessarily F_{K*}(X)≤α. Let x₀ be the largest support point with F_{K*}(x)≤α; the probability of this failure event is ≤F_{K*}(x₀)≤α. If no such point exists, the failure probability is 0. The strict `>α` in the definition here matches rejection at `≤α`.

### Exact formula for zero findings, and the domain of the approximation

When x=0 and n>0:

```math
F_K(0)=\binom{N-K}{n}/\binom Nn
=\prod_{i=0}^{n-1}(1-K/(N-i))
\le(1-K/N)^n\le e^{-nK/N}.
```

So the retained K is strictly less than N(1−α^{1/n}), and also strictly less than N log(1/α)/n. These are conservative analytic upper bounds, not exact finite-population values. When n/N is small and K/N is small, K_u≈N log(1/α)/n; for α=0.05 the coefficient is log20≈2.9957. This is **the scale of the upper bound on contamination counts that still cannot be ruled out after zero findings**, not a lower bound on a contamination count shown to exist, and not a lower bound that applies to every audit design.

When the sampling fraction is large, another expansion is more appropriate: F_K(0)=∏_{j=0}^{K−1}(N−n−j)/(N−j)≈(1−n/N)^K. For the example N=1000,n=500,α=.05, the exact upper bound is 4, while the rule of three gives about 6; hence the approximation in the initial table must not be treated as an exact result. In this example one can check directly that the zero-finding probability for K=4 is >.05, while for K=5 it is <.05. The real size of the EDGAR population was not obtained in this task, and the hypothetical N must not be treated as real data.

### A counterexample to the original necessary condition on the number of shards, and a correction

The original draft said "any robust prediction requires m≥2b+1". Counterexample: m=2,b=1, with both heads voting for class 1. Changing one head can only produce a 1:1 tie, and the rule still picks class 1. Hence m=2b can already be robust. In general this holds when m=2b and all heads vote for the smallest-index class.

For the **vote-margin sufficient condition** of T1.3: when the winning class is a=1, m≥2b is necessary; when a>1, a competitor with a smaller index exists, and m≥2b+1 is necessary. If a strict-majority certificate that does not depend on tie priority is required, m≥2b+1 is the correct necessary condition, but it is still not sufficient; the actual vote margin must be checked. b=0 is handled separately, and m≥1 suffices.

Hence, for small sampling fractions, the design for a strict-majority certificate is approximately n≳2N log(1/α)/(m−1), and for the best tie class n≳2N log(1/α)/m. These are approximate feasibility screens for the specified certificate mechanism, not infeasibility theorems for all possible methods.

### The exact audit gate for a fixed vote-margin budget

A practical design should first obtain from the observed vote margins the integer contamination budget a point can tolerate, B_j=⌊min_{c≠a_j}(n_{a_j}−n_c−1{c<a_j})/2⌋, and then solve for the audit size. If B∈{0,…,N−1} is fixed, monotonicity gives the exact equivalence:

```math
K_u(0)\le B\quad\Longleftrightarrow\quad
\frac{\binom{N-(B+1)}n}{\binom Nn}\le\alpha.
```

A binomial coefficient is 0 when its upper index is less than n. Hence n_min is the smallest integer n for which the right-hand side holds, not a rounded value of the continuous rule-of-three formula. When B≥N, this budget gate is passed without any audit; a negative budget cannot be certified. If the model and vote margins are fixed before the audit and one wants to certify at least a fraction q∈(0,1] of the J predictions, let r=ceil(qJ) and take the r-th largest B_j as the budget gate. Satisfying K_u≤ this gate certifies at least r points. If the shard models or the population are modified based on the audit result, the audit coverage and the certificate's scope must be re-examined.

Exact integer computations in this round (source: [audit machine output](../experiments/local_foundations/audit_results.json), our experiment; hypothetical populations rather than real EDGAR): (N,n,α,x)=(100000,1000,.05,0) gives K_u=297; (10000,1000,.05,0) gives 28; (1000,500,.05,0) gives 4. This section reuses `research/local/audit.py` and does not implement a second P1 auditor.

### "No certified prediction" is different from "a vacuous interval"

We call [L,U] non-vacuous when it is strictly smaller than [0,1]; an interval with L≤U is literally never empty. Example: m=5,b=1, class vote counts (2,2,1); one vote can make the output switch between 1 and 2, but cannot make class 3 win. If the true label is 3, the accuracy is determined to be 0, even though the prediction itself is not robust. Hence "no single-point robustness" does not imply "every statistical certificate must be vacuous". Restrictions from model structure, collective constraints, and loss structure can also narrow the interval. Conversely, a large m does not guarantee usefulness; the shard heads may have no vote margin.

### Stratified and sequential audits

Fix source strata h in advance and take a simple random sample within each stratum; take pre-specified α_h>0 with Σα_h≤α. Obtaining K_{u,h} stratum by stratum with the formula above, K*≤ΣK_{u,h} holds with probability at least 1−α. Independence across strata is not needed. The upper bound for a stratum with no samples is N_h; the error rate of a high-quality stratum cannot be lent unconditionally to a low-quality stratum. One can first run an independent pilot to choose quotas and then make inferences under the frozen design; data-driven stopping requires sequentially valid methods.

An explicit zero-finding sequential procedure: to test H₀:K≥K₀, audit without replacement in random order, and let

```math
E_n=𝟏\{X_n=0\}/F_{K_0,n}(0),\quad 0\le n\le N-K_0.
```

On the zero-finding path, the conditional probability that the next draw is error-free is (N−K−n)/(N−n), which does not exceed that probability under K₀; once an error is found, E is 0 forever. Hence E_n is a nonnegative supermartingale under H₀, starting at 1, and the probability that it crosses 1/α is ≤α (stop at the first crossing and use the expectation inequality for supermartingales with bounded stopping). For K₀=N, the event that all subsequent draws are zero is impossible under H₀ and is handled directly and separately.

This example allows valid early rejection, but it does not automatically improve the log(1/α) constant for zero findings: crossing is exactly F_{K₀,n}(0)≤α. A non-random test at a fixed time that rejects H₀ on zero findings while F_{K₀,n}(0)>α already exceeds its type I error. Whether a general e-process improves efficiency on non-zero-finding paths is a design question; one cannot claim a free increase in audit resolution. Nested tests across several K₀ can be inverted into a confidence sequence; the actual code has not been implemented and cannot be called a deployed anytime-valid auditor.

## T1.5: The certificate chain for the deletion comparator

### All assumptions

- A1: The shared configuration, core, selection, and metadata are point-in-time measurable, including the point-in-time conditions of T1.1.
- A2: The core has no contamination; the fixed shared backbone/vocabulary comes only from this core and exogenous point-in-time information.
- A3: The population of suspicious windows and content versions is frozen before the audit; contamination changes shards only through deletion of these records.
- A4: The fixed-shard and local deterministic-training conditions of T1.3 hold; seeds are fixed in advance or independent and exogenous.
- A5: The uniform sampling without replacement, correct audits, and fixed n / valid sequential rule of T1.4 hold.
- A6: The statistic is the average of a fixed bounded pointwise function; evaluation points, labels, and denominator do not change under clean retraining; inputs for historical applications are available at their respective decision times.
- A7: The checker computes a sound outer envelope; if floating point is used, separate rounding control is needed, since a mathematical real-number proof does not automatically certify a machine-precision implementation.

### Conclusion and proof

F_del is the comparator obtained by deleting all true contamination from the observed corpus and retraining with the algorithm and seeds unchanged. Over the audit randomness, with probability at least 1−α,

```math
S(F_{del})\in[L(K_u),U(K_u)].
```

On the event K*≤K_u, deleting K* documents touches at most K* shards; the other shards have the same inputs, shared parameters, and randomness, and their outputs are bit-for-bit identical. T1.3 is valid for any such change, so the interval contains S(F_del). T1.4 guarantees the event has probability at least 1−α. Premises A1–A2 guarantee that the comparator has the specified point-in-time property; they cannot be omitted while still calling the comparator leak-free.

### The trusted core cannot simply be merged into k

If one contaminated document in the core changes the shared backbone, the inputs of all m heads may change, and the original at-most-k-shards argument immediately fails. One can audit the core separately and require its upper bound to be exactly 0, paying an extra α_core; if the upper bound is greater than 0, the stability of the backbone must be proved separately, or a worst-case envelope must be used for the relevant global effects; k cannot simply be replaced by k_edge+k_core.

### From a fixed test set to the population

Further assume the test points are iid, independent of training/audit, and not used for model selection; the clean comparator is fixed before test sampling. Hoeffding gives ε_J=sqrt(log(2/β)/(2J)), so the population mean falls in [max(0,L−ε_J),min(1,U+ε_J)] with probability at least 1−α−β. If the test examples are clustered or drift over time, this formula does not automatically hold; a general cluster bootstrap is approximate inference and should not be attached unconditionally as an exact finite-sample certificate.

## T2.1: Five classes of permission specifications and non-implications

Given an edit e, explicitly ordered labels, and a fixed tie rule. INV(ρ): TV(q_e,q)≤ρ; LBL: the argmax is the same; REL(a→b,γ): the change in the log-odds of the two classes is ≥γ (requiring the corresponding probabilities to be positive, or using finite logits directly); UP: all upper-tail probabilities do not decrease; FREE: unconstrained.

INV(0) implies LBL; in general, INV(ρ) also implies LBL when the gap between the original largest and second-largest probabilities is >2ρ, because each coordinate's probability changes by ≤ρ. UP does not imply LBL: in (.6,.3,.1)→(.2,.3,.5) no upper tail decreases, but the argmax changes. LBL does not imply UP: (.2,.6,.2)→(.3,.6,.1) keeps the label, but an upper tail decreases. A REL margin does not guarantee a class switch: (.99,.01)→(.98,.02) increases the relative b/a odds, but the winner is still a.

Hence UP is not a synonym for "label preserved but confidence may vary". Negative evidence should use DOWN; strengthening neutral often shrinks the mass on both sides at once, as in (.3,.4,.3)→(.1,.8,.1), and the distributions have no FOSD ordering. These are behavioural specifications and do not prove that the true psychological stance of financial authors obeys monotonicity; contrarian views and the like require FREE or a Lipschitz-only specification.

## T2.2: Ordered monotone heads and numerical Greeks

### Full statement

Numerical features g∈R^d, fixed context c. For each c, h(·,c) is λ-Lipschitz under ℓ₁, with λ≥0. M⊆{1,…,d} is the set of designated monotone coordinates, and η(g,c)=h(g,c)+λΣ_{r∈M}g_r. Fixed thresholds θ₁<…<θ_{K−1} do not depend on g, and Q_i=P(Y≤i)=σ(θ_i−η).

If g'_r≥g_r for r∈M and g'_r=g_r for r∉M, then η(g',c)≥η(g,c), so q(g',c) is no lower than q(g,c) in FOSD. For r∈M, at points where the derivative exists (almost everywhere):

```math
0\le\partial_r\eta\le2\lambda;
\quad0\le\partial_r q_K\le\lambda/2;
\quad-\lambda/2\le\partial_r q_1\le0;
\quad\left\vert\partial_r q_i\right\vert\le\lambda/2\ (1\lt i\lt K).
```

At all points there is still the finite-increment bound |q_i(g',c)−q_i(g,c)|≤(λ/2)||g'−g||₁. Without the residual term the bound is (λ/4)||g'−g||₁, but the direction is not guaranteed.

### Proof

Let Δ=g'−g≥0, supported only on M. The difference in h is ≥−λ||Δ||₁; the difference in the residual is λΣ_MΔ_r=λ||Δ||₁, and the sum of the two is nonnegative. For a change of size u≥0 in a single coordinate, the difference in η lies between 0 and 2λu, so where the derivative exists it lies in [0,2λ]; a Lipschitz function is differentiable almost everywhere. Q_i decreases in η, which gives FOSD.

σ'(z)∈[0,1/4]. The derivative magnitude of the endpoint class probabilities with respect to η is ≤1/4; for a middle class, q_i=σ(θ_i−η)−σ(θ_{i−1}−η), its derivative is the difference of two nonnegative numbers each ≤1/4, so its magnitude is still ≤1/4, not 1/2. Hence the chain rule gives λ/2. The ℓ₁-Lipschitz constant of η with respect to all of g is ≤2λ; applying the 1/4-Lipschitz property of the probability map directly to η gives the finite-increment bound that holds everywhere. Without the residual, the constant for η is λ.

### Counterexamples to the draft, and the implementation contract

If M={1} and h(g₁,g₂)=−λg₂, increasing the non-monotone coordinate g₂ lowers η, so the original unconditional "g'≥g implies FOSD" is too strong. If c=g and h(g,c)=−2λc, then h is even 0-Lipschitz for fixed c, but along the actual inputs η=−λg, and the direction reverses. Replacing only the Arabic numerals in the text is not enough: number words, units/scales, parsing state, auxiliary caches, and tokenizer paths can also make c vary with the numerical value.

Thresholds may depend on the fixed c but not on the g changed in this instance. The checker must verify the whole computation graph from g to the output and should not merely spot-check one set of gradients. The executable example in this file uses h=wᵀg+b(c) and verifies max_r|w_r|≤λ with exact rationals; this certifies only this linear head and does not mean a transformer has been certified.

### Derivatives with respect to raw values

If g=(x−b)/b with b>0 fixed, then ∂q_K/∂x≤λ/(2b). When b can approach zero there is no uniform upper bound in terms of the raw value; at b=0 the ratio is undefined, and for b<0 the direction reverses. In the multi-feature case one should multiply by the Jacobian of the parsing map; a bound with respect to the dimensionless g cannot be taken as a bound with respect to arbitrary numbers in text or real market variables.

### Necessity and real tasks

The structural property does not require training the text encoder from scratch; providing an existing encoder with a fixed normalized context and then attaching a compliant head has the same mathematical property. Hence "P2 can only be obtained by training from scratch" is false. P1 has additional requirements on the point-in-time information set, and the two must not be conflated. If the label is already determined by all the numbers and the baseline, a threshold rule should be a strong baseline; in settings where language contributes, it must be made explicit that the baseline/metric attribution really comes from the text.

## T2.3: Unit invariance and conditions for expressiveness

### Unit invariance

Let x∈R_{>0}^p, the dimension matrix D∈R^{q×p}, and a positive unit transformation s∈R_{>0}^q act by x'_j=x_j∏_a s_a^{D_{aj}}. Take exponents v∈ker D; then Π_v(x)=∏_j x_j^{v_j} satisfies Π_v(x')=Π_v(x), because the exponent of the unit factors is Dv=0. If the numerical channel depends only on these Π, and the text context, unit-word normalization, auxiliary fields, and final post-processing are all invariant under the transformation, then the full model output is invariant.

The unit label itself also changes, from "thousand yuan" to "million yuan"; if the label enters c, dimensionless numbers alone do not prove that the full model is invariant. This proposition is a property of real arithmetic; a machine implementation needs exact rational/interval arithmetic, or must explicitly report a floating-point error tolerance, and cannot be called bitwise exact.

### Expressiveness proposition for complete invariants, and proof

On the strictly positive domain, let the columns of B form a complete basis of ker D. If Bᵀlog x=Bᵀlog y, then log y−log x∈(ker D)⊥=im Dᵀ. Hence y and x lie on the same unit-transformation orbit. Every orbit-invariant function can be defined as a function of these complete invariants. **Only a complete characterization of orbits supports "no loss of expressiveness".** Picking a few ratios at random may be incomplete, and no such claim can be made for them.

Financial quantities can be negative or zero, and log and arbitrary real powers do not apply. One should fix the sign/zero pattern, apply the dimensional treatment to the nonzero absolute values, and add the signs and zero indicators as extra invariants; denominators of ratios must exclude zero. The chosen reference quantities of the same dimension must also change consistently with the units. Exchange-rate movements across currencies are not simple changes of reporting unit; to cover currency conversion, time, exchange rates, and the comparison baseline must all be put into the specification.

## T2.4: Entity slots

For a specified set of renamings Π, if the anonymization a satisfies a(πx)=a(x) for all π∈Π, x∈X, then F=G∘a satisfies F(πx)=F(x); the proof is substitution of functions. The roles of target and non-target entities, coreference relations, and slot order must be preserved; numbering by alphabetical order of names may change slots under renaming and thus fails the premise. Unrecognized aliases, facts about a company's business, or ticker values can still carry identity. Enumeration over a finite set of aliases certifies only that set, not all natural-language entity renamings.

## T3.1: Worst-case convex risk with fixed Bernoulli marginals

### Statement

Each cluster c has finitely many Bernoulli variables e_i with known **true marginals** P(e_i=1)=p_i; clusters are independent, with arbitrary dependence within a cluster. Define the comonotone variables e_i^com=1{U_c≤p_i}, where each cluster shares one U_c~Uniform(0,1) and the U_c are independent across clusters. Then E=Σe_i≤cx E^com, i.e. the expectations of all convex φ satisfy Eφ(E)≤Eφ(E^com). Consequently, the variance, the stop-loss, and the upper-tail ES_β all attain their worst values under this coupling.

### A Bernoulli proof that does not rely on external theorems

The joint distribution within one cluster can be represented by the masses q_A of the error subsets A⊆{1,…,d}, and the fixed marginals give a compact finite-dimensional probability polytope. For any convex φ, choose a distribution maximizing Σ_Aq_Aφ(|A|), and then, among all maximizing distributions, maximize Σ_Aq_A|A|².

If two sets A,B, neither containing the other, both have positive mass, take ε=min(q_A,q_B)>0 and move mass ε each from A and B to A∩B and A∪B. The total mass and each variable's marginal are unchanged. The four sizes have the same sum, and the intersection and union are more spread out, so convexity gives φ(|A∩B|)+φ(|A∪B|)≥φ(|A|)+φ(|B|). The primary objective does not decrease, while the quadratic objective strictly increases by 2ε|A\B||B\A|>0, a contradiction. Hence the sets with positive mass under the optimal distribution form a chain under inclusion; given the marginals, their masses equal the differences of the sorted p_i, which is exactly the comonotone coupling. Hence the convex-order conclusion holds for a single cluster.

If X≤cxY and Z is independent, x↦Eφ(x+Z) is convex, so X+Z≤cxY+Z. Replacing cluster by cluster proves the conclusion for the sum. The mean is fixed by the marginals; taking φ(x)=x² gives the worst-case variance; taking φ(x)=(x−t)_+ gives the worst case for every stop-loss. ES_β(X)=inf_t[t+(1−β)⁻¹E(X−t)_+]; for each t the objective is ordered term by term, and after taking the inf it is still ordered, so the conclusion holds.

### Computation and counterexamples

For a single cluster, use the sorted p_i together with 0 and 1 as breakpoints; each interval of U_c corresponds to a total error count, with mass equal to the interval length. Discrete convolution of the cluster probability vectors computes E^com. Given known marginals, it is the exact distribution, not an estimate of the true distribution when the dependence is unknown.

VaR does not respect the convex order: for two Bernoulli variables with p=.5, the comonotone total puts half its mass on each of 0 and 2, and under the definition VaR_β=inf{x:F(x)≥β}, VaR_.5=0; the countermonotone total is identically 1, with VaR_.5=1. Hence comonotonicity is not the worst case for VaR.

### Statistical links that cannot be ignored

Group calibration P(error=1|predicted probability=.1)=.1 does not imply that every example has true p_i=.1. For example, two equal-sized subgroups with true error rates 0 and .2 respectively, both reported as .1, are still group-calibrated. Plugging fitted probabilities into T3.1 gives a scenario risk conditional on these marginals being correct.

If there are pointwise upper bounds p_i≤u_i with simultaneous coverage probability at least 1−α, then on that event, for increasing convex risks, one can first use the comonotone upper bound for the true p and then increase pointwise to u, obtaining stop-loss/ES upper bounds. Variance is not an increasing risk and cannot be handled this way directly; nor can each future example's p_i be estimated from an ordinary calibration set without assumptions. If independence across clusters fails, one should enlarge the dependence clusters or use the more conservative upper bound with full comonotonicity.

## Evidence and unverified items

| Content | Source and level | Actual use in this file |
|---|---|---|
| Original propositions to be checked | the initial theory notes and draft | object of review, not an authority on theorems |
| GDP definition and source | [Dong–Roth–Su, Gaussian Differential Privacy](https://arxiv.org/abs/1905.02383), abstract page opened | checked authors, title, and the trade-off framework; this file gives the mathematical derivation; the location of theorems in the full text is still left to the literature task to verify |
| Existing source for monotone residuals | [Kitouni–Nolte–Williams, Robust and Provably Monotonic Networks](https://arxiv.org/abs/2112.00038), abstract page opened | confirms that the Lipschitz constraint + residual monotone design has prior work; this file proves a simple structure and does not pass it off as a first |
| Audits, voting, Pi, and Bernoulli convex order | finite-sample/linear-algebra derivations in this file | mathematical proofs, not relying on unverified numbers from papers |
| Program results | `../checks/results.json`, our experiment (mathematical sanity checks) | supports only the recorded finite input checks, not performance on real financial tasks |

Not verified: the real annual size of EDGAR, model training utility, P2 parsing accuracy, non-vacuous certificates on public data, or exhaustive novelty. After I added new restrictions on external access, no further web searches were done. This file does not let these gaps block mathematical derivations that can already be completed independently.

## Correction table and next steps

| Original claim | Corrected claim | Impact on later decisions |
|---|---|---|
| After filtering by record time, only future content needs handling | One must also prove that selection, metadata, and shared components are point-in-time measurable | The contract and attack tests of WP1.2 need to be expanded |
| A single deterministic tester stands for zero failure probability | Mathematical implication + implementation verification; tests are evidence, not a complete proof | The certificate JSON must state the trusted computing base and the assumptions explicitly |
| m≥2k+1 is a necessary condition for any prediction certificate | The tie-priority class can be robust at m=2k | The feasibility plot shows two thresholds, for strict majority and for the tie rule |
| No single-point robustness means statistical certificates are vacuous | Reachable labels/collective constraints can still give non-trivial envelopes | Report interval width; do not look only at the fraction of certified predictions |
| Any increase in g gives FOSD | Only coordinates in M may increase, with the rest fixed | The checker must audit the context and feature pathways |
| Any dimensionless group loses no expressiveness | A complete set of invariants is needed, with handling of the positive domain/signs/zeros | The reference quantities needed by the task must be pre-registered |
| P2 must be trained from scratch | The structural proof can be attached to an existing fixed encoder | The necessity of training from scratch should be shown separately, via P1 or empirical differences |
| Calibrated outputs are known pointwise error probabilities | Separate trustworthiness of marginals, or simultaneous bounds, is needed | P3 can at first only serve as a conditional risk calculator |

Priority order for next steps: freeze the data/algorithm contract of T1.5; complete the G0 foundations; validate P1 with real suspicious-window sizes and vote margins; validate P2 with non-threshold-degenerate tasks, correct parsing, and a comparison of soft/hard constraints. These proofs passing does not mean G0 or G1 has passed.
