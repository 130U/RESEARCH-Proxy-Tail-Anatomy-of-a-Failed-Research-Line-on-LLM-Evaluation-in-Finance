"""Analytic and adversarial checks independent of empirical labels."""
from fractions import Fraction as F
from itertools import product
import unittest
from law_core import (centers_half,evaluate,gradient_radius,range_certificate,
                      classify_range,growth_descriptor,constant)


def fixture(steps,centers,half):
    return {"category":"growth","steps":steps,
            "input_intervals":{k:{"lo":{"exact":str(v-half[k])},"hi":{"exact":str(v+half[k])}} for k,v in centers.items()},
            "input_provenance":{k:{"sig":3} for k in centers}}


class CoreTests(unittest.TestCase):
    def test_growth_sign_and_range(self):
        for a,b in product((F(-12),F(12)),(F(-17),F(17))):
            ha,hb=F(1,2),F(1,10)
            r=fixture([["subtract","x1","x0"],["divide","#0","x0"]],{"x0":a,"x1":b},{"x0":ha,"x1":hb})
            center,radius,grad=gradient_radius(r)
            self.assertEqual(center,b/a-1)
            self.assertEqual(radius,(abs(a)*hb+abs(b)*ha)/(a*a))
            cert=range_certificate(r)
            self.assertTrue(cert["exact"])
            worst=(abs(a)*hb+abs(b)*ha)/(abs(a)*(abs(a)-ha))
            self.assertEqual(max(abs(cert["lo"]-center),abs(cert["hi"]-center)),worst)
            for u,v in product(range(-9,10),repeat=2):
                y=evaluate(r,{"x0":a+ha*F(u,10),"x1":b+hb*F(v,10)})
                self.assertLessEqual(cert["lo"],y);self.assertLessEqual(y,cert["hi"])

    def test_shared_source_cancellation(self):
        r=fixture([["subtract","x0","x0"]],{"x0":F(4)},{"x0":F(1,2)})
        self.assertEqual(gradient_radius(r)[1],0)
        cert=range_certificate(r)
        self.assertTrue(cert["exact"]);self.assertEqual((cert["lo"],cert["hi"]),(0,0))

    def test_zero_denominator_not_cancelled_away(self):
        r=fixture([["divide","x0","x0"]],{"x0":F(0)},{"x0":F(1)})
        self.assertFalse(range_certificate(r)["exact"])

    def test_nonlinear_interior_extremum_not_corner_certified(self):
        r=fixture([["multiply","x0","x0"]],{"x0":F(0)},{"x0":F(1)})
        cert=range_certificate(r)
        self.assertFalse(cert["exact"])

    def test_linear_fractional_shared_variables(self):
        r=fixture([["add","x0","x1"],["subtract","x0","x1"],["divide","#0","#1"]],
                  {"x0":F(10),"x1":F(3)},{"x0":F(1,2),"x1":F(1,2)})
        cert=range_certificate(r);self.assertTrue(cert["exact"])
        self.assertEqual((cert["lo"],cert["hi"]),(F(13,8),F(13,6)))

    def test_equality_and_gold_offset(self):
        cert={"exact":True,"lo":F(99),"hi":F(101)}
        self.assertEqual(classify_range(cert,F(100),F(1,100)),"inside")
        self.assertEqual(classify_range(cert,F(1001,10),F(1,100)),"outside")

    def test_constants_and_output_scale(self):
        self.assertEqual(constant("const_m1"),-1)
        r=fixture([["divide","x1","x0"],["subtract","#0","const_1"],["multiply","#1","const_100"]],
                  {"x0":F(100),"x1":F(105)},{"x0":F(1,2),"x1":F(1,2)})
        d=growth_descriptor(r);self.assertEqual(d["scale"],100);self.assertEqual(d["delta"],5)
        r["steps"][-1]=["subtract","#1","const_100"]
        self.assertIsNone(growth_descriptor(r))

    def test_unit_conversion(self):
        r=fixture([["multiply","x0","const_1000"],["subtract","x1","#0"],["divide","#1","#0"]],
                  {"x0":F(2),"x1":F(2100)},{"x0":F(1,20),"x1":F(1,2)})
        d=growth_descriptor(r)
        self.assertEqual(d["g"],F(1,20));self.assertEqual(d["unit_ratio"],F(1,1000))
        self.assertEqual(d["delta"],F(200,101))


if __name__=="__main__":unittest.main()
