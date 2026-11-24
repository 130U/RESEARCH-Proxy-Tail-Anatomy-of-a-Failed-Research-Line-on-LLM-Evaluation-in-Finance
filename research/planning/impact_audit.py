"""Exact fixed-stratum zero-finding planning for a frozen impact graph.

This module does not audit documents or train models. It enumerates at most
16 documents, with at most 65,536 contamination configurations by default.
Macro-F1 DP is capped at 50,000 states per head union. Configuration visits,
frontier comparisons, and allocation/box search work share a 100,000-unit
default limit. Exhaustion raises BudgetExceeded; no partial plan is returned.
The execution budget and run record are maintained separately by the caller.

Every row is a test point and every column is the same head identity. A
contaminated document i may change any heads in doc_heads[i], jointly across
the test set. Selected heads have arbitrary outputs: an outer relaxation of
actual retraining, not a claim the endpoints are trainable. All inputs,
strata, interval, alpha and audit allocations are fixed before sampling.
"""
from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
from itertools import product
from math import prod

from research.certificates.collective import (
    BudgetExceeded, candidates_for_subset, exact_bounds, interval,
)
from research.planning.audit_frontier import minimum_zero_audit, zero_probability


MAX_DOCUMENTS = 16


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _sequence(value, name):
    if not isinstance(value, (list, tuple)):
        raise ValueError(f'{name} must be a list or tuple')
    return value


def _rational(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, str, Fraction)):
        raise ValueError(f'{name} requires an exact integer, string or Fraction; floats are rejected')
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError(f'invalid rational {name}') from error


def _positive_limit(value, name):
    if not _integer(value) or value < 1:
        raise ValueError(f'{name} must be a positive integer')
    return value


class _Work:
    def __init__(self, limit):
        self.limit = _positive_limit(limit, 'max_search')
        self.used = 0

    def charge(self, amount=1):
        self.used += amount
        if self.used > self.limit:
            raise BudgetExceeded('impact search budget exceeded; no partial plan returned')


@lru_cache(maxsize=4096)
def _zero(N, q, n):
    return zero_probability(N, q, n)


def _validate_problem(votes, labels, classes, doc_heads, strata, target_interval, metric,
                      max_configurations, max_states):
    _positive_limit(max_configurations, 'max_configurations')
    _positive_limit(max_states, 'max_states')
    if not _integer(classes) or classes < 2:
        raise ValueError('classes must be an integer >= 2')
    _sequence(votes, 'votes_by_example_and_head')
    _sequence(labels, 'labels')
    if not votes or len(votes) != len(labels):
        raise ValueError('nonempty votes and exactly one label per example required')
    for row in votes:
        _sequence(row, 'vote row')
    m = len(votes[0])
    if m == 0 or any(len(row) != m for row in votes):
        raise ValueError('votes must be nonempty rectangular rows of ordered head predictions')
    if any(not _integer(x) or not 0 <= x < classes for row in votes for x in row):
        raise ValueError('head predictions must be integer class indices')
    if any(not _integer(x) or not 0 <= x < classes for x in labels):
        raise ValueError('labels must be integer class indices')
    _sequence(doc_heads, 'doc_heads')
    N = len(doc_heads)
    if N > MAX_DOCUMENTS:
        raise BudgetExceeded('general impact enumeration supports at most 16 documents')
    if (1 << N) > max_configurations:
        raise BudgetExceeded('contamination configuration budget exceeded; no partial analysis returned')
    head_masks = []
    for heads in doc_heads:
        _sequence(heads, 'each document head list')
        if any(not _integer(h) or not 0 <= h < m for h in heads):
            raise ValueError('document head IDs must be integers in the vote-column range')
        if len(set(heads)) != len(heads):
            raise ValueError('duplicate head IDs within one document')
        head_masks.append(sum(1 << h for h in heads))
    _sequence(strata, 'strata')
    seen = set()
    stratum_masks = []
    for docs in strata:
        _sequence(docs, 'each stratum document list')
        mask = 0
        for doc in docs:
            if not _integer(doc) or not 0 <= doc < N or doc in seen:
                raise ValueError('strata must partition all document indices without duplicates')
            seen.add(doc)
            mask |= 1 << doc
        stratum_masks.append(mask)
    if seen != set(range(N)):
        raise ValueError('strata must cover every document exactly once')
    _sequence(target_interval, 'target_interval')
    if len(target_interval) != 2:
        raise ValueError('target_interval must have two endpoints')
    lower, upper = (_rational(x, 'interval endpoint') for x in target_interval)
    if not 0 <= lower <= upper <= 1:
        raise ValueError('require 0 <= interval lower <= upper <= 1')
    if metric not in ('accuracy', 'macro_f1'):
        raise ValueError('metric must be accuracy or macro_f1')
    return (tuple(tuple(row) for row in votes), tuple(labels), tuple(head_masks),
            tuple(stratum_masks), (lower, upper))


def _dominates(low, high, work):
    work.charge()
    return all(a <= b for a, b in zip(low, high))


def _analyze(votes, labels, classes, doc_heads, strata, target_interval, metric,
             max_configurations, max_states, work):
    votes, labels, head_masks, stratum_masks, target = _validate_problem(
        votes, labels, classes, doc_heads, strata, target_interval, metric,
        max_configurations, max_states)
    N, m, J = len(head_masks), len(votes[0]), len(labels)
    head_unions = [0] * (1 << N)
    bad = [False] * (1 << N)
    by_heads = {}
    peak_states = 0
    for mask in range(1 << N):
        work.charge()
        if mask:
            bit = mask & -mask
            head_unions[mask] = head_unions[mask ^ bit] | head_masks[bit.bit_length() - 1]
        union = head_unions[mask]
        if union not in by_heads:
            changed = [h for h in range(m) if union & (1 << h)]
            candidates = candidates_for_subset(votes, changed, classes)
            if metric == 'accuracy':
                # CM3: exact additive extrema, without an unnecessary F1 DP.
                lo = Fraction(sum(choices == [y] for choices, y in zip(candidates, labels)), J)
                hi = Fraction(sum(y in choices for choices, y in zip(candidates, labels)), J)
            else:
                bounds, states = exact_bounds(candidates, list(labels), classes, max_states)
                lo, hi = bounds[metric]
                peak_states = max(peak_states, states['peak'])
            by_heads[union] = (lo, hi)
        lo, hi = by_heads[union]
        bad[mask] = lo < target[0] or hi > target[1]

    minimal_masks = []
    for mask, is_bad in enumerate(bad):
        if not is_bad:
            continue
        remainder = mask
        minimal = True
        while remainder:
            work.charge()
            bit = remainder & -remainder
            if bad[mask ^ bit]:
                minimal = False
                break
            remainder ^= bit
        if minimal:
            minimal_masks.append(mask)
    # Monotonicity of head-union feasible sets makes single deletions sufficient.
    # Count profiles may dominate one another even for incomparable document sets.
    profiles = {tuple((mask & group).bit_count() for group in stratum_masks)
                for mask in minimal_masks}
    frontier = []
    for q in sorted(profiles, key=lambda x: (sum(x), x)):
        if not any(_dominates(p, q, work) for p in frontier):
            frontier.append(q)
    frontier.sort()
    baseline = by_heads[0]
    return {
        'metric': metric, 'target_interval': interval(*target),
        'n_documents': N, 'n_heads': m, 'n_examples': J, 'classes': classes,
        'strata_sizes': [group.bit_count() for group in stratum_masks],
        'stratum_document_ids': [list(docs) for docs in strata],
        'document_head_ids': [sorted(heads) for heads in doc_heads],
        'observed_statistic_exact': str(baseline[0]),
        'configuration_count': len(bad), 'bad_configuration_count': sum(bad),
        'distinct_head_unions': len(by_heads), 'oracle_peak_states': peak_states,
        'minimal_bad_document_sets': [[i for i in range(N) if mask & (1 << i)] for mask in minimal_masks],
        'minimal_bad_profiles': [list(q) for q in frontier],
        'metric_oracle': 'CM3 exact accuracy' if metric == 'accuracy' else 'exact joint-count macro-F1 DP',
    }


def analyze_impact(votes_by_example_and_head, labels, classes, doc_heads, strata,
                   target_interval, metric='accuracy', *, max_configurations=65536,
                   max_states=50000, max_search=100000):
    """Enumerate all document configurations and return their bad antichains.

Empty document impact lists and empty strata are allowed. Strata must still
partition the full document population. All interval endpoints are exact:
integers, decimal/fraction strings or Fraction; bool and float are rejected.
"""
    work = _Work(max_search)
    result = _analyze(votes_by_example_and_head, labels, classes, doc_heads, strata,
                      target_interval, metric, max_configurations, max_states, work)
    result['status'] = 'conditional_mathematical_impact_analysis'
    result['search_work'] = work.used
    return result


def _validate_risk_inputs(strata_sizes, bad_profiles, sample_sizes):
    _sequence(strata_sizes, 'strata_sizes')
    _sequence(sample_sizes, 'sample_sizes')
    _sequence(bad_profiles, 'bad_profiles')
    if any(not _integer(N) or N < 0 for N in strata_sizes):
        raise ValueError('stratum sizes must be nonnegative integers')
    if len(sample_sizes) != len(strata_sizes) or any(
            not _integer(n) or not 0 <= n <= N for N, n in zip(strata_sizes, sample_sizes)):
        raise ValueError('one integer sample size in [0,N_h] required per stratum')
    for q in bad_profiles:
        _sequence(q, 'bad profile')
        if len(q) != len(strata_sizes) or any(
                not _integer(k) or not 0 <= k <= N for N, k in zip(strata_sizes, q)):
            raise ValueError('one integer contamination count in [0,N_h] required per profile stratum')


def _risk(sizes, profiles, samples, work):
    maximum = Fraction(0)
    for q in profiles:
        work.charge(1 + len(sizes))
        probability = prod((_zero(N, k, n) for N, k, n in zip(sizes, q, samples)), start=Fraction(1))
        maximum = max(maximum, probability)
    return maximum


def zero_finding_risk(strata_sizes, bad_profiles, sample_sizes, *, max_search=100000):
    """Worst exact miss probability over supplied bad profiles (not a prior).

No bad profiles -> risk 0. A zero profile -> risk 1, even after a census.
Profiles need not form an antichain; the caller is responsible for supplying
the complete bad set or a frontier dominating all its relevant profiles.
"""
    _validate_risk_inputs(strata_sizes, bad_profiles, sample_sizes)
    return _risk(strata_sizes, bad_profiles, sample_sizes, _Work(max_search))


def _cost(samples, costs):
    return sum((n * c for n, c in zip(samples, costs)), Fraction(0))


def _direct_plan(sizes, profiles, costs, alpha, work):
    best = None
    allocations = 0
    for samples in product(*(range(N + 1) for N in sizes)):
        work.charge()
        allocations += 1
        cost = _cost(samples, costs)
        # Lexicographic enumeration supplies a deterministic tie-break.
        if best is not None and cost >= best[0]:
            continue
        risk = _risk(sizes, profiles, samples, work)
        if risk <= alpha:
            best = (cost, samples, risk)
    if best is None:
        return None, allocations
    return {'sample_sizes': list(best[1]), 'cost_exact': str(best[0]),
            'risk_exact': str(best[2])}, allocations


def _rectangle_plan(sizes, profiles, costs, alpha, work):
    safe = set()
    for box in product(*(range(N + 1) for N in sizes)):
        work.charge()
        if not any(_dominates(q, box, work) for q in profiles):
            safe.add(box)
    maximal = []
    for box in sorted(safe):
        has_safe_successor = False
        for h, N in enumerate(sizes):
            work.charge()
            if box[h] < N:
                successor = list(box)
                successor[h] += 1
                if tuple(successor) in safe:
                    has_safe_successor = True
                    break
        if not has_safe_successor:
            maximal.append(box)
    best = None
    for box in maximal:
        work.charge(1 + len(sizes))
        samples = tuple(minimum_zero_audit(N, b, alpha) for N, b in zip(sizes, box))
        risk = max((_zero(N, b + 1, n) for N, b, n in zip(sizes, box, samples) if b < N),
                   default=Fraction(0))
        candidate = (_cost(samples, costs), samples, box, risk)
        if best is None or candidate[:3] < best[:3]:
            best = candidate
    if best is None:
        return None, maximal, len(safe)
    return {
        'sample_sizes': list(best[1]), 'box_upper_counts': list(best[2]),
        'cost_exact': str(best[0]), 'risk_exact': str(best[3]),
        'target_failure_risk_exact': str(_risk(sizes, profiles, best[1], work)),
        'risk_estimand': 'whole count-box coverage under joint-zero reporting; max_h, not Bonferroni sum',
    }, maximal, len(safe)


def plan_impact_audit(votes_by_example_and_head, labels, classes, doc_heads, strata,
                      target_interval, metric='accuracy', alpha='1/20', costs=None, *,
                      max_configurations=65536, max_states=50000, max_search=100000):
    """Globally cheapest fixed zero-finding design for the specified interval.

Compare with the cheapest safe rectangular count-box procedure, which reports
the box only if ALL strata have zero findings and otherwise reports full range.
Its exact worst-case noncoverage is max_h Pr(X_h=0 | q_h=B_h+1), ignoring
B_h=N_h, so this baseline does not pay an unnecessary Bonferroni sum.

The output is a mathematical PLAN, not a record that an audit observed zero.
Positive findings require full-range output/abstention under this procedure.
No search limit ever returns a partially optimized or partially valid plan.
"""
    work = _Work(max_search)
    a = _rational(alpha, 'alpha')
    if not 0 < a < 1:
        raise ValueError('alpha must be in (0,1)')
    _sequence(strata, 'strata')
    if costs is None:
        costs = [1] * len(strata)
    _sequence(costs, 'costs')
    if len(costs) != len(strata):
        raise ValueError('exactly one strictly positive cost per stratum required')
    costs = tuple(_rational(c, 'cost') for c in costs)
    if any(c <= 0 for c in costs):
        raise ValueError('costs must be strictly positive')
    result = _analyze(votes_by_example_and_head, labels, classes, doc_heads, strata,
                      target_interval, metric, max_configurations, max_states, work)
    sizes = tuple(result['strata_sizes'])
    profiles = tuple(tuple(q) for q in result['minimal_bad_profiles'])
    if any(not any(q) for q in profiles):
        direct, rectangle, maximal, safe_count, allocations = None, None, [], 0, 0
        status = 'unattainable_interval'
        reason = 'the empty contamination set is bad; its zero-finding probability is 1 for every design'
    elif not profiles:
        samples = [0] * len(sizes)
        direct = {'sample_sizes': samples[:], 'cost_exact': '0', 'risk_exact': '0'}
        rectangle = {'sample_sizes': samples[:], 'box_upper_counts': list(sizes),
                     'cost_exact': '0', 'risk_exact': '0', 'target_failure_risk_exact': '0',
                     'risk_estimand': 'whole count-box coverage under joint-zero reporting; max_h, not Bonferroni sum'}
        maximal, safe_count, allocations = [sizes], prod(N + 1 for N in sizes), 0
        status, reason = 'conditional_fixed_design_plan', 'no bad configurations; no audit needed in this relaxation'
    else:
        direct, allocations = _direct_plan(sizes, profiles, costs, a, work)
        rectangle, maximal, safe_count = _rectangle_plan(sizes, profiles, costs, a, work)
        if direct is None or rectangle is None:
            raise AssertionError('a census and the zero count box must work when the empty set is good')
        if Fraction(direct['cost_exact']) > Fraction(rectangle['cost_exact']):
            raise AssertionError('direct optimum cannot cost more than a feasible rectangular procedure')
        status, reason = 'conditional_fixed_design_plan', 'exact optimum within fixed independent stratum SRSWOR designs'
    result.update({
        'status': status, 'reason': reason, 'alpha_exact': str(a),
        'costs_exact': [str(c) for c in costs], 'direct': direct, 'rectangle': rectangle,
        'maximal_safe_boxes': [list(box) for box in maximal], 'safe_box_count': safe_count,
        'allocations_visited': allocations, 'search_work': work.used,
        'limits': {'max_documents': MAX_DOCUMENTS, 'max_configurations': max_configurations,
                   'max_states': max_states, 'max_search': max_search},
        'reporting_rule': 'report target_interval only on zero findings in every stratum; otherwise [0,1] or abstain',
        'assumptions': [
            'population versions, impact sets, votes, labels, interval, strata and sample sizes frozen before audit',
            'uniform sampling without replacement within each stratum; sampling independent across strata',
            'audit labels perfectly adjudicated; no unknown judgments counted as clean',
            'all effects of contaminated documents contained in their declared head sets',
            'shared preprocessing/backbone unchanged unless its affected heads are explicitly included',
            'selected-head outputs allowed arbitrary changes, an outer relaxation of retraining',
        ],
        'limitations': [
            'a conditional mathematical plan: no real documents audited and no zero findings observed here',
            'risk is worst-case probability of false interval reporting, not posterior contamination or audit success probability',
            'fixed-sample protocol only, not anytime-valid or an expected stopping-cost result',
            'fixed-test metric only, not population generalization or independently established historical provenance',
            'exact search in a small declared design class is not a novelty claim',
        ],
    })
    return result
