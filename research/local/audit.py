"""Exact fixed-size finite-population confidence inversion (integer arithmetic).

This validates a mathematical component, not the truth of a corpus timestamp.
"""
from fractions import Fraction
from math import comb, nextafter, inf
import itertools
import json
from pathlib import Path


def _integer(x):
    return isinstance(x, int) and not isinstance(x, bool)


def audit_upper(N, n, x, alpha='0.05'):
    if not all(_integer(v) for v in (N, n, x)) or not 0 <= x <= n <= N:
        raise ValueError('require integer 0 <= x <= n <= N')
    a = Fraction(str(alpha))
    if not 0 < a < 1:
        raise ValueError('alpha must be in (0,1)')
    den = comb(N, n)
    def accepted(K):
        low, high = max(0, n - N + K), min(x, K, n)
        num = sum(comb(K, j) * comb(N-K, n-j) for j in range(low, high+1))
        return num * a.denominator > a.numerator * den
    lo, hi = x, N - n + x
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if accepted(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


def reachable(counts, k):
    """Exact pointwise relaxation: up to k arbitrary shard vote replacements.

    A document-ID change can affect two shards; caller must supply shard budget.
    Ties go to smallest class index. Same corrupted shards across examples are
    relaxed independently, so statistic bounds are conservative jointly.
    """
    if not _integer(k) or k < 0 or not counts or not all(_integer(v) and v >= 0 for v in counts) or sum(counts) == 0:
        raise ValueError('nonempty integer votes and nonnegative integer k required')
    m = sum(counts)
    result = []
    for c, count in enumerate(counts):
        for added in range(min(k, m-count)+1):
            new = count + added
            removals = sum(max(0, v - (new - int(j < c))) for j, v in enumerate(counts) if j != c)
            if removals <= added:
                result.append(c)
                break
    return result


def statistic_interval(votes, scores, k):
    if not votes or len(votes) != len(scores):
        raise ValueError('one nonempty score row per vote row required')
    lo, hi, sets = [], [], []
    for v, s in zip(votes, scores):
        if len(v) != len(s) or not all(not isinstance(z, bool) and 0 <= z <= 1 for z in s):
            raise ValueError('scores must lie in [0,1] and match classes')
        # A float denotes its exact binary value, not an intended decimal.
        exact = [Fraction(z) for z in s]
        r = reachable(v, k)
        sets.append(r)
        lo.append(min(exact[c] for c in r))
        hi.append(max(exact[c] for c in r))
    lower, upper = sum(lo)/len(lo), sum(hi)/len(hi)
    l, u = float(lower), float(upper)
    if Fraction(l) > lower: l = nextafter(l, -inf)
    if Fraction(u) < upper: u = nextafter(u, inf)
    return dict(lower=l, upper=u, lower_exact=str(lower), upper_exact=str(upper),
                arithmetic='exact rational scores; outward-rounded binary64 endpoints', reachable=sets,
                pointwise_certified=sum(len(r)==1 for r in sets), n=len(sets))


def run():
    rows = []
    for N, n in [(100000,1000),(10000,1000),(1000,500),(1000,1000),(100,99)]:
        k = audit_upper(N,n,0)
        rows.append(dict(N=N,n=n,x=0,alpha='0.05',upper=k,
                         tie_favourable_min_m=max(1,2*k),strict_margin_min_m=2*k+1,
                         source='assumed design grid, not measured SEC counts'))
    examples = [dict(votes=[[2,0,0]], scores=[[1,0,0]],k=1),
                dict(votes=[[1,1,0]], scores=[[1,1,0]],k=0)]
    data = dict(status='mathematical_component_only',audit_grid=rows,
                examples=[dict(**e,result=statistic_interval(e['votes'],e['scores'],e['k'])) for e in examples],
                assumptions=['uniform sample without replacement, fixed n, perfect timestamp adjudication',
                             'trusted core and all shared components are temporally valid',
                             'stable document IDs, at most k affected independent shards',
                             'fixed test inputs, labels, and additive bounded scores'],
                limitations=['not a real trained model certificate','not a population generalization interval',
                             'not an anytime-valid audit','does not certify trusted core'])
    out = Path('research/experiments/local_foundations/audit_results.json')
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,indent=2),encoding='utf-8')
    print(json.dumps(data,indent=2))


if __name__ == '__main__':
    run()
