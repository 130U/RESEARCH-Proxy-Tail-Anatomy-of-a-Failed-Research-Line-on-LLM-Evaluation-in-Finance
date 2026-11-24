"""Independent tests: exact rational polygon areas and direct uniform draws.

The polygon oracle never calls the implementation's sum-of-uniforms CDF.
Only T1's frozen per-question JSONL is read for empirical spot checks.
"""
from fractions import Fraction as F
import math
from pathlib import Path
import unittest

import numpy as np
import sympy as sp

import probability as p


def make_row(steps, intervals, gold=0):
    return {"steps": steps, "exe_ans": gold,
            "input_intervals": {key: {"lo": {"exact": str(F(lo))},
                                       "hi": {"exact": str(F(hi))}}
                                for key, (lo, hi) in intervals.items()}}


def rational_expression(row):
    names = list(row["input_intervals"])
    syms = {name: sp.Symbol(name) for name in names}
    vals = []
    def v(token):
        if token in syms: return syms[token]
        if token.startswith("#"): return vals[int(token[1:])]
        if token == "const_m1": return sp.Integer(-1)
        return sp.Rational(token.removeprefix("const_"))
    for op, left, right in row["steps"]:
        a, b = v(left), v(right)
        if op == "add": out = a+b
        elif op == "subtract": out = a-b
        elif op == "multiply": out = a*b
        elif op == "divide": out = a/b
        else: raise ValueError(op)
        vals.append(out)
    return sp.cancel(vals[-1]), syms


def polygon_probability(row, lo, hi):
    """Integrate a half-plane over [-1,1]^2 in rational arithmetic."""
    expr, syms = rational_expression(row)
    num, den = sp.fraction(expr)
    substitutions = {}
    u, v = sp.symbols("audit_u audit_v")
    for name, s in syms.items():
        iv = row["input_intervals"][name]
        low, high = sp.Rational(iv["lo"]["exact"]), sp.Rational(iv["hi"]["exact"])
        substitutions[s] = (low+high)/2+(high-low)/2*([u,v][len(substitutions)])
    nn, dd = sp.expand(num.subs(substitutions)), sp.expand(den.subs(substitutions))
    sign = 1 if dd.subs({u:0,v:0}) > 0 else -1
    def cdf(t, strict=False):
        q = sp.Poly(sp.expand(sign*(nn-sp.Rational(t.numerator,t.denominator)*dd)), u,v)
        aa, bb, cc = (F(str(q.coeff_monomial(m))) for m in (u,v,1))
        if aa == bb == 0:
            return F(cc < 0 if strict else cc <= 0)
        poly = [(F(-1),F(-1)),(F(1),F(-1)),(F(1),F(1)),(F(-1),F(1))]
        result = []
        for start, end in zip(poly, poly[1:]+poly[:1]):
            ds, de = aa*start[0]+bb*start[1]+cc, aa*end[0]+bb*end[1]+cc
            if ds <= 0: result.append(start)
            if (ds < 0 < de) or (de < 0 < ds):
                ratio = ds/(ds-de)
                result.append(tuple(x+ratio*(y-x) for x,y in zip(start,end)))
            elif ds > 0 and de == 0:
                result.append(end)
        if len(result)<3: return F(0)
        area2 = abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(result,result[1:]+result[:1])))
        return area2/8
    return cdf(lo, True)+1-cdf(hi)


class ProbabilityAudit(unittest.TestCase):
    def test_sum_uniform_degeneracies(self):
        self.assertEqual(p.uniform_cdf(-1,0,0),0)
        self.assertEqual(p.uniform_cdf(0,0,0),1)
        self.assertEqual(p.uniform_cdf(0,1,0),.5)
        self.assertEqual(p.uniform_cdf(-1,1,1),.125)
        self.assertEqual(p.uniform_cdf(1,1,1),.875)
        for z in np.linspace(-5,5,501):
            self.assertAlmostEqual(p.uniform_cdf(z,2,1),1-p.uniform_cdf(-z,2,1),places=14)

    def test_independent_and_repeated_zero_growth(self):
        independent = make_row([["subtract","b","a"],["divide","#0","a"]],
                               {"a": (99,101),"b":(99,101)})
        shared = make_row([["subtract","a","a"],["divide","#0","a"]],{"a":(99,101)})
        self.assertEqual(p.exact_probability(p.affine_fraction(independent),0,0),1)
        self.assertEqual(p.exact_probability(p.affine_fraction(shared),0,0),0)
        repeated = make_row([["divide","a","a"]],{"a":(99,101)})
        model = p.affine_fraction(repeated)
        self.assertEqual(p.exact_probability(model,1,1),0)
        self.assertEqual(p.exact_probability(model,0,1),0)
        self.assertEqual(p.exact_probability(model,1,2),0)
        self.assertEqual(p.exact_probability(model,0,.9),1)

    def test_minus_one_and_shared_execution(self):
        row = make_row([["subtract","a","a"],["multiply","#0","const_m1"]],{"a":(1,3)})
        samples = np.linspace(1,3,19)
        np.testing.assert_array_equal(p.execute(row,{"a":samples}),np.zeros(19))
        self.assertEqual(p.exact_probability(p.affine_fraction(row),0,0),0)

    def test_negative_denominator_and_gold_offset(self):
        for sign in (-1,1):
            row = make_row([["subtract","b","a"],["divide","#0","a"]],
                           {"a":sorted((F(sign*265,2), F(sign*267,2))),
                            "b":sorted((F(sign*273,2),F(sign*275,2)))})
            for lo,hi in [(F(297792,10000000),F(303808,10000000)),
                          (F(-1), F(1)), (F(0), F(0)), (F(25,1000),F(28,1000))]:
                actual = p.exact_probability(p.affine_fraction(row),float(lo),float(hi))
                expected = float(polygon_probability(row,lo,hi))
                self.assertAlmostEqual(actual,expected,places=12)

    def test_ratio_pole_rejected(self):
        row = make_row([["divide","b","a"]],{"a":(-1,1),"b":(2,4)})
        self.assertIsNone(p.affine_fraction(row))

    def test_zero_width_constant(self):
        row = make_row([["add","a","const_1"]],{"a":(2,2)})
        model = p.affine_fraction(row)
        self.assertEqual(p.exact_probability(model,3,3),0)
        self.assertEqual(p.exact_probability(model,2,3),0)
        self.assertEqual(p.exact_probability(model,3,4),0)
        self.assertEqual(p.exact_probability(model,2,2.9),1)

    def test_fractional_models_against_exact_polygon(self):
        rng = np.random.default_rng(28111991)
        max_error = 0.
        for _ in range(80):
            nn = rng.integers(-5,6,3)
            dd = rng.integers(-2,3,2)
            d0 = int(rng.choice([-100,100]))
            # N = n0+n1*x+n2*y; D=d0+d1*x+d2*y.
            steps = [["multiply","x",str(nn[1])],["multiply","y",str(nn[2])],
                     ["add","#0","#1"],["add","#2",str(nn[0])],
                     ["multiply","x",str(dd[0])],["multiply","y",str(dd[1])],
                     ["add","#4","#5"],["add","#6",str(d0)],["divide","#3","#7"]]
            row = make_row(steps,{"x":(-3,5),"y":(-2,4)})
            model = p.affine_fraction(row)
            self.assertIsNotNone(model)
            for lo,hi in [(F(-1,5),F(1,8)),(F(0),F(1,10)),(F(-1),F(-1,100))]:
                expected = float(polygon_probability(row,lo,hi))
                actual = p.exact_probability(model,float(lo),float(hi))
                max_error = max(max_error,abs(expected-actual))
                self.assertAlmostEqual(actual,expected,places=12)
        print(f"synthetic exact-area oracle: 240 bands, max abs error {max_error:.3g}")

    def test_saved_rows_polygon_and_independent_simulation(self):
        path = Path(__file__).resolve().parent.parent/"t1_rounding/results/per_question.jsonl"
        rows = [r for r in p.load(path) if r["status"]=="analyzed" and len(r["input_intervals"])<=2]
        # Fixed evenly spaced index selection, unrelated to error or correctness.
        selected = [rows[int(i)] for i in np.linspace(0,len(rows)-1,42)]
        max_error, max_mc_z, count = 0.,0.,0
        rng = np.random.default_rng(16112026)
        for row in selected:
            model = p.affine_fraction(row)
            if model is None: continue
            gold = F(str(row["exe_ans"]))
            for tau in (F(1,1000),F(1,100),F(1,20)):
                lo, hi = gold-abs(gold)*tau, gold+abs(gold)*tau
                expected = float(polygon_probability(row,lo,hi))
                actual = p.exact_probability(model,float(lo),float(hi))
                max_error = max(max_error,abs(expected-actual))
                self.assertLess(abs(actual-expected),1e-8,row["id"])
                count += 1
            lo,hi = float(gold-abs(gold)/100),float(gold+abs(gold)/100)
            exact = p.exact_probability(model,lo,hi)
            names,c,h = p.geometry(row)
            n = 65536
            draws = c[:,None]+h[:,None]*rng.uniform(-1,1,(len(names),n))
            vals = np.asarray(p.execute(row,dict(zip(names,draws))))
            estimate = float(np.mean((vals<lo)|(vals>hi)))
            se = math.sqrt(exact*(1-exact)/n)
            self.assertLessEqual(abs(estimate-exact),6*se+2/n,row["id"])
            if se: max_mc_z=max(max_mc_z,abs(estimate-exact)/se)
        print(f"saved-row exact-area oracle: {count} bands, max abs error {max_error:.3g}; MC max z {max_mc_z:.3f}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
