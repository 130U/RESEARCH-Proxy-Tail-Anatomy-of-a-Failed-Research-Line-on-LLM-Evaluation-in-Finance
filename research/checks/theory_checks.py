"""Finite sanity checks for the paper-pencil results in ../theory/notes.md.

No training, external data, packages, or network. Passing is not a proof of a
general learned model, parser, or all-real-valued coupling implementation.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import platform
import random
import time
from fractions import Fraction as F
from pathlib import Path


def winner(votes: tuple[int, ...], classes: int = 3) -> int:
    counts = [votes.count(c) for c in range(classes)]
    return max(range(classes), key=lambda c: (counts[c], -c))


def reachable(votes: tuple[int, ...], budget: int, classes: int = 3) -> set[int]:
    out = set()
    for size in range(min(len(votes), budget) + 1):
        for positions in itertools.combinations(range(len(votes)), size):
            for labels in itertools.product(range(classes), repeat=size):
                changed = list(votes)
                for pos, label in zip(positions, labels):
                    changed[pos] = label
                out.add(winner(tuple(changed), classes))
    return out


def sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    expx = math.exp(x)
    return expx / (1.0 + expx)


def probabilities(eta: float) -> tuple[float, float, float]:
    low, high = sigmoid(-0.7 - eta), sigmoid(0.9 - eta)
    return low, high - low, 1.0 - high


def linear_head_certificate(weights: tuple[F, ...], lam: F, monotone: set[int]) -> dict:
    if lam < 0 or not weights or any(abs(w) > lam for w in weights):
        raise ValueError("Head does not satisfy the declared l1 Lipschitz bound")
    if not monotone <= set(range(len(weights))):
        raise ValueError("Monotone coordinate out of range")
    slopes = [w + (lam if j in monotone else 0) for j, w in enumerate(weights)]
    assert all(0 <= slopes[j] <= 2 * lam for j in monotone)
    return {
        "artifact_kind": "conditional_exact_rational_linear_head_certificate",
        "trained_model": False,
        "assumptions": [
            "h(g,c) = dot(weights,g) + b(c)",
            "c and ordinal thresholds remain fixed under numeric interventions",
            "ordered thresholds and logistic cumulative link",
            "real-valued function semantics; float evaluation separately sanity-checked",
        ],
        "weights": list(map(str, weights)),
        "lambda": str(lam),
        "h_lipschitz_l1": str(max(map(abs, weights))),
        "monotone_coordinates_zero_based": sorted(monotone),
        "eta_partial_derivatives": list(map(str, slopes)),
        "per_class_probability_partial_abs_bound": str(lam / 2),
    }


def compositions(total: int, slots: int):
    if slots == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for rest in compositions(total - first, slots - 1):
            yield (first,) + rest


def es(distribution: dict[int, F], beta: F) -> F:
    if not 0 <= beta < 1:
        raise ValueError("beta outside [0,1)")
    # For finite integer support an optimum is a support point.
    return min(F(t) + sum(p * max(s - t, 0) for s, p in distribution.items()) / (1-beta)
               for t in distribution)


def var_quantile(distribution: dict[int, F], beta: F) -> int:
    total = F(0)
    for s, p in sorted(distribution.items()):
        total += p
        if total >= beta:
            return s
    raise AssertionError("invalid probability distribution")


def run() -> dict:
    start = time.perf_counter()
    # Check margin theorem against all possible vote edits for modest m.
    certified_cases = 0
    for m in range(1, 6):
        for votes in itertools.product(range(3), repeat=m):
            a = winner(votes)
            for budget in range(3):
                condition = all(votes.count(a)-votes.count(c) >= 2*budget + int(c<a)
                                for c in range(3) if c != a)
                if condition:
                    assert reachable(votes, budget) == {a}
                    certified_cases += 1
    tie_example = sorted(reachable((0, 0), 1))
    assert tie_example == [0]  # m=2k contradicts the original necessary bound.
    nontrivial_interval = sorted(reachable((0, 0, 1, 1, 2), 1))
    assert nontrivial_interval == [0, 1]  # true class 2: accuracy fixed at zero.

    # Rational structural certificate; coefficients are chosen, not learned.
    weights, lam, monotone = (F(1, 4), F(-1, 2), F(1, 8)), F(1, 2), {0, 1}
    structural = linear_head_certificate(weights, lam, monotone)
    rejected_invalid = False
    try:
        linear_head_certificate((F(3, 4),), lam, {0})
    except ValueError:
        rejected_invalid = True
    assert rejected_invalid
    rng = random.Random(20261115)
    max_derivative = 0.0
    min_fosd_change = 1.0
    max_probability_sum_error = 0.0
    slopes = [float(w + (lam if j in monotone else 0)) for j, w in enumerate(weights)]
    for _ in range(100_000):
        g = [rng.uniform(-4, 4) for _ in weights]
        context = rng.uniform(-1, 1)
        eta = sum(a*b for a, b in zip(slopes, g)) + context
        probs = probabilities(eta)
        assert min(probs) >= 0
        max_probability_sum_error = max(max_probability_sum_error, abs(sum(probs)-1))
        r = rng.choice(sorted(monotone))
        step = rng.random() * 2
        higher = probabilities(eta + slopes[r]*step)
        tails_change = (higher[1]+higher[2]-probs[1]-probs[2], higher[2]-probs[2])
        assert min(tails_change) >= -1e-15
        min_fosd_change = min(min_fosd_change, *tails_change)
        assert max(abs(x-y) for x, y in zip(higher, probs)) <= float(lam/2)*step + 1e-15
        a, b = sigmoid(-0.7-eta), sigmoid(0.9-eta)
        da, db = a*(1-a), b*(1-b)
        derivatives = (-da*slopes[r], (da-db)*slopes[r], db*slopes[r])
        max_derivative = max(max_derivative, *map(abs, derivatives))
        assert max(map(abs, derivatives)) <= float(lam/2)
    # Context leakage counterexample h(g,c)=-2 lambda c, c=g.
    assert -2*float(lam)*1 + float(lam)*1 < 0
    # Changing a coordinate outside M can reverse the ordering.
    assert (-1.0 * 1 + 1.0*0) < (-1.0 * 0 + 1.0*0)

    # Unit change is checked exactly before float evaluation.
    unit_cases = 0
    for baseline in (F(1), F(3, 7), F(1000)):
        for current in (F(2), F(5, 9), F(2000)):
            for scale in (F(1, 1000), F(1000000), F(7, 3)):
                growth = (current-baseline)/baseline
                changed = (scale*current-scale*baseline)/(scale*baseline)
                assert growth == changed
                unit_cases += 1

    # All mass tables on an exact finite probability grid, not all real couplings.
    bits = tuple(itertools.product((0, 1), repeat=3))
    denominator, marginal_counts = 12, (3, 6, 9)
    com = {0: F(3, 12), 1: F(3, 12), 2: F(3, 12), 3: F(3, 12)}
    com_square = sum(F(s*s)*p for s, p in com.items())
    betas = (F(0), F(1, 2), F(9, 10))
    com_es = [es(com, beta) for beta in betas]
    candidates = feasible = 0
    for masses in compositions(denominator, len(bits)):
        candidates += 1
        if any(sum(masses[a]*bits[a][j] for a in range(8)) != marginal_counts[j] for j in range(3)):
            continue
        feasible += 1
        dist = {s: F(sum(masses[a] for a in range(8) if sum(bits[a]) == s), denominator)
                for s in range(4)}
        assert sum(F(s*s)*p for s, p in dist.items()) <= com_square
        for strike in range(4):
            assert sum(max(s-strike, 0)*p for s, p in dist.items()) <= sum(max(s-strike, 0)*p for s, p in com.items())
        for beta, bound in zip(betas, com_es):
            assert es(dist, beta) <= bound
    assert feasible > 0
    var_com = var_quantile({0: F(1, 2), 2: F(1, 2)}, F(1, 2))
    var_anti = var_quantile({1: F(1)}, F(1, 2))
    assert (var_com, var_anti) == (0, 1)
    return {
        "status": "passed",
        "source_level": "our_experiment_mathematical_sanity_check_only",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "base_commit": "8e4dd0b33c95ac2ac1a6015eba6f2dfafe5c1254",
        "python": platform.python_version(), "platform": platform.platform(),
        "processor": platform.processor(), "seed": 20261115,
        "elapsed_seconds": time.perf_counter() - start,
        "peak_memory_measured": False,
        "gpu_used": False, "training_tokens": 0,
        "vote_margin_certified_cases_exhaustively_checked": certified_cases,
        "tie_counterexample": {"m": 2, "k": 1, "votes": [0, 0], "reachable": tie_example},
        "nonrobust_but_informative_accuracy": {"votes": [0, 0, 1, 1, 2], "k": 1,
            "reachable": nontrivial_interval, "true_label": 2, "interval": [0, 0]},
        "linear_head_certificate": structural,
        "invalid_structural_input_rejected": rejected_invalid,
        "numeric_points": 100000,
        "maximum_abs_probability_derivative": max_derivative,
        "minimum_monotone_tail_change": min_fosd_change,
        "maximum_probability_sum_error": max_probability_sum_error,
        "exact_rational_unit_cases": unit_cases,
        "coupling_grid": {"denominator": denominator, "marginal_counts": marginal_counts,
            "mass_tables_considered": candidates, "feasible_mass_tables": feasible,
            "comonotone_es": {str(beta): str(value) for beta, value in zip(betas, com_es)},
            "all_real_couplings_enumerated": False},
        "var_counterexample": {"beta": "1/2", "comonotone": var_com, "antimonotone": var_anti},
        "limitations": ["no model training or real financial data", "no parser correctness claim",
            "finite checks are not universal proofs", "floating sigmoid evaluation is not interval-arithmetic verified"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("status", "elapsed_seconds", "numeric_points", "coupling_grid")}, ensure_ascii=False))
