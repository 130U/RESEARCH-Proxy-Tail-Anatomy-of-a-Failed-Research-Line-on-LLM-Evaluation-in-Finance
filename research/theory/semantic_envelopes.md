# Numerical envelopes over finite semantic branches, acceptance-rate limits, and parsing risk

Date: 2026-11-16. Status: conditional mathematics with complete pen-and-paper proofs, not verified by a formal proof assistant. This round writes only this file; it does not change models, does no training, uses no internet access, and uses no natural-text gold labels. The interface is tightened on the basis of research paths 02 and 05 and [T2.2](notes.md). What follows is mainly a combination of existing mathematical tools: interval extrema, partial identification, sign comparison, Lipschitz envelopes, and fixed-risk audits. **No novelty check has been completed, and no original theory is claimed**.

The object of certification here is first of all "what the model will output given the true semantics", not that the model's probabilities equal the true class probabilities, still less investment returns. If the task only requires the high/low relation between numbers, the sign oracle of Section 5 is used instead, and it is allowed to replace the learned head entirely.

## 1. Common task, branches, and scope conventions

For a fixed observed text/evidence $`O`$, the parser gives a nonempty finite set of branches $`ℬ(O)`$. Each branch fixes the entity, metric, period, convention, unit normalization, baseline semantics, context $`c_b`$, direction declaration, and head parameters. Continuous numerical uncertainty is allowed within a branch. An empty branch set must be rejected; the vacuous coverage of the empty set cannot be used to give a zero-width certificate.

**Common output contract A0.** All merged branches must target the same frozen objective, the same measurement scale, the same ordered class definition, and the same $`K\ge2`$. If both are three-dimensional vectors but one means "high/low numerical value" and the other "investment stance", they cannot be merged coordinatewise. The checker can verify that the schema declarations agree; it cannot prove that the natural text really matches these semantics.

Each branch has an independent rectangle

```math
x\in[x_-,x_+],\qquad b\in[b_-,b_+],\qquad 0\lt b_-\le b_+, \qquad (1.1)
```

where $`x_-\le x_+`$, the values are finite, and $`x`$ may be negative or zero; the normalized feature is $`g=x/b-1`$. The two variables have the same dimension and consistent unit conversion. If the original semantics additionally constrains the joint values of $`x,b`$, the rectangle can only be an outer relaxation, and "tight" below is only relative to the rectangle; one cannot claim exactness for the original coupled set just because the marginal intervals are correct.

The ordered head has fixed thresholds $`\theta_{b,1}<\cdots<\theta_{b,K-1}`$, which do not change with the values being certified. Let $`\sigma(v)=1/(1+e^{-v})`$,

```math
q_{b,1}(\eta)=\sigma(\theta_{b,1}-\eta), \qquad (1.2)
```

```math
q_{b,i}(\eta)=\sigma(\theta_{b,i}-\eta)-\sigma(\theta_{b,i-1}-\eta),\quad 1\lt i\lt K, \qquad (1.3)
```

```math
q_{b,K}(\eta)=\sigma(\eta-\theta_{b,K-1}). \qquad (1.4)
```

These coordinates are nonnegative and sum to 1. Branch contexts and thresholds may differ from one another, but the class semantics must satisfy A0. The reference checker can use the affine latent value $`\eta=a_bg+d_b`$; a more general T2.2 head can also take a proved interval of latent values as input, but the exact range must be distinguished from a loose outer interval.

## 2. SE1: tight intervals for positive-baseline ratios and affine latent values

**Proposition SE1.** On the independent closed rectangle above, the exact range of $`g`$ is the closed interval $`[g_-,g_+]`$, whose endpoints are the minimum/maximum of the four corners $`x_\pm/b_\pm-1`$. The exact range of the affine head is

```math
\eta_-=\min(a_bg_-+d_b,a_bg_++d_b),\qquad
\eta_+=\max(a_bg_-+d_b,a_bg_++d_b). \qquad (2.1)
```

**Proof.** For fixed $`b>0`$, $`x/b-1`$ is strictly increasing in $`x`$, so the minimum/maximum are attained at $`x_-,x_+`$ respectively. For any fixed endpoint $`x`$, the derivative of the function with respect to $`b`$ is $`-x/b^2`$: nonincreasing when $`x>0`$, nondecreasing when $`x<0`$, constant when $`x=0`$. Hence the extrema on that edge are attained at $`b_-,b_+`$, and the four corners contain the global extrema. The compact rectangle and continuity guarantee that the extrema exist; the rectangle is connected, and so is its continuous real-valued image, so the whole range is the interval between these two endpoints. The maximum/minimum of an affine map are attained at the interval endpoints, including the constant-slope case $`a_b=0`$. ∎

If $`x_-\ge0`$ is known, this simplifies to $`[x_-/b_+-1,x_+/b_--1]`$; for negative values these two positions cannot be copied. If $`b_-=0`$, definedness/boundedness may fail, and this interface should reject; a very small positive number must not be silently substituted for 0. If the true constraint is $`x=b\in[1,2]`$, the true $`g`$ is identically 0, while the independent rectangle gives $`[-1/2,1]`$; this is a direct counterexample to "marginal intervals equal joint tightness".

The proportional unit transformation $`(x,b)\mapsto(sx,sb)`$, $`s>0`$, strictly preserves $`g`$ and its exact rectangle image. But invariance of the full output also requires that the context, direction, thresholds, and post-processing not be affected by a bypass through unit words; the ratio identity cannot prove that the parser satisfies this contract.

## 3. SE2: exact coordinate extrema of ordered probabilities

Fix one branch and drop the subscript $`b`$; let the allowed latent values be the whole closed interval $`[L,U]`$, with $`L=U`$ allowed. Write $`Q_i(v)=q_i(v)`$.

**Proposition SE2.** The exact ranges of the two end classes are

```math
q_1([L,U])=[\sigma(\theta_1-U),\sigma(\theta_1-L)], \qquad (3.1)
```

```math
q_K([L,U])=[\sigma(L-\theta_{K-1}),\sigma(U-\theta_{K-1})]. \qquad (3.2)
```

For a middle class $`1\lt i\lt K`$, let $`m_i=(\theta_{i-1}+\theta_i)/2`$ and $`v_i^*=\min(U,\max(L,m_i))`$; then

```math
q_i([L,U])=\left[\min\{q_i(L),q_i(U)\},\ q_i(v_i^*)\right]. \qquad (3.3)
```

**Proof.** $`\sigma`$ is strictly increasing, so the first class decreases in $`\eta`$ and the last class increases, and the endpoint formulas hold. The derivative of a middle class is

```math
q_i'(\eta)=\sigma'(\theta_{i-1}-\eta)-\sigma'(\theta_i-\eta),\qquad
\sigma'(v)=\frac1{2+2\cosh\,v}. \qquad (3.4)
```

This derivative kernel is even about 0 and strictly decreasing in $`\left\vert v\right\vert`$. When $`\eta\lt m_i`$, $`\left\vert\theta_{i-1}-\eta\right\vert<\left\vert\theta_i-\eta\right\vert`$, so $`q_i'>0`$; when $`\eta>m_i`$ the reverse holds and $`q_i'<0`$; the derivative is 0 at the midpoint. Hence $`q_i`$ is unimodal; on a closed interval its minimum is at one of the two endpoints and its maximum at the projection $`v_i^*`$ of the midpoint. Continuity guarantees that every probability value between the endpoints is attained; the formula also holds for a single-point interval. ∎

If the interval contains the midpoint, the peak value is $`\sigma((\theta_i-\theta_{i-1})/2)-\sigma(- (\theta_i-\theta_{i-1})/2)`$. So checking only the two ends of the interval misses the maximum of a middle class. For example, with thresholds $`(-1,1)`$ and $`\eta\in[-2,2]`$, the middle class peaks at 0, and both endpoints are strictly smaller. **Monotonicity of the upper tails of an ordered distribution does not mean that middle-class probabilities are monotone.**

Let the exact coordinate ranges of the branches be $`[\ell_{b,i},u_{b,i}]`$. The smallest axis-aligned box containing the joint output set over all branches is

```math
\ell_i=\min_b\ell_{b,i},\qquad u_i=\max_bu_{b,i}. \qquad (3.5)
```

Proof: every coordinate of every branch lies in this box; for any box covering the joint set, its $`i`$-th lower end cannot be higher than the joint minimum, and its upper end cannot be lower than the joint maximum. Finitely many branches and compact intervals guarantee that these extrema are attained, so no face can be tightened further. ∎ The corners of this box usually cannot be realized jointly by a single branch/latent value, and they need not sum to 1 as probabilities. It is not the jointly reachable set, and not a mixture over branch probabilities.

If the input $`[L,U]`$ is only a safe outer bound on the latent values, the formulas above are tight only for the **relaxed full scalar interval**. For example, if the actual latent value can only be $`-2`$ or $`2`$, wrapping it as $`[-2,2]`$ makes the middle-class peak at 0 a newly added feasible point; one cannot claim that the final probability upper bound is exact for the original set. Finite branches should be kept separate where possible, rather than merging latent-value intervals early and losing structure.

### Interface for a rigorous numerical checker

Rationals handle ratios, affine endpoints, thresholds, and midpoints; exponentials/sigmoids use proved outward rational brackets. If two sigmoids lie in $`[l_a,u_a]`$ and $`[l_b,u_b]`$ respectively, a sound interval for their difference is $`[l_a-u_b,u_a-l_b]\cap[0,1]`$. Subtracting central values must not be passed off as a lower bound.

For finitely many candidate values, the bracket of the min is $`[\min l_j,\min u_j]`$, and that of the max is $`[\max l_j,\max u_j]`$. The lower extremum of a middle class needs only the two endpoints; the upper extremum checks the endpoints and the midpoint inside the interval; even if the numerical brackets cannot decide which candidate is strictly largest, the max above can still be taken safely. If each sigmoid bracket has width ≤$`\varepsilon`$, the width for the difference is ≤$`2\varepsilon`$; min/max and taking envelopes across branches do not amplify the largest single-term numerical uncertainty.

The exact real range and the numerical outer envelope should be named separately. If each extremum bracket has width ≤$`\delta`$, the final output coordinate outer interval is at most $`2\delta`$ wider than the exact width. For a width threshold $`w`$, suppose the exact lower/upper extrema are enclosed by $`[\ell_-,\ell_+]`$ and $`[u_-,u_+]`$ respectively; then the exact width is enclosed by

```math
[\max(0,u_--\ell_+),\ u_+-\ell_-] \qquad (3.6)
```

An upper end ≤$`w`$ certifies a pass; a lower end >$`w`$ certifies a fail; everything else is **undecided**, requiring higher precision or conservative rejection according to the budget. Near equality, an approximate central value cannot be used to pass, and an undecided result due to an exhausted budget cannot be described as a proved failure.

## 4. SE3: candidate diameter, point estimates, and an upper bound on the acceptance rate for frozen tasks

Let the nonempty compact scalar candidate set $`𝒱(O)`$ be the union of all branch outputs, with all values having the same task semantics and scale. Write $`v_-=\min 𝒱`$, $`v_+=\max 𝒱`$, $`D=v_+-v_-`$.

**Proposition SE3.** For a specification that requires covering all candidates, every sound closed interval has width at least $`D`$; $`[v_-,v_+]`$ attains the lower bound. The worst-case absolute error of any point report $`a`$ is

```math
\sup_{v\in 𝒱}\left\vert a-v\right\vert=\max(\left\vert a-v_-\right\vert,\left\vert a-v_+\right\vert)
=D/2+\left\vert a-(v_-+v_+)/2\right\vert, \qquad (4.1)
```

so the minimum worst-case error is $`D/2`$, attained by reporting the midpoint.

**Proof.** The interval must contain both actually reachable endpoints, so its width is at least their difference; the minimal envelope covers all intermediate candidates. For any candidate $`v\in[v_-,v_+]`$, $`\left\vert a-v\right\vert`$ is at most the larger of the distances to the two endpoints, and the endpoints themselves are feasible, which gives the equality. Translating the center to 0 verifies the last expression, and minimizing gives the result. ∎

Next fix finitely many tasks $`i=1,\ldots,M`$, with weights $`w_i\ge0`$ set in advance, $`\sum_iw_i=1`$, a threshold $`w\ge0`$, and their respective candidate sets. If acceptance means that an interval of width ≤$`w`$ that is sound for all candidates must be output, then the largest possible robust acceptance mass is exactly

```math
A_{\max}(w)=\sum_{i=1}^M w_i𝟏\{D_i\le w\}. \qquad (4.2)
```

Proof: by the lower bound above, tasks with $`D_i>w`$ cannot be accepted; for the rest, outputting the minimal envelope accepts them all simultaneously and attains the upper bound. Random acceptance cannot exceed this upper bound either, as long as every actual acceptance must still be sound for all candidates. ∎ This is the optimum at the level of information/specification; an actual checker limited by compute budget, undecided numerics, or additional quality requirements may be lower. Fixed task weights do not represent population probabilities of natural text.

**Relative to the candidates does not mean intrinsically unidentifiable.** If the parser also lists a semantically invalid extra branch in the set, the increase in $`D`$ is merely the cost of this parser's conservatism. Only by proving one by one that these branches are truly admissible and indistinguishable worlds under the same observable evidence can this lower bound be interpreted as an identification limit of the observed information. Conversely, missing a true branch makes the box narrower but possibly unsound. Enlarging the candidate set can only make $`D`$ not decrease and $`A_{\max}`$ not increase; this by itself neither proves that linguistic ambiguity really exists nor proves that hard branches should be deleted.

## 5. SE4: the sign oracle for direction tasks, and worst-case multi-label error

If the frozen task definition is exactly comparing $`x`$ with $`b`$, let $`f(x,b)=\mathrm{sign}(x-b)\in\{-1,0,1\}`$. On inputs in the same units, the exact range of the difference over the rectangle is $`[x_--b_+,x_+-b_-]`$; which signs are included is determined directly by whether this interval intersects the negative half-line, zero, and the positive half-line. If the task has a tolerance band, the corresponding threshold must be specified in advance; the neutral width cannot be increased after the results are in.

**Proposition SE4.** The set $`ℒ`$ of feasible labels over all branches is a singleton if and only if there is one deterministic point label that is correct for all branches; this label can be given entirely by the sign rule, with no learned head needed. If $`s=\left\vert ℒ\right\vert\ge2`$, the worst-case 0–1 loss of any deterministic prediction is 1. If the predictor first gives a distribution, and the true candidate is chosen after seeing the distribution but before seeing the result of the random draw, then the minimum worst-case error probability is $`1-1/s`$, attained by sampling uniformly on $`ℒ`$.

**Proof.** In the singleton case, outputting the unique element is correct for all candidates; in the non-singleton case, for any fixed prediction there is at least one different feasible label. A randomized prediction is correct for each feasible label with probability equal to the mass $`p_\ell`$ it assigns, and $`\sum_{\ell\in ℒ}p_\ell\le1`$, so the minimum probability of being correct is ≤$`1/s`$, and the worst-case error is ≥$`1-1/s`$. The uniform assignment makes the probability of being correct equal to $`1/s`$ for every feasible label, attaining the lower bound. ∎

This is a robust conclusion without assumptions on branch probabilities; if there are validated branch probabilities or additional semantic evidence, the objective can change, but model confidence must not be silently substituted for it. Once the correct tuple is known, the comparison task is solved by the rule by definition; "the baseline has to be found in the language" may indicate parsing difficulty, but does not prove that a downstream ordered head, an LLM, or training from scratch is necessary. Different programs may produce the same value/direction, and agreement of outputs does not prove that the program semantics are faithful.

## 6. SE5: monotone and Lipschitz envelopes for fixed corresponding branches

On a common edit domain, the branch index set $`ℬ`$ is fixed. For each $`b`$, the context, direction, thresholds, and the map from raw input to features keep a pre-specified correspondence; it is not enough to keep the same branch name. For ordered classes $`k=2,\ldots,K`$, define the upper tails

```math
T_{b,k}(z)=P_b(Y\ge k\mid z)=\sigma(\eta_b(z)-\theta_{b,k-1}). \qquad (6.1)
```

Assume that along the order $`z\preceq z'`$ of this common edit, **every branch** has $`\eta_b(z)\le\eta_b(z')`$. A declared negative direction can first be handled by reversing the axis; undeclared coordinates and the context are fixed. Branch thresholds do not change with $`z`$.

**Proposition SE5.** $`\underline T_k(z)=\min_bT_{b,k}(z)`$ and $`\overline T_k(z)=\max_bT_{b,k}(z)`$ are both nondecreasing along the order above. If every $`f_b`$ satisfies $`\left\vert f_b(z)-f_b(z')\right\vert\le L_b d(z,z')`$ for the same distance, the min/max envelopes over finitely many branches are both $`L=\max_bL_b`$-Lipschitz. Here $`f_b`$ can be a fixed class probability or an upper tail; class probabilities are not required to be monotone.

**Proof.** Take the branch $`b'`$ attaining the minimum at $`z'`$; then $`\min_bT_b(z)\le T_{b'}(z)\le T_{b'}(z')=\min_bT_b(z')`$. Taking the branch attaining the maximum at $`z`$ likewise shows the max is nondecreasing. For the Lipschitz part, branch by branch $`f_b(z)\le f_b(z')+Ld`$; taking the max gives $`\max_bf_b(z)\le\max_bf_b(z')+Ld`$, and swapping the two points gives the bound on the absolute difference. For the min, apply the same argument to $`-f_b`$. ∎

Every class probability and every upper tail of an ordered logit is $`1/4`$-Lipschitz in $`\eta`$: for the first and last classes this comes from $`0\le\sigma'\le1/4`$; the derivative of a middle class is the difference of two numbers in $`[0,1/4]`$, so its magnitude is still ≤$`1/4`$, not $`1/2`$. Hence a fixed affine branch can take $`L_b=\left\vert a_b\right\vert/4`$ with respect to $`g`$; the $`2\lambda`$ latent-value bound of T2.2 gives $`\lambda/2`$. The envelope may be non-differentiable where the maximizing/minimizing branch switches; the finite-increment bound holds everywhere, and the derivative bound holds only where the derivative exists. Inside a real interval or on an open Euclidean domain, the Lipschitz condition guarantees differentiability almost everywhere; on an arbitrary abstract edit domain no existence of derivatives is additionally claimed.

With respect to the raw $`x,b`$, the ratio map must also be propagated. When $`b,b'\ge b_{\min}>0`$ and $`\left\vert x\right\vert,\left\vert x'\right\vert\le M`$,

```math
\left\vert x/b-x'/b'\right\vert\le \left\vert x-x'\right\vert/b_{\min}+M\left\vert b-b'\right\vert/b_{\min}^2. \qquad (6.2)
```

The proof splits the difference into $`(x-x')/b+x'(1/b-1/b')`$ and takes absolute values. When the denominator approaches 0 there are no uniform Greeks in terms of raw values. The direction is simple when only $`x`$ changes with positive $`b`$ fixed; changing the baseline at the same time does not guarantee that $`g`$ moves in the same direction as $`x`$.

**Three limitations.**

1. Each envelope being nondecreasing does not mean that the old and new outputs of two arbitrarily chosen different branches satisfy stochastic order. If the old and new true branches cannot be put in correspondence, a sufficient condition ensuring that all candidates move up is, for each tail $`k`$, $`\underline T_k(z')\ge\overline T_k(z)`$. For a fixed set made of the constant tails 0.2 and 0.8, both the lower and upper envelopes are unchanged, but choosing 0.8 before and 0.2 after is still a decrease.
2. Crossings of the min/max under a fixed branch set can only create kinks and still preserve Lipschitz continuity; **branches appearing/disappearing with the input** are different. Let two branches have constant tails $`\sigma(1)`$ and $`\sigma(-1)`$ respectively, each 0-Lipschitz and nondecreasing. If only the high branch is kept for $`z<0`$ and only the low branch for $`z\ge0`$, the output jumps down, and it is neither monotone nor Lipschitz with any finite global constant. Keeping both branches but letting the high branch disappear at 0 can also make the upper envelope jump down.
3. When a numerical edit changes the context, the direction choice, the thresholds, or the branch parameters, the pairing contract is not satisfied. Correct derivatives of local branches cannot mask dynamic selection at the global level; likewise, the envelope of a mixture of branches with multiple directions can cover safely, but carries no one-directional Greeks guarantee.

## 7. SE6: parsing coverage risk under a fixed acceptance rule, and audit confidence

Fix the parser, the branch-set rule, the head parameters, the calculator, and the acceptance event $`A=A(O)\in\{0,1\}`$; the width gate is part of this rule frozen in advance. Let the true complete semantics be $`Z^*`$, and let $`C=\{Z^*\in 𝒵(O)\}`$ be the event that the parsed set covers it. Here $`Z^*`$ includes the entity, metric, period, unit, baseline, direction, and the correct task semantics; checking only the numbers is not enough.

Assume that when $`A=1`$ and $`C`$ holds, the mathematics/calculator are sound for all branches, so the output interval necessarily contains the target $`u^*=f(Z^*)`$. Let $`E`$ be the event that the output misses $`u^*`$, and $`a=P(A=1)>0`$.

**Proposition SE6.**

```math
P(E\mid A=1)\le r_C:=P(C^c\mid A=1). \qquad (7.1)
```

If there are further events $`B_1,\ldots,B_s`$ of computation failure or model-assumption failure, and $`A\cap E\subseteq A\cap(C^c\cup\bigcup_jB_j)`$, then

```math
P(E\mid A=1)\le\min\left(1,r_C+\sum_jP(B_j\mid A=1)\right). \qquad (7.2)
```

**Proof.** The first inequality follows from $`A\cap E\subseteq A\cap C^c`$ by dividing both sides by $`a`$; the second first applies the union bound and then divides by the same $`a`$. In general equality does not hold, because when the parsed set misses the true branch, the output interval may still happen to cover the correct value. ∎

If only the unconditional $`P(C^c)\le\varepsilon`$ is known, all that follows is

```math
P(E\mid A=1)\le P(C^c\mid A=1)\le\min(1,\varepsilon/a). \qquad (7.3)
```

Counterexample: parsing fails on exactly a set making up 1% of the population, and the acceptor accepts only this set; then the unconditional coverage is 99%, but the failure rate among accepted examples is 100%. When $`a=0`$ the conditional risk is undefined, and one can only report an acceptance mass of 0. The three denominators of acceptance rate, joint error-and-acceptance rate, and post-acceptance risk must be kept separate.

**Two layers of probability in a fixed audit.** Suppose the audit units are drawn independently and representatively from the target distribution conditional on the fixed $`A=1`$, human judgements are correct, the number of coverage failures among a fixed audit of $`n\ge1`$ units is $`X\sim\mathrm{Bin}(n,r_C)`$, and $`0<\alpha<1`$. The one-sided exact upper confidence bound $`U_\alpha(X,n)`$ satisfies

```math
P_{\rm audit}\{r_C\le U_\alpha(X,n)\}\ge1-\alpha. \qquad (7.4)
```

For $`x\lt n`$, let $`U_\alpha(x,n)`$ be the unique solution of $`F_p(x):=P_p(X\le x)=\alpha`$; for $`x=n`$ take 1. For $`x\lt n`$, $`F_p(x)`$ is continuous and strictly decreasing in $`p\in(0,1)`$, going from 1 down to 0, so the solution exists and is unique. With the true rate $`p=r_C`$ fixed, for $`x\lt n`$ we have $`U_\alpha(x,n)\lt p`$ if and only if $`F_p(x)<\alpha`$; $`x=n`$ does not lead to miscoverage. Since $`F_p(x)`$ is nondecreasing in the integer $`x`$, the set of miscoverage counts is empty or of the form $`\{0,\ldots,k\}`$, with probability $`F_p(k)<\alpha`$. The boundary cases $`p=0,1`$ also satisfy coverage directly ($`X=n`$ when $`p=1`$). This gives the stated audit coverage probability of at least $`1-\alpha`$, which, combined with SE6, transfers to the envelope risk on future accepted examples. There is no early stopping based on intermediate audit results here.

If no accepted audit units exist, i.e. $`n=0`$, the convention is $`U_\alpha(0,0)=1`$, which gives only the trivial risk bound, and the binomial equation above is not solved. This is a different case from a population acceptance rate $`a=0`$: the system may accept some inputs while none has yet been audited.

**$`r_C`$ and $`\alpha`$ must not be confused.** The former is the true failure rate of the fixed pipeline on the target acceptance distribution; the latter is the frequency with which the audit procedure's upper bound fails to cover that rate. It is not the case that each prediction is correct with probability $`1-\alpha`$, and passing this audit cannot be treated as a known pointwise probability of being correct. If several risks are audited separately, their respective confidence failure budgets can be combined by a union bound; this is still different from merging prediction risk and audit confidence error into one number.

If the audit results are used to choose the width threshold, delete hard branches, or retune the acceptance rule, the fixed-rule inference above no longer applies directly; a new independent audit or an appropriate simultaneously valid method is needed. Correlation between fragments within a document, errors in human references, unknown event dependence, or deployment drift also need separate treatment. 10,000 bootstrap replicates cannot automatically replace the finite-sample sampling premise here. An audit without replacement on a frozen finite corpus should use the corresponding finite-population inversion and cannot be passed off as a future population risk.

## 8. Proof boundaries and checks for later implementation

| Obligation | Where closed | Premises retained |
|---|---|---|
| Positive-baseline normalization and affine range | SE1, CLOSED-LOCAL | Independent rectangle / relaxation status made explicit, positive denominator |
| Class extrema and the smallest joint coordinate box | SE2, CLOSED-LOCAL | Common output schema, fixed thresholds, full latent interval |
| Diameter and maximum robust acceptance mass | SE3, CLOSED-LOCAL | Full coverage of the specified candidates, no false claim of intrinsic ambiguity |
| Direction rule and worst-case classification loss | SE4, CLOSED-LOCAL | The target really is defined as a sign comparison; the quantifiers for the random adversary are fixed |
| Monotone and Lipschitz upper/lower envelopes | SE5, CLOSED-LOCAL | Fixed branch correspondence, all branches in the same direction, no numerical bypass |
| Layering of conditional risk and audit probability | SE6, CLOSED-LOCAL | Fixed acceptance rule, applicable sampling, and a correct audit reference |

A numerical program should check item by item or reject unsupported domains, and should keep mathematical pass, mathematical fail, and undecided-within-numerical-budget separate. The implementation proof for rigorous exp/sigmoid and the actual CPU records are the responsibility of a separate checker; this file has no run results and does not let finitely many successful examples replace the general proofs above. Whether real text produces complete, valid branches, whether they share the correct target, and whether intervals that are narrow enough with high enough coverage can be obtained remain unresolved weak links.

This result can serve as a theoretical interface and veto device for P2/P05. If a direction task is solved completely by sign comparison after full semantic parsing, the parsing research should be kept and the redundant learned head deleted; if the candidate branches are too wide, first check branch validity and semantic evidence that could be added, rather than only enlarging the model. G0/G1, the risk of natural-text parsing, and the paper's incremental contribution have not passed because this draft is complete.
