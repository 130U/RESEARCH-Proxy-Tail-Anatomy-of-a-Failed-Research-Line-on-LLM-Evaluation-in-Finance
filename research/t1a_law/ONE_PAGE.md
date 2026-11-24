# T1A: the quantitative rule passes its tests, but the worst case must not be read as the typical error

2026-11-16 (America/New_York). **Verdict: the task's numerical acceptance threshold is met.** The conclusion is conditional on T1's fixed input binding and independent half-a-last-digit-unit rounding boxes; 1% is this project's audit tolerance. We did not measure the rate at which models answer wrongly, nor prove that indeterminacy remains after combining full-text disclosures.

**Replication succeeded.** The original "Δ<100" rule of thumb is correct on 1,394 of 1,425 questions, i.e. **97.8246%**. The four bins 60–100, 100–150, 150–300 and ≥300 have 99/99, 16/83, 6/144 and 7/646 out of tolerance, respectively, matching the earlier recomputation. The 1,425 questions are defined as: two bound inputs, growth category, decided by T1; this is not the same as all strict growth-rate programs.

**The exact rule must keep the size of the growth.** For same-sign inputs with the same last-digit unit, a denominator that does not touch zero, and a non-zero growth rate, let $`g=(b-a)/a`$ and $`\Delta=\left\vert b-a\right\vert/d`$. Then the maximum relative error about the center is exactly

```math
R=\frac{1+g/2}{\Delta-\left\vert g\right\vert/2},\qquad
R\le\tau\iff\Delta\ge\frac{1+g/2}{\tau}+\frac{\left\vert g\right\vert}{2}.
```

So "100 units" is a small-growth approximation, not an unconditional theorem. Of the original 31 misclassifications, 24 omit the finite-growth correction, 5 did not put the inputs in a common unit, and 2 are not actually two-number growth rates. On the 1,427 standard growth-rate questions after unit harmonization, the rule of thumb agrees **97.97%** of the time. The significant-digit budget also depends on the leading digits (mantissa): the same number of input digits and the same growth rate can differ by nearly one digit of precision. The complete necessary and sufficient condition is in [Proofs §5](PROOFS.md).

**The zero-parameter rule for all operations passes.** First-order radius $`R_1=\sum_i\left\vert\partial_i f\right\vert h_i`$; out of tolerance is predicted by $`\left\vert f(x)-y\right\vert+R_1>\tau\left\vert y\right\vert`$, with no fitted parameters. The positive class is "out of tolerance"; the table below compares against independently recertified exact ranges:

| Operation | Questions | True positive | True negative | False positive / false negative | Agreement |
|---|---:|---:|---:|---:|---:|
| Growth rate | 1,458 | 585 | 873 | 0 / 0 | 100% |
| Difference | 872 | 332 | 540 | 0 / 0 | 100% |
| Ratio | 2,538 | 459 | 2,079 | 0 / 0 | 100% |
| Sum | 395 | 77 | 318 | 0 / 0 | 100% |
| Other | 74 | 16 | 58 | 0 / 0 | 100% |

All 15 items left undecided in the original T1 are certified stable; there are no contradictions with items T1 had already decided. The 100% is the result on this data at the 1% tolerance: the other four tolerance levels have 5 misclassifications in total, all of which are kept; the first-order approximation is not itself a certifier.

**The Benford prediction passes, but its assumptions must be made complete.** The leading-digit distribution alone cannot uniquely determine the out-of-tolerance rate. After adding a full log-uniform mantissa and its independence from the growth rate and digit-count distributions, and without reading the per-question mantissa, the prediction is **41.52%** and the observed value is **40.50%**, an error of **+1.01 percentage points**. Keeping the joint distribution of growth rate and digit count, the prediction is 42.10%; constraining only the leading digit, the numerically identified range is 38.69%–44.59%. This is a distribution-substitution test on the same data, not validation on an external sample.

**The probabilistic version is about half the worst case.** Under an independent continuous uniform rounding model, the expected number of out-of-tolerance test questions is **98.62**: **13.49%** of the 731 analyzable questions, against the worst case of **196/731=26.81%**. With the denominator of all 1,147 questions, the analyzed contributions are **8.60%** and **17.09%**, respectively; the probability for the other 416 questions is unknown, so 8.60% cannot be called a complete probability estimate for all of test. Writing 17% as "the answer is usually wrong" would exaggerate the result. The in-model probability is also not a known distribution of the true values in actual filings.

**Contribution positioning: a conditional precision audit of financial QA.** [Gittings (1991)](https://www.chicagofed.org/-/media/publications/economic-perspectives/1991/ep-may-jun1991-part1-gittings-pdf.pdf) already studied the rounding distortion of economic growth rates empirically; this round found no complete duplicate of a FinQA threshold validation. The mathematics is not a new discovery. Whether full-text constraints can overturn the conclusion is still to be tested by T1B, and whether models are marked wrong because of it is still to be tested by T1C.

[One figure: threshold, digit budget and tolerance curve](results/t1a_law.png) · [Full proofs](PROOFS.md) · [Replication method and interpretation of results](README.md) · [31 misclassifications of the original rule of thumb](results/simple_rule_mismatches.csv) · [Prior-art check](LITERATURE.md)
