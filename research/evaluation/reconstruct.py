"""Enumerate every integer confusion matrix matching the public rounded report."""
import hashlib
import json
from pathlib import Path
import platform
import time

import numpy as np

from .evaluate import METRICS, metrics_from_confusion


def compatible_matrices():
    # The precision rounding 4 d.p. uniquely gives predicted counts [11,66,24]
    # when correct counts [5,62,12] and actual supports [10,76,15] are accepted.
    result = []
    for a in range(6):
        for b in range(15):
            cm = np.array([[5, a, 5 - a], [b, 62, 14 - b], [6 - b, 4 - a, 12]])
            if (cm >= 0).all() and np.array_equal(cm.sum(axis=1), [10, 76, 15]):
                result.append(cm)
    return result


def main():
    started = time.perf_counter()
    seed, repetitions = 130, 100000
    rows = []
    for index, cm in enumerate(compatible_matrices()):
        rng = np.random.default_rng(np.random.SeedSequence([seed, index]))
        samples = rng.multinomial(101, cm.reshape(-1) / 101, size=repetitions).reshape(-1, 3, 3)
        metric_samples = metrics_from_confusion(samples)
        point = metrics_from_confusion(cm)
        low, high = np.quantile(metric_samples, [0.025, 0.975], axis=0)
        rows.append({"matrix_id": index + 1, "matrix": cm.tolist(), "metrics": {
            name: {"estimate": float(v), "lower": float(lo), "upper": float(hi)}
            for name, v, lo, hi in zip(METRICS, point, low, high)}})
    source = Path("docs/experiment-results.md")
    if not source.is_file():
        source = Path(__file__).resolve().parents[2] / "source_materials/130U-FinLLM/docs/experiment-results.md"
    result = {"experiment": "wp0_1", "input_level": "public report of user-supplied run logs",
              "computation_level": "our experiment", "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "seed": seed, "replicates_per_matrix": repetitions, "numpy": np.__version__,
              "python": platform.python_version(), "machine": platform.machine(), "processor": platform.processor(),
              "elapsed_seconds": time.perf_counter() - started,
              "method": "IID row percentile bootstrap; not event-cluster bootstrap",
              "selection_adjustment": False, "paired_baseline_test": "not identified from reported aggregates",
              "matrices": rows}
    out = Path("research/experiments/wp0_1/reconstruction.json")
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"matrices": len(rows), "seconds": result["elapsed_seconds"],
                      "macro_f1": [r["metrics"]["macro_f1"] for r in rows]}, indent=2))


if __name__ == "__main__":
    main()
