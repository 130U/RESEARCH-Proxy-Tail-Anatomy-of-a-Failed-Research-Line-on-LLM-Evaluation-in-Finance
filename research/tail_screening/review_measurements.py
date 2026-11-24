"""Independent read-only recomputation of the saved measurement experiment.

Does not import the original analysis implementation. Enumerates all complete
candidate-score boundaries to find the minimum feasible 90% release set.
No model calls, networking, training, plotting, or result-file mutations.
"""
from itertools import combinations
import json
import math
from pathlib import Path

from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "research"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def ranks(path):
    value = read(path)
    assert not value["unrankable_ids"]
    flat = sum(value["ordered_groups"], [])
    assert len(flat) == len(set(flat))
    scores, start = {}, 1
    for group in value["ordered_groups"]:
        end = start + len(group) - 1
        scores.update((item, -(start + end)) for item in group)
        start = end + 1
    return scores


def rank_panel(base, model, panel, m=4):
    values = [ranks(base / f"rank_{model}_o{i}.json")
              for i in range(1 + (panel-1)*4, 1 + (panel-1)*4 + m)]
    assert all(set(x) == set(values[0]) for x in values)
    return {item: sum(x[item] for x in values) for item in values[0]}


def pair_panel(base, model, panel):
    choices, endpoints = {}, {}
    for orient in ("a", "b"):
        choices[orient], endpoints[orient] = {}, {}
        for batch in range(1, 5):
            inp = read(base / f"pair_panel{panel}_{orient}_batch{batch:02}.json")
            out = read(base / f"pair_{model}_p{panel}_{orient}_b{batch:02}.json")["preferences"]
            assert set(out) == {x["pair_id"] for x in inp["pairs"]}
            assert not set(choices[orient]) & set(out)
            for row in inp["pairs"]:
                vote = out[row["pair_id"]]
                assert vote in ("L", "R", "T")
                choices[orient][row["pair_id"]] = (None if vote == "T" else
                    row["left"] if vote == "L" else row["right"])
                endpoints[orient][row["pair_id"]] = row["left"], row["right"]
    assert len(choices["a"]) == len(choices["b"]) == 496
    scores = {item: 0 for pair in endpoints["a"].values() for item in pair}
    edges, disagree, opposite = {}, 0, 0
    for pair_id, (i, j) in endpoints["a"].items():
        assert endpoints["b"][pair_id] == (j, i)
        a, b = choices["a"][pair_id], choices["b"][pair_id]
        disagree += a != b
        opposite += a is not None and b is not None and a != b
        winner = a if a == b else None
        if winner:
            scores[winner] += 2
            edges[i, j] = 1 if winner == i else -1
        else:
            scores[i] += 1
            scores[j] += 1
            edges[i, j] = 0
    def edge(i, j):
        return edges[i, j] if (i, j) in edges else -edges[j, i]
    strict = cycles = 0
    for i, j, k in combinations(scores, 3):
        signs = [edge(i, j), edge(j, k), edge(k, i)]
        if 0 not in signs:
            strict += 1
            cycles += len(set(signs)) == 1
    return scores, (disagree, opposite, cycles, strict)


def metric(a, b, p, sign):
    n, k = len(a), math.floor(len(a) * p)
    assert set(a) == set(b)
    def same_budget(values):
        boundary = sorted((sign*x for x in values.values()), reverse=True)[k-1]
        return {item for item in values if sign*values[item] >= boundary}
    target, budget = same_budget(a), same_budget(b)
    required = math.ceil(9 * len(target) / 10)
    # Deliberately use exhaustive sets, rather than the original quantile shortcut.
    candidates = []
    for boundary in sorted({sign*x for x in b.values()}, reverse=True):
        selected = {item for item in b if sign*b[item] >= boundary}
        if len(target & selected) >= required:
            candidates.append(selected)
    selected = min(candidates, key=len)
    return {"A_actual_tail_n": len(target), "same_budget_B_selected_n": len(budget),
            "same_budget_overlap_n": len(target & budget),
            "required_recovered_A_n": required, "B_q90_selected_n": len(selected),
            "recovered_A_n": len(target & selected),
            "actual_recall": len(target & selected) / len(target),
            "same_budget_recall": len(target & budget) / len(target),
            "q90_over_nominal_p": len(selected) / (n*p),
            "A_tie_expansion_fraction": (len(target)-k)/k,
            "same_budget_B_tie_expansion_fraction": (len(budget)-k)/k}


def passed(row):
    return (row["same_budget_recall"] >= .8 and row["q90_over_nominal_p"] <= 1.5
            and row["A_tie_expansion_fraction"] <= .2
            and row["same_budget_B_tie_expansion_fraction"] <= .2)


def compare_published(a, b, published, ps):
    checked = []
    for tail, sign in (("upper", 1), ("lower", -1)):
        for p in ps:
            row = metric(a, b, p, sign)
            saved = next(x for x in published[tail] if x["p"] == p)
            for key, value in row.items():
                assert abs(saved[key] - value) < 1e-12, (tail, p, key, saved[key], value)
            checked.append({"tail": tail, "p": p, **row, "passed": passed(row)})
    return checked


def main():
    old = RESEARCH / "private/agent_tail_pilot/metadata.json"
    base1 = RESEARCH / "private/agent_tail_methods/stage1_n32"
    base2 = RESEARCH / "private/agent_tail_methods/stage2_n128_sol"
    family_sets = [{x["family_id"] for x in read(p)["mapping"]}
                   for p in (old, base1/"metadata.json", base2/"metadata.json")]
    assert list(map(len, family_sets)) == [128, 32, 128]
    assert all(not a & b for a, b in combinations(family_sets, 2))
    inputs = [{x["id"]: x["text"] for x in map(json.loads,
               (base2/f"rank_order{i}.jsonl").read_text(encoding="utf-8").splitlines())}
              for i in range(1, 9)]
    assert len(inputs[0]) == 128 and all(x == inputs[0] for x in inputs)
    assert (base2/"rank_instructions.txt").read_bytes() == (base1/"rank_instructions.txt").read_bytes()
    saved1 = read(RESEARCH / "tail_screening/methods_stage1_all.json")
    summary = {"stage1": [], "stage2": []}
    for method in ("pair", "rank"):
        for model in ("luna", "sol"):
            scores = []
            for panel in (1, 2):
                if method == "rank":
                    score = rank_panel(base1, model, panel)
                else:
                    score, counts = pair_panel(base1, model, panel)
                    panel_saved = saved1["methods"]["pair"]["panel_summaries"][f"{model}_p{panel}"]
                    assert counts == tuple(panel_saved[k] for k in (
                        "raw_swap_disagreement_count_including_T", "opposite_strict_preference_count",
                        "directed_triangle_cycles", "strict_three_edge_triangles"))
                scores.append(score)
            analysis = (saved1["methods"][method]["analysis"] if method == "pair" else
                        saved1["methods"][method]["prefix_analyses"]["m4"])
            rows = []
            for direction, (a, b) in enumerate((scores, scores[::-1]), 1):
                pub = analysis["comparisons"][f"{model}_p{direction}__to__{model}_p{3-direction}"]
                rows += compare_published(a, b, pub, (.125, .25))
            gate_rows = [r for r in rows if r["p"] == .25]
            assert all(r["passed"] for r in gate_rows) == (saved1["methods"][method]["gate"]["per_model"][model] == "PASS")
            summary["stage1"].append({"method": method, "model": model,
                "gate": all(r["passed"] for r in gate_rows), "matched_tail_rows": len(rows)})
    saved2 = read(RESEARCH / "tail_screening/validation_stage2.json")
    for m in (1, 2, 4):
        scores = [rank_panel(base2, "sol", panel, m) for panel in (1, 2)]
        ids = sorted(scores[0])
        rho = float(spearmanr([scores[0][i] for i in ids], [scores[1][i] for i in ids]).statistic)
        for direction, (a, b) in enumerate((scores, scores[::-1]), 1):
            name = f"panel{direction}_to_panel{3-direction}"
            pub = saved2["prefix_analyses"][f"m{m}"]["comparisons"][name]
            assert abs(rho - pub["midrank_Spearman_auxiliary"]) < 1e-12
            rows = compare_published(a, b, pub, (.05, .1, .2))
            if m == 4:
                summary["stage2"] += [{"direction": name, **r} for r in rows if r["p"] != .05]
    assert all(r["passed"] for r in summary["stage2"]) == (saved2["gate"]["status"] == "PASS")
    print(json.dumps({"all_independent_comparisons_match": True, **summary}, indent=2))


if __name__ == "__main__":
    main()
