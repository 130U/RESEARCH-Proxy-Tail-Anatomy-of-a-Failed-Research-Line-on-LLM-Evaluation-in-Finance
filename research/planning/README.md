# Exact frontier planning for a fixed audit size

Run from the repository root; the only dependency is the Python standard library; no network, no training:

```powershell
python -m research.planning.audit_frontier
python -m unittest research.planning.test_audit_frontier -v
```

The first command writes `frontier_results.json`; all N, m and vote counts are hypothetical design values. Rerunning updates the actual elapsed time. `source_hashes.json` records the source bytes used for this check.

Program interface:

```python
from research.planning.audit_frontier import minimum_zero_audit, coverage_plan
n = minimum_zero_audit(N=1000, B=3, alpha="1/20")
plan = coverage_plan(1000, [[11,0,0],[8,2,1],[6,5,0]], q="2/3", alpha="1/20")
```

`votes[j][c]` is the number of votes for class c received by the j-th fixed test point; all test points must have the same number of shards and classes. Ties go to the smallest class index. alpha and q accept Fraction, integers, or exact decimal/fraction strings, and reject float, to avoid implicit binary approximation changing strict boundaries.

Important contract:

- The model, shared core, population content version, shard mapping, test points and vote margins, audit size and sampling mechanism are fixed before the audit.
- Uniform sampling without replacement, and the audit's true judgments are reliable; each contaminated document touches only one shard, and the shared core does not change.
- This is the smallest fixed n that reaches the target coverage **when the future audit happens to find zero mislabels**. It neither guarantees that zero mislabels will be observed nor predicts the probability of that; the actual population contamination count is unknown, and the gate probability cannot replace the success probability.
- If x>0, call `research.local.audit.audit_upper(N,n,x,alpha)` and recompute coverage from the actual upper bound; if it fails, report failure. One must not resample or add audits repeatedly until the fixed-time interval looks good and still claim the same alpha guarantee.
- The output coverage is the label-stable fraction under the specified vote-change mechanism; it is not accuracy, nor does it mean the statistic interval is necessarily useful. A change to an original document ID can touch two shards; the shard budget must be converted, and this deletion-budget interface cannot be called directly.
