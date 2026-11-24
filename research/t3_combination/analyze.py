"""Analyze T3's frozen atom/composition experiment; no model calls.

Run only after all raw calls are complete. Input: atoms.csv, items.csv,
schedule.json, raw/<call_id>.json. --self-test uses synthetic numbers only.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares, minimize_scalar

MODELS = ("additive", "average", "asymmetric", "prior_average")
TYPES = ("PN", "PP", "NN", "P0", "N0")
W_BOUNDS = (0.001, 0.999)
LAMBDA_BOUNDS = (0.05, 20.0)
SEED = 2026111623


def csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_scores(raw):
    """Accept a plain ID mapping or a scores list/mapping; reject duplicates."""
    payload = raw.get("scores", raw) if isinstance(raw, dict) else raw
    if isinstance(payload, dict):
        rows = list(payload.items())
    elif isinstance(payload, list):
        rows = [(row.get("item_id", row.get("id")), row.get("score"))
                for row in payload]
    else:
        raise ValueError("Raw score output must be a mapping or list")
    result = {}
    for item_id, score in rows:
        if not isinstance(item_id, str) or item_id in result:
            raise ValueError(f"Missing/duplicate item ID: {item_id}")
        if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 100:
            raise ValueError(f"Invalid integer score for {item_id}: {score}")
        result[item_id] = score
    return result


@dataclass
class Data:
    atom_ids: list
    polarity: np.ndarray
    item_ids: list
    kind: np.ndarray
    first: np.ndarray
    second: np.ndarray
    singles: np.ndarray
    pairs: np.ndarray
    pn_forward: np.ndarray
    pn_reverse: np.ndarray
    order_forward: np.ndarray
    order_reverse: np.ndarray
    score_rows: list
    call_count: int


def load_data(base):
    atoms, items = csv_rows(base / "atoms.csv"), csv_rows(base / "items.csv")
    atom_ids = [row["atom_id"] for row in atoms]
    polarity = np.array([row["polarity"] for row in atoms])
    if len(atom_ids) != 30 or len(set(atom_ids)) != 30 or any(np.sum(polarity == p) != 10 for p in ("P", "N", "0")):
        # Z is a permitted name for the predeclared neutral class.
        polarity = np.where(polarity == "Z", "0", polarity)
        if len(atom_ids) != 30 or len(set(atom_ids)) != 30 or any(np.sum(polarity == p) != 10 for p in ("P", "N", "0")):
            raise ValueError("Expected 10 P, 10 N, and 10 0/Z atoms")
    ai = {value: index for index, value in enumerate(atom_ids)}
    single_items = [row for row in items if row["kind"] == "single"]
    combined = [row for row in items if row["kind"] != "single"]
    if len(items) != 810 or len(single_items) != 30 or len(combined) != 780:
        raise ValueError("Expected 30 single and 780 combined items")
    ids = [row["item_id"] for row in items]
    if len(ids) != len(set(ids)) or {r["item_id"] for r in single_items} != set(atom_ids):
        raise ValueError("Item IDs must be unique and singles must use atom IDs")
    item_ids = [row["item_id"] for row in combined]
    pi = {value: index for index, value in enumerate(item_ids)}
    first = np.array([ai[row["first"]] for row in combined])
    second = np.array([ai[row["second"]] for row in combined])
    kind = np.array([row["kind"] for row in combined])
    for name, expected in zip(TYPES, (200, 90, 90, 200, 200)):
        if int(np.sum(kind == name)) != expected:
            raise ValueError(f"Incorrect count for {name}")
    mapping = {(int(a), int(b)): j for j, (a, b) in enumerate(zip(first, second))}
    if len(mapping) != 780 or any((b, a) not in mapping for a, b in mapping):
        raise ValueError("Every distinct pair must have exactly two orientations")
    if np.any(first == second):
        raise ValueError("Self-pairs are not part of the frozen design")
    for j, (a, b) in enumerate(zip(first, second)):
        values = {polarity[a], polarity[b]}
        expected = ("PN" if values == {"P", "N"} else
                    "P0" if values == {"P", "0"} else
                    "N0" if values == {"N", "0"} else polarity[a] * 2)
        if kind[j] != expected:
            raise ValueError(f"Wrong pair kind for {item_ids[j]}")
    schedule = json.loads((base / "schedule.json").read_text(encoding="utf-8-sig"))
    if isinstance(schedule, dict):
        schedule = schedule["calls"]
    if len(schedule) != 88 or len({row["call_id"] for row in schedule}) != 88:
        raise ValueError("Expected 88 distinct planned calls")
    singles = np.full((30, 8), np.nan)
    pairs = np.full((780, 4), np.nan)
    rows = []
    for call in schedule:
        cid, round_no = call["call_id"], int(call["round"])
        scores = parse_scores(json.loads((base / "raw" / f"{cid}.json").read_text(encoding="utf-8-sig")))
        if set(scores) != set(call["item_ids"]) or len(call["item_ids"]) != len(scores):
            raise ValueError(f"Raw output differs from scheduled IDs: {cid}")
        for item_id, score in scores.items():
            arr, row_index = (singles, ai[item_id]) if item_id in ai else (pairs, pi[item_id])
            if not 1 <= round_no <= arr.shape[1] or np.isfinite(arr[row_index, round_no - 1]):
                raise ValueError(f"Duplicate or invalid round: {cid}/{item_id}")
            arr[row_index, round_no - 1] = score
            rows.append({"round": round_no, "item_id": item_id, "score": score, "call_id": cid})
    if len(rows) != 3360 or not np.isfinite(singles).all() or not np.isfinite(pairs).all():
        raise ValueError("Scoring is incomplete: require 240 single and 3120 combined scores")
    forward = np.array([j for j in range(780) if kind[j] == "PN" and polarity[first[j]] == "P"])
    reverse = np.array([mapping[(int(second[j]), int(first[j]))] for j in forward])
    all_forward = np.flatnonzero(first < second)
    all_reverse = np.array([mapping[(int(second[j]), int(first[j]))] for j in all_forward])
    return Data(atom_ids, polarity, item_ids, kind, first, second,
                singles - 50, pairs - 50, forward, reverse,
                all_forward, all_reverse, rows, len(schedule))


def predict(model, pars, x1, x2, neg1, neg2):
    if model == "additive":
        return np.clip(x1 + x2, -50, 50)
    if model == "prior_average":
        return np.clip(pars["k"] * (x1 + x2), -50, 50)
    w = pars["w"]
    if model == "average":
        return w * x1 + (1 - w) * x2
    r1, r2 = np.where(neg1, pars["lambda"], 1.0), np.where(neg2, pars["lambda"], 1.0)
    return (w * r1 * x1 + (1 - w) * r2 * x2) / (w * r1 + (1 - w) * r2)


def fit(model, x1, x2, neg1, neg2, y, weights=None):
    weights = np.ones(len(y)) if weights is None else np.asarray(weights)
    active = weights > 0
    x1, x2, neg1, neg2, y, weights = [v[active] for v in (x1, x2, neg1, neg2, y, weights)]
    if not len(y):
        raise ValueError("Fit has no positively weighted observations")
    if model == "additive":
        return {}
    delta = x1 - x2
    denom = np.dot(weights, delta * delta)
    w = np.clip(np.dot(weights * delta, y - x2) / denom if denom else 0.5, *W_BOUNDS)
    if model == "average":
        return {"w": float(w)}
    if model == "prior_average":
        objective = lambda k: float(np.average((np.clip(k * (x1 + x2), -50, 50) - y) ** 2, weights=weights))
        grid = np.linspace(0.5, 1, 101)
        best = int(np.argmin([objective(k) for k in grid]))
        left, right = grid[max(0, best - 1)], grid[min(100, best + 1)]
        opt = minimize_scalar(objective, bounds=(left, right), method="bounded")
        candidates = (0.5, 1.0, float(opt.x))
        return {"k": float(min(candidates, key=objective))}
    sqrt_w = np.sqrt(weights / weights.mean())
    def residual(par):
        return sqrt_w * (predict("asymmetric", {"w": par[0], "lambda": np.exp(par[1])}, x1, x2, neg1, neg2) - y)
    starts = ((float(w), 0.0), (0.5, -0.7), (0.5, 0.7))
    lower = (W_BOUNDS[0], np.log(LAMBDA_BOUNDS[0]))
    upper = (W_BOUNDS[1], np.log(LAMBDA_BOUNDS[1]))
    results = [least_squares(residual, start, bounds=(lower, upper), max_nfev=200,
                             ftol=1e-9, xtol=1e-9, gtol=1e-9) for start in starts]
    ok = [r for r in results if r.success and np.isfinite(r.cost)]
    if not ok:
        raise RuntimeError("Asymmetric optimization failed from all initializations")
    ans = min(ok, key=lambda r: r.cost)
    return {"w": float(ans.x[0]), "lambda": float(np.exp(ans.x[1]))}


def features(data, baseline):
    return (baseline[data.first], baseline[data.second],
            data.polarity[data.first] == "N", data.polarity[data.second] == "N")


def losses(y, prediction, mask, weights=None):
    error = prediction[mask] - y[mask]
    weights = None if weights is None else weights[mask]
    return {"rmse": float(np.sqrt(np.average(error ** 2, weights=weights))),
            "mae": float(np.average(np.abs(error), weights=weights))}


def cross_validate(data, baseline, y):
    """Each pair's two held-atom losses get equal total weight, not two samples."""
    x = features(data, baseline)
    result = {}
    for model in MODELS:
        squared, absolute, prediction_sum, count = [np.zeros(len(y)) for _ in range(4)]
        for a in range(len(data.atom_ids)):
            test = (data.first == a) | (data.second == a)
            train = ~test
            pars = fit(model, *(value[train] for value in x), y[train])
            pred = predict(model, pars, *(value[test] for value in x))
            err = pred - y[test]
            squared[test] += err ** 2
            absolute[test] += np.abs(err)
            prediction_sum[test] += pred
            count[test] += 1
        if not np.all(count == 2):
            raise AssertionError("Every pair must be predicted in exactly two folds")
        table = {}
        for name in ("all", *TYPES):
            mask = np.ones(len(y), dtype=bool) if name == "all" else data.kind == name
            table[name] = {"rmse": float(np.sqrt(np.mean(squared[mask] / count[mask]))),
                           "mae": float(np.mean(absolute[mask] / count[mask]))}
        result[model] = table
    return result


def diagnostics(data, baseline, y, weights):
    x1, x2, _, _ = features(data, baseline)
    neutral = np.isin(data.kind, ("P0", "N0"))
    signal = np.where(data.polarity[data.first] == "0", x2, x1)
    contraction = np.sign(signal) * (signal - y)
    adjusted = np.sign(signal) * (np.clip(x1 + x2, -50, 50) - y)
    result = {}
    for name, mask in (("neutral", neutral), ("P0", data.kind == "P0"), ("N0", data.kind == "N0")):
        result[name + "_contraction"] = float(np.average(contraction[mask], weights=weights[mask]))
        result[name + "_additive_adjusted"] = float(np.average(adjusted[mask], weights=weights[mask]))
    fw, rv = data.pn_forward, data.pn_reverse
    result["PN_order_positive_first_minus_negative_first"] = float(np.average(y[fw] - y[rv], weights=weights[fw]))
    fw, rv = data.order_forward, data.order_reverse
    result["all_pairs_absolute_order_difference"] = float(np.average(np.abs(y[fw] - y[rv]), weights=weights[fw]))
    for name, sign in (("PP", 1), ("NN", -1)):
        mask = data.kind == name
        stronger = np.maximum(sign * x1, sign * x2)
        excess = sign * y - stronger
        result[name + "_beyond_stronger_fraction"] = float(np.average(excess[mask] > 0, weights=weights[mask]))
        between = (y >= np.minimum(x1, x2)) & (y <= np.maximum(x1, x2))
        result[name + "_between_singles_fraction"] = float(np.average(between[mask], weights=weights[mask]))
        result[name + "_excess_points"] = float(np.average(excess[mask], weights=weights[mask]))
    result["additive_saturation_fraction"] = float(np.average(np.abs(x1 + x2) > 50, weights=weights))
    return result


def estimate(data, baseline, y, weights=None):
    weights = np.ones(len(y)) if weights is None else weights
    x = features(data, baseline)
    fits, table, flat = {}, {}, diagnostics(data, baseline, y, weights)
    for model in MODELS:
        fits[model] = fit(model, *x, y, weights)
        pred = predict(model, fits[model], *x)
        table[model] = {name: losses(y, pred, np.ones(len(y), dtype=bool) if name == "all" else data.kind == name, weights)
                        for name in ("all", *TYPES)}
        for key, value in fits[model].items():
            flat[model + "_" + key] = value
        flat[model + "_rmse"] = table[model]["all"]["rmse"]
    flat["average_rmse_improvement"] = flat["additive_rmse"] - flat["average_rmse"]
    return fits, table, flat


def bootstrap(data, count, seed, resample_atoms):
    rng = np.random.default_rng(seed)
    output = []
    for _ in range(count):
        multiplicity = np.ones(30)
        if resample_atoms:
            for polarity in ("P", "N", "0"):
                mask = data.polarity == polarity
                multiplicity[mask] = rng.multinomial(10, np.full(10, 0.1))
        weights = multiplicity[data.first] * multiplicity[data.second]
        # One shared draw per stage preserves observed within-round dependence.
        baseline = data.singles[:, rng.integers(0, 8, 8)].mean(axis=1)
        y = data.pairs[:, rng.integers(0, 4, 4)].mean(axis=1)
        _, _, flat = estimate(data, baseline, y, weights)
        output.append(flat)
    return {key: [float(v) for v in np.percentile([row[key] for row in output], (2.5, 97.5))]
            for key in output[0]}, output


def boundary(pars):
    return {"w": bool(abs(pars["w"] - W_BOUNDS[0]) < 1e-4 or abs(pars["w"] - W_BOUNDS[1]) < 1e-4),
            "lambda": bool(abs(pars["lambda"] - LAMBDA_BOUNDS[0]) < 1e-3 or abs(pars["lambda"] - LAMBDA_BOUNDS[1]) < 1e-3)}


def decision(flat, ci, cv):
    lam = ci["asymmetric_lambda"]
    order = ci["PN_order_positive_first_minus_negative_first"]
    cv_gain = cv["additive"]["all"]["rmse"] - cv["average"]["all"]["rmse"]
    gates = {
        "lambda_interval_excludes_one": bool(lam[0] > 1 or lam[1] < 1),
        "PN_order_at_least_two_and_interval_excludes_zero": bool(abs(flat["PN_order_positive_first_minus_negative_first"]) >= 2 and (order[0] > 0 or order[1] < 0)),
        "averaging_improves_full_and_cv_by_two_with_neutral_contraction": bool(flat["average_rmse_improvement"] >= 2 and cv_gain >= 2 and ci["neutral_contraction"][0] > 0),
    }
    return {"verdict": "continue" if any(gates.values()) else "stop", "gates": gates,
            "average_cv_rmse_improvement": float(cv_gain)}


def draw_figure(base, data, baseline, y, fits, table, cv, flat, ci):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    fig, axes = plt.subplots(2, 3, figsize=(13.5, 8.3), constrained_layout=True)
    colors = ("#6e7781", "#20807e", "#c16b31", "#7554a3")
    x = np.arange(4)
    axes[0, 0].bar(x - .18, [table[m]["all"]["rmse"] for m in MODELS], .36, label="Full fit", color=colors, alpha=.5)
    axes[0, 0].bar(x + .18, [cv[m]["all"]["rmse"] for m in MODELS], .36, label="Held-atom CV", color=colors)
    axes[0, 0].set_xticks(x, ["Add", "Average", "Asym.", "Prior avg."])
    axes[0, 0].set(title="Prediction error", ylabel="RMSE (score points)")
    axes[0, 0].legend(frameon=False)
    for model, color in zip(MODELS, colors):
        axes[0, 1].plot(TYPES, [cv[model][k]["rmse"] for k in TYPES], "o-", color=color, label=model)
    axes[0, 1].set(title="Held-atom CV by pair type", ylabel="RMSE (score points)")
    axes[0, 1].legend(frameon=False, fontsize=7)
    d1, d2, _, _ = features(data, baseline)
    for kind, color in (("P0", "#20807e"), ("N0", "#c16b31")):
        mask = data.kind == kind
        signal = np.where(data.polarity[data.first] == "0", d2, d1)
        axes[0, 2].scatter(signal[mask] + 50, y[mask] + 50, s=9, alpha=.45, color=color, label=kind)
    axes[0, 2].plot([0, 100], [0, 100], "--", color="gray", lw=1, label="No change")
    axes[0, 2].set(title="Adding a neutral fact", xlabel="Single fact score", ylabel="Combined score", xlim=(0, 100), ylim=(0, 100))
    axes[0, 2].legend(frameon=False, fontsize=7)
    fw, rv = data.pn_forward, data.pn_reverse
    axes[1, 0].scatter(y[rv] + 50, y[fw] + 50, color="#20807e", s=18, alpha=.6)
    axes[1, 0].plot([0, 100], [0, 100], "--", color="gray", lw=1)
    axes[1, 0].set(title="Order reversal: same mixed pair", xlabel="Negative first", ylabel="Positive first", xlim=(0, 100), ylim=(0, 100))
    for kind, sign, color in (("PP", 1, "#20807e"), ("NN", -1, "#c16b31")):
        mask = data.kind == kind
        axes[1, 1].scatter(np.maximum(sign * d1[mask], sign * d2[mask]), sign * y[mask], s=12, alpha=.5, color=color, label=kind)
    axes[1, 1].plot([0, 50], [0, 50], "--", color="gray", lw=1)
    axes[1, 1].set(title="Same-sign combination", xlabel="Stronger single: directed deviation", ylabel="Pair: directed deviation", xlim=(0, 50), ylim=(0, 50))
    axes[1, 1].legend(frameon=False)
    axes[1, 2].axis("off")
    keys = (("asymmetric_lambda", "Lambda (asymmetric-average fit)"), ("asymmetric_w", "First-position weight w"),
            ("prior_average_k", "Prior-average k (diagnostic)"), ("neutral_contraction", "Neutral contraction, points"),
            ("PN_order_positive_first_minus_negative_first", "PN order difference, points"))
    lines = ["Point estimate [95% bootstrap interval]", ""]
    for key, label in keys:
        lines.extend((label, f"  {flat[key]:.3f} [{ci[key][0]:.3f}, {ci[key][1]:.3f}]", ""))
    lines.append("30 hand-written atoms; 780 ordered pairs")
    lines.append("Intervals: atom-strata + shared score rounds")
    lines.append("Lambda is conditional on the fitted model")
    axes[1, 2].text(0, 1, "\n".join(lines), va="top", fontsize=10)
    fig.suptitle("T3: How financial sentiment scores combine two facts", fontsize=15)
    for ext in ("png", "pdf"):
        fig.savefig(base / f"combination.{ext}", dpi=180)
    plt.close(fig)


def write_report(base, result):
    flat, ci, cv = result["estimates"], result["bootstrap_95"], result["cv"]
    interval = lambda key: f"{flat[key]:.3f} [{ci[key][0]:.3f}, {ci[key][1]:.3f}]"
    verdict = "continue behavioural validation" if result["decision"]["verdict"] == "continue" else "drop this empirical line"
    lines = ["# T3: combined scoring of two messages", "", f"**Pre-registered decision: {verdict}.** Completed 88 calls and 3,360 valid scores: 30 single facts 8 times each, 780 ordered combinations 4 times each.", "",
             "| Model | Full-sample RMSE | Leave-one-atom-out RMSE | Full-sample MAE | Held-out MAE |", "|---|---:|---:|---:|---:|"]
    for model in MODELS:
        full = result["full_fit"][model]["all"]
        held = cv[model]["all"]
        lines.append(f"| {model} | {full['rmse']:.3f} | {held['rmse']:.3f} | {full['mae']:.3f} | {held['mae']:.3f} |")
    if cv["asymmetric"]["all"]["rmse"] > cv["additive"]["all"]["rmse"]:
        lines += ["", "**Interpretation warning: the asymmetric average model that estimates λ has a larger hold-out error than the additive model. The λ interval excluding 1 only triggers the pre-registered screening gate; it cannot be used to conclude that the real integration mechanism has a corresponding negative weight. Model misspecification should be ruled out first; the coefficient cannot be treated directly as a multiplier of the influence of bad news.**"]
    lines += ["", f"The main intervals are percentile 95% intervals from {result['bootstrap_replicates']:,} resamples of stratified atom weights + shared scoring rounds; their interpretation is limited by the fixed hand-made item bank. The number of replicates and the seeds are in results.json.", "",
              f"- Negative combination weight λ: {interval('asymmetric_lambda')}; first-position weight w: {interval('asymmetric_w')}.",
              f"- Directional shrinkage from adding a neutral fact: {interval('neutral_contraction')} points; additive residual after subtracting the actual neutral baseline: {interval('neutral_additive_adjusted')} points.",
              f"- Positive first minus negative first: {interval('PN_order_positive_first_minus_negative_first')} points.",
              f"- Absolute order difference over all combinations: {interval('all_pairs_absolute_order_difference')} points.",
              f"- Fraction of same-direction combinations beyond the stronger single item: PP {flat['PP_beyond_stronger_fraction']:.1%}, NN {flat['NN_beyond_stronger_fraction']:.1%}; corresponding mean excess {flat['PP_excess_points']:.3f}, {flat['NN_excess_points']:.3f} points.",
              f"- Fraction of same-direction combinations lying between the two single scores (endpoints included): PP {flat['PP_between_singles_fraction']:.1%}, NN {flat['NN_between_singles_fraction']:.1%}.",
              f"- Fraction of additive predictions that hit endpoint truncation: {flat['additive_saturation_fraction']:.1%}; prior-average diagnostic k: {interval('prior_average_k')}.", "",
              f"Gate-by-gate results: {json.dumps(result['decision']['gates'], ensure_ascii=False)}. Optimisation boundary: {json.dumps(result['asymmetric_boundary'], ensure_ascii=False)}. When a boundary is hit the binary decision is kept, but the magnitude of λ or w is not yet sufficiently identified.", "",
              "The hold-out analysis still uses the held-out atom's single-item calibration score; the two hold-out losses of each combination are averaged first and cannot be treated as two independent observations. Cross-validation has no bootstrap intervals. Sensitivity intervals for the fixed item bank, resampling only scoring rounds, are stored separately in results.json.", "",
              "These results describe the output behaviour of a fixed model, prompt and 0–100 scale. λ is a combination weight beyond the single-item baseline and cannot be interpreted as the whole negativity bias; averaging or dilution phenomena alone cannot prove an internal mechanism, financial correctness, economic loss or novelty.", "",
              "[Figure](combination.png) · [Full metrics](results.json) · [Raw scores](scores.csv) · [Analysis code](analyze.py)"]
    (base / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def self_test():
    a = np.array([-30., 20., 40., -20.])
    b = np.array([10., -10., 30., -40.])
    n1, n2 = a < 0, b < 0
    assert np.allclose(predict("additive", {}, a, b, n1, n2), [-20, 10, 50, -50])
    assert np.allclose(predict("average", {"w": .5}, a, b, n1, n2), [-10, 5, 35, -30])
    # Independent hand-calculated negative weight 2 and symmetric position.
    expected = np.array([-50 / 3, 0, 35, -30])
    assert np.allclose(predict("asymmetric", {"w": .5, "lambda": 2}, a, b, n1, n2), expected)
    rng = np.random.default_rng(47)
    x, z = rng.uniform(-45, 45, (2, 100))
    y = (.3 * np.where(x < 0, 3, 1) * x + .7 * np.where(z < 0, 3, 1) * z) / (.3 * np.where(x < 0, 3, 1) + .7 * np.where(z < 0, 3, 1))
    recovered = fit("asymmetric", x, z, x < 0, z < 0, y)
    assert abs(recovered["w"] - .3) < 1e-6 and abs(recovered["lambda"] - 3) < 1e-5
    recovered = fit("prior_average", x, z, x < 0, z < 0, np.clip(.72 * (x + z), -50, 50))
    assert abs(recovered["k"] - .72) < 1e-5
    assert parse_scores({"scores": [{"id": "A", "score": 50}]}) == {"A": 50}
    try:
        parse_scores([{"id": "A", "score": 50}, {"id": "A", "score": 60}])
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate scores must fail")
    print("Synthetic numerical checks passed; no experimental scores read or generated.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if args.bootstrap < 100:
        raise ValueError("Require at least 100 bootstrap replicates for reported intervals")
    data = load_data(args.base)
    baseline, y = data.singles.mean(axis=1), data.pairs.mean(axis=1)
    fits, table, flat = estimate(data, baseline, y)
    cv = cross_validate(data, baseline, y)
    print("All scores validated; full fits and held-atom CV complete.", flush=True)
    ci, draws = bootstrap(data, args.bootstrap, args.seed, True)
    print("Atom-strata and shared-round bootstrap complete.", flush=True)
    sensitivity, _ = bootstrap(data, args.bootstrap, args.seed, False)
    result = {"counts": {"atoms": 30, "ordered_pairs": 780, "calls": data.call_count, "scores": len(data.score_rows)},
              "bootstrap_replicates": args.bootstrap, "seed": args.seed, "sensitivity_seed": args.seed,
              "fits": fits, "full_fit": table, "cv": cv, "estimates": flat,
              "bootstrap_95": ci, "fixed_atom_round_only_95": sensitivity,
              "asymmetric_boundary": boundary(fits["asymmetric"]),
              "bootstrap_boundary_fraction": {key: float(np.mean([boundary({"w": row["asymmetric_w"], "lambda": row["asymmetric_lambda"]})[key] for row in draws])) for key in ("w", "lambda")},
              "neutral_atom_baselines": {atom: float(value + 50) for atom, p, value in zip(data.atom_ids, data.polarity, baseline) if p == "0"},
              "raw_endpoint_counts": {"baseline_0": int(np.sum(data.singles == -50)), "baseline_100": int(np.sum(data.singles == 50)),
                                      "combined_0": int(np.sum(data.pairs == -50)), "combined_100": int(np.sum(data.pairs == 50))},
              "polarity_mismatch_atoms": [atom for atom, p, value in zip(data.atom_ids, data.polarity, baseline) if p == "P" and value <= 0 or p == "N" and value >= 0],
              "decision": decision(flat, ci, cv)}
    with (args.base / "scores.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("round", "item_id", "score", "call_id"), lineterminator="\n")
        writer.writeheader()
        writer.writerows(data.score_rows)
    (args.base / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    draw_figure(args.base, data, baseline, y, fits, table, cv, flat, ci)
    write_report(args.base, result)
    print(json.dumps(result["decision"], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
