"""Meaningful counterexamples and exact arithmetic checks; no dataset access."""

import unittest
from fractions import Fraction as F

from interval_core import (Interval, IntervalDomainError, UnsupportedOperation,
                           classify, eval_interval, eval_scalar)


class ExactIntervalTests(unittest.TestCase):
    def test_exact_decimal_input_and_mixed_sign_product(self):
        self.assertEqual(Interval.point("0.1") + Interval.point("0.2"),
                         Interval.point("0.3"))
        self.assertEqual(Interval(-2, 3) * Interval(-4, 5), Interval(-12, 15))
        with self.assertRaises(TypeError):
            Interval.point(0.1)

    def test_negative_divisor_and_zero_crossing(self):
        self.assertEqual(Interval(2, 4) / Interval(-4, -2), Interval(-2, F(-1, 2)))
        with self.assertRaises(IntervalDomainError):
            Interval(1, 2) / Interval(-1, 1)

    def test_signed_integer_powers(self):
        self.assertEqual(Interval(-2, 3).integer_power(2), Interval(0, 9))
        self.assertEqual(Interval(-2, 3).integer_power(3), Interval(-8, 27))
        self.assertEqual(Interval(-4, -2).integer_power(-2), Interval(F(1, 16), F(1, 4)))
        with self.assertRaises(UnsupportedOperation):
            eval_scalar([("exp", "x", "0.5")], {"x": F(4)})

    def test_dag_references_constants_and_forward_reference(self):
        steps = [("subtract", "b", "a"), ("divide", "#0", "a"),
                 ("multiply", "#1", "const_100")]
        self.assertEqual(eval_scalar(steps, {"a": F(100), "b": F(110)}), F(10))
        self.assertEqual(eval_scalar([("multiply", "x", "const_m1")], {"x": 5}), -5)
        with self.assertRaises(ValueError):
            eval_scalar([("add", "#0", "1")], {})

    def test_dependency_enclosure_is_not_a_counterexample(self):
        steps = [("divide", "x", "x")]
        box = {"x": Interval(F(19, 2), F(21, 2))}
        outcome = classify(steps, box, Interval(F(99, 100), F(101, 100)))
        self.assertEqual(outcome["status"], "unresolved")
        self.assertEqual(outcome["enclosure"], Interval(F(19, 21), F(21, 19)))
        self.assertIsNone(outcome["witness"])
        self.assertTrue(outcome["corner_search_complete"])
        self.assertEqual(outcome["evaluated_witnesses"], 2)

    def test_growth_witness_preserves_reused_a(self):
        steps = [("subtract", "b", "a"), ("divide", "#0", "a")]
        box = {"a": Interval("99.5", "100.5"), "b": Interval("109.5", "110.5")}
        accept = Interval("0.099", "0.101")
        outcome = classify(steps, box, accept)
        self.assertEqual(outcome["status"], "witnessed_outside")
        self.assertTrue(outcome["center_inside"])
        witness = outcome["witness"]
        self.assertEqual(eval_scalar(steps, witness), outcome["witness_value"])
        for name in box:
            self.assertLess(box[name].lo, witness[name])
            self.assertLess(witness[name], box[name].hi)
        self.assertFalse(accept.lo <= outcome["witness_value"] <= accept.hi)

    def test_safe_sum_is_certified_without_search(self):
        result = classify([("add", "a", "b")],
                          {"a": Interval("99.5", "100.5"),
                           "b": Interval("109.5", "110.5")},
                          Interval("207.9", "212.1"))
        self.assertEqual(result["status"], "certified_inside")
        self.assertEqual(result["enclosure"], Interval(209, 211))
        self.assertEqual(result["evaluated_witnesses"], 0)

    def test_open_rounding_boundary_is_not_certified_closed(self):
        steps = [("add", "x", "0")]
        closed = classify(steps, {"x": Interval.point("1.5")}, Interval("0.5", "1.5"))
        opened = classify(steps, {"x": Interval.point("1.5")}, Interval("0.5", "1.5"),
                          upper_closed=False)
        self.assertEqual(closed["status"], "certified_inside")
        self.assertEqual(opened["status"], "witnessed_outside")
        self.assertEqual(opened["witness_kind"], "center")

    def test_spurious_interval_zero_is_not_declared_singular_truth(self):
        # x - x + 1 is actually always 1, though interval propagation crosses 0.
        steps = [("subtract", "x", "x"), ("add", "#0", "1"),
                 ("divide", "1", "#1")]
        result = classify(steps, {"x": Interval(1, 3)}, Interval("0.99", "1.01"))
        self.assertEqual(result["status"], "unresolved")
        self.assertIn("contains zero", result["interval_error"])
        self.assertEqual(result["invalid_witnesses"], 0)
        self.assertIsNone(result["witness"])

    def test_corner_search_cannot_certify_interior_extrema(self):
        # x (1-x): endpoints zero, midpoint .25. Center already catches this.
        steps = [("subtract", "1", "x"), ("multiply", "x", "#0")]
        result = classify(steps, {"x": Interval(0, 1)}, Interval(0, "0.1"))
        self.assertEqual(result["status"], "witnessed_outside")
        self.assertEqual(result["witness_kind"], "center")
        self.assertEqual(result["witness_value"], F(1, 4))

    def test_noninteger_exponent_stays_unresolved(self):
        result = classify([("exp", "x", "0.5")], {"x": Interval(4, 9)}, Interval(1, 4))
        self.assertEqual(result["status"], "unresolved")
        self.assertIn("UnsupportedOperation", result["interval_error"])
        self.assertIsNone(result["witness"])


if __name__ == "__main__":
    unittest.main()
