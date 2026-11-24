"""Analyze frozen absolute-score repetitions; never reads headline text.

Run from the repository root after every scheduled call has a valid score file:
  python research/absolute_scoring/analyze_scores.py

The primary prediction is a fixed benchmark, not an identity for raw-score means.
Bootstrap intervals condition on the observed calls and use paired title rows;
they do not include all uncertainty from shared contexts or future model calls.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from itertools import combinations
import json
import math
from pathlib import Path
import re
import sys

import numpy as np
from scipy.integrate import quad
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq
from scipy.special import ndtri
from scipy.stats import rankdata

PS = (0.20, 0.10, 0.05)
MS = (1, 2, 4)
TAILS = ("upper", "lower")
PAIRS = tuple(combinations(range(8), 2))
BOOTSTRAP_SEED = 2026111605
CONTROL_BOOTSTRAP_SEED = 2026111606


def normal_scores(x: np.ndarray) -> np.ndarray:
    """Column-wise normal scores from average ranks; preserves ties."""
    x = np.asarray(x)
    if x.ndim not in (1, 2) or len(x) < 2 or not np.isfinite(x).all():
        raise ValueError("Scores must be a finite vector/matrix with >=2 rows")
    return ndtri((rankdata(x, method="average", axis=0) - 0.5) / len(x))


def correlation_matrix(x: np.ndarray) -> np.ndarray:
    z = normal_scores(x)
    if z.ndim != 2:
        raise ValueError("Correlation input must have columns")
    z -= z.mean(axis=0)
    norm = np.sqrt(np.sum(z * z, axis=0))
    with np.errstate(divide="ignore", invalid="ignore"):
        ans = (z.T @ z) / np.outer(norm, norm)
    # Only correct floating-point excursions in valid correlation arithmetic.
    return np.clip(ans, -1.0, 1.0)


def reliability(x: np.ndarray) -> tuple[float, np.ndarray]:
    if np.asarray(x).shape[1] != 8:
        raise ValueError("Exactly eight score columns are required")
    corr = correlation_matrix(x)
    pairs = np.array([corr[a, b] for a, b in PAIRS])
    # An undefined round is not silently omitted from the 28-pair mean.
    return float(pairs.mean()), pairs


def paired_resample(x: np.ndarray, indices: np.ndarray) -> np.ndarray:
    """One sampled row carries all its repetitions; duplicates stay duplicated."""
    return np.asarray(x)[np.asarray(indices, dtype=int), :]


def head_set(x: np.ndarray, p: float, tail: str) -> tuple[np.ndarray, dict]:
    x = np.asarray(x)
    if x.ndim != 1 or tail not in TAILS or not (0 < p <= 1):
        raise ValueError("Invalid tail/vector/proportion")
    k = math.floor(len(x) * p + 1e-10)
    if k < 1:
        raise ValueError("Nominal head must contain at least one row")
    oriented = x if tail == "upper" else -x
    threshold = np.partition(oriented, len(x) - k)[len(x) - k]
    selected = oriented >= threshold
    boundary = int(np.count_nonzero(oriented == threshold))
    actual = int(selected.sum())
    return selected, {
        "nominal_n": k, "actual_n": actual,
        "boundary_n": boundary, "expansion_n": actual - k,
        "threshold_sum": int(threshold if tail == "upper" else -threshold),
        "boundary_fraction_of_nominal": boundary / k,
        "tie_gate_failed": boundary > 0.2 * k,
    }


def minimal_release(candidate: np.ndarray, reference: np.ndarray,
                    p: float, tail: str) -> dict:
    """Minimal full score-group boundary recovering at least 90% of reference."""
    candidate = np.asarray(candidate)
    reference = np.asarray(reference, dtype=bool)
    if candidate.shape != reference.shape or not reference.any():
        raise ValueError("Invalid reference set")
    oriented = candidate if tail == "upper" else -candidate
    reference_n = int(reference.sum())
    needed = (9 * reference_n + 9) // 10  # exact ceil(0.9 * reference_n)
    reference_scores = oriented[reference]
    boundary = np.partition(reference_scores, reference_n - needed)[reference_n - needed]
    released = oriented >= boundary
    released_n = int(released.sum())
    recovered_n = int(np.count_nonzero(released & reference))
    return {
        "released_n": released_n, "recovered_n": recovered_n,
        "target_recovered_n": needed, "achieved_recall": recovered_n / reference_n,
        "release_threshold_sum": int(boundary if tail == "upper" else -boundary),
        "widening": released_n / (len(candidate) * p),
        "release_over_actual_reference": released_n / reference_n,
    }


def tail_metrics(x: np.ndarray) -> list[dict]:
    """36 directional estimands in a fixed m,p,tail,reference order."""
    rows = []
    for m in MS:
        a = x[:, :m].sum(axis=1, dtype=np.int64)
        b = x[:, 4:4 + m].sum(axis=1, dtype=np.int64)
        for p in PS:
            for tail in TAILS:
                ha, da = head_set(a, p, tail)
                hb, db = head_set(b, p, tail)
                intersection = int(np.count_nonzero(ha & hb))
                for direction, ref, cand, dref, dcand in (
                        ("A_to_B", ha, b, da, db),
                        ("B_to_A", hb, a, db, da)):
                    rows.append({
                        "m": m, "p": p, "tail": tail, "direction": direction,
                        "intersection_n": intersection,
                        "reference_n": dref["actual_n"], "candidate_n": dcand["actual_n"],
                        "reference_boundary_n": dref["boundary_n"],
                        "candidate_boundary_n": dcand["boundary_n"],
                        "nominal_n": dref["nominal_n"],
                        "tie_gate_failed": dref["tie_gate_failed"] or dcand["tie_gate_failed"],
                        "overlap": intersection / dref["actual_n"],
                        **minimal_release(cand, ref, p, tail),
                    })
    return rows


def boundary_diagnostics(x: np.ndarray) -> list[dict]:
    rows = []
    measurements = [(f"round_{i+1}", 1, x[:, i]) for i in range(8)]
    measurements += [(f"panel_{panel}_m{m}", m, x[:, start:start + m].sum(axis=1))
                     for m in MS for panel, start in (("A", 0), ("B", 4))]
    for label, divisor, scores in measurements:
        unique = len(np.unique(scores))
        for p in PS:
            for tail in TAILS:
                _, detail = head_set(scores, p, tail)
                rows.append({"measurement": label, "m": divisor,
                             "unique_scores": unique, "p": p, "tail": tail,
                             **detail, "threshold": detail["threshold_sum"] / divisor})
    return rows


def gaussian_joint(p: float, q: float, rho: float) -> float:
    """P(X>Phi^-1(1-p),Y>Phi^-1(1-q)) by deterministic 1-D quadrature.

    Integrate the bivariate density over correlation (Plackett's identity),
    substituting r=sin(theta) to remove its square-root singularity.
    """
    if not (0 <= rho <= 1 and 0 <= p <= 1 and 0 <= q <= 1):
        raise ValueError("Gaussian benchmark requires rho in [0,1]")
    if p == 0 or q == 0:
        return 0.0
    if p == 1:
        return q
    if q == 1:
        return p
    if rho == 0:
        return p * q
    if rho == 1:
        return min(p, q)
    a, b = float(ndtri(1 - p)), float(ndtri(1 - q))

    def integrand(theta):
        s = math.sin(theta)
        c = math.cos(theta)
        # This rearrangement avoids cancellation when a == b and rho -> 1.
        numerator = (a - b) ** 2 + 2 * a * b * (1 - s)
        return math.exp(-numerator / (2 * c * c)) / (2 * math.pi)

    integral, _ = quad(integrand, 0.0, math.asin(rho), epsabs=2e-11, epsrel=2e-10,
                       limit=150)
    return p * q + integral


def gaussian_prediction(r: float, m: int, p: float) -> tuple[float, float]:
    if not math.isfinite(r) or not 0 <= r <= 1:
        return math.nan, math.nan
    rho = m * r / (1 + (m - 1) * r)
    if rho == 0:
        return p, 0.9 / p
    if rho == 1:
        return 1.0, 0.9
    overlap = gaussian_joint(p, p, rho) / p
    # Exact endpoint probabilities provide a sign-safe bracket even when rho
    # is so close to one that J(p, .9*p, rho) rounds above its limiting value.
    q = brentq(lambda q0: gaussian_joint(p, q0, rho) - 0.9 * p,
               0.0, 1.0, xtol=2e-11, rtol=2e-11)
    return overlap, q / p


class PredictionGrid:
    """Data-independent quadrature grid for bootstrap evaluation.

    Interpolation is on theta=asin(rho), never fitted to observed overlap.
    Every interval midpoint is checked against fresh quadrature. The observed
    maximum error is a numerical validation, not a certified supremum bound.
    Point estimates use direct quadrature; only bootstrap predictions use this.
    """
    def __init__(self, size=1001, tolerance=5e-5):
        self.theta = np.linspace(0, np.pi / 2, size)
        self.rho = np.sin(self.theta)
        self.tables = {}
        self.validation = {"grid_points": size, "midpoints_per_p": size - 1,
                           "absolute_error_tolerance": tolerance,
                           "coordinates": "asin(rho)", "errors": {}}
        middle = (self.theta[:-1] + self.theta[1:]) / 2
        for p in PS:
            exact = np.array([gaussian_prediction(float(rho), 1, p) for rho in self.rho])
            interpolation = PchipInterpolator(self.theta, exact, axis=0)
            midpoint_exact = np.array([gaussian_prediction(float(np.sin(t)), 1, p)
                                       for t in middle])
            errors = np.max(np.abs(midpoint_exact - interpolation(middle)), axis=0)
            if np.max(errors) > tolerance:
                raise ArithmeticError(f"Gaussian interpolation error {errors} exceeds {tolerance}")
            self.tables[p] = interpolation
            self.validation["errors"][str(p)] = {
                "max_midpoint_overlap_error": float(errors[0]),
                "max_midpoint_widening_error": float(errors[1])}

    def evaluate(self, r: float, m: int, p: float) -> np.ndarray:
        if not math.isfinite(r) or not 0 <= r <= 1:
            return np.full(2, np.nan)
        rho = m * r / (1 + (m - 1) * r)
        return np.asarray(self.tables[p](math.asin(rho)))


def ci(values: np.ndarray) -> list[float]:
    values = np.asarray(values)
    valid = values[np.isfinite(values)]
    if len(valid) == 0:
        return [math.nan, math.nan]
    return np.quantile(valid, [0.025, 0.975]).tolist()


def run_bootstrap(x: np.ndarray, point_rows: list[dict], repetitions: int,
                  grid: PredictionGrid, seed=BOOTSTRAP_SEED) -> dict:
    rng = np.random.default_rng(seed)
    observed = np.empty((repetitions, len(point_rows), 2))
    predicted = np.empty_like(observed)
    rs = np.empty(repetitions)
    for iteration in range(repetitions):
        sample = paired_resample(x, rng.integers(0, len(x), size=len(x)))
        r, _ = reliability(sample)
        rs[iteration] = r
        rows = tail_metrics(sample)
        pred = {(m, p): grid.evaluate(r, m, p) for m in MS for p in PS}
        for j, row in enumerate(rows):
            observed[iteration, j] = (row["overlap"], row["widening"])
            predicted[iteration, j] = pred[row["m"], row["p"]]
    for j, row in enumerate(point_rows):
        for k, metric in enumerate(("overlap", "widening")):
            row[f"{metric}_ci95"] = ci(observed[:, j, k])
            row[f"prediction_{metric}_ci95"] = ci(predicted[:, j, k])
            row[f"delta_{metric}_ci95"] = ci(observed[:, j, k] - predicted[:, j, k])
            row[f"prediction_{metric}_valid_bootstraps"] = int(np.isfinite(predicted[:, j, k]).sum())
    lookup = {(row["m"], row["p"], row["tail"], row["direction"]): j
              for j, row in enumerate(point_rows)}
    asymmetry = []
    for m in MS:
        for p in PS:
            for direction in ("A_to_B", "B_to_A"):
                upper = lookup[m, p, "upper", direction]
                lower = lookup[m, p, "lower", direction]
                row = {"m": m, "p": p, "direction": direction}
                for k, metric in enumerate(("overlap", "widening")):
                    row[f"upper_minus_lower_{metric}"] = point_rows[upper][metric] - point_rows[lower][metric]
                    row[f"upper_minus_lower_{metric}_ci95"] = ci(observed[:, upper, k] - observed[:, lower, k])
                asymmetry.append(row)
    return {"repetitions": repetitions, "seed": seed, "reliability_ci95": ci(rs),
            "invalid_reliability_replicates": int((~np.isfinite(rs)).sum()),
            "outside_benchmark_replicates": int(np.count_nonzero((rs < 0) | (rs > 1))),
            "asymmetry": asymmetry,
            "interpretation": "Paired-title percentile, pointwise 95%; conditional on observed calls, not simultaneous or full context uncertainty."}


def control_analysis(main: np.ndarray, control: np.ndarray, repetitions: int,
                     seed=CONTROL_BOOTSTRAP_SEED) -> dict:
    if len(main) != len(control) or control.shape[1] != 2:
        raise ValueError("Control and main must contain the same target IDs")

    def estimates(a, b):
        diff_r, pairs = reliability(a)
        same_r = float(correlation_matrix(b)[0, 1])
        return np.array([same_r, diff_r, same_r - diff_r]), pairs

    point, pairs = estimates(main, control)
    rng = np.random.default_rng(seed)
    boot = np.empty((repetitions, 3))
    for i in range(repetitions):
        index = rng.integers(0, len(main), size=len(main))
        boot[i], _ = estimates(paired_resample(main, index), paired_resample(control, index))
    original = correlation_matrix(np.column_stack([main[:, 0], control]))
    return {"n": len(main), "same_batch_r": point[0], "different_batch_mean_r": point[1],
            "same_minus_different_r": point[2], "different_batch_pair_r": pairs.tolist(),
            "same_batch_r_ci95": ci(boot[:, 0]), "different_batch_mean_r_ci95": ci(boot[:, 1]),
            "same_minus_different_r_ci95": ci(boot[:, 2]),
            "valid_bootstraps_per_statistic": np.isfinite(boot).sum(axis=0).tolist(),
            "round1_vs_C1_r": float(original[0, 1]), "round1_vs_C2_r": float(original[0, 2]),
            "bootstrap_seed": seed,
            "interpretation": "Matched 100-title correlation contrast; not an identified batch-noise variance percentage."}


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def unique_json_object(pairs):
    answer = {}
    for key, value in pairs:
        if key in answer:
            raise ValueError(f"Duplicate JSON key: {key}")
        answer[key] = value
    return answer


@dataclass
class Inputs:
    ids: list[str]
    main: np.ndarray
    control_indices: np.ndarray
    controls: np.ndarray
    counts: dict


def load_inputs(directory: Path) -> Inputs:
    sample = read_csv(directory / "sample.csv")
    ids = [row["id"] for row in sample]
    if len(ids) not in (500, 1000) or len(set(ids)) != len(ids):
        raise ValueError("Expected 500 or 1000 unique sampled IDs")
    if len({row["family_id"] for row in sample}) != len(ids):
        raise ValueError("Sample is not one title per lexical family")
    index = {identifier: i for i, identifier in enumerate(ids)}
    control_ids = [row["id"] for row in read_csv(directory / "control_ids.csv")]
    if len(control_ids) != 100 or len(set(control_ids)) != 100 or not set(control_ids) <= set(ids):
        raise ValueError("Expected 100 unique control IDs from sample")
    batches = {}
    positions = {}
    for row in read_csv(directory / "batches.csv"):
        key, pos, identifier = row["input_key"], int(row["position"]), row["id"]
        if identifier not in index:
            raise ValueError("Batch contains unknown ID")
        if pos in positions.setdefault(key, set()):
            raise ValueError("Duplicate batch position")
        positions[key].add(pos)
        batches.setdefault(key, []).append(identifier)
    for key, batch in batches.items():
        if len(batch) != len(set(batch)) or len(batch) > 40:
            raise ValueError(f"Invalid batch size or duplicated ID in {key}")
        if len(ids) == 1000 and len(batch) != 40:
            raise ValueError("1000-item experiment requires every batch to contain 40 items")
        if positions[key] != set(range(1, len(batch) + 1)):
            raise ValueError("Batch positions must be consecutive and one-based")
    main = np.full((len(ids), 8), -1, dtype=np.int64)
    controls_all = np.full((len(ids), 2), -1, dtype=np.int64)
    schedule = read_csv(directory / "schedule.csv")
    calls = set()
    control_keys = [set(), set()]
    main_keys = set()
    first_round_keys = set()
    for row in schedule:
        call_id, input_key = row["call_id"], row["input_key"]
        if call_id in calls:
            raise ValueError("Duplicate call ID")
        calls.add(call_id)
        if input_key not in batches:
            raise ValueError(f"No batch definition for {input_key}")
        scores = json.loads((directory / "raw_scores" / f"{call_id}.json").read_text(encoding="utf-8-sig"),
                            object_pairs_hook=unique_json_object)
        if not isinstance(scores, dict) or set(scores) != set(batches[input_key]):
            raise ValueError(f"Score IDs do not match exact scheduled batch: {call_id}")
        if any(type(value) is not int or not 0 <= value <= 100 for value in scores.values()):
            raise ValueError(f"Noninteger or out-of-range score: {call_id}")
        match_main = re.fullmatch(r"r(0[1-8])_b(\d{2})", call_id)
        match_control = re.fullmatch(r"c([12])_b(\d{2})", call_id)
        if match_main:
            round_index = int(match_main[1]) - 1
            if input_key != call_id or int(row["round"]) != round_index + 1:
                raise ValueError("Main call/input/round mismatch")
            main_keys.add(input_key)
            if round_index == 0:
                first_round_keys.add(input_key)
            target = main[:, round_index]
        elif match_control:
            repeat_index = int(match_control[1]) - 1
            if input_key != f"r01_b{match_control[2]}":
                raise ValueError("Control must reuse complete first-round batch")
            control_keys[repeat_index].add(input_key)
            target = controls_all[:, repeat_index]
        else:
            raise ValueError(f"Unexpected call ID {call_id}")
        for identifier, score in scores.items():
            i = index[identifier]
            if target[i] != -1:
                raise ValueError(f"Repeated ID within round/control: {identifier}")
            target[i] = score
    if set(batches) != main_keys or np.any(main < 0):
        raise ValueError("Incomplete eight-round experiment or extraneous batch definitions")
    required_controls = {key for key in first_round_keys if set(batches[key]) & set(control_ids)}
    if control_keys != [required_controls, required_controls]:
        raise ValueError("Control calls must repeat exactly all batches containing designated controls")
    control_index = np.array([index[identifier] for identifier in control_ids])
    if np.any(controls_all[control_index] < 0):
        raise ValueError("Missing control score")
    return Inputs(ids, main, control_index, controls_all[control_index], {
        "titles": len(ids), "rounds": 8, "main_calls": len(main_keys),
        "main_scores": int(main.size), "control_target_titles": 100,
        "control_calls": sum(len(keys) for keys in control_keys),
        "control_all_scores_including_nonfocal": int(np.count_nonzero(controls_all >= 0)),
        "control_focal_scores": 200, "scheduled_calls": len(calls)})


def clean_json(value):
    if isinstance(value, dict):
        return {key: clean_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(item) for item in value]
    if isinstance(value, np.ndarray):
        return clean_json(value.tolist())
    if isinstance(value, np.generic):
        return clean_json(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def write_table(path: Path, rows: list[dict]):
    flattened = []
    for row in rows:
        out = {}
        for key, value in row.items():
            if isinstance(value, list) and len(value) == 2 and key.endswith("ci95"):
                out[key + "_low"], out[key + "_high"] = value
            else:
                out[key] = value
        flattened.append(out)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(flattened[0]))
        writer.writeheader()
        writer.writerows(flattened)


def draw_figure(rows: list[dict], output: Path, n: int, primary_gate_failed: bool = False):
    deps = Path(__file__).resolve().parents[3] / "tmp/tail_plot_deps"
    if deps.is_dir():
        sys.path.insert(0, str(deps))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 3, figsize=(12, 7), sharex=True, sharey=True)
    colors = {"A_to_B": "#1468a0", "B_to_A": "#d16a24"}
    for ti, tail in enumerate(TAILS):
        for pi, p in enumerate(PS):
            ax = axes[ti, pi]
            selected = [row for row in rows if row["tail"] == tail and row["p"] == p]
            prediction = [next(row["prediction_overlap"] for row in selected if row["m"] == m) for m in MS]
            ax.plot(MS, prediction, color="#333333", linewidth=1.6, label="Fixed SB + Gaussian")
            for direction, shift in (("A_to_B", -0.045), ("B_to_A", 0.045)):
                subset = [next(row for row in selected if row["m"] == m and row["direction"] == direction) for m in MS]
                xs = np.asarray(MS, dtype=float) + shift
                for x0, row in zip(xs, subset):
                    lo, hi = row["overlap_ci95"]
                    ax.vlines(x0, lo, hi, color=colors[direction], linewidth=1.3)
                    ax.hlines([lo, hi], x0 - .025, x0 + .025, color=colors[direction], linewidth=1)
                    ax.plot(x0, row["overlap"], marker="x" if row["tie_gate_failed"] else "o",
                            color=colors[direction], markersize=6)
                ax.plot([], [], "o", color=colors[direction], label=direction.replace("_", " "))
            gated = sum(row["tie_gate_failed"] for row in selected)
            ax.set_title(f"{tail.capitalize()} {p:.0%} | tie-gated comparisons {gated}/6", fontsize=10)
            ax.set_xticks(MS, ["1", "2", "4"])
            ax.set_ylim(0, 1.03)
            ax.grid(alpha=.18)
            if pi == 0:
                ax.set_ylabel("Directional head self-overlap")
            if ti == 1:
                ax.set_xlabel("Scores averaged in each panel (m)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles[:3], labels[:3], loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(.5, .005))
    title = f"Absolute-score repeatability | N={n}, eight rounds\n95% paired-title bootstrap intervals; x = boundary ties exceed 20% of nominal head"
    if primary_gate_failed:
        title += "\nOverall 10% resolution gate FAILED in single-round diagnostics; plotted results are descriptive."
    fig.suptitle(title, fontsize=11)
    fig.tight_layout(rect=(0, .05, 1, .92))
    fig.savefig(output / "stability.png", dpi=180)
    fig.savefig(output / "stability.pdf")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--bootstrap", type=int, default=5000)
    parser.add_argument("--no-figure", action="store_true")
    args = parser.parse_args()
    if args.bootstrap < 100:
        raise ValueError("Use at least 100 bootstrap iterations; frozen final analysis requires 5000")
    inputs = load_inputs(args.directory)
    output = args.output or args.directory / "results"
    output.mkdir(parents=True, exist_ok=True)
    r, pairs = reliability(inputs.main)
    rows = tail_metrics(inputs.main)
    for row in rows:
        pred = gaussian_prediction(r, row["m"], row["p"])
        row["prediction_r_m"] = row["m"] * r / (1 + (row["m"] - 1) * r) if math.isfinite(r) and 0 <= r <= 1 else math.nan
        for metric, value in zip(("overlap", "widening"), pred):
            row[f"prediction_{metric}"] = value
            row[f"delta_{metric}"] = row[metric] - value
    print("All score files validated. Building data-independent Gaussian quadrature grid.", flush=True)
    grid = PredictionGrid()
    print(f"Running {args.bootstrap} paired-title resamples.", flush=True)
    bootstrap = run_bootstrap(inputs.main, rows, args.bootstrap, grid)
    control = control_analysis(inputs.main[inputs.control_indices], inputs.controls, args.bootstrap)
    boundaries = boundary_diagnostics(inputs.main)
    failed = [row for row in boundaries if row["tie_gate_failed"]]
    report = {
        "experiment": "Absolute-score replication and stress test, not a new-theory claim",
        "counts": inputs.counts, "r_mean": r, "r_range": [float(pairs.min()), float(pairs.max())],
        "r_pairs": [{"round_a": a + 1, "round_b": b + 1, "r": float(value)} for (a, b), value in zip(PAIRS, pairs)],
        "estimands": rows, "boundary_diagnostics": boundaries,
        "boundary_gate": {"failed_any_prespecified_boundary": bool(failed), "failed_count": len(failed),
                          "tested_count": len(boundaries),
                          "failed_primary_p10": any(row["p"] == .1 for row in failed),
                          "definition": "Entire boundary score group >20% of nominal head, not excess expansion"},
        "bootstrap": bootstrap, "control": control, "numerical_validation": grid.validation,
        "scope": ["Normal-score single-round r predicts raw-score means only as a benchmark.",
                  "The benchmark and averaged outcomes use the same eight rounds; no independent holdout.",
                  "Self-consistency does not establish accuracy or economic value.",
                  "Whole boundary ties are retained; gated statistics are descriptive only.",
                  "Title bootstrap intervals are pointwise and conditional on these calls."],
        "final_protocol_bootstrap_count": args.bootstrap == 5000,
    }
    (output / "results.json").write_text(json.dumps(clean_json(report), ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    write_table(output / "tables.csv", rows)
    write_table(output / "boundaries.csv", boundaries)
    write_table(output / "asymmetry.csv", bootstrap["asymmetry"])
    if not args.no_figure:
        draw_figure(rows, output, len(inputs.ids), report["boundary_gate"]["failed_primary_p10"])
    print(json.dumps(clean_json({"output": str(output), "counts": inputs.counts,
                                 "r_mean": r, "tie_gate": report["boundary_gate"]}), ensure_ascii=False))


if __name__ == "__main__":
    main()
