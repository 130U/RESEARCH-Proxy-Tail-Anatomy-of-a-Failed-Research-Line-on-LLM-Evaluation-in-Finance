"""Independent exact-arithmetic checks for PROOFS.md (Python standard library).

No empirical data are required or modified. The CDF is checked against an
independent rational polygon clipping/area implementation, not itself.
"""
from __future__ import annotations

import json
import random
from fractions import Fraction as F
from itertools import product


def uniform_sum_cdf(z: F, p: F, q: F) -> F:
    """Exact right-continuous CDF, including degenerate distributions."""
    z, p, q = F(z), F(p), F(q)
    assert p >= 0 and q >= 0
    if p == q == 0:
        return F(z >= 0)
    if p == 0 or q == 0:
        width = max(p, q)
        return min(F(1), max(F(0), (z + width) / (2 * width)))
    plus_square = lambda v: max(v, F(0)) ** 2
    return (plus_square(z + p + q) - plus_square(z + p - q)
            - plus_square(z - p + q) + plus_square(z - p - q)) / (8 * p * q)


def growth_cdf(t: F, a: F, b: F, ha: F, hb: F) -> F:
    assert abs(a) > ha >= 0 and hb >= 0
    if a < 0:
        a, b = -a, -b
    r = 1 + t
    return uniform_sum_cdf(r * a - b, hb, abs(r) * ha)


def growth_outside_probability(lo: F, hi: F, a: F, b: F,
                               ha: F, hb: F) -> F:
    assert lo <= hi
    if (ha == hb == 0) or (b == hb == 0):
        return F(not lo <= b / a - 1 <= hi)
    return growth_cdf(lo, a, b, ha, hb) + 1 - growth_cdf(hi, a, b, ha, hb)


def polygon_cdf(t: F, a: F, b: F, ha: F, hb: F) -> F:
    """Independently clip (A,B) rectangle by B <= (1+t)A."""
    assert a > ha > 0 and hb > 0
    polygon = [(a - ha, b - hb), (a + ha, b - hb),
               (a + ha, b + hb), (a - ha, b + hb)]
    distance = lambda v: v[1] - (1 + t) * v[0]
    clipped = []
    for first, second in zip(polygon, polygon[1:] + polygon[:1]):
        f, s = distance(first), distance(second)
        if f <= 0:
            clipped.append(first)
        if (f < 0 < s) or (s < 0 < f):
            w = f / (f - s)
            clipped.append((first[0] + w * (second[0] - first[0]),
                            first[1] + w * (second[1] - first[1])))
    if len(clipped) < 3:
        return F(0)
    twice = sum(x1 * y2 - y1 * x2 for (x1, y1), (x2, y2)
                in zip(clipped, clipped[1:] + clipped[:1]))
    return abs(twice) / (8 * ha * hb)


def main() -> None:
    rng = random.Random(20261116)
    counts = {"rational_corner_radius": 0, "taylor_identity_and_remainder": 0,
              "cdf_polygon_agreement": 0, "digit_budget_equivalence": 0,
              "equal_unit_threshold": 0, "degenerate_cdf": 0,
              "delta_100_counterexamples": 0}
    for _ in range(2000):
        a = F(rng.choice((-1, 1)) * rng.randint(1, 10000), rng.randint(1, 100))
        b = F(rng.randint(-10000, 10000), rng.randint(1, 100))
        ha = abs(a) * F(rng.randint(0, 99), 100)
        hb = F(rng.randint(0, 100), rng.randint(1, 100))
        g = b / a - 1
        radius = (abs(a) * hb + abs(b) * ha) / (abs(a) * (abs(a) - ha))
        corners = [(b + v) / (a + u) - 1
                   for u, v in product((-ha, ha), (-hb, hb))]
        assert max(abs(value - g) for value in corners) == radius
        counts["rational_corner_radius"] += 1
        u = ha * F(rng.randint(-100, 100), 100)
        v = hb * F(rng.randint(-100, 100), 100)
        linear = (a * v - b * u) / a ** 2
        remainder = -u * linear / (a + u)
        exact = (b + v) / (a + u) - b / a
        r1 = (abs(a) * hb + abs(b) * ha) / a ** 2
        eta = ha / abs(a)
        assert exact == linear + remainder
        assert abs(remainder) <= eta * r1 / (1 - eta)
        assert abs(linear) / (1 + eta) <= abs(exact) <= abs(linear) / (1 - eta)
        counts["taylor_identity_and_remainder"] += 1
        if ha and hb:
            ap, bp = (a, b) if a > 0 else (-a, -b)
            t = g + F(rng.randint(-300, 300), 100) * radius
            assert growth_cdf(t, a, b, ha, hb) == polygon_cdf(t, ap, bp, ha, hb)
            counts["cdf_polygon_agreement"] += 1
    for _ in range(1000):
        # Finite rational mantissas avoid numerical log/ceil artifacts.
        ma, mb = F(rng.randint(100, 999), 100), F(rng.randint(100, 999), 100)
        a, b = ma, mb * F(10) ** rng.randint(-3, 3)
        if a == b:
            continue
        k = rng.randint(1, 8)
        q = F(10) ** (1 - k)
        ea, eb = q / (2 * ma), q / (2 * mb)
        ha, hb = a * ea, b * eb
        g, r = b / a - 1, b / a
        tau = rng.choice((F(1, 1000), F(1, 200), F(1, 100), F(1, 50), F(1, 20)))
        radius = (a * hb + b * ha) / (abs(b - a) * (a - ha))
        budget_lhs = q * (abs(r) * (1 / ma + 1 / mb) + tau * abs(g) / ma)
        assert (radius <= tau) == (budget_lhs <= 2 * tau * abs(g))
        counts["digit_budget_equivalence"] += 1
        # Equal displayed unit, with both centers positive and denominator safe.
        ha = hb = min(a, b) / 4
        delta = abs(b - a) / (2 * ha)
        radius = (a * hb + b * ha) / (abs(b - a) * (a - ha))
        threshold = (1 + g / 2) / tau + abs(g) / 2
        assert (radius <= tau) == (delta >= threshold)
        counts["equal_unit_threshold"] += 1
    for a, b, ha, hb, lo, hi, expected in [
        (F(1), F(0), F(1, 2), F(0), F(-1), F(-1), F(0)),
        (F(1), F(0), F(1, 2), F(0), F(0), F(1), F(1)),
        (F(1), F(2), F(0), F(0), F(1), F(1), F(0)),
        (F(-1), F(-2), F(0), F(0), F(2), F(3), F(1)),
        (F(1), F(1), F(0), F(1), F(-1, 2), F(1, 2), F(1, 2)),
    ]:
        assert growth_outside_probability(lo, hi, a, b, ha, hb) == expected
        counts["degenerate_cdf"] += 1
    # Explicit disproofs of both directions of the unqualified Delta=100 rule.
    for a, b, expected_stable in [(F(100), F(10), True), (F(1000), F(1100), False)]:
        h = F(1, 2)
        radius = (a * h + b * h) / (abs(b - a) * (a - h))
        assert (radius <= F(1, 100)) == expected_stable
        counts["delta_100_counterexamples"] += 1
    print(json.dumps({"seed": 20261116, "status": "passed", "checks": counts,
                      "total": sum(counts.values())}, indent=2))


if __name__ == "__main__":
    main()
