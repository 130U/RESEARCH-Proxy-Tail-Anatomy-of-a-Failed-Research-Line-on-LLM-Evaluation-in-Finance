"""Independent finite oracles; no model training or real-data audit."""
from dataclasses import replace
from fractions import Fraction
from itertools import combinations, product
from math import comb
import unittest

from research.planning.total_count_design import (
    Budget, BudgetExceeded, optimal_design, risk_dp, risk_greedy,
)


def count_oracle(populations, samples, k, *, tail=False):
    """Enumerate all labeled count vectors, independent of DP/heap selection."""
    values = []
    for counts in product(*(range(N+1) for N in populations)):
        if (sum(counts) >= k) if tail else (sum(counts) == k):
            value = Fraction(1)
            for N, n, q in zip(populations, samples, counts):
                value *= Fraction(comb(N-q, n), comb(N, n)) if n <= N-q else 0
            values.append(value)
    return max(values, default=Fraction(0))


def sample_outcome_oracle(populations, samples, k):
    """Count actual audit subsets, avoiding both comb ratios and multipliers."""
    worst = Fraction(0)
    all_draws = [list(combinations(range(N), n)) for N, n in zip(populations, samples)]
    for counts in product(*(range(N+1) for N in populations)):
        if sum(counts) != k:
            continue
        value = Fraction(1)
        for q, draws in zip(counts, all_draws):
            value *= Fraction(sum(all(i >= q for i in draw) for draw in draws), len(draws))
        worst = max(worst, value)
    return worst


def allocation_oracle(populations, k, alpha, costs=None):
    weights = costs or (Fraction(1),)*len(populations)
    best = None
    for samples in product(*(range(N+1) for N in populations)):
        if count_oracle(populations, samples, k, tail=True) <= alpha:
            cost = sum((c*n for c, n in zip(weights, samples)), Fraction(0))
            best = cost if best is None else min(best, cost)
    return best


class TotalCountDesignTests(unittest.TestCase):
    def test_dp_and_greedy_against_full_count_boundary_and_tail(self):
        for d in (1, 2, 3):
            for populations in product((1, 2), repeat=d):
                for samples in product(*(range(N+1) for N in populations)):
                    for k in range(sum(populations)+2):
                        expected = count_oracle(populations, samples, k)
                        self.assertEqual(expected, count_oracle(populations, samples, k, tail=True))
                        self.assertEqual(risk_dp(populations, samples, k), expected)
                        self.assertEqual(risk_greedy(populations, samples, k), expected)

    def test_actual_sampling_outcome_oracle(self):
        for populations, samples in [((2, 3), (1, 2)), ((3, 2), (0, 2)), ((2, 2), (2, 2))]:
            for k in range(1, sum(populations)+2):
                self.assertEqual(risk_greedy(populations, samples, k),
                                 sample_outcome_oracle(populations, samples, k))

    def test_unequal_populations_allocation_and_fractional_costs(self):
        cases = [((1, 2, 3), (Fraction(1, 2), Fraction(2), Fraction(3, 2))),
                 ((2, 2, 2), (Fraction(3), Fraction(1), Fraction(2)))]
        for populations, costs in cases:
            for k in (1, 2, 3, 4):
                a = Fraction(1, 3)
                expected = allocation_oracle(populations, k, a, costs)
                result = optimal_design(populations, k, a, costs)
                self.assertEqual(result['search'], 'full_labeled_coordinates')
                self.assertEqual(Fraction(result['cost_exact']), expected)
                self.assertLessEqual(count_oracle(populations, result['samples'], k, tail=True), a)

    def test_sorted_optimization_against_unsorted_labeled_oracle(self):
        for N in (1, 2):
            for d in (1, 2, 3):
                populations = (N,)*d
                for k in range(1, N*d+1):
                    for a in (Fraction(1, 20), Fraction(1, 2)):
                        result = optimal_design(populations, k, a)
                        expected = allocation_oracle(populations, k, a)
                        self.assertEqual(Fraction(result['cost_exact']), expected)
                        self.assertEqual(result['search'], 'sorted_all_d_coordinates')
                        self.assertEqual(result['samples'], sorted(result['samples']))

    def test_unbalanced_total_count_can_improve_over_balanced(self):
        # Five strata of size two, k=3: balanced one-per-layer fails (1/8),
        # balanced census costs 10. The unrestricted total-count optimum is 8.
        result = optimal_design((2,)*5, 3, '1/20')
        self.assertEqual(result['cost_exact'], '8')
        self.assertEqual(allocation_oracle((2,)*5, 3, Fraction(1, 20)), 8)
        self.assertGreater(risk_greedy((2,)*5, (1,)*5, 3), Fraction(1, 20))

    def test_paper_location_sensitive_example(self):
        result = optimal_design((20,)*3, 2, '1/20')
        self.assertEqual(result['cost_exact'], '48')
        self.assertEqual(result['samples'], [16, 16, 16])
        self.assertEqual(risk_dp((20,)*3, result['samples'], 2), Fraction(1, 25))
        self.assertEqual(risk_greedy((20,)*3, (0, 19, 19), 2), 1)

    def test_monotonicity_permutation_zero_and_census(self):
        populations, samples = (2, 3, 4), (0, 1, 2)
        previous = Fraction(1)
        for k in range(11):
            value = risk_greedy(populations, samples, k)
            self.assertLessEqual(value, previous)
            self.assertEqual(value, risk_greedy(populations[::-1], samples[::-1], k))
            previous = value
            for h in range(3):
                if samples[h] < populations[h]:
                    more = list(samples)
                    more[h] += 1
                    self.assertLessEqual(risk_greedy(populations, more, k), value)
        for method in (risk_greedy, risk_dp):
            self.assertEqual(method((2, 3), (0, 0), 5), 1)
            self.assertEqual(method((2, 3), (2, 3), 1), 0)
            self.assertEqual(method((2, 3), (2, 3), 0), 1)
            self.assertEqual(method((2, 3), (0, 0), 6), 0)

    def test_optimization_empty_exclusion_and_impossible_minus_one_bound(self):
        result = optimal_design((2, 3), 6, costs=(2, Fraction(1, 2)))
        self.assertEqual((result['cost_exact'], result['samples'], result['risk_exact']), ('0', [0, 0], '0'))
        result = optimal_design((2, 3), 0)
        self.assertEqual(result['status'], 'infeasible')
        self.assertIsNone(result['samples'])
        self.assertIsNone(result['cost_exact'])

    def test_budget_exhaustion_returns_no_partial_optimum(self):
        with self.assertRaises(BudgetExceeded):
            risk_greedy((3, 3), (0, 0), 3, budget=Budget(max_risk_steps=1))
        with self.assertRaises(BudgetExceeded):
            risk_dp((3, 3), (1, 1), 3, budget=Budget(max_dp_transitions=1))
        with self.assertRaises(BudgetExceeded):
            optimal_design((2,)*5, 3, budget=Budget(max_search_nodes=1))
        with self.assertRaises(BudgetExceeded):
            optimal_design((2,)*5, 3, budget=Budget(max_designs=1))
        with self.assertRaises(BudgetExceeded):
            optimal_design((2,)*5, 3, budget=Budget(max_risk_calls=1))
        with self.assertRaises(BudgetExceeded):
            risk_greedy((4, 4), (0, 0), 2, budget=Budget(max_total_population=7))
        with self.assertRaises(BudgetExceeded):
            risk_greedy((1, 1), (0, 0), 1, budget=Budget(max_strata=1))
        with self.assertRaises(BudgetExceeded):
            optimal_design((2,), 1, costs=(2**50,), budget=Budget(max_scalar_bits=10))

    def test_invalid_types_values_and_budget(self):
        for method in (risk_greedy, risk_dp):
            for populations, samples, k in [([], [], 1), ((0,), (0,), 1), ((True,), (0,), 1),
                    ((1.0,), (0,), 1), ((1,), (False,), 1), ((1,), (0.0,), 1),
                    ((1,), (2,), 1), ((1,), (0,), True), ((1,), (0,), 1.0),
                    ((1,), (0,), -1), ((1,), (), 1)]:
                with self.assertRaises(ValueError):
                    method(populations, samples, k)
        for a in (True, 0.05, 0, 1, '1/0', '1e1000000000'):
            with self.assertRaises(ValueError):
                optimal_design((2,), 1, a)
        for costs in ((True,), (1.0,), (0,), (-1,), ()):
            with self.assertRaises(ValueError):
                optimal_design((2,), 1, costs=costs)
        for value in (True, 1.0, 0, -1):
            with self.assertRaises(ValueError):
                replace(Budget(), max_risk_steps=value)


if __name__ == '__main__':
    unittest.main()
