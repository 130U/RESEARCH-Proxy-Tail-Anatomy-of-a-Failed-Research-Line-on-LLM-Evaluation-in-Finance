"""Synthetic leakage, task-semantics and private-output tests; not model evidence."""
import copy
from fractions import Fraction
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import warnings

import numpy as np
from sklearn.exceptions import ConvergenceWarning

from research.real_baseline import train_baselines as train


def tiny_rows():
    rows = []
    targets = ('Acme', 'Bravo', 'Cygnus')
    words = ('loss decline', 'steady unchanged', 'growth profit')
    for split, marker in [('train', 'training'), ('development', 'devsentinel'), ('test', 'testsentinel')]:
        for i, label in enumerate(train.CLASSES):
            for replicate in range(2):
                identity = f'{split}-{i}-{replicate}'
                rows.append({'id': identity, 'family_id': identity, 'split': split,
                             'headline': f'{targets[i]} reports {words[i]} {marker} {replicate}',
                             'target': targets[i], 'label': label, 'label_id': i})
    return rows


class BaselineTests(unittest.TestCase):
    def test_target_marking_is_literal_bounded_and_shared(self):
        row = {'target': 'Acme', 'headline': 'ACME rises; Acme falls; Acmeology stays.',
               'input_text': 'this display field must never become a feature'}
        self.assertEqual(train.model_text(row),
                         '[ENTITY] Acme\n[TITLE] TARGET_ENTITY rises; TARGET_ENTITY falls; Acmeology stays.')
        punctuation = {'target': 'A+B', 'headline': 'A+B and a+b rise; XA+B is distinct.'}
        self.assertEqual(train._marked_headline(punctuation)[1], 2)
        self.assertEqual(train._marked_headline({'target': 'Missing', 'headline': 'A company changes.'})[1], 0)

    def test_fixed_class_macro_and_majority_tie(self):
        metrics = train.metric_summary(['negative'], ['negative'])
        self.assertEqual(Fraction(metrics['macro_f1_exact']), Fraction(1, 3))
        models, predictions, summary = train.fit_baselines(tiny_rows())
        self.assertEqual(summary['systems']['majority']['majority_label'], 'negative')
        self.assertTrue(all(row['prediction'] == 'negative' for row in predictions['majority']['test']))
        self.assertEqual(tuple(models['majority'].classes_), train.CLASSES)

    def test_only_train_fits_vocabulary_idf_and_weights(self):
        models, _, summary = train.fit_baselines(tiny_rows())
        word = models['word_tfidf_lr'].named_steps['tfidf']
        self.assertIn('training', word.vocabulary_)
        self.assertNotIn('devsentinel', word.vocabulary_)
        self.assertNotIn('testsentinel', word.vocabulary_)
        entity = models['entity_only_tfidf_lr'].named_steps['tfidf']
        self.assertEqual(set(entity.vocabulary_), {'acme', 'bravo', 'cygnus'})
        for system in train.SYSTEMS[1:]:
            item = summary['systems'][system]
            candidates = item['candidate_development_results']
            expected = min(candidates, key=lambda c: (-Fraction(c['development']['macro_f1_exact']), c['C']))
            self.assertEqual(item['selected_C'], expected['C'])
            self.assertEqual(item['fit_rows'], 6)
        for stage in ('libraries_before_fit', 'libraries_after_fit'):
            self.assertTrue(summary['thread_control'][stage])
            self.assertTrue(all(1 <= item['num_threads'] <= 2 for item in summary['thread_control'][stage]))

    def test_test_label_changes_cannot_select_C_or_change_fitted_parameters(self):
        rows = tiny_rows()
        original, _, summary = train.fit_baselines(rows)
        changed = copy.deepcopy(rows)
        for row in changed:
            if row['split'] == 'test':
                row['label_id'] = (row['label_id'] + 1) % 3
                row['label'] = train.CLASSES[row['label_id']]
        alternate, _, other = train.fit_baselines(changed)
        for system in train.SYSTEMS[1:]:
            self.assertEqual(summary['systems'][system]['selected_C'], other['systems'][system]['selected_C'])
            np.testing.assert_array_equal(original[system].named_steps['classifier'].coef_,
                                          alternate[system].named_steps['classifier'].coef_)
            np.testing.assert_array_equal(original[system].named_steps['tfidf'].idf_,
                                          alternate[system].named_steps['tfidf'].idf_)

    def test_split_leakage_and_invalid_data_rejected_without_resplitting(self):
        rows = tiny_rows()
        corruptions = []
        duplicate = copy.deepcopy(rows); duplicate[-1]['id'] = duplicate[0]['id']; corruptions.append(duplicate)
        family = copy.deepcopy(rows); family[-1]['family_id'] = family[0]['family_id']; corruptions.append(family)
        headline = copy.deepcopy(rows); headline[-1]['headline'] = '  ' + headline[0]['headline'].upper() + ' '; corruptions.append(headline)
        label = copy.deepcopy(rows); label[0]['label'] = 'bullish'; corruptions.append(label)
        label_id = copy.deepcopy(rows); label_id[0]['label_id'] = False; corruptions.append(label_id)
        raw = copy.deepcopy(rows); raw[0]['input_text'] = 'label-leaking alternative input'; corruptions.append(raw)
        corruptions.append([r for r in rows if r['split'] != 'test'])
        corruptions.append([r for r in rows if not (r['split'] == 'train' and r['label'] == 'positive')])
        for index, data in enumerate(corruptions):
            with self.subTest(case=index), self.assertRaises(ValueError):
                train.validate_rows(data)

    def test_convergence_warnings_are_recorded(self):
        actual_fit = train.LogisticRegression.fit
        def warned_fit(model, *args, **kwargs):
            warnings.warn('synthetic convergence-warning propagation check', ConvergenceWarning)
            return actual_fit(model, *args, **kwargs)
        with patch.object(train.LogisticRegression, 'fit', warned_fit):
            _, _, summary = train.fit_baselines(tiny_rows())
        for system in train.SYSTEMS[1:]:
            self.assertTrue(summary['systems'][system]['selected_convergence_warning'])
            self.assertTrue(all(c['convergence_warning'] for c in summary['systems'][system]['candidate_development_results']))

    def test_private_artifacts_and_aggregate_no_raw_text(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            private, aggregate = base / 'private', base / 'aggregate'
            private.mkdir(); aggregate.mkdir()
            input_path = private / 'rows.jsonl'
            rows = tiny_rows()
            input_path.write_text(''.join(json.dumps(r) + '\n' for r in rows), encoding='utf-8')
            summary_path = aggregate / 'summary.json'
            with patch.object(train, 'PRIVATE_ROOT', private), patch.object(train, 'AGGREGATE_ROOT', aggregate):
                summary = train.run(input_path, private / 'new-run', summary_path)
                with self.assertRaises(ValueError):
                    train.run(input_path, base / 'public-models', aggregate / 'another.json')
                with self.assertRaises(ValueError):
                    train.run(input_path, private / 'new-run', aggregate / 'another.json')
            text = summary_path.read_text(encoding='utf-8')
            for row in rows:
                self.assertNotIn(row['headline'], text)
                self.assertNotIn(row['id'], text)
            self.assertNotIn('"vocabulary_":', text)
            self.assertEqual(set(summary['systems']), set(train.SYSTEMS))
            files = list((private / 'new-run').rglob('*.joblib'))
            self.assertEqual(len(files), 4)
            self.assertEqual(len(list((private / 'new-run' / 'predictions').glob('*.jsonl'))), 12)
            joint = [json.loads(line) for line in (private / 'new-run' / 'predictions_test.jsonl').read_text().splitlines()]
            self.assertEqual(len(joint), 6)
            self.assertTrue(all(set(row['predictions']) == set(train.SYSTEMS) for row in joint))
            self.assertEqual(list(aggregate.iterdir()), [summary_path])

    def test_manifest_hash_mismatch_rejected_before_any_fitting(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            private, aggregate, manifests = base / 'private', base / 'aggregate', base / 'manifests'
            private.mkdir(); aggregate.mkdir(); manifests.mkdir()
            source = private / 'rows.jsonl'
            source.write_text('{}\n', encoding='utf-8')
            manifest = manifests / 'aggregate_manifest.json'
            manifest.write_text(json.dumps({'labels': list(train.CLASSES),
                                           'private_artifact_fingerprints': {'rows.jsonl': {'sha256': 'wrong'}}}), encoding='utf-8')
            with patch.object(train, 'PRIVATE_ROOT', private), patch.object(train, 'AGGREGATE_ROOT', aggregate), \
                    patch.object(train, 'MANIFEST_ROOT', manifests), patch.object(train, 'fit_baselines') as fit:
                with self.assertRaises(ValueError):
                    train.run(source, private / 'run', aggregate / 'summary.json', manifest)
                fit.assert_not_called()


if __name__ == '__main__':
    unittest.main()
