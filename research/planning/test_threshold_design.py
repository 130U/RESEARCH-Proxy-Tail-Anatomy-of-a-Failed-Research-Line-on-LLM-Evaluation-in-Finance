from fractions import Fraction
from itertools import combinations, product
import unittest

from research.certificates.collective import BudgetExceeded
from research.planning.threshold_design import balanced_design, bonferroni_design, optimal_design, rectangle_design, risk


class ThresholdDesignTests(unittest.TestCase):
    def test_sorted_search_matches_unreduced_allocation_oracle(self):
        for N in (1, 2, 3):
            for h in range(1, 6):
                for r in range(1, h+1):
                    for alpha in (Fraction(1, 20), Fraction(1, 2)):
                        oracle = None
                        for samples in product(range(N+1), repeat=h):
                            # Enumerate actual minimally bad layer subsets independently.
                            misses = []
                            for affected in combinations(range(h), r):
                                p = Fraction(1)
                                for i in affected:
                                    p *= Fraction(N-samples[i], N)
                                misses.append(p)
                            if max(misses) <= alpha:
                                oracle = sum(samples) if oracle is None else min(oracle, sum(samples))
                        got = optimal_design(N, h, r, alpha)
                        self.assertEqual(got['cost'], oracle)
                        self.assertLessEqual(risk(N, got['samples'], r), alpha)

    def test_rectangle_formula_matches_all_safe_boxes_and_allocations(self):
        for N in (1, 2):
            for h in (2, 3):
                for r in range(1, h+1):
                    alpha = Fraction(1, 2)
                    best = None
                    for box in product(range(N+1), repeat=h):
                        if sum(b > 0 for b in box) >= r:
                            continue
                        # Positive budgets may be expanded to N without making box unsafe.
                        for samples in product(range(N+1), repeat=h):
                            # Directly count audit outcomes missing a given bad box violation.
                            worst = Fraction(0)
                            for count in product(range(N+1), repeat=h):
                                if all(c <= b for c, b in zip(count, box)):
                                    continue
                                p = Fraction(1)
                                for c, n in zip(count, samples):
                                    draws = list(combinations(range(N), n))
                                    misses = sum(all(i >= c for i in draw) for draw in draws)
                                    p *= Fraction(misses, len(draws))
                                worst = max(worst, p)
                            if worst <= alpha:
                                best = sum(samples) if best is None else min(best, sum(samples))
                    self.assertEqual(rectangle_design(N, h, r, alpha)['cost'], best)

    def test_strict_separation_and_no_gain_negative_control(self):
        direct = optimal_design(20, 11, 6)
        rect = rectangle_design(20, 11, 6)
        self.assertLessEqual(direct['cost'], 88)
        self.assertEqual(rect['cost'], 114)
        self.assertEqual(balanced_design(20, 11, 6)['risk_exact'], '729/15625')
        self.assertEqual(optimal_design(20, 2, 2)['cost'], rectangle_design(20, 2, 2)['cost'])

    def test_bonferroni_formula_against_all_count_box_support_designs(self):
        for N in (1, 2, 3):
            for h, r in ((3,2), (5,3), (4,2)):
                constrained = h-r+1
                for a in (Fraction(1,20), Fraction(1,2)):
                    oracle = min(sum(ns) for ns in product(range(N+1),repeat=constrained)
                                 if sum(Fraction(N-n,N) for n in ns) <= a)
                    self.assertEqual(bonferroni_design(N,h,r,a)['cost'],oracle)

    def test_limits_and_invalid_inputs_fail_closed(self):
        with self.assertRaises(BudgetExceeded):
            optimal_design(100, 11, 6)
        for args in [(0, 1, 1), (1, True, 1), (1, 2, 3), (1.0, 1, 1)]:
            with self.assertRaises(ValueError): optimal_design(*args)
        for alpha in (0, 1, 0.05, True, '1/0'):
            with self.assertRaises(ValueError): optimal_design(2, 3, 2, alpha)
        for samples in ([], [True], [2.0], [-1], [3]):
            with self.assertRaises(ValueError): risk(2, samples, 1)


if __name__ == '__main__':
    unittest.main()
