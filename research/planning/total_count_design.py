"""Exact fixed zero-finding certificates for total contamination K <= k-1.

For positive stratum populations N and fixed uniform-without-replacement audit
sizes n, risk is max_{sum(q)=k} prod_h C(N_h-q_h,n_h)/C(N_h,n_h). Contamination
counts are fixed, not random. Monotonicity reduces the excluded set K >= k to
its boundary K=k. This module does not audit documents or establish provenance.

Two independent arithmetic kernels are supplied: a combinatorial-probability
dynamic program and a maximum-head heap over decreasing prefix multipliers.
All comparisons use Fraction. Risk(0)=1; Risk(k>sum(N))=0 (empty excluded set).
The optimization searches *all* fixed allocations, up to safe symmetry/cost
pruning, and never equates the balanced design with the unrestricted optimum.

Arithmetic-operation complexity (integer bit costs are additional): greedy
O(d + k log d), DP O(d*k*min(k,max(N))), general design search exponential in d.
Equal populations AND equal costs permit all d coordinates to be sorted,
reducing the allocation grid from (N+1)^d to C(N+d,d). This implementation does
not assume an additional shorter-prefix reduction. In particular, it never
replaces total-count risk by the product of the first factor of each chain.
Budget limits bound input population, search nodes, evaluated allocations,
aggregate greedy steps/calls, and DP transitions. Exhaustion raises and returns
no partial optimum. No wall-time/resource measurement is claimed by these caps.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, fields
from fractions import Fraction
import heapq
from math import comb, prod
import re

from research.certificates.collective import BudgetExceeded


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


@dataclass(frozen=True)
class Budget:
    max_total_population: int = 10000
    max_strata: int = 128
    max_scalar_bits: int = 4096
    max_risk_calls: int = 250000
    max_risk_steps: int = 2000000
    max_dp_transitions: int = 200000
    max_search_nodes: int = 500000
    max_designs: int = 250000

    def __post_init__(self):
        if any(not _integer(getattr(self, f.name)) or getattr(self, f.name) < 1
               for f in fields(self)):
            raise ValueError('every budget must be a strictly positive integer, not bool/float')


@dataclass
class _Meter:
    budget: Budget
    risk_calls: int = 0
    risk_steps: int = 0
    dp_transitions: int = 0
    search_nodes: int = 0
    designs: int = 0

    def charge(self, name, amount=1):
        value = getattr(self, name) + amount
        if value > getattr(self.budget, 'max_' + name):
            raise BudgetExceeded(f'total-count {name} budget exceeded; no partial optimum returned')
        setattr(self, name, value)

    def counts(self):
        return {name: getattr(self, name) for name in
                ('risk_calls', 'risk_steps', 'dp_transitions', 'search_nodes', 'designs')}


def _validate_population(populations, k, budget):
    if not isinstance(budget, Budget):
        raise ValueError('budget must be a validated Budget')
    if not isinstance(populations, Sequence) or isinstance(populations, (str, bytes)) or not populations:
        raise ValueError('nonempty finite population sequence required; omit empty strata')
    if len(populations) > budget.max_strata:
        raise BudgetExceeded('stratum input budget exceeded')
    if any(not _integer(N) or N < 1 for N in populations):
        raise ValueError('stratum populations must be positive integers, not bool/float')
    if sum(populations) > budget.max_total_population:
        raise BudgetExceeded('total-population input budget exceeded')
    if not _integer(k) or k < 0:
        raise ValueError('k must be a nonnegative integer, not bool/float')
    return tuple(populations)


def _validate_design(populations, samples, k, budget):
    populations = _validate_population(populations, k, budget)
    if not isinstance(samples, Sequence) or isinstance(samples, (str, bytes)) or len(samples) != len(populations):
        raise ValueError('one integer sample size per stratum is required')
    if any(not _integer(n) or not 0 <= n <= N for N, n in zip(populations, samples)):
        raise ValueError('sample sizes must be integers in [0,N], not bool/float')
    return populations, tuple(samples)


def _exact(value, name, budget):
    if isinstance(value, bool) or not isinstance(value, (int, str, Fraction)):
        raise ValueError(f'{name} must be an exact integer, Fraction, or string; no bool/float')
    if isinstance(value, str) and len(value) > budget.max_scalar_bits:
        raise BudgetExceeded(f'{name} input size budget exceeded')
    if isinstance(value, str) and not re.fullmatch(r'[+-]?(?:\d+(?:/\d+)?|\d+\.\d*|\.\d+)', value.strip()):
        # Reject exponent syntax BEFORE Fraction constructs its potentially
        # enormous power of ten; a short string is not an arithmetic-size cap.
        raise ValueError(f'{name} string must be an integer, p/q, or finite decimal without exponent')
    try:
        result = Fraction(value)
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError(f'invalid exact {name}') from error
    if max(abs(result.numerator).bit_length(), result.denominator.bit_length()) > budget.max_scalar_bits:
        raise BudgetExceeded(f'{name} bit-size budget exceeded')
    return result


def _greedy(populations, samples, k, meter):
    meter.charge('risk_calls')
    if k == 0:
        return Fraction(1)
    if k > sum(populations):
        return Fraction(0)
    # Each heap item exposes only the next available member of one decreasing
    # chain. Ties are resolved by the frozen stratum index. Zero multipliers can
    # be omitted: if k needs any of them, every feasible product is zero.
    heap = [(-Fraction(N - n, N), h, 0)
            for h, (N, n) in enumerate(zip(populations, samples)) if n < N]
    heapq.heapify(heap)
    value = Fraction(1)
    for _ in range(k):
        meter.charge('risk_steps')
        if not heap:
            return Fraction(0)
        negative_factor, h, j = heapq.heappop(heap)
        value *= -negative_factor
        N, n = populations[h], samples[h]
        next_j = j + 1
        if next_j < N - n:
            heapq.heappush(heap, (-Fraction(N - n - next_j, N - next_j), h, next_j))
    return value


def risk_greedy(populations, samples, k, *, budget=Budget()):
    """Exact risk by prefix greedy; arbitrary unequal positive populations."""
    populations, samples = _validate_design(populations, samples, k, budget)
    return _greedy(populations, samples, k, _Meter(budget))


def risk_dp(populations, samples, k, *, budget=Budget()):
    """Exact risk by direct combinatorial probabilities and maximum convolution.

    This kernel does not call the greedy kernel or use its multiplier identity.
    Reachability uses None, keeping zero-probability states distinct from absent
    states. Precomputed layer probabilities are bounded by the population cap;
    every feasible convolution transition is charged to the DP budget.
    """
    populations, samples = _validate_design(populations, samples, k, budget)
    if k == 0:
        return Fraction(1)
    if k > sum(populations):
        return Fraction(0)
    meter = _Meter(budget)
    previous = [Fraction(1)] + [None] * k
    for N, n in zip(populations, samples):
        denominator = comb(N, n)
        probabilities = [Fraction(comb(N-q, n), denominator) if n <= N-q else Fraction(0)
                         for q in range(min(N, k)+1)]
        current = [None] * (k+1)
        for total, prior in enumerate(previous):
            if prior is None:
                continue
            for q in range(min(N, k-total)+1):
                meter.charge('dp_transitions')
                candidate = prior * probabilities[q]
                index = total + q
                if current[index] is None or candidate > current[index]:
                    current[index] = candidate
        previous = current
    assert previous[k] is not None  # 0 <= k <= total population.
    return previous[k]


def optimal_design(populations, k, alpha='1/20', costs=None, *, budget=Budget()):
    """Global minimum cost over fixed per-stratum audit counts, or raise.

    `cost_exact` and `risk_exact` are rational strings for JSON-safe transport;
    `audit_count` is unweighted, and must not replace cost for unequal costs.
    `status=infeasible` is possible only at k=0 (the asserted upper bound is -1).

    A necessary lower bound on each n_h comes from placing all k contaminations
    in that stratum whenever k <= N_h. Search then enumerates every allocation
    cheaper than an already certified incumbent, using only positive-cost and
    (when allowed) permutation pruning. These lower bounds are NOT assumed
    sufficient. The search meter is shared across every risk evaluation.
    """
    populations = _validate_population(populations, k, budget)
    a = _exact(alpha, 'alpha', budget)
    if not 0 < a < 1:
        raise ValueError('alpha must lie strictly between zero and one')
    d = len(populations)
    if costs is None:
        weights = (Fraction(1),) * d
    else:
        if not isinstance(costs, Sequence) or isinstance(costs, (str, bytes)) or len(costs) != d:
            raise ValueError('one exact positive cost per stratum required')
        weights = tuple(_exact(c, 'cost', budget) for c in costs)
        if any(c <= 0 for c in weights):
            raise ValueError('all costs must be positive')
    meter = _Meter(budget)
    symmetric = len(set(populations)) == 1 and len(set(weights)) == 1
    grid_size = comb(populations[0]+d, d) if symmetric else prod(N+1 for N in populations)
    common = dict(k=k, certified_total_upper=k-1, alpha_exact=str(a),
                  populations=list(populations), costs_exact=[str(c) for c in weights],
                  search='sorted_all_d_coordinates' if symmetric else 'full_labeled_coordinates',
                  unpruned_allocation_count=grid_size,
                  optimality='global among fixed per-stratum uniform zero-finding total-count procedures')
    if k == 0:
        return dict(common, status='infeasible', samples=None, cost_exact=None,
                    risk_exact='1', audit_count=None, lower_bounds=None, counts=meter.counts())
    if k > sum(populations):
        return dict(common, status='optimal', samples=[0]*d, cost_exact='0',
                    risk_exact='0', audit_count=0, lower_bounds=[0]*d, counts=meter.counts())

    # Census is always a feasible initial design for k>=1. A balanced incumbent
    # speeds symmetric search without restricting the optimization domain.
    best_samples = list(populations)
    if symmetric:
        lo, hi = 0, populations[0]
        while lo < hi:
            mid = (lo + hi) // 2
            if _greedy(populations, (mid,)*d, k, meter) <= a:
                hi = mid
            else:
                lo = mid + 1
        best_samples = [lo]*d
    best_cost = sum((c*n for c, n in zip(weights, best_samples)), Fraction(0))
    best_risk = _greedy(populations, best_samples, k, meter)
    assert best_risk <= a

    lower = []
    for N in populations:
        if k > N:
            lower.append(0)
            continue
        lo, hi = 0, N
        while lo < hi:
            mid = (lo + hi) // 2
            # One-layer call tests the necessary all-k-in-this-layer condition.
            if _greedy((N,), (mid,), k, meter) <= a:
                hi = mid
            else:
                lo = mid + 1
        lower.append(lo)
    suffix_minimum = [Fraction(0)] * (d+1)
    for h in range(d-1, -1, -1):
        suffix_minimum[h] = suffix_minimum[h+1] + weights[h]*lower[h]
    prefix = []

    def visit(h, current_cost):
        nonlocal best_samples, best_cost, best_risk
        meter.charge('search_nodes')
        if h == d:
            if current_cost >= best_cost:
                return
            meter.charge('designs')
            candidate_risk = _greedy(populations, prefix, k, meter)
            if candidate_risk <= a:
                best_samples = list(prefix)
                best_cost = current_cost
                best_risk = candidate_risk
            return
        minimum_n = max(lower[h], prefix[-1] if symmetric and prefix else 0)
        if symmetric:
            if current_cost + weights[h]*minimum_n*(d-h) >= best_cost:
                return
        elif current_cost + suffix_minimum[h] >= best_cost:
            return
        for n in range(minimum_n, populations[h]+1):
            cost = current_cost + weights[h]*n
            remaining = weights[h]*n*(d-h-1) if symmetric else suffix_minimum[h+1]
            if cost + remaining >= best_cost:
                break
            prefix.append(n)
            visit(h+1, cost)
            prefix.pop()

    visit(0, Fraction(0))
    return dict(common, status='optimal', samples=best_samples, cost_exact=str(best_cost),
                risk_exact=str(best_risk), audit_count=sum(best_samples),
                lower_bounds=lower, counts=meter.counts())
