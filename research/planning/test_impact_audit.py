"""Independent modified-vote and explicit audit-sample oracles on small inputs.

Planned budget: standard-library CPU tests, no training/network, <60 seconds
on the existing local Python environment; test execution is recorded by root.
The oracle enumerates vote cells and actual sampled document subsets rather
than reusing the implementation's count-state DP or hypergeometric formula.
"""
from fractions import Fraction
from itertools import combinations, product
import random
import unittest

from research.planning.impact_audit import (
    BudgetExceeded, analyze_impact, plan_impact_audit, zero_finding_risk,
)


def subsets(items):
    return [frozenset(c) for r in range(len(items) + 1) for c in combinations(items, r)]


def actual_metric(votes, labels, classes, metric):
    predictions = [max(range(classes), key=lambda c: (row.count(c), -c)) for row in votes]
    if metric == 'accuracy':
        return Fraction(sum(y == z for y, z in zip(labels, predictions)), len(labels))
    values = []
    for c in range(classes):
        den = labels.count(c) + predictions.count(c)
        num = 2 * sum(y == c and z == c for y, z in zip(labels, predictions))
        values.append(Fraction(num, den) if den else Fraction(0))
    return sum(values) / classes


def bad_configuration_oracle(votes, labels, classes, doc_heads, target, metric):
    """Brute-force each changed vote cell; no candidate-label/DP code reused."""
    bad = set()
    for contamination in subsets(list(range(len(doc_heads)))):
        changed = sorted(set().union(*(set(doc_heads[i]) for i in contamination)))
        for replacements in product(range(classes), repeat=len(votes) * len(changed)):
            modified = [row[:] for row in votes]
            for j in range(len(votes)):
                for s, h in enumerate(changed):
                    modified[j][h] = replacements[j * len(changed) + s]
            score = actual_metric(modified, labels, classes, metric)
            if not target[0] <= score <= target[1]:
                bad.add(contamination)
                break
    return bad


def audit_miss_probability(strata, samples, contamination):
    """List actual equally likely audit subsets; no comb/CDF formula reused."""
    draws = [list(combinations(group, n)) for group, n in zip(strata, samples)]
    total = misses = 0
    for draw in product(*draws):
        total += 1
        audited = set().union(*(set(d) for d in draw))
        misses += not (audited & contamination)
    return Fraction(misses, total)


def design_oracle(strata, bad, alpha, costs):
    designs = list(product(*(range(len(group) + 1) for group in strata)))
    scored = []
    for samples in designs:
        risk = max((audit_miss_probability(strata, samples, C) for C in bad), default=Fraction(0))
        if risk <= alpha:
            scored.append((sum(c * n for c, n in zip(costs, samples)), samples, risk))
    return min(scored, key=lambda x: (x[0], x[1])) if scored else None


def box_oracle(strata, bad, alpha, costs):
    """Enumerate ALL boxes and ALL designs and their actual rejection events."""
    all_C = subsets([i for group in strata for i in group])
    best = None
    for box in product(*(range(len(group) + 1) for group in strata)):
        def inside(C):
            return all(len(set(group) & C) <= b for group, b in zip(strata, box))
        if any(inside(C) for C in bad):
            continue
        outside = [C for C in all_C if not inside(C)]
        for samples in product(*(range(len(group) + 1) for group in strata)):
            risk = max((audit_miss_probability(strata, samples, C) for C in outside), default=Fraction(0))
            if risk <= alpha:
                candidate = (sum(c * n for c, n in zip(costs, samples)), samples, box, risk)
                if best is None or candidate[:3] < best[:3]:
                    best = candidate
    return best


class ImpactAuditTests(unittest.TestCase):
    def compare_oracles(self, votes, labels, classes, doc_heads, strata, target,
                        metric='accuracy', alpha=Fraction(1, 4), costs=None):
        costs = costs or [Fraction(1)] * len(strata)
        bad = bad_configuration_oracle(votes, labels, classes, doc_heads, target, metric)
        result = plan_impact_audit(votes, labels, classes, doc_heads, strata, target,
                                  metric, alpha, costs)
        self.assertEqual(result['bad_configuration_count'], len(bad))
        minimal = {C for C in bad if not any(D < C for D in bad)}
        self.assertEqual({frozenset(C) for C in result['minimal_bad_document_sets']}, minimal)
        for C in subsets(list(range(len(doc_heads)))):
            q = [len(set(group) & C) for group in strata]
            can_be_bad_at_q = any(all(len(set(group) & D) == k for group, k in zip(strata, q)) for D in bad)
            frontier_says_bad = any(all(a <= b for a, b in zip(p, q)) for p in result['minimal_bad_profiles'])
            self.assertEqual(frontier_says_bad, can_be_bad_at_q)
        expected = design_oracle(strata, bad, alpha, costs)
        rectangle = box_oracle(strata, bad, alpha, costs)
        if expected is None:
            self.assertEqual(result['status'], 'unattainable_interval')
            self.assertIsNone(result['direct'])
            self.assertIsNone(rectangle)
        else:
            direct = result['direct']
            self.assertEqual((Fraction(direct['cost_exact']), tuple(direct['sample_sizes']),
                              Fraction(direct['risk_exact'])), expected)
            self.assertEqual(Fraction(result['rectangle']['cost_exact']), rectangle[0])
            # Restricting to maximal boxes may choose a different tied box.
            chosen_box = result['rectangle']['box_upper_counts']
            self.assertFalse(any(all(len(set(group) & C) <= b for group, b in zip(strata, chosen_box)) for C in bad))
            outside = [C for C in subsets([i for g in strata for i in g])
                       if any(len(set(g) & C) > b for g, b in zip(strata, chosen_box))]
            measured = max((audit_miss_probability(strata, result['rectangle']['sample_sizes'], C)
                            for C in outside), default=Fraction(0))
            self.assertEqual(measured, Fraction(result['rectangle']['risk_exact']))
            self.assertLessEqual(measured, alpha)
        return result

    def test_direct_cell_and_sample_oracles_for_both_metrics(self):
        # Includes missing classes, tie priority and zero-impact documents.
        rng = random.Random(30617)
        maps = [[[0], [1], []], [[0, 1], [1], [0]], [[0], [0], [1]]]
        for classes in (2, 3):
            for doc_heads in maps:
                votes = [[rng.randrange(classes) for _ in range(2)] for _ in range(2)]
                labels = [rng.randrange(classes) for _ in range(2)]
                for metric in ('accuracy', 'macro_f1'):
                    center = actual_metric(votes, labels, classes, metric)
                    target = (max(Fraction(0), center - Fraction(1, 4)), min(Fraction(1), center + Fraction(1, 4)))
                    self.compare_oracles(votes, labels, classes, doc_heads, [[0, 2], [1]],
                                         target, metric, costs=[Fraction(1, 3), Fraction(7, 5)])

    def test_exact_risk_matches_all_actual_audit_samples(self):
        strata = [[0, 1], [], [2, 3]]
        for samples in product(range(3), [0], range(3)):
            for C in subsets(list(range(4))):
                profile = [len(set(group) & C) for group in strata]
                self.assertEqual(zero_finding_risk([2, 0, 2], [profile], samples),
                                 audit_miss_probability(strata, samples, C))
        self.assertEqual(zero_finding_risk([2, 2], [], [0, 0]), 0)
        self.assertEqual(zero_finding_risk([2, 2], [[0, 0]], [2, 2]), 1)

    def test_joint_zero_rectangle_uses_max_not_sum(self):
        # A bad singleton in either stratum: count box B=(0,0) is the only safe box.
        result = self.compare_oracles([[1]], [1], 2, [[0], [], [0], []], [[0, 1], [2, 3]],
                                      (1, 1), alpha=Fraction(1, 2))
        self.assertEqual(result['rectangle']['sample_sizes'], [1, 1])
        self.assertEqual(result['rectangle']['risk_exact'], '1/2')
        self.assertEqual(result['rectangle']['cost_exact'], '2')

    def test_direct_product_can_strictly_beat_strong_rectangle(self):
        # Two of three unanimous heads must change. One draw from each size-2
        # layer misses each bad pair with probability 1/4 (cost 3); a safe box
        # must set two layer budgets to zero, requiring two censuses (cost 4).
        result = self.compare_oracles([[0, 0, 0]], [0], 2,
                                      [[0], [0], [1], [1], [2], [2]],
                                      [[0, 1], [2, 3], [4, 5]], (1, 1), alpha=Fraction(1, 4))
        self.assertEqual(result['minimal_bad_profiles'], [[0, 1, 1], [1, 0, 1], [1, 1, 0]])
        self.assertEqual(result['direct']['sample_sizes'], [1, 1, 1])
        self.assertEqual(result['direct']['risk_exact'], '1/4')
        self.assertEqual(result['direct']['cost_exact'], '3')
        self.assertEqual(result['rectangle']['cost_exact'], '4')

    def test_two_level_minimality_repeated_impacts(self):
        # {0} and {1,2} are incomparable minimal document sets; profiles 1 and 2
        # in one stratum are comparable, so only profile (1,) remains.
        result = self.compare_oracles([[0, 0, 0]], [0], 2, [[0, 1], [0], [1]], [[0, 1, 2]], (1, 1))
        self.assertEqual({frozenset(x) for x in result['minimal_bad_document_sets']},
                         {frozenset([0]), frozenset([1, 2])})
        self.assertEqual(result['minimal_bad_profiles'], [[1]])

    def test_no_bad_empty_bad_and_empty_population(self):
        self.compare_oracles([[0, 0]], [0], 2, [[], []], [[0], [], [1]], (1, 1))
        self.compare_oracles([[0]], [0], 2, [[0]], [[0]], (0, 0))
        for strata in ([], [[]]):
            good = plan_impact_audit([[0]], [0], 2, [], strata, (1, 1))
            bad = plan_impact_audit([[0]], [0], 2, [], strata, (0, 0))
            self.assertEqual(good['direct']['cost_exact'], '0')
            self.assertEqual(good['bad_configuration_count'], 0)
            self.assertEqual(bad['status'], 'unattainable_interval')
            self.assertIsNone(bad['direct'])

    def test_census_zero_sampling_equality_and_exact_costs(self):
        result = self.compare_oracles([[1]], [1], 2, [[0], [], [], []], [[0, 1, 2, 3]],
                                      (1, 1), alpha=Fraction(1, 4), costs=[Fraction(1, 7)])
        self.assertEqual(result['direct']['sample_sizes'], [3])
        self.assertEqual(result['direct']['risk_exact'], '1/4')
        self.assertEqual(result['direct']['cost_exact'], '3/7')

    def test_invalid_inputs_and_fail_closed_limits(self):
        base = dict(votes_by_example_and_head=[[0]], labels=[0], classes=2,
                    doc_heads=[[0]], strata=[[0]], target_interval=(0, 1))
        cases = [
            {'votes_by_example_and_head': []}, {'votes_by_example_and_head': [[True]]},
            {'votes_by_example_and_head': [[0.0]]}, {'votes_by_example_and_head': [[0], [0, 1]], 'labels': [0, 1]},
            {'labels': [False]}, {'labels': [0.0]}, {'labels': [2]}, {'classes': True}, {'classes': 2.0},
            {'classes': 1}, {'doc_heads': [[True]]}, {'doc_heads': [[0.0]]}, {'doc_heads': [[1]]},
            {'doc_heads': [[0, 0]]}, {'doc_heads': [{0}]}, {'strata': [[0], [0]]}, {'strata': [[]]},
            {'strata': [[True]]}, {'strata': [[0.0]]}, {'strata': [[-1]]}, {'strata': [{0}]},
            {'target_interval': [0.0, 1]}, {'target_interval': [False, 1]}, {'target_interval': [1, 0]},
            {'target_interval': [0, 2]}, {'target_interval': [0]}, {'target_interval': ['NaN', 1]},
            {'metric': 'F1'}, {'alpha': 0.05}, {'alpha': True}, {'alpha': 0}, {'alpha': 1},
            {'costs': [0]}, {'costs': [-1]}, {'costs': [0.5]}, {'costs': [True]}, {'costs': []},
            {'max_configurations': 1.0}, {'max_states': True}, {'max_search': 0},
        ]
        for update in cases:
            with self.subTest(update=update), self.assertRaises(ValueError):
                plan_impact_audit(**(base | update))
        for update in ({'max_configurations': 1}, {'max_search': 1},
                       {'metric': 'macro_f1', 'max_states': 1},
                       {'doc_heads': [[0]] * 17, 'strata': [list(range(17))]}):
            with self.subTest(limit=update), self.assertRaises(BudgetExceeded):
                plan_impact_audit(**(base | update))
        for sizes, profiles, samples in [([True], [[0]], [0]), ([1], [[0.0]], [0]),
                                          ([1], [[0]], [False]), ([1], [[2]], [0]),
                                          ([1], [[]], [0]), ([1], [[0]], [2])]:
            with self.assertRaises(ValueError):
                zero_finding_risk(sizes, profiles, samples)


if __name__ == '__main__':
    unittest.main()
