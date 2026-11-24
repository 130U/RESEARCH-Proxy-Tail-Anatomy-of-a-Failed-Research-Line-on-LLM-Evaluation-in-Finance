"""Analyze four saved blind grouped rankings; no inference or model training.

Budget fixed before execution: CPU <=120 seconds, memory target <=512 MB.
No network, external API, dependency installation, bootstrap or alpha fitting.
Example: ../130U-FinLLM/.venv/Scripts/python.exe
research/tail_screening/analyze_agent_pilot.py --plot-deps ../tmp/tail_plot_deps
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys
import time


NAMES = ("luna_order1", "luna_order2", "sol_order1", "sol_order2")
P_GRID = (0.05, 0.1, 0.2)
CROSS = tuple((a, b) for a in ("sol_order1", "sol_order2")
              for b in ("luna_order1", "luna_order2"))
REPEATS = (("luna_order1", "luna_order2"), ("luna_order2", "luna_order1"),
           ("sol_order1", "sol_order2"), ("sol_order2", "sol_order1"))


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON object key")
        result[key] = value
    return result


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_object)


def validate_inputs(base):
    orders = []
    for name in ("input_order1.jsonl", "input_order2.jsonl"):
        rows = [json.loads(line, object_pairs_hook=strict_object)
                for line in (base / name).read_text(encoding="utf-8").splitlines()]
        if len(rows) != 128:
            raise ValueError("Blind input must contain exactly 128 rows")
        for row in rows:
            if (type(row) is not dict or set(row) != {"id", "text"} or
                    type(row["id"]) is not str or type(row["text"]) is not str or not row["text"]):
                raise ValueError("Invalid blind-input schema")
        identifiers = [row["id"] for row in rows]
        if len(set(identifiers)) != 128 or set(identifiers) != {f"P{i:04d}" for i in range(1, 129)}:
            raise ValueError("Input IDs duplicate, unknown or missing")
        orders.append(rows)
    if {r["id"]: r["text"] for r in orders[0]} != {r["id"]: r["text"] for r in orders[1]}:
        raise ValueError("Input orders do not contain identical ID/text pairs")
    if [r["id"] for r in orders[0]] == [r["id"] for r in orders[1]]:
        raise ValueError("Input orders unexpectedly identical")
    return set(r["id"] for r in orders[0])


def validate_ranking(value, expected):
    if type(value) is not dict or set(value) != {"ordered_groups", "unrankable_ids"}:
        raise ValueError("Ranking requires exactly ordered_groups and unrankable_ids")
    groups, unrankable = value["ordered_groups"], value["unrankable_ids"]
    if type(groups) is not list or type(unrankable) is not list:
        raise ValueError("Ranking fields must be lists")
    if any(type(group) is not list or not group for group in groups):
        raise ValueError("Ranking groups must be nonempty lists")
    flattened = [identifier for group in groups for identifier in group] + unrankable
    if any(type(identifier) is not str for identifier in flattened):
        raise ValueError("Ranking IDs must be strings")
    if len(flattened) != len(set(flattened)):
        raise ValueError("An ID occurs more than once, including ranked/unrankable overlap")
    if set(flattened) != expected:
        raise ValueError("Unknown or missing IDs in ranking output")
    return groups, unrankable


def group_summary(groups, unrankable=()):
    sizes = [len(group) for group in groups]
    tied = [size for size in sizes if size > 1]
    return {"total_ranked": sum(sizes), "unrankable": len(unrankable),
            "total_groups": len(sizes), "genuine_tie_groups_size_gt_1": len(tied),
            "maximum_tie_group_size": max(tied, default=0),
            "maximum_group_size": max(sizes, default=0),
            "group_size_counts": dict(sorted(Counter(sizes).items()))}


def scores_for(groups, ordered_ids, np):
    """After complete-case restriction, recompute midranks from retained groups."""
    position, scores = 1, {}
    for group in groups:
        middle = position + (len(group) - 1) / 2
        for identifier in group:
            scores[identifier] = -middle  # larger means more favorable
        position += len(group)
    return np.asarray([scores[identifier] for identifier in ordered_ids], dtype=float)


def tail_metrics(a, b, p, sign, np):
    aa, bb = sign * a, sign * b
    n = len(aa)
    nominal = math.floor(n * p)
    if nominal < 1:
        raise ValueError("No observations in nominal tail")
    a_threshold = np.sort(aa)[n - nominal]
    a_tail = aa >= a_threshold
    actual_a = int(a_tail.sum())
    required = (9 * actual_a + 9) // 10
    b_threshold = np.sort(bb[a_tail])[actual_a - required]
    b_tail = bb >= b_threshold
    selected_b = int(b_tail.sum())
    recovered = int(np.count_nonzero(a_tail & b_tail))
    strictly_recovered = int(np.count_nonzero(a_tail & (bb > b_threshold)))
    if recovered < required or strictly_recovered >= required:
        raise AssertionError("B cutoff is not the highest cutoff achieving 90% recall")
    same_b_threshold = np.sort(bb)[n - nominal]
    same_b = bb >= same_b_threshold
    same_b_n = int(same_b.sum())
    overlap = int(np.count_nonzero(a_tail & same_b))
    return {
        "p": p, "nominal_tail_n": nominal, "A_actual_tail_n": actual_a,
        "A_actual_fraction": actual_a / n,
        "required_recovered_A_n": required,
        "B_q90_selected_n": selected_b, "q90": selected_b / n,
        "q90_over_p": selected_b / n / p,
        "recovered_A_n": recovered, "actual_recall": recovered / actual_a,
        "A_boundary_tie_n": int(np.count_nonzero(aa == a_threshold)),
        "A_boundary_tie_expansion_n": actual_a - nominal,
        "A_boundary_tie_expansion_relative_to_nominal": (actual_a - nominal) / nominal,
        "B_q90_boundary_tie_n": int(np.count_nonzero(bb == b_threshold)),
        "B_q90_boundary_tie_in_A_n": int(np.count_nonzero(a_tail & (bb == b_threshold))),
        "B_q90_strictly_beyond_cutoff_n": int(np.count_nonzero(bb > b_threshold)),
        "B_q90_boundary_extra_beyond_one_n": int(np.count_nonzero(bb == b_threshold)) - 1,
        "same_nominal_budget_B_selected_n": same_b_n,
        "same_nominal_budget_B_actual_fraction": same_b_n / n,
        "same_nominal_budget_overlap_n": overlap,
        "same_nominal_budget_recall_of_A": overlap / actual_a,
        "same_nominal_budget_overlap_over_nominal_n": overlap / nominal,
        "same_nominal_budget_B_boundary_tie_n": int(np.count_nonzero(bb == same_b_threshold)),
        "same_nominal_budget_B_tie_expansion_n": same_b_n - nominal,
        "same_nominal_budget_B_tie_expansion_relative_to_nominal": (same_b_n - nominal) / nominal,
    }


def gaussian_curve(rho, norm, quad, brentq):
    if rho is None:
        return None
    result = []
    for p in P_GRID:
        if rho >= 1 - 1e-14:
            q = 0.9 * p
        elif rho <= -1 + 1e-14:
            q = 1 - 0.1 * p
        else:
            z, scale = norm.isf(p), math.sqrt(1 - rho * rho)

            def error(q):
                w = norm.isf(q)
                joint, _ = quad(lambda x: norm.pdf(x) * norm.sf((w - rho * x) / scale),
                                z, math.inf, epsabs=1e-11, epsrel=1e-9)
                return joint / p - 0.9

            q = float(brentq(error, 1e-12, 1 - 1e-12, xtol=1e-12))
        result.append({"p": p, "q90": q, "q90_over_p": q / p})
    return result


def pair_metrics(a, b, np, rankdata, norm, quad, brentq):
    n = len(a)
    ra, rb = rankdata(a, method="average"), rankdata(b, method="average")
    if np.std(ra) == 0 or np.std(rb) == 0:
        spearman, normal_rho = None, None
    else:
        spearman = float(np.corrcoef(ra, rb)[0, 1])
        za, zb = norm.ppf((ra - 0.5) / n), norm.ppf((rb - 0.5) / n)
        normal_rho = float(np.corrcoef(za, zb)[0, 1])
    return {"midrank_Spearman": spearman, "normal_score_rho": normal_rho,
            "upper": [tail_metrics(a, b, p, 1, np) for p in P_GRID],
            "lower": [tail_metrics(a, b, p, -1, np) for p in P_GRID],
            "Gaussian_normal_score_comparator": gaussian_curve(normal_rho, norm, quad, brentq)}


def pair_key(a, b):
    return a + "__to__" + b


def draw(result, output, variant, plt, np):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "pdf.fonttype": 42})
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), sharey=True)
    x = np.asarray(P_GRID) * 100
    for ax, tail in zip(axes, ("upper", "lower")):
        cross = np.asarray([[r["q90_over_p"] for r in result["pairs"][pair_key(a, b)][tail]]
                            for a, b in CROSS])
        ax.fill_between(x, cross.min(axis=0), cross.max(axis=0), color="#2D648D", alpha=.18,
                        label="Four Sol-to-Luna combinations: range")
        ax.plot(x, cross[0], color="#194E79", marker="o", linewidth=2,
                label="Sol 1 to Luna 1 (prespecified pair)")
        for model, color, marker in (("luna", "#B95A19", "s"), ("sol", "#2D7E55", "^")):
            for direction, style in (((1, 2), "--"), ((2, 1), ":")):
                rows = result["pairs"][pair_key(f"{model}_order{direction[0]}",
                                                f"{model}_order{direction[1]}")][tail]
                ax.plot(x, [r["q90_over_p"] for r in rows], color=color, linestyle=style,
                        marker=marker, markersize=4.5,
                        label=f"{model.title()} repeat {direction[0]} to {direction[1]}")
        ax.axhline(1.5, color="#888888", linestyle="-.", linewidth=.8)
        ax.set_xscale("log")
        ax.set_xticks([5, 10, 20], ["5 (tiny tail)", "10", "20"])
        ax.minorticks_off()
        ax.set_xlabel("Nominal reference tail fraction p (%)")
        ax.set_title(("Most favorable" if tail == "upper" else "Least favorable") + " tail")
        ax.grid(axis="y", color="#E5E5E5", linewidth=.6)
    axes[0].set_ylabel("Proxy fraction required for 90% recall / p")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False,
               bbox_to_anchor=(.5, .08), fontsize=8.2)
    n = result["complete_case_diagnostic"]["n"]
    population_label = ("post-hoc common rankable subset" if result["full_population_gate"]["unrankable_any_output"]
                        else "same 128-item development sample")
    fig.suptitle(f"Blind agent rankings {variant}: {population_label} (n = {n}/128)", fontsize=13)
    status = result["full_population_gate"]["status"]
    reason = "unrankable items" if result["full_population_gate"]["unrankable_any_output"] else "working thresholds"
    fig.text(.5, .022,
             f"Full 128-item gate: {status} ({reason}). Range = repeat/order sensitivity, not a confidence interval.\n"
             "All threshold ties retained; 5% tail contains only " + str(math.floor(n * .05)) +
             " nominal items. Horizontal line: 1.5 working threshold; no independent validation set.",
             ha="center", fontsize=8.3)
    fig.tight_layout(rect=(0, .23, 1, .94))
    fig.savefig(output / f"agent_widening_{variant}.png", dpi=190)
    fig.savefig(output / f"agent_widening_{variant}.pdf")
    plt.close(fig)


def main():
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot-deps", type=Path)
    parser.add_argument("--variant", choices=("v1", "v2"), default="v1")
    args = parser.parse_args()
    if args.plot_deps:
        sys.path.insert(0, str(args.plot_deps.resolve()))
    import numpy as np
    from scipy.stats import rankdata, norm
    from scipy.integrate import quad
    from scipy.optimize import brentq
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    root = Path(__file__).resolve().parents[2]
    base = root / "research/private/agent_tail_pilot"
    output = Path(__file__).resolve().parent
    expected = validate_inputs(base)
    suffix = "" if args.variant == "v1" else "_v2"
    rankings = {name: validate_ranking(load_json(base / (name + suffix + ".json")), expected) for name in NAMES}
    common = set(expected)
    for groups, unrankable in rankings.values():
        common.difference_update(unrankable)
    if len(common) < 20:
        raise RuntimeError("Insufficient common rankable cases for specified 5% diagnostic")
    ordered_ids = sorted(common)
    restricted = {name: [retained for group in groups if (retained := [i for i in group if i in common])]
                  for name, (groups, _) in rankings.items()}
    scores = {name: scores_for(groups, ordered_ids, np) for name, groups in restricted.items()}
    any_unrankable = any(unrankable for _, unrankable in rankings.values())
    result = {
        "design": "research/tail_screening/agent_pilot.md; saved grouped rankings, no new inference",
        "variant": args.variant,
        "variant_task": ("Financial favorability to the designated entity's equity holders" if args.variant == "v1"
                         else "Financial-context textual sentiment toward the designated entity; absence of direction is neutral, not automatically unrankable"),
        "development_status": "Both variants use the same 128-item development sample. V2 is a revised measurement task after V1 inspection, not a new validation set.",
        "budget": {"CPU_seconds": 120, "memory_MB_target": 512, "bootstrap": False,
                   "alpha_fitting": False, "training": False, "network": False, "external_API": False},
        "input_validation": {"n": 128, "same_ID_text_pairs": True, "different_input_orders": True,
                             "exact_ID_partition_each_output": True, "duplicate_unknown_missing_IDs": 0},
        "output_summaries_full_128": {name: group_summary(*value) for name, value in rankings.items()},
        "full_population_gate": {
            "status": "FAIL" if any_unrankable else "requires_remaining_stability_checks",
            "unrankable_any_output": any_unrankable,
            "four_output_comparison_status": "not_identifiable_on_all_128" if any_unrankable else "identifiable",
            "explanation": ("Unrankable items are neither assigned neutral ranks nor silently removed from the original population. Complete-case diagnostics cannot turn the prespecified full-population gate into a pass. Full-population comparisons involving an incomplete ranking are not identified; no full-population curve is reported here." if any_unrankable
                            else "All original IDs are rankable. The working gate uses the full 128-item development population and all specified same-model directions/tails at 10% and 20%; this is not an independently validated statistical test."),
        },
        "complete_case_diagnostic": {
            "n": len(common), "excluded_n": len(expected) - len(common),
            "population": ("Post-hoc intersection of IDs rankable in all four outputs; not the original prespecified 128-item population" if any_unrankable
                           else "All 128 original development items are rankable; common subset equals original finite population"),
            "post_hoc_complete_case_restriction": any_unrankable,
            "rank_recalculation": "Filter each ordered group to the common subset, drop empty groups, then recompute within-subset midranks",
            "output_summaries": {name: group_summary(groups) for name, groups in restricted.items()},
        },
        "metric_definitions": {
            "reference_and_proxy": "A defines target tail, B is the screening ordering; Sol is a reference, not truth",
            "nominal_tail": "floor(n*p); include every member of the boundary tie group",
            "q90": "Highest B threshold recovering ceil(0.9*A_actual_tail_n), retaining its entire boundary tie group",
            "widening": "q90 / nominal p, not divided by tie-expanded A fraction",
            "same_budget": "Both cutoffs use the same nominal floor(n*p), then retain their respective complete boundary groups; actual admitted counts can differ",
            "same_budget_recall": "Intersection size / actual A tail size; overlap/nominal is also shown and can exceed one due to ties",
            "boundary_expansion": "A and same-budget B: actual count minus nominal count. q90 B has no independent nominal budget, so report its cutoff tie size, strict count, and tie size minus one explicitly",
            "correlations": "Midrank Spearman; normal-score rho uses Phi^-1((average_rank-.5)/n) on the common subset",
            "Gaussian": "Optional symmetric Gaussian-copula numerical comparator using normal-score rho; no test or assertion that its model fits grouped rankings",
            "sensitivity_range": "Minimum/maximum across four cross-model combinations; not a confidence interval or independent replication",
            "small_tail": "5% is exploratory and tiny; formal working thresholds were specified for 10% and 20% only",
        },
        "p_grid": list(P_GRID), "primary_pair": pair_key("sol_order1", "luna_order1"),
        "pairs": {},
    }
    for a, b in CROSS + REPEATS:
        if time.process_time() - start_cpu > 120:
            raise RuntimeError("CPU budget exceeded")
        result["pairs"][pair_key(a, b)] = {
            "A": a, "B": b, "role": "cross_model" if (a, b) in CROSS else "same_model_repeat",
            "population": "post_hoc_common_rankable_subset" if any_unrankable else "original_128_development_items", "n": len(common),
            **pair_metrics(scores[a], scores[b], np, rankdata, norm, quad, brentq),
        }
    checks = []
    for a, b in REPEATS:
        for tail in ("upper", "lower"):
            for row in result["pairs"][pair_key(a, b)][tail]:
                if row["p"] == .05:
                    continue
                checks.append({"pair": pair_key(a, b), "tail": tail, "p": row["p"],
                               "overlap_at_least_0_8": row["same_nominal_budget_recall_of_A"] >= .8,
                               "q90_over_p_at_most_1_5": row["q90_over_p"] <= 1.5,
                               "A_tie_expansion_at_most_0_2": row["A_boundary_tie_expansion_relative_to_nominal"] <= .2,
                               "B_same_budget_tie_expansion_at_most_0_2": row["same_nominal_budget_B_tie_expansion_relative_to_nominal"] <= .2})
    result["same_model_complete_case_working_threshold_diagnostics"] = {
        "not_a_full_population_gate": any_unrankable, "checks": checks,
        "all_diagnostic_checks_satisfied": all(all(value for key, value in check.items()
                                                  if key not in ("pair", "tail", "p")) for check in checks),
    }
    diagnostic_ok = result["same_model_complete_case_working_threshold_diagnostics"]["all_diagnostic_checks_satisfied"]
    if not any_unrankable:
        result["full_population_gate"]["status"] = "PASS" if diagnostic_ok else "FAIL"
    result["full_population_gate"]["same_model_working_thresholds_satisfied"] = None if any_unrankable else diagnostic_ok
    result["cross_model_sensitivity_ranges"] = {
        tail: [{"p": p,
                "q90_over_p_min": min(result["pairs"][pair_key(a, b)][tail][i]["q90_over_p"] for a, b in CROSS),
                "q90_over_p_max": max(result["pairs"][pair_key(a, b)][tail][i]["q90_over_p"] for a, b in CROSS)}
               for i, p in enumerate(P_GRID)] for tail in ("upper", "lower")
    }
    draw(result, output, args.variant, plt, np)
    result["execution"] = {"wall_seconds": time.perf_counter() - start_wall,
                           "CPU_seconds": time.process_time() - start_cpu,
                           "memory_peak_measured": False}
    if result["execution"]["CPU_seconds"] > 120:
        raise RuntimeError("CPU budget exceeded; aggregate not published")
    (output / f"agent_pilot_results_{args.variant}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"full_summaries": result["output_summaries_full_128"],
                      "gate": result["full_population_gate"]["status"],
                      "common_n": len(common),
                      "cross_ranges": result["cross_model_sensitivity_ranges"],
                      "diagnostic_thresholds_all_satisfied": result["same_model_complete_case_working_threshold_diagnostics"]["all_diagnostic_checks_satisfied"],
                      "execution": result["execution"]}, indent=2))


if __name__ == "__main__":
    main()
