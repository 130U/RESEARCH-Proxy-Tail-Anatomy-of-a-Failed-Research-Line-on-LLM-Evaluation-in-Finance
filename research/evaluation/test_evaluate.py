import unittest
import numpy as np
from research.evaluation.evaluate import (
    cluster_bootstrap, connected_groups, chronological_split,
    deduplicate_events, metrics_from_confusion,
)
from research.evaluation.reconstruct import compatible_matrices


class EvaluationTests(unittest.TestCase):
    def rows(self):
        return [{"id": str(i), "family_id": str(i // 2), "event_id": str(i // 2),
                 "target": "A", "available_at": f"2020-01-{i + 1:02d}T00:00:00Z",
                 "label": "neutral", "prediction": "neutral", "baseline_prediction": "neutral"}
                for i in range(8)]

    def test_four_matrices_complete(self):
        matrices = compatible_matrices()
        self.assertEqual(len(matrices), 4)
        for cm in matrices:
            np.testing.assert_array_equal(cm.sum(0), [11, 66, 24])
            np.testing.assert_array_equal(cm.sum(1), [10, 76, 15])
            np.testing.assert_array_equal(cm.diagonal(), [5, 62, 12])
            self.assertAlmostEqual(metrics_from_confusion(cm)[0], 79 / 101)

    def test_paired_identical_is_exactly_zero(self):
        result = cluster_bootstrap(self.rows(), 500)
        for value in result["paired_difference"].values():
            self.assertEqual(value, {"estimate": 0.0, "lower": 0.0, "upper": 0.0})
        self.assertEqual(result["n_clusters"], 4)

    def test_transitive_family_and_event_join(self):
        rows = self.rows()[:3]
        rows[0]["family_id"], rows[1]["family_id"] = "F", "F"
        rows[1]["event_id"], rows[2]["event_id"] = "E", "E"
        self.assertEqual(len(set(connected_groups(rows))), 1)

    def test_group_with_future_member_never_enters_training(self):
        result = chronological_split(self.rows(), "2020-01-03T00:00:00Z", "2020-01-06T00:00:00Z")
        self.assertEqual([r["id"] for r in result["train"]], ["0", "1"])
        self.assertEqual([r["id"] for r in result["development"]], ["2", "3", "4", "5"])

    def test_dedupe_rejects_label_conflict(self):
        rows = self.rows()
        self.assertEqual(len(deduplicate_events(rows)), 4)
        rows[1]["label"] = "bullish"
        with self.assertRaises(ValueError):
            deduplicate_events(rows)

    def test_missing_groups_or_partial_baseline_rejected(self):
        rows = self.rows()
        del rows[0]["baseline_prediction"]
        with self.assertRaises(ValueError):
            cluster_bootstrap(rows, 100)
        del rows[0]["event_id"]
        del rows[0]["family_id"]
        with self.assertRaises(ValueError):
            connected_groups(rows)

    def test_metrics_absent_class_and_bad_input(self):
        values = metrics_from_confusion(np.diag([0, 3, 0]))
        self.assertAlmostEqual(values[1], 1 / 3)
        with self.assertRaises(ValueError):
            metrics_from_confusion(np.zeros((3, 3)))

    def test_explicit_source_labels_preserve_semantics_and_numeric_results(self):
        names = ('negative', 'neutral', 'positive')
        legacy = ('bearish', 'neutral', 'bullish')
        rows = self.rows()
        for i, row in enumerate(rows):
            row['label'] = names[i % 3]
            row['prediction'] = names[(i + int(i == 0)) % 3]
            row['baseline_prediction'] = names[(i + int(i < 3)) % 3]
        result = cluster_bootstrap(rows, 500, label_names=names)
        renamed = [{**row, **{key:legacy[names.index(row[key])]
                              for key in ('label','prediction','baseline_prediction')}} for row in rows]
        numeric_reference = cluster_bootstrap(renamed, 500)
        self.assertEqual(result['label_names'], list(names))
        self.assertIn('negative_f1', result['systems']['prediction'])
        self.assertNotIn('bearish_f1', result['systems']['prediction'])
        self.assertEqual(result['paired_difference']['macro_f1'],
                         numeric_reference['paired_difference']['macro_f1'])
        for invalid in ([], ['negative'], ['a','a','b'], ['a','b',None], 'abc'):
            with self.assertRaises(ValueError):
                cluster_bootstrap(rows, 100, label_names=invalid)


if __name__ == "__main__":
    unittest.main()
