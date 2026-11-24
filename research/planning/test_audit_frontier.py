from fractions import Fraction
from math import comb
import unittest

from research.local.audit import audit_upper, reachable
from research.planning.audit_frontier import (
    coverage_plan, discrete_frontier, minimum_zero_audit, vote_radii, zero_probability,
)


class AuditFrontierTests(unittest.TestCase):
    def test_all_small_N_gates_match_confidence_inversion(self):
        for N in range(0, 19):
            for B in range(N + 2):
                for alpha in (Fraction(1, 20), Fraction(1, 2), Fraction(3, 4)):
                    expected = next(n for n in range(N + 1) if audit_upper(N, n, 0, alpha) <= B)
                    self.assertEqual(minimum_zero_audit(N, B, alpha), expected)
                    if B < N:
                        for n in range(N + 1):
                            self.assertEqual(zero_probability(N, B + 1, n) <= alpha,
                                             audit_upper(N, n, 0, alpha) <= B)

    def test_probability_dual_formula_and_boundaries(self):
        for N in range(10):
            for K in range(N + 1):
                for n in range(N + 1):
                    expected = Fraction(comb(N - K, n) if n <= N - K else 0, comb(N, n))
                    self.assertEqual(zero_probability(N, K, n), expected)
        self.assertEqual(zero_probability(0, 0, 0), 1)

    def test_monotonicity_in_budget_alpha_and_population(self):
        for N in range(1, 31):
            values = [minimum_zero_audit(N, B) for B in range(N + 1)]
            self.assertEqual(values, sorted(values, reverse=True))
            for B in range(N):
                self.assertGreaterEqual(minimum_zero_audit(N, B, "1/100"), minimum_zero_audit(N, B, "1/20"))
                self.assertLessEqual(minimum_zero_audit(N, B), minimum_zero_audit(N + 1, B))

    def test_census_and_equality_edge(self):
        # K=1: zero probability=(N-n)/N, equality is sufficient for rejection.
        self.assertEqual(minimum_zero_audit(20, 0, "1/20"), 19)
        self.assertEqual(minimum_zero_audit(19, 0, "1/20"), 19)
        self.assertEqual(minimum_zero_audit(20, 1, "1/1000000"), 19)
        self.assertEqual(minimum_zero_audit(20, 20), 0)
        self.assertEqual(minimum_zero_audit(0, 0), 0)

    def test_tie_priority_radius(self):
        info = vote_radii([[2, 0], [0, 2], [1, 1]])
        self.assertEqual(info["winners"], [0, 1, 0])
        self.assertEqual(info["radii"], [1, 0, 0])
        self.assertEqual(reachable([2, 0], 1), [0])
        self.assertEqual(reachable([0, 2], 1), [0, 1])

    def test_small_vote_radius_implies_unique_reachable_label(self):
        for m in range(1, 9):
            for a in range(m + 1):
                for b in range(m - a + 1):
                    row = [a, b, m - a - b]
                    info = vote_radii([row])
                    self.assertEqual(reachable(row, info["radii"][0]), info["winners"])

    def test_order_statistic_rounding_and_frontier(self):
        votes = [[11, 0, 0], [8, 2, 1], [6, 5, 0], [4, 4, 3], [0, 11, 0], [3, 2, 6]]
        plan = coverage_plan(1000, votes, "1/2")
        self.assertEqual(plan["required_certified_points"], 3)
        self.assertEqual(plan["budget_B"], 3)
        self.assertEqual(coverage_plan(1000, votes, "0.5001")["required_certified_points"], 4)
        front = discrete_frontier(1000, votes)
        ns = [r["minimum_n_if_zero_findings"] for r in front]
        self.assertEqual(ns, sorted(ns))
        for row in front:
            self.assertGreaterEqual(row["certified_points_if_zero_findings"], row["required_certified_points"])

    def test_invalid_inputs_rejected(self):
        for N, B, alpha in [(-1, 0, "1/20"), (1, -1, "1/20"), (True, 0, "1/20"),
                            (1, 0.0, "1/20"), (1, 0, 0.05), (1, 0, "0"), (1, 0, "1")]:
            with self.assertRaises(ValueError):
                minimum_zero_audit(N, B, alpha)
        for q in [0, -1, "1.01", 0.5, True]:
            with self.assertRaises(ValueError):
                coverage_plan(2, [[2, 0]], q)
        for votes in [[], [[1]], [[0, 0]], [[1, -1]], [[1.0, 0]], [[True, 0]], [[1, 0], [2, 0]], [[1, 0], [1, 0, 0]]]:
            with self.assertRaises(ValueError):
                vote_radii(votes)


if __name__ == "__main__":
    unittest.main()
