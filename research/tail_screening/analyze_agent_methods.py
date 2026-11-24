"""Direct analysis of saved stage-1 grouped rankings and 4x124 pair judgments.

Budget: CPU <=120 seconds; memory target <=512 MB. No model calls, network,
training, bootstrap or alpha estimation. Missing inputs stop before publication.
Run --self-check for artificial numerical checks only. Real runs support
--method pair/rank/all and --plot-deps ../tmp/tail_plot_deps.
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations
import json
import math
from pathlib import Path
import sys
import time

MODELS = ("luna", "sol")
PANELS = (1, 2)
P_GRID = (.125, .25)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON object key")
        result[key] = value
    return result


def parse(text):
    return json.loads(text, object_pairs_hook=unique_object)


def load(path):
    return parse(path.read_text(encoding="utf-8"))


def check_documents(rows, expected=None):
    if type(rows) is not list or len(rows) != 32:
        raise ValueError("Expected exactly 32 documents")
    for row in rows:
        if (type(row) is not dict or set(row) != {"id", "text"}
                or type(row["id"]) is not str or type(row["text"]) is not str or not row["text"]):
            raise ValueError("Invalid document schema")
    mapping = {row["id"]: row["text"] for row in rows}
    if set(mapping) != {f"S{i:04d}" for i in range(1, 33)}:
        raise ValueError("Document IDs duplicate, missing or unknown")
    if expected is not None and mapping != expected:
        raise ValueError("Documents differ between input files")
    return mapping


def check_rank(value, expected):
    if type(value) is not dict or set(value) != {"ordered_groups", "unrankable_ids"}:
        raise ValueError("Invalid ranking output schema")
    groups, unrankable = value["ordered_groups"], value["unrankable_ids"]
    if type(groups) is not list or type(unrankable) is not list:
        raise ValueError("Ranking fields must be lists")
    if any(type(group) is not list or not group for group in groups):
        raise ValueError("Empty or invalid ranking group")
    flat = [i for group in groups for i in group] + unrankable
    if any(type(i) is not str for i in flat) or len(flat) != len(set(flat)) or set(flat) != set(expected):
        raise ValueError("Ranking IDs duplicate, missing or unknown")
    return groups, unrankable


def check_preferences(value, expected):
    if type(value) is not dict or set(value) != {"preferences"} or type(value["preferences"]) is not dict:
        raise ValueError("Pair output requires exactly a preferences object")
    preferences = value["preferences"]
    if set(preferences) != set(expected):
        raise ValueError("Pair output has missing or unknown pair IDs")
    if any(type(v) is not str or v not in ("L", "R", "T", "U") for v in preferences.values()):
        raise ValueError("Pair judgment must be L, R, T or U")
    return preferences


def twice_midranks(groups):
    result, before = {}, 0
    for group in groups:
        twice_rank = 2 * before + len(group) + 1
        result.update((i, twice_rank) for i in group)
        before += len(group)
    return result


def borda_numerators(rankings, ids):
    n, m = len(ids), len(rankings)
    ranks = [twice_midranks(groups) for groups in rankings]
    if any(set(r) != set(ids) for r in ranks):
        raise ValueError("Cannot assign Borda scores to unrankable or missing items")
    sums = {i: sum(r[i] for r in ranks) for i in ids}
    scores = {i: 2 * m * n - sums[i] for i in ids}
    if sum(scores.values()) != m * n * (n - 1):
        raise AssertionError("Borda conservation failed")
    return scores, sums, 2 * m * (n - 1)


def aggregate_pairs(ids, inputs, preferences):
    """Inputs contain both orientations keyed by stable canonical pair ID."""
    ids = sorted(ids)
    halfwins = dict.fromkeys(ids, 0)
    edges, reasons = {}, Counter()
    comparable = disagree = opposite = both_strict = u_judgments = 0
    for pair_id, (left_a, right_a) in inputs["a"].items():
        left_b, right_b = inputs["b"][pair_id]
        if (left_b, right_b) != (right_a, left_a):
            raise ValueError("a/b inputs do not swap every pair exactly")
        first, second = sorted((left_a, right_a))
        values = []
        for orientation in ("a", "b"):
            judgment = preferences[orientation][pair_id]
            if judgment == "U":
                values.append(None)
                u_judgments += 1
            elif judgment == "T":
                values.append(0)
            else:
                endpoints = inputs[orientation][pair_id]
                preferred = endpoints[0 if judgment == "L" else 1]
                values.append(1 if preferred == first else -1)
        va, vb = values
        if va is None or vb is None:
            reasons["unrankable_any_orientation"] += 1
            merged = 0  # Explicit failed-measurement diagnostic, never a valid tie.
        else:
            comparable += 1
            disagree += va != vb
            both_strict += va != 0 and vb != 0
            opposite += va * vb == -1
            if va == vb and va != 0:
                reasons["consistent_strict"] += 1
                merged = va
            elif va == vb == 0:
                reasons["both_explicit_tie"] += 1
                merged = 0
            elif va * vb == -1:
                reasons["opposite_strict"] += 1
                merged = 0
            else:
                reasons["tie_vs_strict"] += 1
                merged = 0
        edges[first, second] = merged
        halfwins[first] += 1 + merged
        halfwins[second] += 1 - merged
    n = len(ids)
    if len(edges) != n * (n - 1) // 2 or sum(halfwins.values()) != n * (n - 1):
        raise AssertionError("Pair coverage or Copeland conservation failed")
    strict_triangles = cycles = 0
    for i, j, k in combinations(ids, 3):
        ij, ik, jk = edges[i, j], edges[i, k], edges[j, k]
        if ij and ik and jk:
            strict_triangles += 1
            cycles += ij == jk and ij == -ik
    total = len(edges)
    tie_count = total - reasons["consistent_strict"]
    summary = {
        "unordered_pairs": total, "raw_judgments": 2 * total,
        "unrankable_raw_judgments": u_judgments,
        "pairs_with_any_U": reasons["unrankable_any_orientation"],
        "comparable_pairs_excluding_U": comparable,
        "raw_swap_disagreement_count_including_T": disagree,
        "raw_swap_disagreement_rate_among_comparable": disagree / comparable if comparable else None,
        "raw_swap_disagreement_rate_all_pairs": disagree / total,
        "opposite_strict_preference_count": opposite,
        "opposite_strict_preference_rate_all_pairs": opposite / total,
        "both_orientations_strict_pairs": both_strict,
        "opposite_strict_preference_rate_among_both_strict": opposite / both_strict if both_strict else None,
        "merged_tie_edges": tie_count, "merged_tie_fraction": tie_count / total,
        "merged_zero_reasons": dict(reasons),
        "merged_zero_is_not_all_semantic_equivalence": True,
        "strict_three_edge_triangles": strict_triangles,
        "directed_triangle_cycles": cycles,
        "cycle_rate_among_all_strict_triangles": cycles / strict_triangles if strict_triangles else None,
        "integer_score": "twice wins + ties; denominator 2*(N-1)",
        "denominator": 2 * (n - 1),
        "diagnostic_only_due_to_U": bool(u_judgments),
    }
    return halfwins, summary


def score_summary(scores, denominator):
    histogram = Counter(scores.values())
    return {"n": len(scores), "integer_numerator_counts": dict(sorted(histogram.items())),
            "denominator": denominator, "distinct_scores": len(histogram),
            "tie_groups_size_gt_1": sum(count > 1 for count in histogram.values()),
            "largest_tie_group": max((count for count in histogram.values() if count > 1), default=0)}


def tail_metrics(a, b, p, sign):
    n = len(a)
    aa, bb = [sign * v for v in a], [sign * v for v in b]
    nominal = math.floor(n * p)
    if not nominal:
        raise ValueError("Empty nominal tail")
    threshold_a = sorted(aa)[n - nominal]
    indices_a = {i for i, value in enumerate(aa) if value >= threshold_a}
    actual_a = len(indices_a)
    required = (9 * actual_a + 9) // 10
    threshold_b = sorted(bb[i] for i in indices_a)[actual_a - required]
    selected_b = {i for i, value in enumerate(bb) if value >= threshold_b}
    recovered = len(indices_a & selected_b)
    if recovered < required or sum(bb[i] > threshold_b for i in indices_a) >= required:
        raise AssertionError("q90 threshold not minimal in complete-group boundaries")
    budget_b_threshold = sorted(bb)[n - nominal]
    budget_b = {i for i, value in enumerate(bb) if value >= budget_b_threshold}
    overlap = len(indices_a & budget_b)
    return {"p": p, "nominal_tail_n": nominal, "A_actual_tail_n": actual_a,
            "A_actual_fraction": actual_a / n, "required_recovered_A_n": required,
            "B_q90_selected_n": len(selected_b), "q90": len(selected_b) / n,
            "q90_over_nominal_p": len(selected_b) / n / p,
            "B_over_actual_A": len(selected_b) / actual_a,
            "recovered_A_n": recovered, "actual_recall": recovered / actual_a,
            "A_boundary_tie_n": aa.count(threshold_a),
            "A_tie_expansion_n": actual_a - nominal,
            "A_tie_expansion_fraction": (actual_a - nominal) / nominal,
            "B_q90_boundary_tie_n": bb.count(threshold_b),
            "B_q90_strictly_beyond_threshold_n": sum(v > threshold_b for v in bb),
            "same_budget_B_selected_n": len(budget_b),
            "same_budget_B_actual_fraction": len(budget_b) / n,
            "same_budget_overlap_n": overlap,
            "same_budget_recall": overlap / actual_a,
            "same_budget_B_boundary_tie_n": bb.count(budget_b_threshold),
            "same_budget_B_tie_expansion_n": len(budget_b) - nominal,
            "same_budget_B_tie_expansion_fraction": (len(budget_b) - nominal) / nominal}


def compare_panels(scores, np, rankdata, norm):
    pairs = [(f"sol_p{a}", f"luna_p{b}", "cross_model") for a in PANELS for b in PANELS]
    pairs += [(f"{model}_p{a}", f"{model}_p{b}", "self_repeat")
              for model in MODELS for a, b in ((1, 2), (2, 1))]
    comparisons = {}
    for a_name, b_name, role in pairs:
        if scores[a_name] is None or scores[b_name] is None:
            comparisons[a_name + "__to__" + b_name] = {"available": False, "reason": "unrankable rank output"}
            continue
        ids = sorted(scores[a_name])
        a, b = [scores[a_name][i] for i in ids], [scores[b_name][i] for i in ids]
        ra, rb = rankdata(a, method="average"), rankdata(b, method="average")
        if np.std(ra) == 0 or np.std(rb) == 0:
            rho = normal_rho = None
        else:
            rho = float(np.corrcoef(ra, rb)[0, 1])
            normal_rho = float(np.corrcoef(norm.ppf((ra - .5) / len(a)), norm.ppf((rb - .5) / len(b)))[0, 1])
        comparisons[a_name + "__to__" + b_name] = {
            "available": True, "A": a_name, "B": b_name, "role": role,
            "midrank_Spearman": rho, "normal_score_rho": normal_rho,
            "upper": [tail_metrics(a, b, p, 1) for p in P_GRID],
            "lower": [tail_metrics(a, b, p, -1) for p in P_GRID]}
    ranges = {}
    for tail in ("upper", "lower"):
        cross = [row for row in comparisons.values() if row.get("role") == "cross_model" and row["available"]]
        ranges[tail] = [{"p": p, "available_combinations": len(cross),
                         "minimum": min(row[tail][i]["q90_over_nominal_p"] for row in cross) if cross else None,
                         "maximum": max(row[tail][i]["q90_over_nominal_p"] for row in cross) if cross else None}
                        for i, p in enumerate(P_GRID)]
    return {"comparisons": comparisons, "cross_model_sensitivity_ranges_not_CI": ranges}


def gate(analysis, model_complete):
    complete = all(model_complete.values())
    checks = []
    for model in MODELS:
        for a, b in ((1, 2), (2, 1)):
            key = f"{model}_p{a}__to__{model}_p{b}"
            pair = analysis["comparisons"][key]
            for tail in ("upper", "lower"):
                if not pair["available"]:
                    checks.append({"model": model, "pair": key, "tail": tail, "available": False, "passed": False})
                    continue
                row = next(r for r in pair[tail] if r["p"] == .25)
                conditions = {"same_budget_recall_at_least_0_8": row["same_budget_recall"] >= .8,
                              "q90_over_nominal_p_at_most_1_5": row["q90_over_nominal_p"] <= 1.5,
                              "A_tie_expansion_at_most_0_2": row["A_tie_expansion_fraction"] <= .2,
                              "B_tie_expansion_at_most_0_2": row["same_budget_B_tie_expansion_fraction"] <= .2}
                checks.append({"model": model, "pair": key, "tail": tail, "p": .25,
                               "available": True, **conditions, "passed": all(conditions.values())})
    return {"status": "PASS" if complete and all(c["passed"] for c in checks) else "FAIL",
            "all_outputs_rankable": complete, "model_outputs_rankable": model_complete,
            "gate_p": .25, "checks": checks,
            "per_model": {m: "PASS" if model_complete[m] and all(c["passed"] for c in checks if c["model"] == m) else "FAIL" for m in MODELS},
            "meaning": "Prespecified finite-sample working gate, not a calibrated statistical test; no U may be hidden by diagnostic tie scores"}


def required_files(method):
    names = ["metadata.json", "rank_order1.jsonl"]
    if method in ("rank", "all"):
        names += [f"rank_order{o}.jsonl" for o in range(2, 9)]
        names += [f"rank_{model}_o{o}.json" for model in MODELS for o in range(1, 9)]
    if method in ("pair", "all"):
        names += [f"pair_panel{p}_{o}_batch{b:02d}.json" for p in PANELS for o in ("a", "b") for b in range(1, 5)]
        names += [f"pair_{m}_p{p}_{o}_b{b:02d}.json" for m in MODELS for p in PANELS for o in ("a", "b") for b in range(1, 5)]
    return names


def analyze_pair(base, documents, np, rankdata, norm):
    ids = sorted(documents)
    canonical = {f"E{i:04d}": pair for i, pair in enumerate(combinations(ids, 2), 1)}
    inputs, chunk_ids = {}, {}
    for panel in PANELS:
        inputs[panel] = {}
        for orientation in ("a", "b"):
            merged = {}
            for batch in range(1, 5):
                value = load(base / f"pair_panel{panel}_{orientation}_batch{batch:02d}.json")
                if type(value) is not dict or set(value) != {"documents", "pairs"}:
                    raise ValueError("Invalid pair input schema")
                check_documents(value["documents"], documents)
                rows = value["pairs"]
                if type(rows) is not list or len(rows) != 124:
                    raise ValueError("Every pair batch must contain 124 pairs")
                chunk = {}
                for row in rows:
                    if type(row) is not dict or set(row) != {"pair_id", "left", "right"}:
                        raise ValueError("Invalid pair-input row")
                    key, left, right = row["pair_id"], row["left"], row["right"]
                    if (any(type(v) is not str for v in (key, left, right)) or key not in canonical
                            or key in chunk or key in merged or tuple(sorted((left, right))) != canonical[key]):
                        raise ValueError("Invalid, repeated or mismatched pair-input ID")
                    chunk[key] = (left, right)
                merged.update(chunk)
                chunk_ids[panel, orientation, batch] = set(chunk)
            if set(merged) != set(canonical):
                raise ValueError("Four pair batches do not cover all 496 pairs")
            inputs[panel][orientation] = merged
        for batch in range(1, 5):
            if chunk_ids[panel, "a", batch] != chunk_ids[panel, "b", batch]:
                raise ValueError("a/b batch pair sets differ")
        if any(inputs[panel]["b"][key] != value[::-1] for key, value in inputs[panel]["a"].items()):
            raise ValueError("Panel orientations are not exact swaps")
    scores, summaries, raw_counts = {}, {}, {}
    for model in MODELS:
        for panel in PANELS:
            preferences = {}
            for orientation in ("a", "b"):
                merged = {}
                for batch in range(1, 5):
                    name = f"pair_{model}_p{panel}_{orientation}_b{batch:02d}.json"
                    values = check_preferences(load(base / name), chunk_ids[panel, orientation, batch])
                    if set(merged) & set(values):
                        raise ValueError("Duplicate pair across output chunks")
                    merged.update(values)
                    raw_counts[name] = dict(Counter(values.values()))
                preferences[orientation] = merged
            key = f"{model}_p{panel}"
            scores[key], summaries[key] = aggregate_pairs(ids, inputs[panel], preferences)
            summaries[key]["score_groups"] = score_summary(scores[key], 62)
    complete = {model: not any(summaries[f"{model}_p{panel}"]["unrankable_raw_judgments"] for panel in PANELS)
                for model in MODELS}
    comparison = compare_panels(scores, np, rankdata, norm)
    return {"method": "pair", "input_mode": "Four fixed 124-pair fresh batches per model/panel/orientation; original oversized 496-pair outputs are never read",
            "scoring_calls_in_analyzed_design": 32, "raw_judgments": 3968,
            "oversized_attempts_not_used": "Reported separately in the protocol; not scored here",
            "raw_output_value_counts": raw_counts, "panel_summaries": summaries,
            "U_rule": "Any U fails the full gate. U-affected merged edges enter diagnostic scores as zero with a separate failure count, never as a semantic tie assertion.",
            "analysis": comparison, "gate": gate(comparison, complete)}


def analyze_rank(base, documents, np, rankdata, norm):
    ids = sorted(documents)
    rankings, raw_summaries = {}, {}
    for order in range(1, 9):
        check_documents([parse(line) for line in (base / f"rank_order{order}.jsonl").read_text(encoding="utf-8").splitlines()], documents)
    for model in MODELS:
        for order in range(1, 9):
            name = f"rank_{model}_o{order}.json"
            groups, unrankable = check_rank(load(base / name), ids)
            rankings[model, order] = (groups, unrankable)
            sizes = [len(g) for g in groups]
            raw_summaries[name] = {"ranked": sum(sizes), "unrankable": len(unrankable),
                                   "groups": len(sizes), "tie_groups_size_gt_1": sum(s > 1 for s in sizes),
                                   "largest_tie_group": max((s for s in sizes if s > 1), default=0)}
    analyses = {}
    for m in (1, 2, 4):
        scores, summaries = {}, {}
        for model in MODELS:
            for panel in PANELS:
                orders = list(range(1 + (panel - 1) * 4, 1 + (panel - 1) * 4 + m))
                selected = [rankings[model, order] for order in orders]
                key = f"{model}_p{panel}"
                if any(unrankable for _, unrankable in selected):
                    scores[key] = None
                    summaries[key] = {"available": False, "orders": orders, "reason": "U: no complete Borda ranking imputed"}
                else:
                    scores[key], twice_rank_sums, denominator = borda_numerators([groups for groups, _ in selected], ids)
                    summaries[key] = {"available": True, "orders": orders,
                                      "twice_midrank_sum_counts": dict(sorted(Counter(twice_rank_sums.values()).items())),
                                      "score_groups": score_summary(scores[key], denominator)}
        analyses[f"m{m}"] = {"panel_summaries": summaries, **compare_panels(scores, np, rankdata, norm)}
    complete = {model: not any(rankings[model, order][1] for order in range(1, 9)) for model in MODELS}
    return {"method": "rank", "scoring_calls_in_analyzed_design": 16,
            "aggregation": "Exact integer 2*midrank sums; Borda numerator=2*m*N-sum, denominator=2*m*(N-1); all exact equalities retained",
            "raw_output_summaries": raw_summaries, "prefix_analyses": analyses,
            "gate_prefix": "m4", "gate": gate(analyses["m4"], complete)}


def self_check():
    checks = []
    ids = ["A", "B", "C"]
    inputs = {"a": {"1": ("A", "B"), "2": ("A", "C"), "3": ("B", "C")}}
    inputs["b"] = {key: value[::-1] for key, value in inputs["a"].items()}
    a = {"1": "L", "2": "R", "3": "L"}
    b = {"1": "R", "2": "L", "3": "R"}
    scores, summary = aggregate_pairs(ids, inputs, {"a": a, "b": b})
    assert scores == dict.fromkeys(ids, 2) and summary["directed_triangle_cycles"] == summary["strict_three_edge_triangles"] == 1
    assert summary["raw_swap_disagreement_count_including_T"] == 0
    checks.append("three-edge strict directed cycle has equal Copeland scores, not a transitive truth")
    scores, summary = aggregate_pairs(ids, inputs, {"a": a, "b": a})
    assert scores == dict.fromkeys(ids, 2) and summary["opposite_strict_preference_count"] == 3 and summary["strict_three_edge_triangles"] == 0
    checks.append("same displayed side after swapping means opposite item preferences")
    two = {"a": {"1": ("A", "B")}, "b": {"1": ("B", "A")}}
    _, summary = aggregate_pairs(["A", "B"], two, {"a": {"1": "T"}, "b": {"1": "L"}})
    assert summary["merged_zero_reasons"]["tie_vs_strict"] == 1 and summary["raw_swap_disagreement_count_including_T"] == 1
    _, summary = aggregate_pairs(["A", "B"], two, {"a": {"1": "U"}, "b": {"1": "L"}})
    assert summary["diagnostic_only_due_to_U"] and summary["pairs_with_any_U"] == 1 and summary["comparable_pairs_excluding_U"] == 0
    checks.append("explicit tie disagreement and U failure retain distinct identities")
    ids4 = ["A", "B", "C", "D"]
    assert twice_midranks([["A"], ["B", "C"], ["D"]]) == dict(zip(ids4, [2, 5, 5, 8]))
    scores, _, denominator = borda_numerators([[["A"], ["B", "C"], ["D"]]], ids4)
    assert scores == dict(zip(ids4, [6, 3, 3, 0])) and denominator == 6
    forward = [[i] for i in ids4]
    scores, _, denominator = borda_numerators([forward, forward[::-1]], ids4)
    assert scores == dict.fromkeys(ids4, 6) and denominator == 12
    checks.append("tied midranks and opposite rankings produce exact half-score Borda ties")
    row = tail_metrics([8, 7, 6, 5, 4, 3, 2, 1], [8, 6, 6, 5, 4, 3, 2, 1], .25, 1)
    assert row["B_q90_selected_n"] == 3 and row["same_budget_B_tie_expansion_fraction"] == .5 and row["q90_over_nominal_p"] == 1.5
    row = tail_metrics([8, 8, 8, 5, 4, 3, 2, 1], [8, 7, 6, 5, 4, 3, 2, 1], .25, 1)
    assert row["A_actual_tail_n"] == row["required_recovered_A_n"] == 3 and row["B_over_actual_A"] == 1
    checks.append("boundary ties expand nominal budgets and actual-vs-nominal ratios differ")
    for bad in ('{"preferences":{},"preferences":{}}',):
        try:
            parse(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("Duplicate JSON key accepted")
    try:
        check_rank({"ordered_groups": [["A", "A"]], "unrankable_ids": ["B"]}, ["A", "B"])
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate ranking ID accepted")
    checks.append("duplicate JSON keys and ranking IDs rejected")
    return checks


def plot_results(results, output, selection, plt, np):
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42})
    fig, axes = plt.subplots(len(results), 2, figsize=(11.8, 4.2 * len(results)), squeeze=False)
    for row_index, (method, result) in enumerate(results.items()):
        analysis = result["analysis"] if method == "pair" else result["prefix_analyses"]["m4"]
        for col, tail in enumerate(("upper", "lower")):
            ax = axes[row_index, col]
            cross = [v for v in analysis["comparisons"].values() if v.get("role") == "cross_model" and v["available"]]
            if len(cross) != 4:
                ax.text(.5, .5, "Complete comparison unavailable\n(unrankable output)", ha="center", va="center", transform=ax.transAxes)
            else:
                values = np.asarray([[r["q90_over_nominal_p"] for r in v[tail]] for v in cross])
                ax.fill_between([12.5, 25], values.min(axis=0), values.max(axis=0), color="#215E8B", alpha=.18, label="Four cross-model pairs: range")
                ax.plot([12.5, 25], values[0], "o-", color="#215E8B", label="Sol panel 1 to Luna panel 1")
            for model, color in (("luna", "#B65A20"), ("sol", "#32835B")):
                for a, b, style in ((1, 2, "--"), (2, 1, ":")):
                    v = analysis["comparisons"][f"{model}_p{a}__to__{model}_p{b}"]
                    if v["available"]:
                        ax.plot([12.5, 25], [r["q90_over_nominal_p"] for r in v[tail]], marker="s", linestyle=style, color=color, label=f"{model.title()} repeat {a} to {b}")
            ax.axhline(1.5, color="#888888", linestyle="-.", linewidth=.8)
            ax.set_xticks([12.5, 25], ["12.5 (4 items)", "25 (8 items; gate)"])
            ax.set_xlabel("Nominal reference tail fraction p (%)")
            ax.set_ylabel("q90 / nominal p")
            title = "Swap-consistent pair aggregation" if method == "pair" else "Four-ranking Borda aggregation"
            ax.set_title(f"{title}: {tail} tail\nWorking gate: {result['gate']['status']}")
            ax.grid(axis="y", color="#E5E5E5")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False, fontsize=8, bbox_to_anchor=(.5, .035))
    fig.suptitle("Stage 1: same 32 new items, repeated within-model measurements", fontsize=13)
    fig.text(.5, .012, "Ranges show combination sensitivity, not confidence intervals. Boundary ties retained. No bootstrap or tail-exponent fitting.", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .14 if len(results) == 1 else .09, 1, .94))
    fig.savefig(output / f"methods_stage1_{selection}.png", dpi=190)
    fig.savefig(output / f"methods_stage1_{selection}.pdf")
    plt.close(fig)


def write_report(result, output, selection):
    lines = ["# 32 new samples: stage results of the ranking methods", "", f"Scope of this analysis: `{selection}`. Only saved outputs were read; no model calls, training or network access.", "",
             "Every nominal tail includes all ties at the boundary. The gate uses nominal p=25%; the JSON also records the actual A count, the actual fraction and the B/A factor. 12.5% is only a diagnostic with a nominal four items.", ""]
    for method, values in result["methods"].items():
        lines += [f"## {method}", "", f"Full overall working gate: **{values['gate']['status']}**; all outputs judgeable: {values['gate']['all_outputs_rankable']}.", ""]
        for model, status in values["gate"]["per_model"].items():
            lines.append(f"- {model}, combined verdict over both directions and both tails: {status}.")
        lines += ["", "Work items not met:", ""]
        failures = [c for c in values["gate"]["checks"] if not c["passed"]]
        if not failures:
            lines.append("- All numerical work items are met; any U still separately blocks a full overall pass.")
        for check in failures:
            failed = [k for k, v in check.items() if (k.endswith("0_8") or k.endswith("1_5") or k.endswith("0_2")) and not v]
            lines.append(f"- {check['pair']}, {check['tail']}: " + (", ".join(failed) if check["available"] else "not computable, unrankable output present") + ".")
        if method == "pair":
            lines += ["", "| Model/panel | Swap disagreements/comparable pairs | Merged zero edges/496 | Strict three-edge cycles/strict triangles | U judgments |", "|---|---:|---:|---:|---:|"]
            for key, s in values["panel_summaries"].items():
                lines.append(f"| {key} | {s['raw_swap_disagreement_count_including_T']}/{s['comparable_pairs_excluding_U']} | {s['merged_tie_edges']}/496 | {s['directed_triangle_cycles']}/{s['strict_three_edge_triangles']} | {s['unrankable_raw_judgments']} |")
        else:
            lines += ["", "All prefix results for m=1, 2, 4 are kept in the JSON; only m=4 decides this method's gate, and the most favorable m was not picked."]
        lines.append("")
    lines += ["Combination ranges are not confidence intervals; judgments in the same batch share context, and repeated rankings do not add independent financial samples. If a pair U enters the zero-edge diagnostic, it always keeps its failure identity; a rank U is not filled in with a made-up complete rank.", "",
              f"Results: [methods_stage1_{selection}.json](methods_stage1_{selection}.json); [figure](methods_stage1_{selection}.png). Raw inputs/outputs are in `research/private/agent_tail_methods/stage1_n32/`.", "",
              f"Actual CPU {result['execution']['CPU_seconds']:.3f} s; wall {result['execution']['wall_seconds']:.3f} s; peak memory not measured.", ""]
    (output / "stage1_report.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", choices=("pair", "rank", "all"), default="all")
    parser.add_argument("--plot-deps", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    checks = self_check()
    if args.self_check:
        print(json.dumps({"artificial_checks_passed": len(checks), "checks": checks}))
        return 0
    start_cpu, start_wall = time.process_time(), time.perf_counter()
    root = Path(__file__).resolve().parents[2]
    base = root / "research/private/agent_tail_methods/stage1_n32"
    missing = [name for name in required_files(args.method) if not (base / name).is_file()]
    if missing:
        print(json.dumps({"status": "missing_inputs_no_results_written", "method": args.method, "missing": missing}, indent=2))
        return 2
    if args.plot_deps:
        sys.path.insert(0, str(args.plot_deps.resolve()))
    import numpy as np
    from scipy.stats import rankdata, norm
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    documents = check_documents([parse(line) for line in (base / "rank_order1.jsonl").read_text(encoding="utf-8").splitlines()])
    metadata = load(base / "metadata.json")
    if metadata["selected_samples"] != 32 or metadata["selected_families"] != 32 or metadata["excluded_family_intersection_n"] != 0:
        raise ValueError("Sampling metadata does not match fixed stage")
    methods = {}
    if args.method in ("pair", "all"):
        methods["pair"] = analyze_pair(base, documents, np, rankdata, norm)
    if args.method in ("rank", "all"):
        methods["rank"] = analyze_rank(base, documents, np, rankdata, norm)
    result = {"stage": "stage1_n32", "n": 32, "selection": args.method,
              "budget": {"CPU_seconds": 120, "memory_MB_target": 512},
              "strict_schema_ID_and_pair_coverage_checks": "passed",
              "artificial_numerical_checks_passed": len(checks),
              "metric_scope": "Finite fixed 32-item population; midrank correlations and tie-safe lists; not calibrated probabilities or tail limits",
              "gate_denominator": "q90 divided by nominal p, per methods_protocol; B_count/A_actual_count additionally reported",
              "same_budget_rule": "Both models use floor(N*p) cutoffs plus complete boundary groups; actual released counts can differ",
              "methods": methods}
    output = Path(__file__).resolve().parent
    plot_results(methods, output, args.method, plt, np)
    result["execution"] = {"CPU_seconds": time.process_time() - start_cpu,
                           "wall_seconds": time.perf_counter() - start_wall,
                           "peak_memory_measured": False, "model_calls": 0, "network_requests": 0}
    if result["execution"]["CPU_seconds"] > 120:
        raise RuntimeError("CPU budget exceeded; numerical results not published")
    (output / f"methods_stage1_{args.method}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    write_report(result, output, args.method)
    print(json.dumps({"status": "complete", "method": args.method,
                      "gates": {name: value["gate"]["status"] for name, value in methods.items()},
                      "execution": result["execution"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
