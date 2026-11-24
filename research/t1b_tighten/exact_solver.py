"""Rationally certified ranges on a box intersected with linear equalities.

HiGHS is a *candidate generator*. Every reported outer bound is proved again
using Fraction arithmetic and the elementary dual-residual bound in notes.
An outside label additionally requires a strictly interior rational witness.
"""
from __future__ import annotations

import itertools
import math
import sys
from dataclasses import dataclass
from fractions import Fraction as F
from pathlib import Path

import numpy as np
import sympy as sp
from scipy.optimize import linprog

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "t1_rounding"))
from interval_core import Interval, eval_interval, eval_scalar


def frac(x):
    if isinstance(x, float):
        raise TypeError("Supply exact decimal strings, not floats")
    return F(x)


def dot(a, b):
    return sum((x * y for x, y in zip(a, b)), F(0))


def rational_candidate(x):
    if not math.isfinite(float(x)):
        raise ValueError("Non-finite solver candidate")
    return F(str(float(x))).limit_denominator(10**9)


@dataclass
class LP:
    c: list
    bounds: list
    eq: list
    rhs: list
    ub: list
    limits: list
    offset: F = F(0)


def feasible(lp, point):
    return (len(point) == len(lp.c)
            and all(lo <= x <= hi for x, (lo, hi) in zip(point, lp.bounds))
            and all(dot(a, point) == b for a, b in zip(lp.eq, lp.rhs))
            and all(dot(a, point) <= b for a, b in zip(lp.ub, lp.limits)))


def _reconstruct(lp, approx):
    """Solve candidate active equalities exactly; never accept by tolerance."""
    n = len(lp.c)
    if n == 0:
        return [] if feasible(lp, []) else None
    approx = list(approx)
    for tol in (1e-8, 1e-6, 1e-10, -1):
        rows = [list(a) + [b] for a, b in zip(lp.eq, lp.rhs)]
        for i, (lo, hi) in enumerate(lp.bounds):
            if lo == hi or (tol >= 0 and abs(approx[i] - float(lo)) <= tol):
                a = [F(0)] * n
                a[i] = F(1)
                rows.append(a + [lo])
            elif tol >= 0 and abs(approx[i] - float(hi)) <= tol:
                a = [F(0)] * n
                a[i] = F(1)
                rows.append(a + [hi])
        for a, b in zip(lp.ub, lp.limits):
            if tol >= 0 and abs(sum(float(v) * x for v, x in zip(a, approx)) - float(b)) <= tol:
                rows.append(list(a) + [b])
        point = [rational_candidate(x) for x in approx]
        if rows:
            matrix, pivots = sp.Matrix(rows).rref()
            if n in pivots:
                continue
            for row, col in enumerate(pivots):
                point[col] = F(matrix[row, n]) - sum(
                    (F(matrix[row, j]) * point[j] for j in range(n) if j not in pivots), F(0))
        if feasible(lp, point):
            return point
    return None


def dual_bound(lp, cert):
    """Check an arbitrary rational dual candidate and compute its lower bound.

    For z <= 0, c.x >= b.y + h.z + min_box((c-E'y-G'z).x).
    The residual term makes approximate multipliers rigorous, without rounding
    a floating objective or assuming optimality/strong duality.
    """
    y = [F(x) for x in cert["eq_multipliers"]]
    z = [F(x) for x in cert["ub_multipliers"]]
    if len(y) != len(lp.eq) or len(z) != len(lp.ub) or any(v > 0 for v in z):
        raise ValueError("Invalid dual certificate dimensions or signs")
    residual = [c - sum((a[i] * v for a, v in zip(lp.eq, y)), F(0))
                - sum((a[i] * v for a, v in zip(lp.ub, z)), F(0))
                for i, c in enumerate(lp.c)]
    bound = lp.offset + dot(lp.rhs, y) + dot(lp.limits, z)
    bound += sum((min(r * lo, r * hi) for r, (lo, hi) in zip(residual, lp.bounds)), F(0))
    return bound


def _active_dual(lp, point, floating):
    """Reconstruct stationarity on the exact primal active set if possible.

    Bound multipliers are used only to reconstruct equality/inequality duals;
    dual_bound independently accounts for them through its box residual term.
    Failure leaves the always-valid residual-corrected certificate unchanged.
    """
    n = len(lp.c)
    columns = [list(a) for a in lp.eq]
    approximations = [rational_candidate(x) for x in floating.eqlin.marginals]
    tags = [("eq", i) for i in range(len(lp.eq))]
    for i, (a, limit) in enumerate(zip(lp.ub, lp.limits)):
        if dot(a, point) == limit and abs(floating.ineqlin.marginals[i]) > 1e-14:
            columns.append(list(a))
            approximations.append(rational_candidate(floating.ineqlin.marginals[i]))
            tags.append(("ub", i))
    for i, (lo, hi) in enumerate(lp.bounds):
        for sign, edge, marginal in ((-1, lo, -floating.lower.marginals[i]),
                                     (1, hi, floating.upper.marginals[i])):
            if point[i] == edge and abs(marginal) > 1e-14:
                col = [F(0)] * n
                col[i] = F(sign)
                columns.append(col)
                approximations.append(rational_candidate(marginal))
                tags.append(("bound", i))
    if not columns:
        return None
    count = len(columns)
    matrix = sp.Matrix([[col[i] for col in columns] + [lp.c[i]] for i in range(n)])
    reduced, pivots = matrix.rref()
    if count in pivots:
        return None
    values = list(approximations)
    for row, col in enumerate(pivots):
        values[col] = F(reduced[row, count]) - sum(
            (F(reduced[row, j]) * values[j] for j in range(count) if j not in pivots), F(0))
    if any(v > 0 for v, (tag, _) in zip(values, tags) if tag != "eq"):
        return None
    y, z = [F(0)] * len(lp.eq), [F(0)] * len(lp.ub)
    for value, (tag, i) in zip(values, tags):
        if tag == "eq":
            y[i] = value
        elif tag == "ub":
            z[i] = value
    cert = {"eq_multipliers": list(map(str, y)), "ub_multipliers": list(map(str, z))}
    if dual_bound(lp, cert) == lp.offset + dot(lp.c, point):
        return cert
    return None


def optimize(lp):
    """Return a certified lower bound and optionally an exact feasible point."""
    n = len(lp.c)
    result = linprog(
        np.asarray(lp.c, dtype=float),
        A_ub=np.asarray(lp.ub, dtype=float) if lp.ub else None,
        b_ub=np.asarray(lp.limits, dtype=float) if lp.ub else None,
        A_eq=np.asarray(lp.eq, dtype=float) if lp.eq else None,
        b_eq=np.asarray(lp.rhs, dtype=float) if lp.eq else None,
        bounds=[(float(a), float(b)) for a, b in lp.bounds],
        method="highs", options={"primal_feasibility_tolerance": 1e-9,
                                  "dual_feasibility_tolerance": 1e-9})
    if result.success:
        y = [rational_candidate(x) for x in result.eqlin.marginals]
        z = [min(F(0), rational_candidate(x)) for x in result.ineqlin.marginals]
        point = _reconstruct(lp, result.x)
    else:
        # Zero multipliers still prove the elementary box bound. Solver status
        # never proves infeasibility, containment, or a feasible witness.
        y, z, point = [F(0)] * len(lp.eq), [F(0)] * len(lp.ub), None
    cert = {"eq_multipliers": list(map(str, y)), "ub_multipliers": list(map(str, z))}
    bound = dual_bound(lp, cert)
    if point is not None and bound != dot(lp.c, point) + lp.offset:
        exact_dual = _active_dual(lp, point, result)
        if exact_dual is not None:
            cert = exact_dual
            bound = dual_bound(lp, cert)
    cert["lower_bound"] = str(bound)
    cert["candidate_solver_status"] = int(result.status)
    cert["primal"] = list(map(str, point)) if point is not None else None
    cert["exact_optimum"] = point is not None and dot(lp.c, point) + lp.offset == bound
    return bound, point, cert


def _normalized(bounds, equations):
    # Certificates must survive JSON replay and hash-randomized processes.
    names = sorted(bounds)
    box = {k: (frac(bounds[k][0]), frac(bounds[k][1])) for k in names}
    if any(lo > hi for lo, hi in box.values()):
        raise ValueError("Empty input interval")
    centers = [(lo + hi) / 2 for lo, hi in box.values()]
    widths = [(hi - lo) / 2 for lo, hi in box.values()]
    zbox = [(F(-1), F(1)) if w else (F(0), F(0)) for w in widths]
    eq, rhs = [], []
    for equation in equations:
        if set(equation) - set(names):
            raise ValueError("Unknown variable in equality")
        coeff = [frac(equation.get(k, 0)) for k in names]
        row = [v * w for v, w in zip(coeff, widths)]
        val = -dot(coeff, centers)
        scale = max([abs(v) for v in row] + [abs(val), F(1)])
        eq.append([v / scale for v in row])
        rhs.append(val / scale)
    return names, box, centers, widths, LP([F(0)] * len(names), zbox, eq, rhs, [], [])


def _symbolic(steps, names, centers, widths):
    symbols = sp.symbols("z0:" + str(len(names)))
    values = {k: sp.Rational(c.numerator, c.denominator) + sp.Rational(w.numerator, w.denominator) * z
              for k, c, w, z in zip(names, centers, widths, symbols)}
    outputs = []

    def resolve(arg):
        if isinstance(arg, str) and arg.startswith("#"):
            return outputs[int(arg[1:])]
        if arg in values:
            return values[arg]
        if isinstance(arg, str) and arg.startswith("const_"):
            arg = arg[6:].replace("m", "-").replace("_", ".")
        q = frac(arg)
        return sp.Rational(q.numerator, q.denominator)

    for op, a, b in steps:
        a, b = resolve(a), resolve(b)
        value = {"add": lambda: a + b, "subtract": lambda: a - b,
                 "multiply": lambda: a * b, "divide": lambda: a / b,
                 "exp": lambda: a**b}[op]()
        outputs.append(value)
    numerator, denominator = sp.fraction(sp.cancel(outputs[-1]))

    def affine(expr):
        poly = sp.Poly(expr, *symbols)
        if poly.total_degree() > 1:
            return None
        constant = F(poly.eval({s: 0 for s in symbols}))
        return [F(poly.coeff_monomial(s)) for s in symbols], constant

    try:
        return affine(numerator), affine(denominator)
    except (sp.PolynomialError, TypeError):
        return None, None


def _objective_lp(base, numerator, denominator):
    n = len(base.c)
    nc, n0 = numerator
    dc, d0 = denominator
    dl = d0 + sum((min(c * lo, c * hi) for c, (lo, hi) in zip(dc, base.bounds)), F(0))
    dh = d0 + sum((max(c * lo, c * hi) for c, (lo, hi) in zip(dc, base.bounds)), F(0))
    if dh < 0:
        nc, n0, dc, d0, dl, dh = [-x for x in nc], -n0, [-x for x in dc], -d0, -dh, -dl
    if dl <= 0:
        return None, "denominator_not_certified_nonzero"
    if not any(dc):
        return LP([x / d0 for x in nc], base.bounds, base.eq, base.rhs, [], [], n0 / d0), "affine"
    # Denominator scaling keeps t and y O(1), improving candidate quality.
    scale = (dl + dh) / 2
    nc, n0, dc, d0, dl, dh = ([x / scale for x in nc], n0 / scale,
                             [x / scale for x in dc], d0 / scale, dl / scale, dh / scale)
    tlo, thi = 1 / dh, 1 / dl
    ccbox = []
    for lo, hi in base.bounds:
        products = [lo * tlo, lo * thi, hi * tlo, hi * thi]
        ccbox.append((min(products), max(products)))
    ccbox.append((tlo, thi))
    eq = [list(a) + [-b] for a, b in zip(base.eq, base.rhs)]
    rhs = [F(0)] * len(eq)
    eq.append(list(dc) + [d0])
    rhs.append(F(1))
    ub, limits = [], []
    for i, (lo, hi) in enumerate(base.bounds):
        row = [F(0)] * (n + 1)
        row[i], row[-1] = F(1), -hi
        ub.append(row)
        limits.append(F(0))
        row = [F(0)] * (n + 1)
        row[i], row[-1] = F(-1), lo
        ub.append(row)
        limits.append(F(0))
    return LP(list(nc) + [n0], ccbox, eq, rhs, ub, limits), "linear_fractional"


def _interior_lp(base):
    n = len(base.c)
    ub, limits = [], []
    for i, (lo, hi) in enumerate(base.bounds):
        if lo == hi:
            continue
        for sign in (-1, 1):
            row = [F(0)] * (n + 1)
            row[i], row[-1] = F(sign), F(1)
            ub.append(row)
            limits.append(F(1))
    return LP([F(0)] * n + [F(-1)], base.bounds + [(F(0), F(1))],
              [list(a) + [F(0)] for a in base.eq], base.rhs, ub, limits)


def _phase1_lp(base):
    # Always feasible: z=0, t=max(abs(rhs)) is admissible. A positive certified
    # objective lower bound proves no point satisfies the original equalities.
    n = len(base.c)
    top = max([abs(b) for b in base.rhs] + [F(1)])
    ub, limits = [], []
    for a, b in zip(base.eq, base.rhs):
        ub.extend([list(a) + [F(-1)], [-v for v in a] + [F(-1)]])
        limits.extend([b, -b])
    return LP([F(0)] * n + [F(1)], base.bounds + [(F(0), top)], [], [], ub, limits)


def _negate(lp):
    return LP([-x for x in lp.c], lp.bounds, lp.eq, lp.rhs, lp.ub, lp.limits, -lp.offset)


def verify_witness(bounds, equations, steps, witness, acceptance, strict=True):
    point = {k: F(v) for k, v in witness.items()}
    if set(point) != set(bounds):
        return False
    for key, (lo, hi) in bounds.items():
        lo, hi = frac(lo), frac(hi)
        if not lo <= point[key] <= hi:
            return False
        if strict and lo < hi and not lo < point[key] < hi:
            return False
    if any(sum((frac(a) * point[k] for k, a in eq.items()), F(0)) != 0 for eq in equations):
        return False
    try:
        value = eval_scalar(steps, point)
    except (ValueError, ZeroDivisionError):
        return False
    lo, hi = map(frac, acceptance)
    return value < lo or value > hi


def solve_range(bounds, equations, steps, acceptance):
    """JSON-compatible certified result; equations use sum(coeff*x)=0.

    Input bounds are closed enclosures. Outside witnesses are strictly inside
    every nondegenerate input bound, so ties in display rounding are irrelevant.
    A mere enclosure extending outside acceptance is never labeled outside.
    """
    names, box, centers, widths, base = _normalized(bounds, equations)
    acceptance = tuple(map(frac, acceptance))
    output = {"status": "unresolved", "method": None, "enclosure": None,
              "witness": None, "witness_value": None, "certificates": {},
              "feasible_point": None, "strict_interior_point": None, "extrema": {}, "warnings": []}
    _, feasible_z, phase0 = optimize(base)
    if feasible_z is None:
        low, _, cert = optimize(_phase1_lp(base))
        output["certificates"]["phase1"] = cert
        if low > 0:
            output.update(status="infeasible", method="exact_phase1_certificate")
            return output
        output["warnings"].append("Could not reconstruct an exact feasible point")
    _, interior_raw, interior_cert = optimize(_interior_lp(base))
    interior_z = interior_raw[:-1] if interior_raw is not None and interior_raw[-1] > 0 else None
    output["certificates"]["interior"] = interior_cert

    def original(z):
        return {k: c + w * v for k, c, w, v in zip(names, centers, widths, z)}

    if feasible_z is not None:
        output["feasible_point"] = {k: str(v) for k, v in original(feasible_z).items()}
    if interior_z is not None:
        output["strict_interior_point"] = {k: str(v) for k, v in original(interior_z).items()}
    candidates = [v for v in (interior_z, feasible_z) if v is not None]
    numerator, denominator = _symbolic(steps, names, centers, widths)
    lp, kind = _objective_lp(base, numerator, denominator) if numerator is not None and denominator is not None else (None, "nonlinear")
    try:
        eval_interval(steps, {k: Interval(lo, hi) for k, (lo, hi) in box.items()})
    except (ValueError, ZeroDivisionError):
        # Algebraic cancellation must not make an undefined original program
        # appear defined. Coordinate tightening below may recover a safe domain.
        lp, kind = None, "original_program_domain_not_certified"
    output["method"] = kind
    if lp is not None:
        low, pmin, cmin = optimize(lp)
        neghi, pmax, cmax = optimize(_negate(lp))
        output["enclosure"] = {"lo": str(low), "hi": str(-neghi)}
        output["certificates"].update(minimum=cmin, maximum=cmax)
        for label, point in (("minimum", pmin), ("maximum", pmax)):
            if point is not None:
                z = [p / point[-1] for p in point[:-1]] if kind == "linear_fractional" else point
                if feasible(base, z):
                    candidates.append(z)
                    original_point = original(z)
                    try:
                        value = eval_scalar(steps, original_point)
                        output["extrema"][label] = {
                            "point": {k: str(v) for k, v in original_point.items()},
                            "value": str(value), "boundary_allowed": True}
                    except (ValueError, ZeroDivisionError):
                        output["warnings"].append("An extremal candidate has an undefined program intermediate")
        output["range_exact"] = cmin["exact_optimum"] and cmax["exact_optimum"]
    else:
        # Rigorous fallback: optimize each used coordinate, then propagate its
        # certified envelope with exact interval arithmetic. Correlations may
        # widen this enclosure, so the result is explicitly not an exact range.
        used = {a for _, a, b in steps for a in (a, b) if a in box}
        intervals, coordinate_certs = {}, {}
        for i, name in enumerate(names):
            lo, hi = box[name]
            if name in used and widths[i]:
                obj = [F(0)] * len(names)
                obj[i] = F(1)
                coordlp = LP(obj, base.bounds, base.eq, base.rhs, [], [])
                zl, p1, cert1 = optimize(coordlp)
                nzh, p2, cert2 = optimize(_negate(coordlp))
                lo = max(lo, centers[i] + widths[i] * zl)
                hi = min(hi, centers[i] - widths[i] * nzh)
                coordinate_certs[name] = {"minimum": cert1, "maximum": cert2}
                candidates.extend(p for p in (p1, p2) if p is not None)
            intervals[name] = Interval(lo, hi)
        output["certificates"]["coordinates"] = coordinate_certs
        try:
            envelope = eval_interval(steps, intervals)
            output["enclosure"] = {"lo": str(envelope.lo), "hi": str(envelope.hi)}
        except (ValueError, ZeroDivisionError) as error:
            output["warnings"].append(str(error))
        output["range_exact"] = False
        indices = [i for i, k in enumerate(names) if k in used]
        if len(indices) <= 8:
            for signs in itertools.product((-1, 1), repeat=len(indices)):
                objective = [F(0)] * len(names)
                for i, sign in zip(indices, signs):
                    objective[i] = F(sign)
                _, point, _ = optimize(LP(objective, base.bounds, base.eq, base.rhs, [], []))
                if point is not None:
                    candidates.append(point)
        # Even a nonlinear interval enclosure can be an exact range when its
        # two bounds are attained by exactly feasible assignments. This claim
        # is certified by endpoint values, never by the search being complete.
        if output["enclosure"] is not None:
            for candidate in candidates:
                point = original(candidate)
                try:
                    value = eval_scalar(steps, point)
                except (ValueError, ZeroDivisionError):
                    continue
                for label, edge in (("minimum", "lo"), ("maximum", "hi")):
                    if value == F(output["enclosure"][edge]):
                        output["extrema"][label] = {
                            "point": {k: str(v) for k, v in point.items()},
                            "value": str(value), "boundary_allowed": True}
            output["range_exact"] = all(k in output["extrema"] for k in ("minimum", "maximum"))

    # A feasible rational interior point mixed with any feasible endpoint
    # remains exactly feasible; let the mixing weight shrink for narrow gaps.
    for candidate in candidates:
        trial_points = [candidate]
        if interior_z is not None:
            for denominator in (1000, 10**6, 10**9, 10**12, 10**18):
                weight = F(1, denominator)
                trial_points.append([(1 - weight) * a + weight * b for a, b in zip(candidate, interior_z)])
        for trial in trial_points:
            point = original(trial)
            if verify_witness(box, equations, steps, point, acceptance, strict=True):
                output.update(status="witnessed_outside", witness={k: str(v) for k, v in point.items()},
                              witness_value=str(eval_scalar(steps, point)))
                return output
    if output["enclosure"] is not None and feasible_z is not None:
        lo, hi = (F(output["enclosure"][k]) for k in ("lo", "hi"))
        if acceptance[0] <= lo <= hi <= acceptance[1]:
            output["status"] = "certified_inside"
    if interior_z is None:
        output["warnings"].append("No strictly interior feasible point certified")
    return output


def verify_result(bounds, equations, steps, acceptance, result):
    """Recompute proof bounds and witness from the serialized certificate.

    No optimizer is called. Raises AssertionError/ValueError on tampering.
    """
    names, box, centers, widths, base = _normalized(bounds, equations)
    certs = result["certificates"]

    def check_certificate(lp, cert):
        bound = dual_bound(lp, cert)
        assert bound == F(cert["lower_bound"]), "Incorrect certificate bound"
        if cert["primal"] is not None:
            point = list(map(F, cert["primal"]))
            assert feasible(lp, point), "Invalid exact primal point"
            if cert["exact_optimum"]:
                assert dot(lp.c, point) + lp.offset == bound
        else:
            assert not cert["exact_optimum"]
        return bound

    if "phase1" in certs:
        pbound = check_certificate(_phase1_lp(base), certs["phase1"])
        if result["status"] == "infeasible":
            assert pbound > 0
            return True
    if "interior" in certs:
        check_certificate(_interior_lp(base), certs["interior"])
    if "minimum" in certs:
        eval_interval(steps, {k: Interval(lo, hi) for k, (lo, hi) in box.items()})
        numerator, denominator = _symbolic(steps, names, centers, widths)
        lp, kind = _objective_lp(base, numerator, denominator)
        assert result["method"] == kind
        lo = check_certificate(lp, certs["minimum"])
        hi = -check_certificate(_negate(lp), certs["maximum"])
        assert result["range_exact"] == (certs["minimum"]["exact_optimum"] and certs["maximum"]["exact_optimum"])
    elif "coordinates" in certs:
        intervals = {}
        for i, name in enumerate(names):
            low, high = box[name]
            if name in certs["coordinates"]:
                obj = [F(0)] * len(names)
                obj[i] = F(1)
                lp = LP(obj, base.bounds, base.eq, base.rhs, [], [])
                c = certs["coordinates"][name]
                low = max(low, centers[i] + widths[i] * check_certificate(lp, c["minimum"]))
                high = min(high, centers[i] - widths[i] * check_certificate(_negate(lp), c["maximum"]))
            intervals[name] = Interval(low, high)
        try:
            interval = eval_interval(steps, intervals)
            lo, hi = interval.lo, interval.hi
        except (ValueError, ZeroDivisionError):
            assert result["enclosure"] is None
            lo = hi = None
        if result["range_exact"]:
            assert lo is not None and hi is not None
            assert F(result["extrema"]["minimum"]["value"]) == lo
            assert F(result["extrema"]["maximum"]["value"]) == hi
    else:
        lo = hi = None
    if result["enclosure"] is not None:
        assert lo == F(result["enclosure"]["lo"]) and hi == F(result["enclosure"]["hi"])
        assert lo <= hi
    for field in ("feasible_point", "strict_interior_point"):
        if result[field] is not None:
            point = {k: F(v) for k, v in result[field].items()}
            assert set(point) == set(box)
            assert all(l <= point[k] <= h for k, (l, h) in box.items())
            assert all(sum((frac(v) * point[k] for k, v in eq.items()), F(0)) == 0 for eq in equations)
            if field == "strict_interior_point":
                assert all(l == h or l < point[k] < h for k, (l, h) in box.items())
    for item in result.get("extrema", {}).values():
        point = {k: F(v) for k, v in item["point"].items()}
        assert set(point) == set(box)
        assert all(l <= point[k] <= h for k, (l, h) in box.items())
        assert all(sum((frac(v) * point[k] for k, v in eq.items()), F(0)) == 0 for eq in equations)
        assert F(item["value"]) == eval_scalar(steps, point)
    if result["status"] == "witnessed_outside":
        assert verify_witness(bounds, equations, steps, result["witness"], acceptance)
        assert str(eval_scalar(steps, {k: F(v) for k, v in result["witness"].items()})) == result["witness_value"]
    elif result["status"] == "certified_inside":
        assert result["feasible_point"] is not None
        assert frac(acceptance[0]) <= lo <= hi <= frac(acceptance[1])
    else:
        assert result["status"] == "unresolved"
    return True
