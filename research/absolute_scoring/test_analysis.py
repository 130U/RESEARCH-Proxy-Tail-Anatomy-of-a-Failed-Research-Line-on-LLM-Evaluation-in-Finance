"""Synthetic checks of statistical semantics; no experimental scores are read."""
import csv
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from scipy.integrate import quad
from scipy.stats import norm

from analyze_scores import (PredictionGrid, control_analysis, gaussian_joint, gaussian_prediction,
                            head_set, minimal_release, normal_scores,
                            paired_resample, reliability, tail_metrics, load_inputs,
                            run_bootstrap)


class TailSemanticsTests(unittest.TestCase):
    def test_entire_boundary_group_not_only_expansion(self):
        scores = np.array([100, 99, 98, 97, 96, 95, 95, 95, 95, 95,
                           90, 80, 70, 60, 50, 40, 30, 20, 10, 0])
        head, info = head_set(scores, .5, "upper")
        self.assertEqual(head.sum(), 10)
        self.assertEqual(info["expansion_n"], 0)
        self.assertEqual(info["boundary_n"], 5)
        self.assertTrue(info["tie_gate_failed"])

    def test_directional_overlap_can_differ(self):
        a = np.array([5, 5, 5, 4, 3, 2, 1, 0, 0, 0] + [0] * 10)
        b = np.array([5, 4, 3, 5, 2, 1, 0, 0, 0, 0] + [0] * 10)
        scores = np.column_stack([a] * 4 + [b] * 4)
        rows = [r for r in tail_metrics(scores) if r["m"] == 1 and r["p"] == .1 and r["tail"] == "upper"]
        self.assertAlmostEqual(rows[0]["overlap"], 1 / 3)
        self.assertAlmostEqual(rows[1]["overlap"], 1 / 2)

    def test_minimal_release_includes_full_candidate_boundary(self):
        candidate = np.array([10, 9, 8, 8, 8, 7, 6, 5, 4, 3])
        reference = np.array([True, True, True] + [False] * 7)
        result = minimal_release(candidate, reference, .2, "upper")
        self.assertEqual(result["released_n"], 5)
        self.assertEqual(result["target_recovered_n"], 3)
        self.assertEqual(result["widening"], 2.5)

    def test_release_may_be_less_than_nominal_head(self):
        candidate = np.arange(100)
        reference, _ = head_set(candidate, .2, "upper")
        result = minimal_release(candidate, reference, .2, "upper")
        self.assertEqual(result["released_n"], 18)
        self.assertEqual(result["widening"], .9)

    def test_bootstrap_carries_all_rounds_and_duplicate_weight(self):
        matrix = np.arange(32).reshape(4, 8)
        result = paired_resample(matrix, np.array([2, 2, 0, 3]))
        np.testing.assert_array_equal(result[0], matrix[2])
        np.testing.assert_array_equal(result[1], matrix[2])
        self.assertEqual(result.shape, (4, 8))

    def test_normal_scores_preserve_ties_and_constant_undefined(self):
        z = normal_scores(np.array([1, 1, 2, 3]))
        self.assertEqual(z[0], z[1])
        r, pairs = reliability(np.ones((30, 8)))
        self.assertTrue(np.isnan(r))
        self.assertTrue(np.isnan(pairs).all())

    def test_perfect_repeats_and_control(self):
        scores = np.tile(np.arange(100)[:, None], (1, 8))
        r, pairs = reliability(scores)
        self.assertAlmostEqual(r, 1)
        np.testing.assert_allclose(pairs, 1)
        controls = scores[:, :2]
        result = control_analysis(scores, controls, 30, seed=66)
        self.assertAlmostEqual(result["same_minus_different_r"], 0, places=12)


class GaussianTests(unittest.TestCase):
    def test_independent_and_perfect_limits(self):
        for p in (.2, .1, .05):
            self.assertEqual(gaussian_prediction(0, 4, p), (p, .9 / p))
            self.assertEqual(gaussian_prediction(1, 4, p), (1, .9))
            self.assertAlmostEqual(gaussian_joint(p, .3, 0), p * .3)
            self.assertEqual(gaussian_joint(p, .3, 1), min(p, .3))

    def test_quadrature_against_independent_conditional_integral(self):
        for p, q, rho in ((.1, .1, .5), (.05, .3, .92), (.2, .19, .999)):
            a, b = norm.isf(p), norm.isf(q)
            expected, _ = quad(lambda x: norm.pdf(x) * norm.sf((b - rho * x) / np.sqrt(1 - rho**2)),
                               a, np.inf, epsabs=1e-11)
            self.assertAlmostEqual(gaussian_joint(p, q, rho), expected, places=8)

    def test_release_root_and_sb(self):
        r, p, m = .7, .1, 4
        overlap, widening = gaussian_prediction(r, m, p)
        rho = m * r / (1 + (m - 1) * r)
        self.assertAlmostEqual(gaussian_joint(p, widening * p, rho) / p, .9, places=8)
        self.assertAlmostEqual(gaussian_joint(p, p, rho) / p, overlap, places=10)
        self.assertGreater(overlap, gaussian_prediction(r, 1, p)[0])

    def test_invalid_r_not_clamped(self):
        self.assertTrue(np.isnan(gaussian_prediction(-.1, 2, .1)[0]))
        self.assertTrue(np.isnan(gaussian_prediction(float("nan"), 2, .1)[0]))

    def test_full_prediction_grid_and_bootstrap_smoke(self):
        grid = PredictionGrid()
        self.assertLess(max(v["max_midpoint_widening_error"] for v in grid.validation["errors"].values()), 1e-6)
        rng = np.random.default_rng(19)
        common = rng.normal(size=(200, 1))
        scores = np.rint(np.clip(50 + 14 * common + rng.normal(size=(200, 8)) * 4, 0, 100)).astype(int)
        rows = tail_metrics(scores)
        result = run_bootstrap(scores, rows, 100, grid, seed=144)
        self.assertEqual(result["repetitions"], 100)
        self.assertEqual(len(result["asymmetry"]), 18)
        self.assertEqual(len(rows), 36)
        self.assertTrue(all(row["prediction_overlap_valid_bootstraps"] == 100 for row in rows))
        self.assertTrue(all(0 <= row["overlap_ci95"][0] <= row["overlap_ci95"][1] <= 1 for row in rows))


class InputValidationTests(unittest.TestCase):
    def test_complete_synthetic_input_contract_and_reject_bool_score(self):
        # Synthetic fixture exists only in a temporary directory, never in the
        # research score directory; IDs deliberately differ from experiment IDs.
        with tempfile.TemporaryDirectory(prefix="absolute_analysis_test_") as tmp:
            root = Path(tmp)
            raw = root / "raw_scores"
            raw.mkdir()
            ids = [f"SYNTH_{i:04}" for i in range(1000)]

            def csv_write(name, fields, rows):
                with (root / name).open("w", newline="", encoding="utf-8") as stream:
                    writer = csv.DictWriter(stream, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows(rows)

            csv_write("sample.csv", ["id", "original_id", "family_id", "source_ids"],
                      [{"id": i, "original_id": i, "family_id": f"F_{i}", "source_ids": "[]"} for i in ids])
            csv_write("control_ids.csv", ["id"], [{"id": i} for i in ids[:100]])
            batches, schedule = [], []
            for r in range(1, 9):
                for b in range(1, 26):
                    key = f"r{r:02}_b{b:02}"
                    group = ids[(b - 1) * 40:b * 40]
                    batches.extend({"input_key": key, "position": p + 1, "id": i} for p, i in enumerate(group))
                    schedule.append({"call_id": key, "kind": "main", "round": r, "batch": b, "input_key": key})
                    scores = {i: (j + b + r) % 101 for j, i in enumerate(group)}
                    (raw / f"{key}.json").write_text(json.dumps(scores), encoding="utf-8")
                    if r == 1 and b <= 3:
                        for c in (1, 2):
                            call = f"c{c}_b{b:02}"
                            schedule.append({"call_id": call, "kind": "control", "round": "", "batch": b, "input_key": key})
                            (raw / f"{call}.json").write_text(json.dumps(scores), encoding="utf-8")
            csv_write("batches.csv", ["input_key", "position", "id"], batches)
            csv_write("schedule.csv", ["call_id", "kind", "round", "batch", "input_key"], schedule)
            loaded = load_inputs(root)
            self.assertEqual(loaded.main.shape, (1000, 8))
            self.assertEqual(loaded.controls.shape, (100, 2))
            self.assertEqual(loaded.counts["main_calls"], 200)
            self.assertEqual(loaded.counts["control_all_scores_including_nonfocal"], 240)
            invalid = json.loads((raw / "r01_b01.json").read_text())
            invalid[ids[0]] = True
            (raw / "r01_b01.json").write_text(json.dumps(invalid))
            with self.assertRaisesRegex(ValueError, "Noninteger"):
                load_inputs(root)


if __name__ == "__main__":
    unittest.main()
