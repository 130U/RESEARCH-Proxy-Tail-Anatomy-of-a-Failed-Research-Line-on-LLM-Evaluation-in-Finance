"""Analyze a saved Sol-only fresh-set validation with two four-ranking panels.

Budget before execution: CPU <=120 seconds, memory target <=512 MB. No model,
training, network, external API, bootstrap, confidence interval or alpha fitting.
Defaults to stage2_n128_sol; --data-dir and --output-stem allow the same analysis
on a later fresh set. The nominal-p gate remains 10% and 20%, with 5% diagnostic.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
import sys
import time

sys.dont_write_bytecode = True
from analyze_agent_methods import (borda_numerators, check_rank, parse,
                                   score_summary, self_check, tail_metrics)

P_GRID = (.05, .1, .2)
GATE_P = (.1, .2)


def artificial_checks():
    checks = self_check()
    ordered = list(range(128))
    row = tail_metrics(ordered, ordered, .1, 1)
    assert row["nominal_tail_n"] == row["A_actual_tail_n"] == 12
    assert row["required_recovered_A_n"] == row["B_q90_selected_n"] == 11
    assert row["q90_over_nominal_p"] == 11 / 12.8
    assert row["B_over_actual_A"] == 11 / 12
    row = tail_metrics(ordered, ordered, .2, 1)
    assert row["nominal_tail_n"] == 25 and row["required_recovered_A_n"] == 23
    assert row["q90_over_nominal_p"] == 23 / 25.6
    tied = ordered[:-15] + [999] * 15
    row = tail_metrics(tied, ordered, .1, 1)
    assert row["A_actual_tail_n"] == 15 and row["A_tie_expansion_fraction"] == .25
    row = tail_metrics([1] * 128, ordered, .1, 1)
    assert row["A_actual_tail_n"] == 128 and row["required_recovered_A_n"] == 116
    checks.append("N128 floor/ceil arithmetic, nominal-p denominator, and boundary-tie expansion")
    scores, _, denominator = borda_numerators([[["first"], ["last"]]] * 4, ["first", "last"])
    assert scores["first"] == denominator and scores["last"] == 0
    checks.append("highest-positive-first groups map to higher exact Borda numerators")
    return checks


def input_documents(path):
    rows = [parse(line) for line in path.read_text(encoding="utf-8").splitlines()]
    if not rows:
        raise ValueError("Empty input")
    for row in rows:
        if (type(row) is not dict or set(row) != {"id", "text"}
                or type(row["id"]) is not str or type(row["text"]) is not str or not row["text"]):
            raise ValueError("Invalid blind input schema")
    mapping = {r["id"]: r["text"] for r in rows}
    if len(mapping) != len(rows):
        raise ValueError("Repeated input ID")
    return mapping


def compare(a, b, np, rankdata, norm):
    if a is None or b is None:
        return {"available": False, "reason": "Unrankable output; complete Borda ranks not imputed"}
    identifiers = sorted(a)
    if set(identifiers) != set(b):
        raise ValueError("Panels do not have the same IDs")
    aa, bb = [a[i] for i in identifiers], [b[i] for i in identifiers]
    ra, rb = rankdata(aa, method="average"), rankdata(bb, method="average")
    if np.std(ra) == 0 or np.std(rb) == 0:
        rho = normal_rho = None
    else:
        rho = float(np.corrcoef(ra, rb)[0, 1])
        normal_rho = float(np.corrcoef(norm.ppf((ra - .5) / len(aa)), norm.ppf((rb - .5) / len(bb)))[0, 1])
    return {"available": True, "midrank_Spearman_auxiliary": rho,
            "normal_score_rho_auxiliary": normal_rho,
            "upper": [tail_metrics(aa, bb, p, 1) for p in P_GRID],
            "lower": [tail_metrics(aa, bb, p, -1) for p in P_GRID]}


def working_gate(primary, no_u):
    checks = []
    for direction, comparison in primary["comparisons"].items():
        for tail in ("upper", "lower"):
            for p in GATE_P:
                if not comparison["available"]:
                    checks.append({"direction": direction, "tail": tail, "p": p,
                                   "available": False, "passed": False})
                    continue
                row = next(r for r in comparison[tail] if r["p"] == p)
                conditions = {"same_budget_recall_at_least_0_8": row["same_budget_recall"] >= .8,
                              "q90_over_nominal_p_at_most_1_5": row["q90_over_nominal_p"] <= 1.5,
                              "A_tie_expansion_at_most_0_2": row["A_tie_expansion_fraction"] <= .2,
                              "B_tie_expansion_at_most_0_2": row["same_budget_B_tie_expansion_fraction"] <= .2}
                checks.append({"direction": direction, "tail": tail, "p": p,
                               "available": True, **conditions, "passed": all(conditions.values())})
    return {"status": "PASS" if no_u and all(c["passed"] for c in checks) else "FAIL",
            "all_eight_outputs_rankable": no_u, "primary_prefix": "m4", "gate_p": list(GATE_P),
            "checks": checks,
            "scope": "Selected Sol-only four-ranking branch on a fresh finite sample; not a joint two-model pass or a calibrated statistical test"}


def plot(result, output, stem, plt):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "pdf.fonttype": 42})
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex="col", sharey="row")
    n = result["n"]
    for column, tail in enumerate(("upper", "lower")):
        for m, color in ((1, "#929292"), (2, "#C77A27"), (4, "#195F91")):
            for direction, style in (("panel1_to_panel2", "-"), ("panel2_to_panel1", "--")):
                comparison = result["prefix_analyses"][f"m{m}"]["comparisons"][direction]
                if not comparison["available"]:
                    continue
                for row_index, metric in enumerate(("q90_over_nominal_p", "same_budget_recall")):
                    axes[row_index, column].plot(
                        [p * 100 for p in P_GRID], [row[metric] for row in comparison[tail]],
                        color=color, linestyle=style, marker="o" if m == 4 else ".",
                        linewidth=2.2 if m == 4 else 1.1,
                        label=f"m={m}{' primary' if m == 4 else ''}, " +
                              ("1 to 2" if direction == "panel1_to_panel2" else "2 to 1"))
        axes[0, column].axhline(1.5, color="#666666", linestyle=":", linewidth=1)
        axes[1, column].axhline(.8, color="#666666", linestyle=":", linewidth=1)
        axes[0, column].text(.98, 1.5, "limit 1.5", transform=axes[0, column].get_yaxis_transform(),
                              ha="right", va="bottom", fontsize=8, color="#666666")
        axes[1, column].text(.98, .8, "minimum 0.80", transform=axes[1, column].get_yaxis_transform(),
                              ha="right", va="bottom", fontsize=8, color="#666666")
        for ax in axes[:, column]:
            ax.set_xscale("log")
            ax.set_xlim(4.5, 22)
            ax.set_xticks([5, 10, 20], [f"5\n(diagnostic; n={math.floor(.05*n)})",
                                       f"10\n(main; n={math.floor(.1*n)})",
                                       f"20\n(main; n={math.floor(.2*n)})"])
            ax.minorticks_off()
            ax.tick_params(axis="x", labelsize=9)
            ax.grid(axis="y", color="#E5E5E5", linewidth=.6)
        axes[1, column].set_ylim(-.035, 1.065)
        axes[1, column].set_xlabel("Nominal tail p (%) and floor(Np) items")
        axes[0, column].set_title(("Most positive" if tail == "upper" else "Most negative") + " textual sentiment")
        for check in result["gate"]["checks"]:
            if check["tail"] == tail and check["available"] and not check["same_budget_recall_at_least_0_8"]:
                comparison = result["prefix_analyses"]["m4"]["comparisons"][check["direction"]]
                row = next(r for r in comparison[tail] if r["p"] == check["p"])
                axes[1, column].scatter([check["p"] * 100], [row["same_budget_recall"]],
                                        s=75, facecolors="none", edgecolors="#9C5819", linewidths=1.4, zorder=6)
                axes[1, column].annotate(
                    f"Primary {'1 to 2' if check['direction'] == 'panel1_to_panel2' else '2 to 1'}: "
                    f"{row['same_budget_overlap_n']}/{row['A_actual_tail_n']}"
                    f" = {row['same_budget_recall']:.3f}\nbelow 0.80",
                    xy=(check["p"] * 100, row["same_budget_recall"]),
                    xytext=(.62, .38), textcoords="axes fraction", ha="center", fontsize=9,
                    arrowprops={"arrowstyle": "->", "color": "#9C5819", "linewidth": 1}, color="#754011")
    axes[0, 0].set_ylabel("Screening widening\nq90 / nominal p")
    axes[1, 0].set_ylabel("Same-budget recall")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False,
               fontsize=8.6, bbox_to_anchor=(.5, .062))
    failed = sum(not check["passed"] for check in result["gate"]["checks"])
    total = len(result["gate"]["checks"])
    status_text = (f"Only 1 of {total} main checks fails" if failed == 1 else
                   f"{failed} of {total} main checks fail" if failed else f"All {total} main checks pass")
    fig.suptitle(f"Sol-only fresh-sample validation (N={n}): {status_text}", fontsize=13)
    fig.text(.5, .015, "All boundary ties retained. Solid/dashed lines and their ranges show repeat-direction sensitivity, not confidence intervals.\n"
             "Primary decision uses m=4 at 10% and 20%; 5% is diagnostic. No bootstrap or tail-exponent fitting.",
             ha="center", fontsize=8.5)
    if not result["gate"]["all_eight_outputs_rankable"]:
        fig.text(.5, .9, "Unrankable items: missing complete comparisons are not imputed", ha="center", color="#9C2929", fontsize=9)
    fig.tight_layout(rect=(0, .155, 1, .94))
    fig.savefig(output / f"{stem}.png", dpi=190)
    fig.savefig(output / f"{stem}.pdf")
    plt.close(fig)


def write_report(result, output, stem):
    n = result["n"]
    lines = [f"# Sol four-ranking aggregation: validation on {n} new samples", "",
             f"Main result: **{result['gate']['status']}**. Applies only to the selected branch of Sol + four-run aggregation per panel; it does not mean the joint two-model gate passed.", "",
             f"The sample comes from {result['sample']['selected_families']} new lexical families, with an intersection of {result['sample']['excluded_family_intersection_n']} with the previously excluded families; the IDs and texts of the eight inputs are identical. The ranking instruction puts the most positive first, and the integer Borda gives higher scores accordingly. Lexical families do not guarantee fully independent events.", "",
             "The two panels use order1–4 and order5–8; the m=1, 2, 4 prefixes are all kept, and only m=4 is used for the main working gate. All eight outputs are strictly checked for each ID appearing exactly once, and U items are not filled in with ranks.", "",
             "## Raw outputs and exact aggregation", "", "| Output | Ranked | U | Groups | True tie groups | Largest tie group |", "|---|---:|---:|---:|---:|---:|"]
    for name, s in result["raw_output_summaries"].items():
        lines.append(f"| {name} | {s['ranked']} | {s['unrankable']} | {s['groups']} | {s['tie_groups_size_gt_1']} | {s['largest_tie_group']} |")
    lines += ["", "Borda computes integer numerators from sums of twice the midrank; identical integer numerators are kept as ties.", "",
              "## Item-by-item values for the main working gate", "", "| Direction | Tail | p | Nominal/A actual count | Needed for 90%/B pass-through count | Actual recall | Same-budget recall | q90/p | A/B boundary expansion | Passed |",
              "|---|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    primary = result["prefix_analyses"]["m4"]
    for check in result["gate"]["checks"]:
        if not check["available"]:
            lines.append(f"| {check['direction']} | {check['tail']} | {check['p']:.0%} | — | — | — | — | — | — | not computable because of U |")
            continue
        row = next(r for r in primary["comparisons"][check["direction"]][check["tail"]] if r["p"] == check["p"])
        lines.append(f"| {check['direction']} | {check['tail']} | {check['p']:.0%} | {row['nominal_tail_n']}/{row['A_actual_tail_n']} | {row['required_recovered_A_n']}/{row['B_q90_selected_n']} | {row['actual_recall']:.3f} | {row['same_budget_recall']:.3f} | {row['q90_over_nominal_p']:.3f} | {row['A_tie_expansion_fraction']:.1%}/{row['same_budget_B_tie_expansion_fraction']:.1%} | {'yes' if check['passed'] else 'no'} |")
    lines += ["", f"With N={n}, the nominal counts for p=10% and 20% are floor(Np)={math.floor(n*.1)} and {math.floor(n*.2)}. The main gate's widening factor is always the B pass-through count/(N×p), not changed to B/floor(Np); the JSON lists the actual B/A counts separately. 90% requires ceil(0.9×A actual count), so the actual recall of a finite list will be above 90%. The same-budget lists also each include their complete boundary groups, so the two actual counts can differ.", "",
              "The working thresholds require, in both directions and for both tails: same-budget recall ≥80%, q90/p≤1.5, nominal boundary-tie expansion of A and B ≤20%, and no U. This is a pre-set working gate, not a significance test.", "",
              "## Prefix sensitivity (not post-hoc selection)", "", "| m | midrank Spearman | Minimum same-budget recall over the main p | Maximum q90/p |", "|---:|---:|---:|---:|"]
    for m in (1, 2, 4):
        comparisons = result["prefix_analyses"][f"m{m}"]["comparisons"]
        rows = [r for c in comparisons.values() if c["available"] for tail in ("upper", "lower") for r in c[tail] if r["p"] in GATE_P]
        rho = comparisons["panel1_to_panel2"].get("midrank_Spearman_auxiliary")
        if rows:
            rho_text = f"{rho:.4f}" if rho is not None else "undefined"
            lines.append(f"| {m} | {rho_text} | {min(r['same_budget_recall'] for r in rows):.3f} | {max(r['q90_over_nominal_p'] for r in rows):.3f} |")
        else:
            lines.append(f"| {m} | not computable because of U | — | — |")
    lines += ["", "Spearman is auxiliary only. The 5% lists are diagnostic only; repeated calls do not increase the financial sample size, and the variation between the two directions is not a confidence interval; no bootstrap, alpha fitting or tail-limit inference was done.", "",
              f"[Full numbers]({stem}.json) · [Curves]({stem}.png) · [PDF]({stem}.pdf). Location of the raw blind outputs: `{result['data_directory']}`.", "",
              f"This read-only analysis: CPU {result['execution']['CPU_seconds']:.3f} s, wall {result['execution']['wall_seconds']:.3f} s; peak memory not measured. No model calls, training, external API or network.", ""]
    report_name = stem.removeprefix("validation_") + "_report.md"
    (output / report_name).write_text("\n".join(lines), encoding="utf-8")


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=root / "research/private/agent_tail_methods/stage2_n128_sol")
    parser.add_argument("--output-stem", default="validation_stage2")
    parser.add_argument("--plot-deps", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    checks = artificial_checks()
    if args.self_check:
        print(json.dumps({"artificial_checks_passed": len(checks), "checks": checks}))
        return 0
    start_cpu, start_wall = time.process_time(), time.perf_counter()
    base = args.data_dir.resolve()
    if not base.is_relative_to((root / "research/private/agent_tail_methods").resolve()):
        raise ValueError("Data directory must resolve inside the private agent-methods directory")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.output_stem):
        raise ValueError("Output stem must be a simple filename stem")
    required = ["metadata.json", "rank_instructions.txt"]
    required += [f"rank_order{i}.jsonl" for i in range(1, 9)]
    required += [f"rank_sol_o{i}.json" for i in range(1, 9)]
    missing = [name for name in required if not (base / name).is_file()]
    if missing:
        print(json.dumps({"status": "missing_inputs_no_results_written", "missing": missing}, indent=2))
        return 2
    metadata = parse((base / "metadata.json").read_text(encoding="utf-8"))
    documents = input_documents(base / "rank_order1.jsonl")
    n = len(documents)
    if n < 20 or metadata["selected_samples"] != n or metadata["selected_families"] != n or metadata["excluded_family_intersection_n"] != 0:
        raise ValueError("Sampling metadata does not match a fresh one-per-family input")
    mapping_ids = [row["blind_id"] for row in metadata["mapping"]]
    if len(mapping_ids) != n or len(set(mapping_ids)) != n or set(mapping_ids) != set(documents):
        raise ValueError("Private mapping and blind input IDs differ")
    if base.name == "stage2_n128_sol" and set(documents) != {f"V{i:04d}" for i in range(1, 129)}:
        raise ValueError("Stage-2 IDs must be exactly V0001..V0128")
    for order in range(2, 9):
        if input_documents(base / f"rank_order{order}.jsonl") != documents:
            raise ValueError("ID/text pairs differ between ranking inputs")
    instructions = (base / "rank_instructions.txt").read_text(encoding="utf-8")
    if "from most positive to most negative" not in instructions:
        raise ValueError("Instructions do not confirm highest-positive-first ordering")
    rankings, raw_summaries = {}, {}
    for order in range(1, 9):
        name = f"rank_sol_o{order}.json"
        groups, unrankable = check_rank(parse((base / name).read_text(encoding="utf-8")), documents)
        rankings[order] = (groups, unrankable)
        sizes = [len(g) for g in groups]
        raw_summaries[name] = {"ranked": sum(sizes), "unrankable": len(unrankable),
                               "groups": len(sizes), "tie_groups_size_gt_1": sum(s > 1 for s in sizes),
                               "largest_tie_group": max((s for s in sizes if s > 1), default=0)}
    if args.plot_deps:
        sys.path.insert(0, str(args.plot_deps.resolve()))
    import numpy as np
    from scipy.stats import rankdata, norm
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    analyses = {}
    for m in (1, 2, 4):
        scores, summaries = {}, {}
        for panel in (1, 2):
            orders = list(range(1 + (panel - 1) * 4, 1 + (panel - 1) * 4 + m))
            selected = [rankings[o] for o in orders]
            if any(unrankable for _, unrankable in selected):
                scores[panel] = None
                summaries[f"panel{panel}"] = {"available": False, "orders": orders, "reason": "Unrankable output; no imputed ranks"}
            else:
                scores[panel], rank_sums, denominator = borda_numerators([groups for groups, _ in selected], sorted(documents))
                summaries[f"panel{panel}"] = {"available": True, "orders": orders,
                                              "twice_midrank_sum_counts": dict(sorted(Counter(rank_sums.values()).items())),
                                              "score_groups": score_summary(scores[panel], denominator)}
        analyses[f"m{m}"] = {"panel_summaries": summaries,
                              "comparisons": {"panel1_to_panel2": compare(scores[1], scores[2], np, rankdata, norm),
                                              "panel2_to_panel1": compare(scores[2], scores[1], np, rankdata, norm)}}
    no_u = not any(unrankable for _, unrankable in rankings.values())
    result = {"method": "selected Sol-only four-ranking Borda validation", "n": n,
              "data_directory": base.relative_to(root).as_posix(),
              "sample": {key: metadata[key] for key in ("selected_samples", "selected_families", "excluded_family_intersection_n", "family_seed", "within_family_seed")},
              "input_validation": "Eight identical ID/text sets, expected metadata IDs, strict output partitions, positive-first instructions verified",
              "budget": {"CPU_seconds": 120, "memory_MB_target": 512},
              "artificial_numerical_checks_passed": len(checks),
              "p_grid": list(P_GRID), "primary_prefix": "m4",
              "aggregation": "Integer 2*midrank sums, exact Borda numerator 2*m*N-sum, denominator 2*m*(N-1); no numeric tie breaking",
              "metric_scope": "q90/nominal p is B_count/(N*p); actual B_count/A_actual_count also retained. ceil(.9*A_actual_count) governs integer recall. Same-budget lists each retain their full boundary ties.",
              "selection_scope": "Single model-method branch selected after stage 1; not a claim that both models passed stage 1",
              "raw_output_summaries": raw_summaries, "prefix_analyses": analyses,
              "gate": working_gate(analyses["m4"], no_u)}
    output = Path(__file__).resolve().parent
    plot(result, output, args.output_stem, plt)
    result["execution"] = {"CPU_seconds": time.process_time() - start_cpu,
                           "wall_seconds": time.perf_counter() - start_wall,
                           "peak_memory_measured": False, "model_calls": 0, "network_requests": 0}
    if result["execution"]["CPU_seconds"] > 120:
        raise RuntimeError("CPU budget exceeded; numerical results not published")
    (output / f"{args.output_stem}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    write_report(result, output, args.output_stem)
    print(json.dumps({"status": "complete", "n": n, "gate": result["gate"], "execution": result["execution"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
