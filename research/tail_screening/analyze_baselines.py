"""Recompute widening curves from fixed, previously saved lexical-model scores.

Pre-execution budget: CPU 120 seconds; memory 512 MB; no network, installation,
model training or model fitting. Use 200 paired family-cluster bootstrap draws
per displayed scope. Only curve statistics and finite-window slopes are fitted.
The output contains aggregate statistics only, never IDs, headlines or labels.

Run from the worktree with the existing Python environment, for example:
  ../130U-FinLLM/.venv/Scripts/python.exe research/tail_screening/analyze_baselines.py \
      --plot-deps ../tmp/tail_plot_deps
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import time


P_GRID = (0.01, 0.015, 0.02, 0.03, 0.05, 0.075, 0.1)
SLOPE_GRID = (0.01, 0.02, 0.05, 0.1)
REPLICATES = 200
SEED = 130


def load_pairs(directory, np):
    """Pair strictly by ID; all score ordering below preserves threshold ties."""
    models = []
    for model in ("word", "char"):
        items = {}
        for split in ("train", "development", "test"):
            source = directory / f"{model}_tfidf_lr_{split}.jsonl"
            with source.open(encoding="utf-8") as stream:
                for line in stream:
                    row = json.loads(line)
                    identifier = row["id"]
                    family = row["family_id"]
                    if not isinstance(identifier, str) or not isinstance(family, str):
                        raise ValueError("ID/family schema mismatch")
                    if identifier in items or row["split"] != split:
                        raise ValueError("Duplicate ID or inconsistent split")
                    probabilities = np.asarray(row["probabilities"], dtype=float)
                    if (probabilities.shape != (3,) or
                            not np.all(np.isfinite(probabilities)) or
                            np.any(probabilities < 0) or np.any(probabilities > 1) or
                            not np.isclose(probabilities.sum(), 1.0, atol=1e-6, rtol=0)):
                        raise ValueError("Invalid three-class probabilities")
                    # Source class order: negative, neutral, positive.
                    score = float(probabilities[2] - probabilities[0])
                    items[identifier] = (family, split, score)
        models.append(items)
    first, second = models
    if first.keys() != second.keys():
        raise ValueError("Word/character predictions have different ID sets")
    a, b, families, splits = [], [], [], []
    family_split = {}
    for identifier, (family, split, score) in first.items():
        other_family, other_split, other_score = second[identifier]
        if (family, split) != (other_family, other_split):
            raise ValueError("Paired family/split mismatch")
        if family in family_split and family_split[family] != split:
            raise ValueError("Family crosses stored splits")
        family_split[family] = split
        a.append(score)
        b.append(other_score)
        families.append(family)
        splits.append(split)
    return tuple(np.asarray(x) for x in (a, b, families, splits))


def empirical_curve(a, b, direction, np):
    aa, bb = direction * a, direction * b
    n = len(aa)
    sorted_a = np.sort(aa)
    result = []
    for p in P_GRID:
        nominal = math.floor(n * p)
        if nominal < 1:
            raise ValueError("Tail has no observations at this nominal fraction")
        a_cutoff = float(sorted_a[n - nominal])
        a_tail = aa >= a_cutoff
        a_n = int(a_tail.sum())
        # Exact integer ceil(0.9 * actual_A_tail_n), avoiding binary rounding.
        needed = (9 * a_n + 9) // 10
        b_among_a = np.sort(bb[a_tail])
        b_cutoff = float(b_among_a[a_n - needed])
        b_tail = bb >= b_cutoff
        b_n = int(b_tail.sum())
        recovered = int(np.count_nonzero(a_tail & b_tail))
        if recovered < needed:
            raise AssertionError("Chosen threshold did not achieve target recall")
        # Any strictly larger threshold drops the cutoff tie group and fails.
        if np.count_nonzero(a_tail & (bb > b_cutoff)) >= needed:
            raise AssertionError("Threshold is not the highest feasible value")
        result.append({
            "p": p,
            "nominal_A_tail_n": nominal,
            "actual_A_tail_n": a_n,
            "actual_A_tail_fraction": a_n / n,
            "A_threshold": direction * a_cutoff,
            "A_threshold_tie_n": int(np.count_nonzero(aa == a_cutoff)),
            "A_tail_tie_expansion_n": a_n - nominal,
            "required_recovered_A_n": needed,
            "B_threshold": direction * b_cutoff,
            "B_threshold_tie_n": int(np.count_nonzero(bb == b_cutoff)),
            "B_threshold_tie_in_A_n": int(np.count_nonzero(a_tail & (bb == b_cutoff))),
            "B_selected_n": b_n,
            "q": b_n / n,
            "q_over_p": (b_n / n) / p,
            "recovered_A_n": recovered,
            "recall": recovered / a_n,
        })
    return result


def normal_score_correlation(a, b, np, rankdata, norm):
    n = len(a)
    za = norm.ppf((rankdata(a, method="average") - 0.5) / n)
    zb = norm.ppf((rankdata(b, method="average") - 0.5) / n)
    return float(np.corrcoef(za, zb)[0, 1])


def gaussian_q(p, rho, quad, brentq, norm):
    if rho == 1.0:
        return 0.9 * p
    if rho == -1.0:
        return 1.0 - 0.1 * p
    if not -1.0 < rho < 1.0:
        raise ValueError("Invalid Gaussian correlation")
    z = norm.isf(p)
    scale = math.sqrt(1.0 - rho * rho)

    def error(q):
        w = norm.isf(q)
        joint, _ = quad(
            lambda x: norm.pdf(x) * norm.sf((w - rho * x) / scale),
            z, math.inf, epsabs=1e-11, epsrel=1e-9,
        )
        return joint / p - 0.9

    return float(brentq(error, 1e-12, 1.0 - 1e-12, xtol=1e-12))


def slope(curve, np):
    rows = [row for row in curve if row["p"] in SLOPE_GRID]
    return float(np.polyfit(np.log([r["p"] for r in rows]),
                            np.log([r["q"] for r in rows]), 1)[0])


def analyze_scope(a, b, families, seed, np, rankdata, norm, quad, brentq, deadline):
    _, inverse, sizes = np.unique(families, return_inverse=True, return_counts=True)
    order = np.argsort(inverse, kind="stable")
    groups = np.split(order, np.cumsum(sizes)[:-1])
    rng = np.random.default_rng(seed)
    curves = {name: empirical_curve(a, b, sign, np)
              for name, sign in (("upper", 1), ("lower", -1))}
    boot = {name: [] for name in curves}
    boot_slopes = {name: [] for name in curves}
    for _ in range(REPLICATES):
        if time.process_time() > deadline:
            raise RuntimeError("CPU budget exceeded; no partial aggregate is published")
        chosen = rng.integers(0, len(groups), size=len(groups))
        idx = np.concatenate([groups[i] for i in chosen])
        for name, sign in (("upper", 1), ("lower", -1)):
            curve = empirical_curve(a[idx], b[idx], sign, np)
            boot[name].append([row["q_over_p"] for row in curve])
            boot_slopes[name].append(slope(curve, np))
    for name, rows in curves.items():
        bounds = np.percentile(np.asarray(boot[name]), [2.5, 97.5], axis=0)
        for i, row in enumerate(rows):
            row["q_over_p_bootstrap_95_percentile"] = bounds[:, i].tolist()
            row["q_bootstrap_95_percentile"] = (bounds[:, i] * row["p"]).tolist()
    rho = normal_score_correlation(a, b, np, rankdata, norm)
    gauss = [{"p": p, "q": gaussian_q(p, rho, quad, brentq, norm)} for p in P_GRID]
    for row in gauss:
        row["q_over_p"] = row["q"] / row["p"]
    return {
        "n": len(a), "family_clusters": len(groups),
        "maximum_family_size": int(sizes.max()),
        "unique_A_scores": int(len(np.unique(a))),
        "unique_B_scores": int(len(np.unique(b))),
        "raw_Pearson_rho": float(np.corrcoef(a, b)[0, 1]),
        "normal_score_rho": rho,
        "upper": curves["upper"], "lower": curves["lower"],
        "Gaussian_normal_score_comparator": gauss,
        "alpha_eff": {
            name: {"estimate": slope(rows, np),
                   "bootstrap_95_percentile": np.percentile(boot_slopes[name], [2.5, 97.5]).tolist()}
            for name, rows in curves.items()
        },
        "Gaussian_alpha_eff": slope(gauss, np),
        "bootstrap_replicates_completed": REPLICATES,
        "bootstrap_seed": seed,
    }


def plot_results(results, output, plt, np):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "pdf.fonttype": 42})
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.7), sharey=True)
    for ax, key, title in zip(axes, ("all_splits", "test"),
                              ("All saved splits (includes training)", "Held-out test split")):
        scope = results["scopes"][key]
        for name, color, marker, label in (("upper", "#1764A0", "o", "Upper tail"),
                                           ("lower", "#B35316", "s", "Lower tail")):
            rows = scope[name]
            x = np.asarray([row["p"] for row in rows]) * 100
            y = [row["q_over_p"] for row in rows]
            ci = np.asarray([row["q_over_p_bootstrap_95_percentile"] for row in rows])
            ax.fill_between(x, ci[:, 0], ci[:, 1], color=color, alpha=0.14, linewidth=0)
            ax.plot(x, y, color=color, marker=marker, markersize=4.5, label=label, linewidth=1.8)
        gauss = scope["Gaussian_normal_score_comparator"]
        ax.plot([r["p"] * 100 for r in gauss], [r["q_over_p"] for r in gauss],
                color="#333333", linestyle="--", linewidth=1.5,
                label="Gaussian (normal-score correlation)")
        ax.axhline(1, color="#888888", linewidth=0.7, linestyle=":")
        ax.set_xscale("log")
        ax.set_xticks([1, 1.5, 2, 3, 5, 7.5, 10], ["1", "1.5", "2", "3", "5", "7.5", "10"])
        ax.set_xlabel("Nominal A tail fraction p (%)")
        ax.set_title(f"{title}\nn = {scope['n']:,}; normal-score correlation = {scope['normal_score_rho']:.3f}", fontsize=11)
        ax.grid(axis="y", color="#E5E5E5", linewidth=0.6)
    axes[0].set_ylabel("B fraction required for 90% recall / p")
    axes[0].legend(frameon=False, fontsize=8.6, loc="upper right")
    fig.suptitle("Tail screening with fixed lexical-model scores", fontsize=14, y=0.995)
    fig.text(0.5, 0.025,
             "A: word TF-IDF + logistic regression; B: character TF-IDF + logistic regression. "
             "Score: P(positive) - P(negative).\n"
             "Threshold ties retained. Shading: 200 paired lexical-family bootstrap draws, pointwise 95% intervals. "
             "No LLM scores or new training.",
             ha="center", fontsize=8.4)
    fig.tight_layout(rect=(0, 0.105, 1, 0.94))
    fig.savefig(output / "widening.png", dpi=190)
    fig.savefig(output / "widening.pdf")
    plt.close(fig)


def main():
    started_wall, started_cpu = time.perf_counter(), time.process_time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot-deps", type=Path)
    args = parser.parse_args()
    if args.plot_deps:
        sys.path.insert(0, str(args.plot_deps.resolve()))
    import numpy as np
    from scipy.integrate import quad
    from scipy.optimize import brentq
    from scipy.stats import norm, rankdata
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    worktree = Path(__file__).resolve().parents[2]
    output = Path(__file__).resolve().parent
    a, b, families, splits = load_pairs(worktree / "research/private/real_baseline/trained/predictions", np)
    results = {
        "description": "Fixed lexical baselines only; not LLM evidence or newly trained models.",
        "score": "P(positive) - P(negative), source class order negative/neutral/positive",
        "A": "word_tfidf_lr", "B": "char_tfidf_lr",
        "pairing": "Strict ID pairing with identical family/split; no ID-based tie breaking",
        "tail_rule": "A includes all ties at its top floor(n*p) cutoff. B uses the highest cutoff recovering ceil(0.9*actual_A_tail_n), also including all ties. Lower tail reverses both scores.",
        "ratio_denominator": "Nominal p, not realized tie-expanded A tail fraction",
        "normal_scores": "Phi^-1((average_rank - 0.5)/n), retaining score ties",
        "Gaussian_comparator": "Gaussian copula with normal-score rho; exact numerical quadrature and root inversion for 90% conditional recall; symmetric upper/lower comparator; no raw-rho substitution",
        "uncertainty": "200 paired family-cluster resamples per scope; variable sample size; percentile pointwise 95% intervals, not simultaneous bands. Models and stored lexical families fixed; not event-independence assurance, retraining uncertainty or LLM generalization.",
        "alpha_eff_definition": "OLS slope of log(q) on log(p) over p=0.01,0.02,0.05,0.1. Finite-window descriptive statistic, not a Heffernan-Tawn structural alpha or proof of tail limits.",
        "all_splits_warning": "Includes training predictions and development data; descriptive in-sample aggregate, not out-of-sample performance.",
        "p_grid": list(P_GRID), "alpha_eff_p_grid": list(SLOPE_GRID),
        "budget": {"CPU_seconds": 120, "memory_MB_target": 512, "training": False, "network": False},
        "scopes": {},
    }
    for offset, (name, mask) in enumerate((("all_splits", np.ones(len(a), dtype=bool)),
                                         ("test", splits == "test"))):
        results["scopes"][name] = analyze_scope(
            a[mask], b[mask], families[mask], SEED + offset,
            np, rankdata, norm, quad, brentq, started_cpu + 120,
        )
    plot_results(results, output, plt, np)
    results["execution"] = {"wall_seconds": time.perf_counter() - started_wall,
                            "CPU_seconds": time.process_time() - started_cpu,
                            "numpy_version": np.__version__,
                            "matplotlib_version": matplotlib.__version__}
    if results["execution"]["CPU_seconds"] > 120:
        raise RuntimeError("CPU budget exceeded; aggregate not published")
    (output / "baseline_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"scopes": {
        name: {"n": s["n"], "raw_rho": s["raw_Pearson_rho"], "normal_rho": s["normal_score_rho"],
               "upper_1pct": s["upper"][0], "lower_1pct": s["lower"][0], "alpha_eff": s["alpha_eff"]}
        for name, s in results["scopes"].items()}, "execution": results["execution"]}, indent=2))


if __name__ == "__main__":
    main()
