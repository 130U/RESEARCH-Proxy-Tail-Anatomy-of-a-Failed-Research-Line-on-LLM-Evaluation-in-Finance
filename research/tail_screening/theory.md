# Tail screening: recall targets, conditional extremes and the Gaussian baseline

This document discusses the tail-screening relation between an expensive score A and a cheap proxy B; no model is trained. The marginal transformation is used only to put the tails on a common scale; it preserves order but not means or actual returns. The derivations below do not write a first-order conditional-extremes approximation as a stronger multiplicative equivalence, and do not automatically stitch pairwise tail relations into multi-stage results.

## 1. What must be kept, and what screening is allowed

First transform continuous A and B to standard Laplace margins, whose upper tails are $`\Pr(A>u)=\Pr(B>u)=e^{-u}/2`$, $`u\ge0`$. When the raw scores have discrete ties, randomization or tie handling must be specified in advance; one cannot claim directly that the continuous formulas apply exactly. Let $`0\lt p\lt1/2`$ and $`u_p=\log(1/(2p))`$; the goal is to keep a fixed fraction $`0<\gamma<1`$ of the top p fraction of A.

This document first restricts attention to **upper-tail threshold screening** on B. Let $`v_q=F_L^{-1}(1-q)`$ and define

```math
R(p,q)=\Pr(B>v_q\mid A>u_p),\qquad
q_\gamma(p)=\inf\{q\in[0,1]:R(p,q)\ge\gamma\}. \qquad (1.1)
```

When the quantile of the conditional distribution is unique and continuous, $`b_\gamma(u)`$ is the $`1-\gamma`$ quantile of $`B\mid A>u`$, and $`q_\gamma(p)=\overline F_L(b_\gamma(u_p))`$. Any screening satisfies $`q_\gamma\ge\gamma p`$. Here $`q_\gamma/p`$ is called the **widening factor**; its reciprocal is not the recall. When recall γ is reached exactly, the precision of the passed samples is $`\gamma p/q_\gamma`$.

If arbitrary B-measurable screening regions are allowed, the method that minimizes the pass-through amount ranks by $`\Pr(A>u_p\mid B=b)`$. Only when this function is increasing in b is the upper tail of B the globally optimal region. A general conditional-extremes assumption does not provide this monotonicity; positively correlated Gaussians have it, and with negative correlation one should use the lower tail of B instead. So "upper-tail screening fails under negative correlation" does not mean the proxy has no screening value at all.

## 2. How strong an asymptotic the conditional-extremes form actually gives

Convergence in probability must take place under the conditional distribution $`\Pr(\cdot\mid A>u)`$, which changes with u. Let $`\beta<1`$, and suppose that in this sense

```math
B=\alpha A+A^\beta Z_u+o_p(A^\beta),\qquad Z_u\Rightarrow Z, \qquad (2.1)
```

where Z is a suitable real-valued limit with no mass at infinity. Laplace margins give $`A-u\mid A>u\sim\mathrm{Exp}(1)`$, so $`A/u\to1`$. As long as the residual is tight, $`B/u\to\alpha`$. Hence when $`\alpha>0`$, any fixed interior recall quantile satisfies

```math
b_\gamma(u)/u\to\alpha,\qquad
\frac{\log\,q_\gamma(p)}{\log\,p}\to\alpha. \qquad (2.2)
```

The proof only needs to concentrate the conditional probability between $`(\alpha-\varepsilon)u`$ and $`(\alpha+\varepsilon)u`$ and then squeeze the quantile. What it gives is $`q_\gamma=p^{\alpha+o(1)}`$, **not** $`q_\gamma\sim Cp^\alpha`$. α=0 gives at most a log ratio of 0, and the pass-through rate can tend to 0, a constant or 1; when α<0 the upper-tail gate on B needs to pass nearly all samples, $`q_\gamma\to1`$, and a negative α cannot be plugged into the power law above. In that case one instead has $`\log(1-q_\gamma)/\log\,p\to-\alpha`$.

For $`0<\beta<1`$, if Z is continuous near $`z_\gamma=G^{-1}(1-\gamma)`$ and the quantile is identifiable, then the excess $`A-u=O_p(1)`$ is smaller than $`u^\beta`$, which gives

```math
b_\gamma(u)=\alpha u+u^\beta z_\gamma+o(u^\beta),\qquad
q_\gamma(p)=2^{\alpha-1}p^\alpha
\exp\{-z_\gamma u_p^\beta+o(u_p^\beta)\}. \qquad (2.3)
```

The little-o in the exponent can still diverge. Even if $`z_\gamma=0`$, it cannot be cut down to $`1+o(1)`$. For α>0, the exact condition for a finite positive C with $`q_\gamma\sim Cp^\alpha`$ to exist is that the quantile offset converges:

```math
b_\gamma(u)-\alpha u\to c\in ℝ,
\qquad C=2^{\alpha-1}e^{-c}. \qquad (2.4)
```

A common sufficient case is β=0 together with the existence of the joint limit $`(A-u,Z_u)\mid A>u\Rightarrow(E,Z)`$. If the target quantile c of $`\alpha E+Z`$ is unique, the formula above holds; if the excess–residual independence of the HT-type limit is used, it should be stated explicitly as a joint assumption. When β<0 and the residual is tight, $`B-\alpha u\Rightarrow\alpha E`$, so for α>0, $`q_\gamma\sim2^{\alpha-1}\gamma^\alpha p^\alpha`$. β>0 can also give multiplicative equivalence, but one must separately prove that the target quantile error is $`c+o(1)`$; the first-order normalization alone is not enough.

**Mass at infinity cannot be ignored.** Let B=A with probability π, and A and B independent with the remaining probability; the margins are still Laplace. Given that A is extreme, the limit of $`B-A`$ has mass $`1-\pi`$ escaping to minus infinity. If γ<π, then $`q_\gamma\sim(\gamma/\pi)p`$; if γ>π, then $`q_\gamma\to(\gamma-\pi)/(1-\pi)`$. So fitting α=1 without checking whether the target quantile falls in the finite part of the residual may not even give the same log exponent for all recall targets.

### α=1, β>0 can still have an unbounded widening factor

Fix $`0<\beta<1`$, take $`S\sim\mathrm{Exp}(1)`$ and independent $`U,V\sim\mathrm{Uniform}[0,1]`$, and let

```math
X=S+S^\beta U,\qquad Y=S+S^\beta V. \qquad (2.5)
```

X and Y have the same margin and are continuous. Using their common CDF, transform them into exact Laplace variables $`A=T(X),B=T(Y)`$, where on the positive tail $`T(x)=-\log(2\Pr(X>x))`$. Then

```math
T(x)=x-x^\beta+o(x^\beta). \qquad (2.6)
```

Proof: let $`r+r^\beta=x`$; then $`\Pr(X>x)\le e^{-r}`$. Fix any ε>0; on $`U\ge1-\varepsilon`$ we have $`\Pr(X>x)\ge\varepsilon e^{-r_\varepsilon}`$, where $`r_\varepsilon+(1-\varepsilon)r_\varepsilon^\beta=x`$. The two roots are $`x-x^\beta+o(x^\beta)`$ and $`x-(1-\varepsilon)x^\beta+o(x^\beta)`$; letting x tend to infinity first and then ε tend to 0 squeezes out this equivalence.

Under $`A>u`$, $`X>T^{-1}(u)=u+u^\beta+o(u^\beta)`$, so $`S\ge u+o(u^\beta)`$; on the other hand, for any δ>0,

```math
\Pr(S>u+\delta u^\beta\mid A>u)\le2e^{-\delta u^\beta}\to0. \qquad (2.7)
```

So $`S=u+o_p(u^\beta)`$. V is not affected by the conditioning event; substituting into Y and T gives $`B=u+u^\beta(V-1)+o_p(u^\beta)`$. Since also $`A-u=O_p(1)`$,

```math
\frac{B-A}{A^\beta}\mid A>u\Rightarrow V-1,
\qquad
q_\gamma(p)/p=\exp\{\gamma u_p^\beta+o(u_p^\beta)\}\to\infty. \qquad (2.8)
```

This is a counterexample with true Laplace margins and a finite non-degenerate residual, not an arbitrarily assembled incompatible conditional model. α=1 only says that the log scales are the same. Note also: with α=1 and β>0, the Laplace margins force Z to have no mass on positive values, because $`\Pr(B>A+\varepsilon A^\beta\mid A>u)\le e^{-\varepsilon u^\beta}`$; but Z lying entirely on the non-positive half-line still allows the unbounded widening factor above.

## 3. Gaussian copula: the full recall integral and lower-order corrections

Let $`(X,Y)`$ be standard bivariate normal with correlation coefficient ρ, and A, B their respective Laplace marginal transformations. **ρ is the latent correlation after the normal-score transformation, not the Pearson correlation of arbitrary raw bounded scores.** For continuous margins, the normal scores are $`\Phi^{-1}(F_A(A))`$ and $`\Phi^{-1}(F_B(B))`$. A mismatch of a curve matched on the raw Pearson correlation is not enough to reject the Gaussian copula.

Let $`-1<\rho<1`$, $`\sigma=\sqrt{1-\rho^2}`$, $`x=\overline\Phi^{-1}(p)`$, $`y=\overline\Phi^{-1}(q)`$. The overlap probability of the two upper-tail lists and the recall are exactly

```math
J_\rho(p,q)=\int_x^\infty\phi(s)\overline\Phi\!\left(\frac{y-\rho s}{\sigma}\right)ds,
\qquad R_\rho(p,q)=J_\rho(p,q)/p. \qquad (3.1)
```

The precision is $`J_\rho(p,q)/q`$; $`q_\gamma`$ is obtained uniquely by inverting $`J_\rho(p,q)=\gamma p`$. When ρ>0, $`\Pr(X>x\mid Y=y)=\overline\Phi((x-\rho y)/\sigma)`$ is increasing in y, so this threshold is also optimal among all screening regions that use only B.

If both lists take only the fraction p, then for fixed $`-1<\rho<1`$ the corner integral gives

```math
J_\rho(p,p)\sim\frac{(1+\rho)^2}{2\pi x^2\sqrt{1-\rho^2}}
\exp\!\left(-\frac{x^2}{1+\rho}\right). \qquad (3.2)
```

For example, substituting $`(s,t)=(x+a/x,x+b/x)`$ into the bivariate normal density, the main exponent increment is $`-(a+b)/(1+\rho)`$ and the integration constant is $`(1+\rho)^2`$. So for any fixed ρ<1 the equal-budget upper-tail recall $`J(p,p)/p\to0`$; high correlation does not mean overlap of very deep tail lists.

### Full multiplicative asymptotics at fixed recall, 0<ρ<1

Let $`z=\Phi^{-1}(1-\gamma)`$ and $`L=\log(1/p)`$. On the normal scale the threshold satisfies

```math
y_\gamma(p)=\rho x+\sigma z+\frac\rho x+O(x^{-2}). \qquad (3.3)
```

The reason is that $`D=X-x\mid X>x`$ satisfies $`𝔼D=x^{-1}+O(x^{-3})`$ and $`𝔼D^2=O(x^{-2})`$. The conditional CDF is $`𝔼\Phi((y-\rho x-\rho D)/\sigma)`$; expanding at $`y=\rho x+\sigma z+\rho/x`$, the error is $`O(x^{-2})`$, and the density there tends to $`\phi(z)/\sigma>0`$, so the quantile error is also $`O(x^{-2})`$.

Then, using the Mills ratio, the constant term in the square is $`\sigma^2z^2/2+\rho^2`$, which gives

```math
q_\gamma(p)\sim
\frac{e^{-\rho^2-\sigma^2z^2/2}}{\rho}
(4\pi L)^{-\sigma^2/2}\,p^{\rho^2}
\exp\{-\rho\sigma z\sqrt{2L}\}. \qquad (3.4)
```

Equivalently, keeping the normal quantile x, the lower-order factor is $`(2\pi)^{-\sigma^2/2}x^{-\sigma^2}\exp(-\rho\sigma zx)`$. $`e^{-\rho^2}`$ comes from the mean excess under the condition $`X>x`$; mistakenly replacing it with $`X=x`$ would miss this constant. Replacing the linear exponent using $`x=\sqrt{2L}+O(\log\,L/\sqrt L)`$ causes only a relative error of $`1+o(1)`$.

So the Gaussian copula does have $`\log\,q_\gamma/\log\,p\to\rho^2`$, but in general there is no finite positive C with $`q_\gamma\sim Cp^{\rho^2}`$. When γ>1/2, z<0 and there is a growing $`\exp(c\sqrt L)`$ correction; when γ=1/2 this correction disappears, but $`L^{-\sigma^2/2}`$ remains. For any fixed $`0<\rho<1`$, $`q_\gamma/p\to\infty`$: the power term $`p^{-(1-\rho^2)}`$ eventually dominates these lower-order terms. "Close to Gaussian with high correlation, so only a fixed factor is needed" is at most an empirical approximation within a finite window of p.

HT2004 §8.6 and Table 1 give the centering term $`\rho^2u`$ and the scale $`u^{1/2}`$ for the positively correlated Gaussian; the original uses Gumbel margins. The Laplace positive tail differs from the Gumbel only by a constant, so here too α=ρ², β=1/2, and

```math
\frac{B-\rho^2A}{\sqrt A}\mid A>u
\Rightarrow N\bigl(0,2\rho^2(1-\rho^2)\bigr). \qquad (3.5)
```

The residual scale contains $`\sqrt2`$, which must not be omitted; α is also not the $`\eta=(1+\rho)/2`$ of the equal-threshold joint tail index. [HT2004 original §8.6](https://www.d.umn.edu/~yqi/mydownload/heffemantawn.pdf)

Finite-threshold corrections have clear prior work: Lugrin, Tawn and Davison (2021) §3.1, Theorem 1, directly study the Gaussian copula with Laplace margins, giving the signed centering $`\mathrm{sign}(\rho)\rho^2x`$, the residual variance above and a finer normalization, and formulas (12)–(13) discuss the effective parameter shift at finite thresholds. The fixed-recall quantile expansion in this document serves the screening problem; one cannot claim a new conditional-extremes theory merely because it has been rewritten as a pass-through cost, and a slope over a finite range does not automatically equal the structural α. [Original §3.1](https://onlinelibrary.wiley.com/doi/full/10.1002/sta4.401)

### Zero, negative and perfect correlation

When ρ=0 the variables are independent and $`q_\gamma=\gamma`$ for all p. For fixed $`-1<\rho<0`$ the same $`y_\gamma=\rho x+\sigma z+\rho/x+O(x^{-2})`$ still holds, but it tends to minus infinity, so the B upper-tail pass-through $`q_\gamma\to1`$. More precisely, letting $`a=\left\vert\rho\right\vert`$,

```math
1-q_\gamma(p)\sim
\frac{e^{-a^2-\sigma^2z^2/2}}{a}
(4\pi L)^{-\sigma^2/2}p^{a^2}
\exp\{a\sigma z\sqrt{2L}\}. \qquad (3.6)
```

The Laplace conditional centering under negative correlation is $`-\rho^2A`$, not $`+\rho^2A`$. After switching to screening on −B, the cost is that of the positive correlation |ρ|. The endpoints must be listed separately: at ρ=1, $`q_\gamma=\gamma p`$; at ρ=−1, for the B upper tail, $`q_\gamma=1-(1-\gamma)p`$. These endpoints cannot be obtained by direct substitution into the formulas for fixed $`0<\left\vert\rho\right\vert<1`$; the two limits do not agree.

## 4. Multi-stage screening: multiplying α needs a common conditional structure

Suppose the variables from expensive to cheap are $`A_0,A_1,\ldots,A_k`$. Pairwise fits $`A_j\approx\alpha_jA_{j-1}`$ are not enough to imply the endpoint exponent $`\prod_j\alpha_j`$, because the intermediate samples picked out by $`A_0`$ being extreme can differ from the samples when $`A_{j-1}`$ alone is extreme.

A counterexample already exists in the trivariate Gaussian: the correlation matrix with $`\rho_{01}=\rho_{12}=1/2`$ and $`\rho_{02}=0`$ is positive definite. The Laplace α of each adjacent pair is 1/4, the product is 1/16, but the endpoints are independent and α is 0. In this example it is not estimation error; the pairwise structure simply does not specify the trivariate relation.

A sufficient joint condition is that, under the same condition $`A_0>u`$, for all j,

```math
A_j-\alpha_jA_{j-1}=o_p(u),\qquad \alpha_j>0. \qquad (4.1)
```

A finite recursion immediately gives $`A_k/u\to\prod_j\alpha_j`$, and squeezing the endpoint quantile then gives the log screening exponent. A more interpretable sufficient condition is a Markov chain $`A_0\to A_1\to\cdots\to A_k`$ whose transition kernels satisfy $`\Pr(\left\vert A_j/y-\alpha_j\right\vert>\varepsilon\mid A_{j-1}=y)\to0`$ as $`y\to\infty`$, valid for the large-y version used. The Markov property means that selecting $`A_0>u`$ no longer changes the transition kernel given the intermediate value, which is what allows step-by-step propagation. A Gaussian Markov chain has $`\rho_{02}=\rho_{01}\rho_{12}`$, so only with positive correlations does it correspond to multiplying α.

This still gives only the log order at the endpoint. The multiplicative constant, the lower-order losses and the threshold at each stage need a common residual limit and sufficiently fine control of the quantile error. The total recall of gates in series is exactly the product of the recalls at each stage **conditional on the true A upper tail and on having passed the earlier stages**; multiplying recalls measured separately for each pair of variables usually has no such meaning. The overall pass-through amount is likewise the probability of the intersection of the gate events and cannot be multiplied unconditionally.

## 5. MES and "a negative proxy exercise" must correspond to different payoffs

Here we return to the actual utility/return scores $`\widetilde A,\widetilde B`$, assuming the expectations exist. Laplace transformation preserves only order, and its means cannot replace returns in the original units. With the upper-tail convention, define

```math
\mathrm{MES}_{A\mid B}(q)=𝔼[\widetilde A\mid\widetilde B>b_q]. \qquad (5.1)
```

This is not $`𝔼[\widetilde B\mid\widetilde A>a_p]`$; the two condition in different directions. Literature on financial losses or negative returns may use the lower tail and the opposite sign, so the convention should be declared first. MES measures the average value of the selected samples and is not the same as recall of the target's upper tail.

If whenever the proxy exceeds the threshold one must pay K in exchange for the actual return, the strategy value can be defined as

```math
V_{\rm proxy}(K,b)=𝔼[(\widetilde A-K)𝟏\{\widetilde B>b\}]
=\Pr(\widetilde B>b)\{\mathrm{MES}_{A\mid B}-K\}. \qquad (5.2)
```

The value of this forced proxy decision can be negative. The value of exercising only after actually seeing A is $`V_{\rm oracle}(K)=𝔼[(\widetilde A-K)_+]\ge0`$, and

```math
V_{\rm oracle}-V_{\rm proxy}
=𝔼[(\widetilde A-K)_+𝟏\{\widetilde B\le b\}]
+𝔼[(K-\widetilde A)_+𝟏\{\widetilde B>b\}]\ge0. \qquad (5.3)
```

The two nonnegative terms are the loss from missing high value and the loss from wrongly selecting low value. $`𝔼[(\widetilde A-K)_+]`$, $`(𝔼\widetilde A-K)_+`$ and $`𝔼[(𝔼[\widetilde A\mid\widetilde B]-K)_+]`$ are themselves never negative; net returns after deducting prices or evaluation costs are a different matter. A negative proxy strategy value cannot be written as "the true option value is negative".

Under the original standard normal X, Y, $`𝔼[X\mid Y>y]=\rho\phi(y)/\overline\Phi(y)`$. For example, with K=x and B also taking only the top p, $`V_{\rm proxy}=\rho\phi(x)-xp`$; the Mills ratio makes it $`p\{(\rho-1)x+\rho/x+O(x^{-3})\}`$, which is eventually negative for any fixed ρ<1. This shows that a buy rule triggered by the proxy can lose money; it does not violate the nonnegativity of the positive-part payoff, and does not prove that every optimal decision based on B has no value.

## Sources and the limits of the derivations in this document

- Heffernan, J. E. & Tawn, J. A. (2004), *A conditional approach for multivariate extreme values*, JRSS B 66(3), 497–546. Read the original §8.6, Table 1 and the conditional model sections; the Gaussian α, β and residual covariance were checked against them. [Original PDF](https://www.d.umn.edu/~yqi/mydownload/heffemantawn.pdf); [DOI](https://doi.org/10.1111/j.1467-9868.2004.02050.x).
- Keef, C., Papastathopoulos, I. & Tawn, J. A. (2013), *Estimation of the conditional distribution of a multivariate variable given that one of its components is large: Additional constraints for the Heffernan and Tawn model*, Journal of Multivariate Analysis 115, 396–404. [DOI](https://doi.org/10.1016/j.jmva.2012.10.012); [author institution entry](https://research.lancaster-university.uk/en/publications/estimation-of-the-conditional-distribution-of-a-vector-variable-g/). This check covered the metadata and abstract; the request for the publisher's full text returned 403, and we do not claim to have read all of that paper's constraints.
- Rohrbeck, C. & Tawn, J. A., *Some benefits of standardisation for conditional extremes*; the authors' public manuscript §1–2 explicitly restates Keef's Laplace framework and the joint excess limit, and also points out the limits of standardization and of conditional models. [Author manuscript](https://eprints.lancs.ac.uk/id/document/119955). This is a statement in the authors' manuscript and does not pretend that Keef's original was obtained.
- Lugrin, T., Tawn, J. A. & Davison, A. C. (2021), *Sub-asymptotic motivation for new conditional multivariate extreme models*, Stat 10(1), e401. Read the open original §3.1 and Theorem 1, checking the Laplace normalization of the Gaussian and the finite-threshold correction. [Original and DOI](https://onlinelibrary.wiley.com/doi/full/10.1002/sta4.401).

The full Gaussian fixed-recall expansion, the counterexamples and the multi-stage conditions in this report are all derived in the text; no first discovery is claimed on this basis. What should be tested empirically is the actual overlap, recall, pass-through cost and utility within pre-specified ranges of p and γ, not declaring a cheap proxy reliable on the basis of an overall correlation coefficient or a single fitted α.
