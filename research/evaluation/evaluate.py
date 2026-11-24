"""Research evaluation: grouped resampling and leakage-conscious split helpers.

Run from repository root: python -m research.evaluation.evaluate input.jsonl output.json
No headlines or individual predictions are written to the aggregate output.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np

LABELS = ("bearish", "neutral", "bullish")
METRICS = ("accuracy", "macro_f1") + tuple(
    f"{label}_{metric}" for label in LABELS for metric in ("precision", "recall", "f1")
)


def metrics_from_confusion(cm):
    """Vectorized metrics. Rows true, columns predicted; absent class -> zero."""
    cm = np.asarray(cm, dtype=float)
    if cm.shape[-2:] != (3, 3) or not np.isfinite(cm).all() or (cm < 0).any():
        raise ValueError("Expected nonnegative finite (...,3,3) confusion matrices")
    n = cm.sum(axis=(-1, -2))
    if (n <= 0).any():
        raise ValueError("Empty confusion matrix")
    tp = np.diagonal(cm, axis1=-2, axis2=-1)
    actual, predicted = cm.sum(axis=-1), cm.sum(axis=-2)
    precision = np.divide(tp, predicted, out=np.zeros_like(tp), where=predicted != 0)
    recall = np.divide(tp, actual, out=np.zeros_like(tp), where=actual != 0)
    f1 = np.divide(2 * tp, actual + predicted, out=np.zeros_like(tp), where=(actual + predicted) != 0)
    return np.concatenate(((tp.sum(axis=-1) / n)[..., None], f1.mean(axis=-1)[..., None],
                           np.stack((precision, recall, f1), axis=-1).reshape(cm.shape[:-2] + (9,))), axis=-1)


def _timestamp(value):
    result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Timestamps must include a timezone")
    return result.astimezone(timezone.utc)


def connected_groups(records):
    """Join family AND event links transitively; never invent independent groups."""
    parents = list(range(len(records)))
    def root(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i
    seen = {}
    for i, row in enumerate(records):
        if not row.get("family_id") and not row.get("event_id"):
            raise ValueError("Every row needs an audited family_id or event_id")
        for field in ("family_id", "event_id"):
            if row.get(field):
                key = (field, str(row[field]))
                if key in seen:
                    parents[root(i)] = root(seen[key])
                else:
                    seen[key] = i
    return [root(i) for i in range(len(records))]


def chronological_split(records, train_end, development_end):
    """Assign each connected event/family wholly by its latest availability.

    Earlier views may be moved to a later partition; no future view moves earlier.
    A split timestamp is not an assertion that its source timestamp is correct.
    """
    first, second = _timestamp(train_end), _timestamp(development_end)
    if first >= second:
        raise ValueError("train_end must precede development_end")
    groups = connected_groups(records)
    latest = {}
    for group, row in zip(groups, records):
        time = _timestamp(row["available_at"])
        latest[group] = max(latest.get(group, time), time)
    result = {"train": [], "development": [], "test": []}
    for group, row in zip(groups, records):
        time = latest[group]
        split = "train" if time <= first else "development" if time <= second else "test"
        result[split].append(row)
    return result


def deduplicate_events(records):
    """Prespecified one-record-per-(event,target) estimand, earliest view retained.

    Requires audited event IDs; does not infer semantic identity from text.
    Conflicting labels within an event-target must be reviewed, not silently merged.
    """
    selected = {}
    for row in sorted(records, key=lambda r: (_timestamp(r["available_at"]), str(r["id"]))):
        if not row.get("event_id") or not row.get("target"):
            raise ValueError("Event deduplication requires event_id and target")
        key = (str(row["event_id"]), str(row["target"]))
        if key in selected and selected[key]["label"] != row["label"]:
            raise ValueError("Conflicting event-target labels require manual review")
        selected.setdefault(key, row)
    return list(selected.values())


def cluster_bootstrap(records, repetitions=10000, seed=130, alpha=0.05, label_names=None):
    """Percentile bootstrap of row-weighted metrics, resampling entire clusters.

    Uses identical draws for paired model-baseline differences. Approximate
    uncertainty under independent representative clusters, not a finite-sample
    certificate and not a correction for model selection or temporal drift.
    """
    if len(records) == 0 or repetitions < 100 or not 0 < alpha < 1:
        raise ValueError("Need nonempty records, >=100 repetitions, 0<alpha<1")
    names = LABELS if label_names is None else label_names
    if (not isinstance(names, (list, tuple)) or len(names) != 3
            or any(not isinstance(name, str) or not name for name in names)
            or len(set(names)) != 3):
        raise ValueError("Exactly three distinct nonempty label names required")
    names = tuple(names)
    metric_names = ("accuracy", "macro_f1") + tuple(
        f"{label}_{metric}" for label in names for metric in ("precision", "recall", "f1"))
    ids = [str(row["id"]) for row in records]
    if len(set(ids)) != len(ids):
        raise ValueError("Prediction row IDs must be unique")
    groups = connected_groups(records)
    unique = sorted(set(groups))
    if len(unique) < 2:
        raise ValueError("At least two independent clusters are needed; many more are advisable")
    paired = ["baseline_prediction" in row for row in records]
    if any(paired) and not all(paired):
        raise ValueError("Paired comparison needs baseline predictions for every same row")
    systems = ["prediction"] + (["baseline_prediction"] if all(paired) else [])
    group_index = {group: i for i, group in enumerate(unique)}
    matrices = np.zeros((len(systems), len(unique), 3, 3), dtype=int)
    for row, group in zip(records, groups):
        actual = names.index(row["label"])
        for s, field in enumerate(systems):
            matrices[s, group_index[group], actual, names.index(row[field])] += 1
    rng = np.random.default_rng(seed)
    values = np.empty((len(systems), repetitions, len(METRICS)))
    # Bounded memory; count-cluster multinomial is equivalent to drawing clusters.
    for start in range(0, repetitions, 256):
        count = min(256, repetitions - start)
        weights = rng.multinomial(len(unique), np.full(len(unique), 1 / len(unique)), size=count)
        cms = np.einsum("bg,sgij->sbij", weights, matrices)
        values[:, start:start + count] = metrics_from_confusion(cms)
    point = metrics_from_confusion(matrices.sum(axis=1))
    def summary(observed, samples):
        low, high = np.quantile(samples, [alpha / 2, 1 - alpha / 2], axis=0)
        return {name: {"estimate": float(v), "lower": float(lo), "upper": float(hi)}
                for name, v, lo, hi in zip(metric_names, observed, low, high)}
    result = {"n_rows": len(records), "n_clusters": len(unique), "seed": seed,
              "repetitions": repetitions, "confidence_level": 1 - alpha, "label_names": list(names),
              "estimand": "row-weighted metric; connected family/event clusters resampled",
              "method": "percentile cluster bootstrap; approximate, selection unadjusted",
              "systems": {field: summary(point[s], values[s]) for s, field in enumerate(systems)}}
    if len(systems) == 2:
        result["paired_difference"] = summary(point[0] - point[1], values[0] - values[1])
    if len(unique) < 30:
        result["warning"] = "Fewer than 30 clusters: percentile coverage may be poor; no certified coverage."
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--repetitions", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=130)
    parser.add_argument("--labels", nargs=3, default=None,
                        help="Explicit source-task labels in the intended order; default retains legacy labels")
    args = parser.parse_args()
    raw = args.input.read_bytes()
    rows = [json.loads(line) for line in raw.decode("utf-8-sig").splitlines() if line.strip()]
    result = cluster_bootstrap(rows, args.repetitions, args.seed, label_names=args.labels)
    result["input_sha256"] = hashlib.sha256(raw).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
