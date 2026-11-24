"""Independent midpoint integration of four-corner radii for Benford predictor."""
from __future__ import annotations

import json
import math
import random

from benford import mantissa_prediction


def main():
    rng = random.Random(20261116)
    n = 32768
    max_error = 0.0
    cases = 0
    for _ in range(100):
        g = 10 ** rng.uniform(-3, 1)
        if rng.random() < .5:
            g = -min(g, .999)
        ka, kb = rng.randint(1, 6), rng.randint(1, 6)
        tau = rng.choice((.001, .005, .01, .02, .05))
        predicted, within, lo, hi = mantissa_prediction(g, ka, kb, tau)
        count = 0
        for j in range(n):
            a = 10 ** ((j + .5) / n)
            b = (1 + g) * a
            ha = .5 * 10 ** (1 - ka)
            hb = .5 * 10 ** (math.floor(math.log10(b)) - kb + 1)
            # Deliberately do not use the production threshold formula.
            values = [(b + db) / (a + da) - 1
                      for da in (-ha, ha) for db in (-hb, hb)]
            outside = max(abs(v - g) for v in values) > tau * abs(g)
            count += outside
        measured = count / n
        max_error = max(max_error, abs(measured - predicted))
        # Within [1,10), r*a crosses at most one decimal exponent boundary:
        # at most two monotone pieces, with discretization error O(1/n).
        assert abs(measured - predicted) < 3 / n, (
            g, ka, kb, tau, predicted, measured)
        assert lo - 1e-12 <= predicted <= hi + 1e-12
        assert lo - 1e-12 <= within <= hi + 1e-12
        cases += 1
    print(json.dumps({
        "status": "passed", "seed": 20261116, "cases": cases,
        "quadrature_points_per_case": n, "max_abs_error": max_error,
        "error_limit": 3 / n}, indent=2))


if __name__ == "__main__":
    main()
