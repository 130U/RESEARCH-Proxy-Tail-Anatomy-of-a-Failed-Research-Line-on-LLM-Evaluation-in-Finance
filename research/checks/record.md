# WP0.3 mathematical soundness check record

Date: 2026-11-15 (America/New_York). This record goes with `theory/notes.md`.

## Propositions checked

The tie counterexamples of T1.3–T1.4; the specification counterexamples of T2.1; the structural constants, monotonicity and probability-derivative bound of the linear ordered head in T2.2; the rational unit transformations of T2.3; the convex order, ES and VaR counterexamples of T3.1 on a finite probability grid.

This is Phase 0 proof-support computation; it is not Phase 1 main-line training and not an experiment on financial model performance.

## Budget (before execution)

- Hardware: CPU, single process; 0 GPU memory; 0 training tokens; no network, no data download.
- Expected time: under 30 seconds; expected memory: under 100 MB. Both are pre-execution estimates; the actual resources are as recorded in the results file.
- Data: constructed vote/probability vectors; 100,000 numeric points with a fixed seed; 3 Bernoulli variables on a probability grid with denominator 12.
- Software: Python standard library; no packages installed.
- Base commit: `8e4dd0b33c95ac2ac1a6015eba6f2dfafe5c1254`; the executor writes the hash of the check source into the results.
- Seeds: `20261115`.

## Reproduction

Run from the repository root:

```powershell
python research/checks/theory_checks.py --output research/checks/results.json
```

## Limits of interpretation

`results.json` stores the actual number of checks, the elapsed time, software and machine information, and the source SHA256. Passing finite tests only shows that these inputs did not expose an implementation error; the global conclusions come from the proofs in `notes.md`. The linear head is a mathematical example with known weights; it is not attached to a transformer, and there is no real parser, training or financial data. The enumeration with denominator 12 is not an enumeration of all real-valued probability couplings; the conclusion for all couplings rests on the finite-dimensional extremal proof of T3.1.

`pdflatex`, `xelatex` and `tectonic` were not found in this environment. The `notes.tex` source is provided; **no PDF was compiled, and layout acceptance is not claimed as complete**.

## Executed results (our experiment)

First execution: Python 3.13.12, Windows 11, Intel64 Family 6 Model 170, 0.9293 seconds; peak memory not measured.

- 439 configurations that satisfy the vote-margin condition were checked against all vote changes within budget; both the tie counterexample and the statistic-interval counterexample were reproduced.
- 100,000 numeric points passed: the largest observed absolute probability derivative was 0.1874999991, below the stated bound of 0.25; the smallest upper-tail probability increment was −1.11e−16, within the 1e−15 floating-point tolerance. This floating-point residual is not reported as a counterexample to mathematical monotonicity, nor as exactly zero error.
- 27 rational unit transformations were exactly equal; invalid structural weights were rejected.
- 50,388 probability mass tables with denominator 12 were enumerated, of which 50 satisfy the marginals (3/12,6/12,9/12). Their stop-loss, second moment and ES all do not exceed the comonotone upper bound.
- VaR median counterexample: 0 for comonotone, 1 for countermonotone.

These checks did not sample a financial population, so no confidence interval for financial accuracy is reported. `notes.tex` only received a static check for ASCII content and matching environment begin/end pairs; this is not a TeX compilation test.
