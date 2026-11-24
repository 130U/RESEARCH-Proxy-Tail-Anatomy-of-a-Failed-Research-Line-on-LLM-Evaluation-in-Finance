"""Regression checks for conclusions that cannot be inferred from LP success."""
import copy
import unittest
from fractions import Fraction as F

from exact_solver import LP, dual_bound, solve_range, verify_result, verify_witness


class ExactSolverTests(unittest.TestCase):
    def solve(self, bounds, equations, steps, acceptance):
        result = solve_range(bounds, equations, steps, acceptance)
        self.assertTrue(verify_result(bounds, equations, steps, acceptance, result))
        return result

    def test_growth_closed_form_and_strict_witness(self):
        b = {"a": (F("132.5"), F("133.5")), "b": (F("136.5"), F("137.5"))}
        r = self.solve(b, [], [("subtract", "b", "a"), ("divide", "#0", "a")], (F(".0297"), F(".0303")))
        self.assertEqual(r["enclosure"], {"lo": "2/89", "hi": "2/53"})
        self.assertTrue(r["range_exact"])
        self.assertEqual(r["status"], "witnessed_outside")
        self.assertTrue(all(lo < F(r["witness"][k]) < hi for k, (lo, hi) in b.items()))

    def test_accounting_identity_can_certify_sum(self):
        b = {"a": (F("9.5"), F("10.5")), "b": (F("19.5"), F("20.5")),
             "total": (F("29.95"), F("30.05"))}
        r = self.solve(b, [{"a": 1, "b": 1, "total": -1}], [("add", "a", "b")], (F("29.7"), F("30.3")))
        self.assertEqual(r["status"], "certified_inside")
        self.assertEqual(r["enclosure"], {"lo": "599/20", "hi": "601/20"})

    def test_fractional_constraint_extrema_and_signed_denominator(self):
        b = {"a": (-3, -2), "b": (-6, -4)}
        r = self.solve(b, [{"a": 2, "b": -1}], [("divide", "b", "a")], (F("1.99"), F("2.01")))
        self.assertEqual(r["enclosure"], {"lo": "2", "hi": "2"})
        self.assertEqual(r["status"], "certified_inside")

    def test_empty_polytope_is_not_determined(self):
        r = self.solve({"a": (1, 2)}, [{"a": 1}], [("add", "a", "const_0")], (1, 2))
        self.assertEqual(r["status"], "infeasible")
        self.assertGreater(F(r["certificates"]["phase1"]["lower_bound"]), 0)
        broken = copy.deepcopy(r)
        broken["certificates"]["phase1"]["lower_bound"] = "0"
        with self.assertRaises(AssertionError):
            verify_result({"a": (1, 2)}, [{"a": 1}], [("add", "a", "const_0")], (1, 2), broken)

    def test_boundary_only_failure_is_not_strict_witness(self):
        r = self.solve({"a": (1, 2), "b": (2, 3)}, [{"a": 1, "b": -1}],
                       [("add", "a", "const_0")], (F("1.4"), F("1.6")))
        self.assertEqual(r["enclosure"], {"lo": "2", "hi": "2"})
        self.assertEqual(r["status"], "unresolved")
        self.assertIsNone(r["witness"])

    def test_nonlinear_exact_range_requires_attained_endpoints(self):
        b = {"a": (1, 2), "b": (1, 2)}
        r = self.solve(b, [], [("multiply", "a", "b")], (F("2.2"), F("2.3")))
        self.assertEqual(r["method"], "nonlinear")
        self.assertEqual(r["enclosure"], {"lo": "1", "hi": "4"})
        self.assertTrue(r["range_exact"])
        self.assertEqual(r["status"], "witnessed_outside")
        # Correlated product cannot attain the coordinate-box upper bound.
        b["total"] = (3, 3)
        dependent = self.solve(b, [{"a": 1, "b": 1, "total": -1}],
                               [("multiply", "a", "b")], (F("2.2"), F("2.3")))
        self.assertFalse(dependent["range_exact"])

    def test_dependent_equalities_and_fixed_fact(self):
        b = {"a": (1, 3), "b": (1, 3), "t": (4, 4)}
        r = self.solve(b, [{"a": 1, "b": 1, "t": -1}, {"a": 2, "b": 2, "t": -2}],
                       [("add", "a", "b")], (F("3.99"), F("4.01")))
        self.assertEqual(r["status"], "certified_inside")
        self.assertEqual(r["enclosure"], {"lo": "4", "hi": "4"})

    def test_dual_residual_corrects_inexact_multipliers(self):
        # min x, x=y, x,y in [1,2]. A slightly wrong equality multiplier
        # would give an unsafe zero-residual proof; our residual restores 1.
        lp = LP([F(1), F(0)], [(F(1), F(2))] * 2,
                [[F(1), F(-1)]], [F(0)], [], [])
        bound = dual_bound(lp, {"eq_multipliers": ["1000001/1000000"], "ub_multipliers": []})
        self.assertEqual(bound, F(999999, 1000000))
        self.assertLessEqual(bound, F(1))

    def test_tampered_certificate_or_witness_is_rejected(self):
        b, eq, s, a = {"x": (1, 2)}, [], [("add", "x", "const_0")], (F("1.4"), F("1.6"))
        r = self.solve(b, eq, s, a)
        broken = copy.deepcopy(r)
        broken["certificates"]["minimum"]["lower_bound"] = "100"
        with self.assertRaises(AssertionError):
            verify_result(b, eq, s, a, broken)
        self.assertFalse(verify_witness(b, eq, s, {"x": "1"}, a))
        broken = copy.deepcopy(r)
        broken["witness"]["x"] = "100"
        with self.assertRaises(AssertionError):
            verify_result(b, eq, s, a, broken)

    def test_unit_scale_invariance(self):
        steps = [("subtract", "b", "a"), ("divide", "#0", "a")]
        acc = (F(".0297"), F(".0303"))
        b = {"a": (F("132.5"), F("133.5")), "b": (F("136.5"), F("137.5"))}
        original = self.solve(b, [], steps, acc)
        scaled = self.solve({k: (lo * 10**9, hi * 10**9) for k, (lo, hi) in b.items()}, [], steps, acc)
        self.assertEqual(original["enclosure"], scaled["enclosure"])

    def test_cancellation_does_not_define_zero_over_zero(self):
        r = self.solve({"x": (0, 0)}, [], [("divide", "x", "x")], (F(".99"), F("1.01")))
        self.assertEqual(r["status"], "unresolved")
        self.assertIsNone(r["enclosure"])

    def test_large_denominator_active_dual_reconstruction(self):
        b = {"principal": (F("212.65"), F("212.75")),
             "interest": (F("4.75"), F("4.85")),
             "price": (F("221.85"), F("221.95"))}
        eq = [{"price": 1, "interest": -1, "principal": -F("1.02083")}]
        r = self.solve(b, eq, [("divide", "interest", "price")], (F(".021"), F(".023")))
        self.assertTrue(r["range_exact"])
        self.assertEqual(r["enclosure"], {"lo": "1900000/88772633", "hi": "9700000/443858999"})


if __name__ == "__main__":
    unittest.main()
