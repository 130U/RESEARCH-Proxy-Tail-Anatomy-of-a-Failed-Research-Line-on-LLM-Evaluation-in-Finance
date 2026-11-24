"""Exact audit planning conditional on zero findings in a fixed-size audit.

Inputs are hypothetical design quantities. No data acquisition or model training.
Each vote row contains class counts, with ties won by smallest class index.
"""
from fractions import Fraction
from math import comb
import json
from pathlib import Path
import platform
import time

from research.local.audit import audit_upper


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _rational(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, str, Fraction)):
        raise ValueError(f"{name} requires an integer, exact decimal/fraction string, or Fraction; no floats")
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError(f"invalid rational {name}") from error


def zero_probability(N, K, n):
    """Exact Hyp(N,K,n) zero-count probability; dual form saves arithmetic."""
    if not all(_integer(v) for v in (N, K, n)) or not 0 <= K <= N or not 0 <= n <= N:
        raise ValueError("require integers N>=0, 0<=K<=N, 0<=n<=N")
    if n > N - K:
        return Fraction(0)
    if K < n:
        return Fraction(comb(N - n, K), comb(N, K))
    return Fraction(comb(N - K, n), comb(N, n))


def minimum_zero_audit(N, B, alpha="1/20"):
    """Smallest n with audit_upper(N,n,0,alpha)<=B.

    The equivalent gate is Pr_Hyp(N,B+1,n)(X=0)<=alpha. Model/population
    must be fixed before sampling; this design does not promise zero findings.
    """
    if not all(_integer(v) for v in (N, B)) or N < 0 or B < 0:
        raise ValueError("N and B must be nonnegative integers")
    a = _rational(alpha, "alpha")
    if not 0 < a < 1:
        raise ValueError("alpha must lie in (0,1)")
    if B >= N:
        return 0
    # At this upper endpoint zero findings would rule out K=B+1 with certainty.
    low, high = 0, N - B
    while low < high:
        mid = (low + high) // 2
        if zero_probability(N, B + 1, mid) <= a:
            high = mid
        else:
            low = mid + 1
    return low


def vote_radii(votes):
    """Sufficient pointwise deletion/shard-replacement radii from vote margins."""
    if not isinstance(votes, (list, tuple)) or not votes:
        raise ValueError("nonempty vote matrix required")
    if not isinstance(votes[0], (list, tuple)) or len(votes[0]) < 2:
        raise ValueError("at least two classes required")
    classes = len(votes[0])
    total = None
    winners, radii = [], []
    for row in votes:
        if not isinstance(row, (list, tuple)) or len(row) != classes:
            raise ValueError("all vote rows need the same classes")
        if not all(_integer(v) and v >= 0 for v in row) or sum(row) == 0:
            raise ValueError("nonnegative integer votes and positive totals required")
        if total is None:
            total = sum(row)
        if sum(row) != total:
            raise ValueError("all examples must use the same number of shards")
        winner = max(range(classes), key=lambda c: (row[c], -c))
        radius = min(row[winner] - row[c] - int(c < winner) for c in range(classes) if c != winner) // 2
        winners.append(winner)
        radii.append(radius)
    return {"shards": total, "classes": classes, "winners": winners, "radii": radii}


def coverage_plan(N, votes, q, alpha="1/20"):
    """Plan the minimal zero-finding audit for at least q pointwise coverage."""
    proportion = _rational(q, "q")
    if not 0 < proportion <= 1:
        raise ValueError("q must lie in (0,1]")
    a = _rational(alpha, "alpha")
    margins = vote_radii(votes)
    J = len(votes)
    r = (proportion.numerator * J + proportion.denominator - 1) // proportion.denominator
    B = sorted(margins["radii"], reverse=True)[r - 1]
    n = minimum_zero_audit(N, B, a)
    # Reuse the existing exact confidence inversion as the output cross-check.
    upper = audit_upper(N, n, 0, a)
    previous_upper = audit_upper(N, n - 1, 0, a) if n else None
    certified = sum(radius >= upper for radius in margins["radii"])
    if upper > B or (previous_upper is not None and previous_upper <= B) or certified < r:
        raise AssertionError("planner and fixed-n confidence inversion disagree")
    return {"N": N, "alpha_exact": str(a), "target_coverage_exact": str(proportion),
            "evaluation_points": J, "required_certified_points": r,
            "budget_B": B, "minimum_n_if_zero_findings": n,
            "zero_finding_upper": upper, "upper_at_n_minus_one": previous_upper,
            "certified_points_if_zero_findings": certified,
            "coverage_if_zero_findings_exact": str(Fraction(certified, J)),
            "gate_probability_exact": str(zero_probability(N, B + 1, n)) if B < N else None,
            "gate_probability_at_n_minus_one_exact": str(zero_probability(N, B + 1, n - 1)) if B < N and n else None,
            **margins}


def discrete_frontier(N, votes, alpha="1/20"):
    """All attainable requested fractions r/J; repeated n plateaus retained."""
    vote_radii(votes)
    return [coverage_plan(N, votes, Fraction(r, len(votes)), alpha) for r in range(1, len(votes) + 1)]


def main():
    start = time.perf_counter()
    scenarios = [
        {"name": "assumed_m11", "N": 1000,
         "votes": [[11, 0, 0], [8, 2, 1], [6, 5, 0], [4, 4, 3], [0, 11, 0], [3, 2, 6]]},
        {"name": "assumed_m31", "N": 10000,
         "votes": [[31, 0, 0], [24, 4, 3], [18, 12, 1], [11, 10, 10], [0, 31, 0], [6, 5, 20]]},
        {"name": "tie_favourable_m2", "N": 20, "votes": [[2, 0], [0, 2]]},
        {"name": "empty_edge_population", "N": 0, "votes": [[2, 0], [0, 2]]},
    ]
    result = {"status": "mathematical_design_only", "date": "2026-11-15",
              "source": "hypothetical population sizes and handwritten vote counts, not SEC measurements",
              "python": platform.python_version(), "platform": platform.platform(),
              "alpha_exact": "1/20", "scenarios": [dict(s, frontier=discrete_frontier(s["N"], s["votes"])) for s in scenarios],
              "assumptions": ["model, population, shard rule, vote matrix and audit design fixed before sampling",
                              "uniform sample without replacement and correct audit labels",
                              "clean comparator differs only by deleting suspicious records with stable IDs",
                              "trusted shared core and deterministic shard-local training",
                              "fixed-n plan conditional on future zero findings; not guaranteed to observe zero"],
              "limitations": ["not a real-data certificate or model experiment", "not anytime-valid",
                              "for x>0 recompute audit_upper at actual x; do not keep using the zero-finding plan",
                              "coverage is pointwise label robustness, not task accuracy or statistic-interval usefulness"]}
    result["elapsed_seconds"] = time.perf_counter() - start
    out = Path("research/planning/frontier_results.json")
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for s in result["scenarios"]:
        print(s["name"], [(r["target_coverage_exact"], r["budget_B"], r["minimum_n_if_zero_findings"]) for r in s["frontier"]])
    print("elapsed_seconds", result["elapsed_seconds"])


if __name__ == "__main__":
    main()
