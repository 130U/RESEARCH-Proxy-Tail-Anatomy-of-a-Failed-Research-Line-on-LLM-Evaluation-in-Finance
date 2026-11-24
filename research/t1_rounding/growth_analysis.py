"""Independent exact growth-rate ranges and untuned first-order predictions.

Reads saved results only. It neither changes source bindings nor reruns the
general FinQA evaluator. The precision counterfactual fixes centers and gold,
and divides the input halfwidths by 1, 10, 100, or 1000.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from fractions import Fraction as F
from itertools import product
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FACTORS = (1, 10, 100, 1000)


def exact(value):
    return F(value["exact"]) if isinstance(value, dict) else F(str(value))


def exact_hundred(token, inputs):
    if token in inputs or token.startswith("#"):
        return False
    value = token[6:] if token.startswith("const_") else token
    try:
        return F(value) == 100
    except (ValueError, ZeroDivisionError):
        return False


def structure(row):
    """Return (a-name, b-name, output-scale) only for the exact requested DAG."""
    steps = row.get("steps", [])
    if len(steps) not in (2, 3):
        return None
    op0, b, a = steps[0]
    if op0 != "subtract" or steps[1] != ["divide", "#0", a]:
        return None
    inputs = row.get("input_intervals", {})
    if a not in inputs or b not in inputs:
        return None
    scale = F(1)
    if len(steps) == 3:
        operation, left, right = steps[2]
        if operation != "multiply":
            return None
        if not ((left == "#1" and exact_hundred(right, inputs))
                or (right == "#1" and exact_hundred(left, inputs))):
            return None
        scale = F(100)
    return a, b, scale


def serialize_scalar(value):
    return {"exact": str(value), "decimal": float(value)}


def analyze_growth(row, a_name, b_name, scale, factor):
    a_interval = row["input_intervals"][a_name]
    b_interval = row["input_intervals"][b_name]
    a_lo, a_hi = exact(a_interval["lo"]), exact(a_interval["hi"])
    b_lo, b_hi = exact(b_interval["lo"]), exact(b_interval["hi"])
    a, b = (a_lo + a_hi) / 2, (b_lo + b_hi) / 2
    ha, hb = (a_hi - a_lo) / (2 * factor), (b_hi - b_lo) / (2 * factor)
    assert abs(a) > ha, "Denominator must stay strictly away from zero"
    corners = [(scale * ((b + db) / (a + da) - 1), da, db)
               for da, db in product((-ha, ha), (-hb, hb))]
    lo, hi = min(value for value, _, _ in corners), max(value for value, _, _ in corners)
    center = scale * (b / a - 1)
    assert center == exact(row["center"])
    gold = F(str(row["exe_ans"]))
    band_lo, band_hi = gold - abs(gold) / 100, gold + abs(gold) / 100
    assert band_lo <= center <= band_hi
    first_radius = abs(scale) * (abs(a) * hb + abs(b) * ha) / (a * a)
    strict_radius = abs(scale) * (abs(a) * hb + abs(b) * ha) / (abs(a) * (abs(a) - ha))
    # Independent exact check: the closed-form worst absolute deviation must
    # equal the worst of the four actual ratio values, for either sign of a,b.
    assert strict_radius == max(abs(lo - center), abs(hi - center))
    exact_crossing = lo < band_lo or hi > band_hi
    first_crossing = center - first_radius < band_lo or center + first_radius > band_hi
    strict_symmetric_crossing = (center - strict_radius < band_lo
                                 or center + strict_radius > band_hi)
    assert not exact_crossing or strict_symmetric_crossing

    generic = row["relative_1pct"] if factor == 1 else row["precision_counterfactual"][str(factor)]
    if generic["enclosure"] is not None:
        old_lo = exact(generic["enclosure"]["lo"])
        old_hi = exact(generic["enclosure"]["hi"])
        assert old_lo <= lo <= hi <= old_hi
    if generic["status"] == "witnessed_outside":
        assert exact_crossing, "General evaluator produced a non-feasible witness"
    if generic["status"] == "certified_inside":
        assert not exact_crossing, "General evaluator incorrectly certified containment"

    return {
        "id": row["id"], "split": row["split"], "factor": factor,
        "a_variable": a_name, "b_variable": b_name, "scale": scale,
        "a": a, "b": b, "half_a": ha, "half_b": hb,
        "center": center, "gold": gold, "center_minus_gold": center-gold,
        "band_lo": band_lo, "band_hi": band_hi,
        "exact_lo": lo, "exact_hi": hi,
        "first_order_radius": first_radius, "strict_radius": strict_radius,
        "exact_crossing": exact_crossing, "first_order_crossing": first_crossing,
        "first_order_error": first_crossing != exact_crossing,
        "first_order_false_positive": first_crossing and not exact_crossing,
        "first_order_false_negative": exact_crossing and not first_crossing,
        "strict_symmetric_crossing": strict_symmetric_crossing,
        "strict_symmetric_false_positive": strict_symmetric_crossing and not exact_crossing,
        "general_status": generic["status"],
    }


def stats(cases):
    n = len(cases)
    out = {"n": n}
    for field in ("exact_crossing", "first_order_crossing", "first_order_error",
                  "first_order_false_positive", "first_order_false_negative",
                  "strict_symmetric_crossing", "strict_symmetric_false_positive"):
        out[field] = sum(case[field] for case in cases)
    out["exact_crossing_fraction"] = out["exact_crossing"] / n if n else None
    out["general_status"] = dict(Counter(case["general_status"] for case in cases))
    out["general_unresolved_closed_as_inside"] = sum(
        case["general_status"] == "unresolved" and not case["exact_crossing"] for case in cases)
    out["general_unresolved_closed_as_outside"] = sum(
        case["general_status"] == "unresolved" and case["exact_crossing"] for case in cases)
    out["center_gold_offset_nonzero"] = sum(case["center_minus_gold"] != 0 for case in cases)
    ratios = [case["strict_radius"] / case["first_order_radius"] for case in cases
              if case["first_order_radius"] != 0]
    out["strict_to_first_radius_ratio_min"] = serialize_scalar(min(ratios)) if ratios else None
    out["strict_to_first_radius_ratio_max"] = serialize_scalar(max(ratios)) if ratios else None
    out["first_order_error_examples"] = [
        {key: serialize_scalar(value) if isinstance(value, F) else value
         for key, value in case.items()}
        for case in cases if case["first_order_error"]][:20]
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "results" / "per_question.jsonl")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines()]
    exclusions = Counter()
    eligible = []
    for row in rows:
        if row["status"] != "analyzed":
            exclusions["not_in_main_analyzed_set"] += 1
            continue
        parsed = structure(row)
        if parsed is None:
            exclusions["not_strict_growth_structure"] += 1
            continue
        a_name, b_name, scale = parsed
        if a_name == b_name:
            exclusions["same_source_identity"] += 1
            continue
        denominator = row["input_intervals"][a_name]
        if exact(denominator["lo"]) <= 0 <= exact(denominator["hi"]):
            exclusions["denominator_contains_zero"] += 1
            continue
        eligible.append((row, a_name, b_name, scale))
    cases = [analyze_growth(row, a, b, scale, factor)
             for row, a, b, scale in eligible for factor in FACTORS]
    summary = {
        "date": "2026-11-16", "timezone": "America/New_York",
        "input": args.input.name,
        "scope": "Main analyzed rows; strict subtract(b,a), divide(#0,a), optional exact times 100; distinct bound source variables; denominator away from zero.",
        "interpretation": "Conditional rounding-box calculation. Exact range uses four coherent ratio endpoints. First-order symmetric interval is an approximation, not a bound. Strict radius is an exact maximum absolute deviation but its symmetric envelope can be wider on one side than the true range. Strict crossing has interior witnesses by continuity; source-boundary ties are not needed.",
        "counterfactual": "Fixed original centers and fixed exe_ans-based 1% acceptance band; divide both source halfwidths by factor. This is simulated precision refinement, not actual finer disclosure.",
        "n_input_rows": len(rows), "n_eligible_questions": len(eligible),
        "exclusions": dict(exclusions),
        "formula": {
            "center": "scale * (b/a - 1)",
            "first_order_radius": "abs(scale) * (abs(a)*half_b + abs(b)*half_a)/a**2",
            "strict_radius": "abs(scale) * (abs(a)*half_b + abs(b)*half_a)/(abs(a)*(abs(a)-half_a))",
            "gold_band": "[exe_ans - abs(exe_ans)/100, exe_ans + abs(exe_ans)/100]",
        },
        "formula_checks": {
            "n_case_checks": len(cases), "exact_radius_equals_corner_max_errors": 0,
            "exact_range_outside_general_enclosure_errors": 0,
            "general_certificate_contradictions": 0,
            "detail": "Assertions halt execution before any output if one of these equalities/containments fails.",
        },
        "by_factor": {str(factor): stats([case for case in cases if case["factor"] == factor])
                      for factor in FACTORS},
        "by_split": {
            split: {str(factor): stats([case for case in cases
                                       if case["split"] == split and case["factor"] == factor])
                    for factor in FACTORS}
            for split in sorted({row["split"] for row, _, _, _ in eligible})
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "growth_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if cases:
        with (args.output_dir / "growth_cases.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(cases[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(cases)
    print(json.dumps({"n_eligible_questions": len(eligible),
                      "by_factor": {factor: {key: value for key, value in count.items()
                                              if key in ("n", "exact_crossing", "first_order_error",
                                                         "first_order_false_positive", "first_order_false_negative",
                                                         "general_unresolved_closed_as_inside",
                                                         "general_unresolved_closed_as_outside")}
                                    for factor, count in summary["by_factor"].items()}}, indent=2))


if __name__ == "__main__":
    main()
