"""Synthetic rational cases; an independent Lagrange oracle checks arithmetic."""
from dataclasses import replace
from fractions import Fraction as F
import math
import unittest

from research.numeric.semantic_envelope import (
    Budget, BudgetExceeded, Interval, SemanticBranch, branch_probability_extrema,
    branch_probability_ranges, difference_interval, exp_bounds, label_set,
    probabilities_at_eta, ratio_interval, relative_change_interval,
    rescale_interval, robust_label, semantic_envelope, sigmoid_bounds, width_gate,
)


def oracle_exp(x):
    """Different remainder: Lagrange with exp(x)<=3**ceil(x), x>=0.

    e<3 follows from k!>=2**(k-1), with strict inequality for k>=3.
    The 96-degree exact sum plus this bound encloses the true exponential.
    This is an independent finite-test oracle, not the implementation's tail.
    """
    x = F(x)
    y = abs(x)
    degree = 96
    lower = sum((y**k / math.factorial(k) for k in range(degree+1)), F(0))
    ceiling = (y.numerator+y.denominator-1)//y.denominator
    upper = lower + 3**ceiling * y**(degree+1) / math.factorial(degree+1)
    if x >= 0:
        return Interval(lower, upper)
    return Interval(1/upper, 1/lower)


def oracle_sigmoid(x):
    exponential = oracle_exp(-F(x))
    return Interval(1/(1+exponential.upper), 1/(1+exponential.lower))


def oracle_probabilities(eta, thresholds):
    cumulative = [oracle_sigmoid(theta-eta) for theta in thresholds]
    values = [cumulative[0]]
    values += [Interval(max(F(0), cumulative[i].lower-cumulative[i-1].upper), min(F(1), cumulative[i].upper-cumulative[i-1].lower)) for i in range(1, len(cumulative))]
    values += [oracle_sigmoid(eta-thresholds[-1])]
    return values


class SemanticEnvelopeTests(unittest.TestCase):
    def assert_contains(self, outer, inner):
        self.assertLessEqual(outer.lower, inner.lower)
        self.assertGreaterEqual(outer.upper, inner.upper)

    def test_positive_negative_exp_and_sigmoid_with_independent_rational_oracle(self):
        budget = Budget(tolerance=F(1,10**12))
        for x in [F(0), F(1,2), F(1), F(3), F(5), F(-1,2), F(-3), F(-5)]:
            exponential = exp_bounds(x,budget)
            sigmoid = sigmoid_bounds(x,budget)
            self.assert_contains(exponential, oracle_exp(x))
            self.assert_contains(sigmoid, oracle_sigmoid(x))
            self.assertLessEqual(exponential.width,budget.tolerance)
            self.assertLessEqual(sigmoid.width,budget.tolerance)

    def test_zero_and_sigmoid_symmetry_exact(self):
        self.assertEqual(exp_bounds(0),Interval(1,1))
        self.assertEqual(sigmoid_bounds(0),Interval(F(1,2),F(1,2)))
        for x in [F(1,3),F(2),F(7,2)]:
            positive,negative=sigmoid_bounds(x),sigmoid_bounds(-x)
            self.assertEqual(negative,Interval(1-positive.upper,1-positive.lower))

    def test_fail_closed_term_and_argument_budget(self):
        with self.assertRaises(BudgetExceeded):
            exp_bounds(1,Budget(max_terms=1))
        with self.assertRaises(BudgetExceeded):
            sigmoid_bounds(3,Budget(max_abs_argument=2))
        good=SemanticBranch("good",Interval(0,0),1,0,(F(0),))
        bad=SemanticBranch("bad",Interval(100,100),1,0,(F(0),))
        with self.assertRaises(BudgetExceeded):
            semantic_envelope([good,bad])

    def test_exact_ratio_corners_and_unit_scale_invariance(self):
        for x in [Interval(-3,-1),Interval(-2,5),Interval(0,0),Interval(2,7)]:
            baseline=Interval(F(1,2),3)
            original=ratio_interval(x,baseline)
            for scale in [F(1,1000),F(3,2),F(1000000)]:
                self.assertEqual(original,ratio_interval(rescale_interval(x,scale),rescale_interval(baseline,scale)))
                self.assertEqual(relative_change_interval(x,baseline),relative_change_interval(rescale_interval(x,scale),rescale_interval(baseline,scale)))
            for i in range(5):
                for j in range(5):
                    value=(x.lower+x.width*F(i,4))/(baseline.lower+baseline.width*F(j,4))
                    self.assertLessEqual(original.lower,value)
                    self.assertGreaterEqual(original.upper,value)

    def test_zero_or_negative_baseline_rejected(self):
        for baseline in [Interval(-1,1),Interval(0,1),Interval(0,0),Interval(-3,-1)]:
            with self.assertRaises(ValueError):
                ratio_interval(Interval(1,2),baseline)
        for scale in [0,-1]:
            with self.assertRaises(ValueError):
                rescale_interval(Interval(1,2),scale)

    def test_affine_range_handles_negative_and_zero_slope(self):
        branch=SemanticBranch("negative",Interval(-1,2),-2,F(1,3),(F(-1),F(1)))
        self.assertEqual(branch.eta_interval,Interval(F(-11,3),F(7,3)))
        zero=replace(branch,semantic_id="zero",slope=F(0))
        self.assertEqual(zero.eta_interval,Interval(F(1,3),F(1,3)))
        for enclosure in branch_probability_ranges(zero):
            self.assertLessEqual(enclosure.width,Budget().tolerance)

    def test_middle_peak_is_interior_not_endpoint_only(self):
        branch=SemanticBranch("middle",Interval(-2,3),1,0,(F(-1),F(2)))
        bounds=branch_probability_extrema(branch)
        peak=oracle_probabilities(F(1,2),branch.thresholds)[1]
        endpoint=[oracle_probabilities(eta,branch.thresholds)[1] for eta in [-2,3]]
        self.assertGreater(peak.lower,max(value.upper for value in endpoint))
        self.assert_contains(bounds[1].maximum,peak)
        self.assertGreater(bounds[1].interval.upper,max(value.upper for value in endpoint))

    def test_branch_ranges_contain_exact_rational_oracle_grid(self):
        for slope in [F(-2),F(0),F(3,2)]:
            branch=SemanticBranch(str(slope),Interval(-1,2),slope,F(1,3),(F(-1),F(0),F(2)))
            bounds=branch_probability_ranges(branch)
            for point in range(13):
                g=branch.g_interval.lower+branch.g_interval.width*F(point,12)
                values=oracle_probabilities(slope*g+branch.offset,branch.thresholds)
                for outer,inner in zip(bounds,values):
                    self.assert_contains(outer,inner)

    def test_point_probability_bounds_and_extremum_tolerances(self):
        budget=Budget(tolerance=F(1,10**10))
        branch=SemanticBranch("three",Interval(-2,2),1,0,(F(-1),F(1)))
        for eta in [F(-2),F(0),F(2)]:
            values=probabilities_at_eta(eta,branch.thresholds,budget)
            self.assertLessEqual(sum(x.lower for x in values),1)
            self.assertGreaterEqual(sum(x.upper for x in values),1)
            self.assertTrue(all(0<=x.lower<=x.upper<=1 and x.width<=budget.tolerance for x in values))
        for certificate in branch_probability_extrema(branch,budget):
            self.assertLessEqual(certificate.minimum.width,budget.tolerance)
            self.assertLessEqual(certificate.maximum.width,budget.tolerance)

    def test_union_is_coordinate_hull_not_probabilistic_mixture(self):
        a=SemanticBranch("a",Interval(-2,-1),1,0,(F(0),),target_id="same",class_labels=("low","high"))
        b=replace(a,semantic_id="b",g_interval=Interval(1,2))
        joined=semantic_envelope([a,b])
        separate=[branch_probability_ranges(branch) for branch in [a,b]]
        for i,outer in enumerate(joined.class_intervals):
            self.assertEqual(outer.lower,min(bounds[i].lower for bounds in separate))
            self.assertEqual(outer.upper,max(bounds[i].upper for bounds in separate))
        # Both coordinate maxima together exceed one: the box corner is not a
        # probability vector and is not claimed to be jointly attainable.
        self.assertGreater(sum(x.upper for x in joined.class_intervals),1)
        self.assertFalse(joined.to_json()["all_box_points_attainable"])
        self.assertFalse(joined.to_json()["branch_probabilities_assumed"])

    def test_union_requires_same_declared_target_and_ordered_labels(self):
        a=SemanticBranch("a",Interval(0,1),1,0,(F(0),),target_id="metric",class_labels=("low","high"))
        for b in [replace(a,semantic_id="b",target_id="other"),replace(a,semantic_id="b",class_labels=("high","low")),SemanticBranch("b",Interval(0,1),1,0,(F(-1),F(1)))]:
            with self.assertRaises(ValueError):
                semantic_envelope([a,b])
        with self.assertRaises(ValueError):
            semantic_envelope([a,a])
        with self.assertRaises(ValueError):
            semantic_envelope([])

    def test_symbolic_labels_and_abstention(self):
        self.assertEqual(label_set(Interval(-1,0)),("below","equal"))
        self.assertEqual(label_set(Interval(0,0)),("equal",))
        self.assertEqual(label_set(Interval(F(-1,10),F(1,10)),F(1,10)),("equal",))
        self.assertEqual(robust_label([Interval(1,2),Interval(3,4)]),"above")
        self.assertIsNone(robust_label([Interval(-2,-1),Interval(1,2)]))
        self.assertIsNone(robust_label([Interval(0,1)]))
        self.assertEqual(difference_interval(Interval(1,3),Interval(2,4)),Interval(-3,1))

    def test_width_gate_distinguishes_rounding_uncertainty(self):
        envelope=semantic_envelope([SemanticBranch("a",Interval(-1,1),1,0,(F(0),))],Budget(tolerance=F(1,1000)))
        general=width_gate(envelope,1)
        lower,upper=general.width_bounds.lower,general.width_bounds.upper
        self.assertGreater(lower,0)
        self.assertGreater(upper,lower)
        self.assertEqual(general.status,"pass")
        self.assertEqual(width_gate(envelope,upper).status,"pass")
        self.assertEqual(width_gate(envelope,lower/2).status,"fail")
        self.assertEqual(width_gate(envelope,(lower+upper)/2).status,"undetermined")
        self.assertEqual(width_gate(envelope,lower).status,"undetermined")

    def test_strict_constructors_reject_float_bool_and_bad_shapes(self):
        for invalid in [0.1,True,"1/2"]:
            with self.assertRaises(TypeError):
                Interval(invalid,1)
            with self.assertRaises(TypeError):
                Budget(tolerance=invalid)
            with self.assertRaises(TypeError):
                SemanticBranch("a",Interval(0,1),invalid,0,(F(0),))
            with self.assertRaises(TypeError):
                sigmoid_bounds(invalid)
        for kwargs in [{"max_terms":True},{"max_terms":0},{"tolerance":F(0)},{"max_abs_argument":F(-1)}]:
            with self.assertRaises(ValueError):
                Budget(**kwargs)
        for thresholds in [(),(F(0),F(0)),(F(1),F(0))]:
            with self.assertRaises(ValueError):
                SemanticBranch("a",Interval(0,1),1,0,thresholds)
        with self.assertRaises(ValueError):
            SemanticBranch("a",Interval(0,1),1,0,(F(0),),class_labels=("only",))
        with self.assertRaises(ValueError):
            Interval(2,1)


if __name__ == "__main__":
    unittest.main()
