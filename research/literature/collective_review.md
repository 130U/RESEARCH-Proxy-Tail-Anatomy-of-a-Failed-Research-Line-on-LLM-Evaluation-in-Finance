# Independent review of the collective-statistic checker

Date: 2026-11-15. Read-only review of `research/certificates/collective.py`, its tests, the example generator, the README, `research/theory/collective_metrics.md` and the saved JSON/reports; no internet access, no training, and no modification of the implementation under review.

**Conclusion: within the declared fixed test set, jointly affected heads, the outer-relaxation threat model with arbitrary head outputs, and the K≥2 interface scope, no substantive error affecting the correctness of the reported envelopes was found. The two statistics of the audit wrapper share the same coverage event, and the conditional interpretation is correct. This conclusion does not verify real corpora, training sources, the amount of contamination or novelty.**

## Correspondence between mathematics and implementation

| Object checked | Review conclusion |
|---|---|
| Reachable classes for a fixed affected set B | For a class c, changing all votes in B to c both maximizes its votes and minimizes its rivals' votes, so `u_c+|B| >= u_d+1{d<c}` is necessary and sufficient; the tie rule favouring the smallest class index is implemented correctly |
| Enumerating only exactly min(k,m) heads | A larger set can keep the original votes of the added heads, so it covers the union of the "at most k" sets; no real possibility under a smaller budget is missed |
| Collective vs pointwise relaxation | The implementation keeps the same column identities and the same B; pointwise `reachable` lets different points use different affected heads, so the collective interval is contained in the pointwise envelope computed by the same method |
| Accuracy | For a fixed B, points whose true label is the only reachable label give the worst-case number correct, and points where the true label is reachable give the best-case number correct; any cross-point choice is allowed within this relaxed model, so the bound is exact |
| Macro-F1 component bounds | With fixed support counts, F1 is non-decreasing in TP and non-increasing in FP. Each class's endpoints are safe, but different classes are not necessarily attained at the same time; `component` is not wrongly labelled as the exact extreme of the macro average |
| Macro-F1 DP | The state is TP and the prediction counts; future admissible labels do not depend on past choices, so merging identical counts loses no reachable value. All K classes are fixed and classes with empty support contribute 0, consistent with the formula |
| Handling of budget overruns | The number of subsets is checked in advance, and the DP raises an exception immediately when it exceeds the state budget; no partial-search extreme is treated as a complete interval. `exact` may refuse because the pointwise-relaxation state is too large, even when some collective subproblems are small; this is a computational limit, not a wrongly issued certificate |
| Numeric endpoints | Fraction computes exactly and keeps fraction strings; if the binary64 display rounds inward, `nextafter` corrects it outward; the tests include non-binary rationals such as 1/5 and 11/15 |
| Audit wrapper | An exact hypergeometric upper bound at fixed n acts on the number of contaminated documents, and is converted to a head budget under explicit assumptions such as stable IDs, each document affecting at most one partition, and an unchanged shared core. Accuracy and macro-F1 are both derived from the same event K_true≤K_upper, so α does not need to be split again between the two |

## Independent checks actually carried out

Source level: **our experiment, independent review of collective**. Local Windows CPU, Python 3.12.14; commands use `-B`, no bytecode is written, no network.

1. Reran `python -B -m unittest research.certificates.test_collective -v`: all 7 tests pass, framework timing 0.346 seconds. The oracle in the tests directly enumerates the modified voting cells, which differs from the counting DP of the implementation.
2. Extended to 112 input/budget combinations with fixed seed 4781: K∈{2,3,4}, J∈{2,3}, m∈{2,3}, random true labels (missing classes allowed), budgets from 0 to m+1; compared with a direct modified-vote-cell oracle. All exact collective endpoints equal the oracle, all component bounds contain the oracle, and all floating-point display endpoints contain the exact fractions from outside.
3. Recomputed the audit wrapper from the saved `audit_example.json` as-is; apart from identity fields it is identical to `audit_certificate.json`; the input SHA256 and the checker SHA256 both match the current bytes. The constructed input N=20, n=16, x=0, α=1/20 gives K_upper=1, and at the same time accuracy [1/4,3/4] and macro-F1 [1/5,11/15]. This is a hand-made mathematical input, not a finding of an actual audit.
4. Checked the results table item by item: the shared-head constraint strictly tightens the first example; in the second example the exact macro-F1 is always 5/9, while the component envelope [4/9,2/3] is wider. The boundaries k=0 and k≥m follow the fixed class convention.

## Limitations that must be kept

- exact refers only to the explicitly stated finite test points and the model with arbitrary outputs from affected heads; consistency on identical inputs, achievability by actual training and achievability at the document level are all relaxed. It cannot be called "the tightest certificate for real retraining".
- If a modification of an original document spans two IDs/partitions, or a shared tokenizer/backbone is contaminated, the number of contaminated documents cannot be used directly as the head budget. The checker does not verify these premises.
- Fixed n, uniform sampling without replacement, a correct audit and a fixed population are statistical premises; this is not a sequential confidence sequence, does not certify population generalization, and cannot fix problems with test labels or sample selection.
- Each input column is the class predictions of one head; it cannot be replaced with the per-class vote-count matrix from planning; the `input_kind` in the README and CLI already makes this explicit.
- The theory allows discussing the trivial case K=1; the current public interface explicitly requires K≥2 and rejects K=1. The acceptance scope should state this difference clearly and not describe the code as implementing every boundary case of the theory.
- A single `checker_sha256` binds only `collective.py`; reproduction also depends on imported code such as `local/audit.py`. The deliverable should carry the complete source code together with the package manifest; a single-file hash cannot serve as the identity of the dependency closure.
- The 7 tests and the 112 extended cases are checks for implementation errors; general correctness depends on the proofs of the propositions above. A new mathematical component does not make G0/G1 or the final state on real data pass automatically.
