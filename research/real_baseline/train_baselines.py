"""Train frozen local entity-sentiment baselines; no downloads or model loads.

Only development macro-F1 selects C. Both main models consume the same literal
target-marker rendering, and all vocabularies/IDF/weights use train rows only.
Entity-only is a prespecified shortcut diagnostic, not a competing main result.
Individual predictions and newly fitted joblib models are confined to private/;
only aggregate counts, metrics, hashes and runtime metadata leave that directory.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import ExitStack, contextmanager
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
import unicodedata
import warnings
from unittest.mock import patch

# Set process-local startup hints before importing any numerical library. The
# runtime controller below also verifies limits if a caller imported NumPy first.
THREAD_ENVIRONMENT = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'BLIS_NUM_THREADS')
for _thread_environment_name in THREAD_ENVIRONMENT:
    os.environ[_thread_environment_name] = '2'

import joblib
import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from threadpoolctl import ThreadpoolController, threadpool_info


CLASSES = ('negative', 'neutral', 'positive')
SPLITS = ('train', 'development', 'test')
SYSTEMS = ('majority', 'word_tfidf_lr', 'char_tfidf_lr', 'entity_only_tfidf_lr')
SEED = 130
C_VALUES = (0.1, 1.0, 10.0)
MAX_FEATURES = 50000
THREADS = 2
RESEARCH_ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = RESEARCH_ROOT / 'private'
AGGREGATE_ROOT = RESEARCH_ROOT / 'experiments' / 'real_baseline'
MANIFEST_ROOT = RESEARCH_ROOT / 'real_baseline'


def frozen_config():
    return {
        'classes': list(CLASSES), 'splits': list(SPLITS), 'seed': SEED,
        'main_comparison': 'char_tfidf_lr minus word_tfidf_lr, paired test macro-F1',
        'diagnostics': ['train-majority sanity baseline', 'entity-only identity shortcut'],
        'selection': 'maximum development fixed-three-class macro-F1; exact-score ties choose smaller C',
        'fit_scope': 'train only; no refit on development after C selection',
        'evaluation_scope': 'same fixed rows for every system; test does not select model or C',
        'input_rule': "[ENTITY] {original target}\\n[TITLE] {headline with whole-word case-insensitive literal target replaced by TARGET_ENTITY}",
        'target_pattern': r'(?<!\w)' + '{re.escape(target)}' + r'(?!\w)',
        'input_text_field': 'raw display metadata only; never consumed as features',
        'target_marker': 'fixed literal rule, not NER or semantic entity disambiguation',
        'tfidf_common': {'lowercase': True, 'max_features': MAX_FEATURES, 'min_df': 1,
                         'max_df': 1.0, 'norm': 'l2', 'use_idf': True, 'smooth_idf': True,
                         'sublinear_tf': False, 'dtype': 'float64'},
        'word': {'analyzer': 'word', 'ngram_range': [1, 2], 'token_pattern': r'(?u)\b\w+\b'},
        'char': {'analyzer': 'char_wb', 'ngram_range': [3, 5]},
        'entity_only': {'analyzer': 'word', 'ngram_range': [1, 2], 'token_pattern': r'(?u)\b\w+\b',
                        'input': 'target string only'},
        'logistic_regression': {'C_values': list(C_VALUES), 'class_weight': 'balanced',
                                'max_iter': 1000, 'tol': 1e-4, 'solver': 'lbfgs',
                                'random_state': SEED},
        'cpu_threads': THREADS, 'zero_division': 0,
        'probabilities': 'fitted class scores; no calibration guarantee',
        'task': 'dataset entity-conditioned negative/neutral/positive sentiment, not asset-holder stance',
    }


def _marked_headline(row):
    pattern = r'(?<!\w)' + re.escape(row['target']) + r'(?!\w)'
    return re.subn(pattern, 'TARGET_ENTITY', row['headline'], flags=re.IGNORECASE)


def model_text(row):
    """Shared main-model input. Raw input_text is deliberately ignored."""
    headline, _ = _marked_headline(row)
    return '[ENTITY] ' + row['target'] + '\n[TITLE] ' + headline


def _headline_key(value):
    return ' '.join(unicodedata.normalize('NFKC', value).casefold().split())


def validate_rows(rows):
    if not isinstance(rows, (list, tuple)) or not rows:
        raise ValueError('nonempty list/tuple of prepared rows required')
    grouped = {split: [] for split in SPLITS}
    ids, family_splits, headline_splits = set(), {}, {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f'row {index} is not a mapping')
        for field in ('id', 'headline', 'target', 'label', 'family_id', 'split'):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError(f'row {index} requires nonempty string field {field}')
        if row['id'] in ids:
            raise ValueError(f'duplicate row ID at row {index}')
        ids.add(row['id'])
        if row['label'] not in CLASSES or row['split'] not in SPLITS:
            raise ValueError(f'invalid class or split at row {index}')
        if 'label_id' in row and (type(row['label_id']) is not int or row['label_id'] != CLASSES.index(row['label'])):
            raise ValueError(f'label_id disagrees with label at row {index}')
        if 'input_text' in row:
            expected = '[ENTITY] ' + row['target'] + '\n[TITLE] ' + row['headline']
            if row['input_text'] != expected:
                raise ValueError(f'raw display input_text is inconsistent at row {index}')
        split = row['split']
        family = row['family_id']
        if family in family_splits and family_splits[family] != split:
            raise ValueError('a family crosses dataset splits')
        family_splits[family] = split
        key = _headline_key(row['headline'])
        if key in headline_splits and headline_splits[key] != split:
            raise ValueError('a normalized identical headline crosses dataset splits')
        headline_splits[key] = split
        grouped[split].append(row)
    if any(not group for group in grouped.values()):
        raise ValueError('train, development and test must each be nonempty; no automatic resplit')
    if {row['label'] for row in grouped['train']} != set(CLASSES):
        raise ValueError('the frozen three-class training protocol requires all classes in train')
    return grouped


def metric_summary(labels, predictions):
    if len(labels) != len(predictions) or not labels:
        raise ValueError('nonempty aligned labels and predictions required')
    confusion = [[0] * len(CLASSES) for _ in CLASSES]
    for actual, predicted in zip(labels, predictions):
        confusion[CLASSES.index(actual)][CLASSES.index(predicted)] += 1
    actual_counts = [sum(row) for row in confusion]
    predicted_counts = [sum(row[j] for row in confusion) for j in range(len(CLASSES))]
    per_class, exact_f1 = {}, []
    for i, label in enumerate(CLASSES):
        tp, support, predicted = confusion[i][i], actual_counts[i], predicted_counts[i]
        precision = Fraction(tp, predicted) if predicted else Fraction(0)
        recall = Fraction(tp, support) if support else Fraction(0)
        f1 = Fraction(2 * tp, support + predicted) if support + predicted else Fraction(0)
        exact_f1.append(f1)
        per_class[label] = {'precision': float(precision), 'recall': float(recall),
                            'f1': float(f1), 'support': support, 'predicted': predicted}
    macro = sum(exact_f1) / len(CLASSES)
    accuracy = Fraction(sum(confusion[i][i] for i in range(len(CLASSES))), len(labels))
    return {'n_rows': len(labels), 'accuracy': float(accuracy), 'accuracy_exact': str(accuracy),
            'macro_f1': float(macro), 'macro_f1_exact': str(macro),
            'classes': list(CLASSES), 'confusion_matrix': confusion, 'per_class': per_class}


def _vectorizer(kind):
    common = dict(lowercase=True, max_features=MAX_FEATURES, min_df=1, max_df=1.0,
                  norm='l2', use_idf=True, smooth_idf=True, sublinear_tf=False, dtype=np.float64)
    if kind == 'char_tfidf_lr':
        return TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), **common)
    return TfidfVectorizer(analyzer='word', ngram_range=(1, 2), token_pattern=r'(?u)\b\w+\b', **common)


def _warning_record(caught):
    return [{'category': item.category.__name__, 'message': str(item.message)} for item in caught]


def _verified_thread_info():
    info = [{'user_api': item.get('user_api'), 'internal_api': item.get('internal_api'),
             'num_threads': item.get('num_threads')} for item in threadpool_info()]
    if not info or any(type(item['num_threads']) is not int or not 1 <= item['num_threads'] <= THREADS for item in info):
        raise RuntimeError('cannot verify numerical-library thread limits <= 2; training stopped')
    return info


@contextmanager
def _cpu_thread_limits():
    """Use native controls; narrowly recover a Windows Unicode snapshot failure.

In this environment Module32 snapshot paths contain '?' in place of Chinese
directory names. The library's own EnumProcessModulesEx/GetModuleFileNameW
fallback resolves the loaded modules correctly. The patch is process-local,
scoped to this context, and does not modify site-packages or ignore failures.
It also covers sklearn's internally constructed ThreadpoolControllers.
"""
    with ExitStack() as stack:
        discovery = 'native threadpoolctl discovery'
        try:
            controller = ThreadpoolController()
        except FileNotFoundError:
            if sys.platform != 'win32' or not hasattr(ThreadpoolController, '_snapshot_loaded_modules'):
                raise
            stack.enter_context(patch.object(ThreadpoolController, '_snapshot_loaded_modules', return_value=None))
            controller = ThreadpoolController()
            discovery = 'Windows snapshot FileNotFoundError: scoped fallback to EnumProcessModulesEx and Unicode module paths'
        stack.enter_context(controller.limit(limits=THREADS))
        evidence = {'discovery': discovery, 'environment_requests': {name: os.environ[name] for name in THREAD_ENVIRONMENT},
                    'libraries_before_fit': _verified_thread_info(),
                    'measurement': 'library-reported configured thread limits; not measured peak OS thread count'}
        yield evidence
        evidence['libraries_after_fit'] = _verified_thread_info()


def _predict_records(model, rows, texts):
    predicted = model.predict(texts).tolist()
    probabilities = model.predict_proba(texts)
    class_order = list(model.classes_)
    if set(class_order) != set(CLASSES):
        raise AssertionError('fitted model lost a required training class')
    probabilities = probabilities[:, [class_order.index(label) for label in CLASSES]]
    if not np.isfinite(probabilities).all() or not np.allclose(probabilities.sum(axis=1), 1):
        raise ArithmeticError('invalid fitted probabilities')
    records = [{'id': row['id'], 'family_id': row['family_id'], 'split': row['split'],
                'label': row['label'], 'prediction': prediction,
                'probabilities': [float(v) for v in probability]}
               for row, prediction, probability in zip(rows, predicted, probabilities)]
    return records, metric_summary([row['label'] for row in rows], predicted)


def fit_baselines(rows):
    """Fit new objects from rows; return models/private predictions/aggregates.

This in-memory function is also used by leakage tests. It never reads an old
checkpoint or lets test labels/text fit a vectorizer, classifier or C selector.
"""
    grouped = validate_rows(rows)
    texts = {split: [model_text(row) for row in group] for split, group in grouped.items()}
    labels = {split: [row['label'] for row in group] for split, group in grouped.items()}
    started, cpu_started = time.perf_counter(), time.process_time()
    models, private_predictions, systems = {}, {}, {}
    with _cpu_thread_limits() as thread_evidence:
        tick, cpu_tick = time.perf_counter(), time.process_time()
        majority = DummyClassifier(strategy='prior', random_state=SEED)
        majority.fit(texts['train'], labels['train'])
        models['majority'] = majority
        systems['majority'] = {
            'role': 'sanity_baseline', 'fit_rows': len(grouped['train']),
            'majority_label': str(majority.classes_[int(np.argmax(majority.class_prior_))]),
            'tie_rule': 'first in fixed negative/neutral/positive class order',
            'selected_C': None, 'candidate_development_results': [], 'warnings': [],
            'fit_wall_seconds': time.perf_counter() - tick, 'fit_cpu_seconds': time.process_time() - cpu_tick,
        }
        for kind in SYSTEMS[1:]:
            fit_texts = ({split: [row['target'] for row in group] for split, group in grouped.items()}
                         if kind == 'entity_only_tfidf_lr' else texts)
            tick, cpu_tick = time.perf_counter(), time.process_time()
            vectorizer = _vectorizer(kind)
            X_train = vectorizer.fit_transform(fit_texts['train'])
            X_development = vectorizer.transform(fit_texts['development'])
            vectorizer_wall, vectorizer_cpu = time.perf_counter() - tick, time.process_time() - cpu_tick
            candidates, best_model, best_score, best_C, best_warnings = [], None, None, None, None
            for C in C_VALUES:
                classifier = LogisticRegression(C=C, class_weight='balanced', max_iter=1000,
                                                tol=1e-4, solver='lbfgs', random_state=SEED)
                tick, cpu_tick = time.perf_counter(), time.process_time()
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always')
                    classifier.fit(X_train, labels['train'])
                fit_wall, fit_cpu = time.perf_counter() - tick, time.process_time() - cpu_tick
                prediction = classifier.predict(X_development).tolist()
                metrics = metric_summary(labels['development'], prediction)
                score = Fraction(metrics['macro_f1_exact'])
                captured = _warning_record(caught)
                candidates.append({'C': C, 'development': metrics,
                                   'n_iter': classifier.n_iter_.tolist(), 'warnings': captured,
                                   'convergence_warning': any(issubclass(w.category, ConvergenceWarning) for w in caught),
                                   'fit_wall_seconds': fit_wall, 'fit_cpu_seconds': fit_cpu})
                if best_score is None or score > best_score:
                    best_model, best_score, best_C, best_warnings = classifier, score, C, captured
            models[kind] = Pipeline([('tfidf', vectorizer), ('classifier', best_model)])
            systems[kind] = {
                'role': 'identity_shortcut_diagnostic' if kind == 'entity_only_tfidf_lr' else 'main_baseline',
                'selected_C': best_C, 'selection_score_exact': str(best_score),
                'fit_rows': len(grouped['train']), 'vocabulary_size': len(vectorizer.vocabulary_),
                'vectorizer_fit_scope': 'train only', 'selected_classifier_fit_scope': 'train only',
                'vectorizer_wall_seconds': vectorizer_wall, 'vectorizer_cpu_seconds': vectorizer_cpu,
                'candidate_development_results': candidates, 'warnings': best_warnings,
                'selected_convergence_warning': any(w['category'] == 'ConvergenceWarning' for w in best_warnings),
            }
        # Test labels first affect metrics here, after every C has been selected.
        for name, model in models.items():
            private_predictions[name], systems[name]['metrics_by_split'] = {}, {}
            for split in SPLITS:
                features = ([row['target'] for row in grouped[split]]
                            if name == 'entity_only_tfidf_lr' else texts[split])
                records, metrics = _predict_records(model, grouped[split], features)
                private_predictions[name][split] = records
                systems[name]['metrics_by_split'][split] = metrics
    counts = {}
    for split, group in grouped.items():
        replacements = [_marked_headline(row)[1] for row in group]
        frequencies = Counter(row['label'] for row in group)
        counts[split] = {'n_rows': len(group), 'n_families': len({row['family_id'] for row in group}),
                         'class_counts': {label: frequencies[label] for label in CLASSES},
                         'literal_target_matched_rows': sum(n > 0 for n in replacements),
                         'literal_target_unmatched_rows': sum(n == 0 for n in replacements),
                         'literal_replacements': sum(replacements)}
    aggregate = {
        'status': 'new_local_baselines_fitted', 'config': frozen_config(), 'split_counts': counts,
        'systems': systems, 'thread_control': thread_evidence,
        'fit_and_evaluation_wall_seconds': time.perf_counter() - started,
        'fit_and_evaluation_cpu_seconds': time.process_time() - cpu_started,
        'limitations': [
            'family denotes prepared lexical grouping, not an independently audited semantic event',
            'non-temporal split cannot establish historical look-ahead freedom or future drift coverage',
            'point metrics only here; independent paired cluster uncertainty is calculated separately',
            'these local baselines do not include the planned FinBERT and zero-shot LLM baselines',
            'entity-only is a prespecified diagnostic and is not used to choose the main reported result',
            'fixed literal target markers do not establish correct semantic entity binding',
            'trained probability scores have not been certified or calibrated',
        ],
    }
    return models, private_predictions, aggregate


def _hash_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _confined(path, root, name):
    path, root = Path(path).resolve(), Path(root).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError(f'{name} must be a descendant of its designated output/input root')
    return path


def _version(name):
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def run(input_path, private_output_dir, summary_path, manifest_path=None):
    """Execute the frozen run, persisting only new private artifacts and aggregates."""
    input_path = _confined(input_path, PRIVATE_ROOT, 'input rows')
    private_output_dir = _confined(private_output_dir, PRIVATE_ROOT, 'private output directory')
    summary_path = _confined(summary_path, AGGREGATE_ROOT, 'aggregate summary')
    if not input_path.is_file():
        raise ValueError('prepared input file does not exist')
    if private_output_dir.exists() and (not private_output_dir.is_dir() or any(private_output_dir.iterdir())):
        raise ValueError('private output must be absent or empty; use a new run directory')
    if summary_path.exists():
        raise ValueError('summary already exists; use a new run identity rather than overwrite')
    raw = input_path.read_bytes()
    manifest = None
    if manifest_path is not None:
        manifest_path = _confined(manifest_path, MANIFEST_ROOT, 'preparation aggregate manifest')
        manifest_bytes = manifest_path.read_bytes()
        manifest_data = json.loads(manifest_bytes)
        expected = manifest_data.get('private_artifact_fingerprints', {}).get('rows.jsonl', {}).get('sha256')
        if expected != _hash_bytes(raw) or manifest_data.get('labels') != list(CLASSES):
            raise ValueError('input rows hash or class schema does not match frozen preparation manifest')
        manifest = {'file': manifest_path.name, 'sha256': _hash_bytes(manifest_bytes),
                    'input_hash_verified': True}
    rows = [json.loads(line) for line in raw.decode('utf-8-sig').splitlines() if line.strip()]
    started, cpu_started = time.perf_counter(), time.process_time()
    models, predictions, summary = fit_baselines(rows)
    private_output_dir.mkdir(parents=True, exist_ok=True)
    (private_output_dir / 'models').mkdir(exist_ok=True)
    (private_output_dir / 'predictions').mkdir(exist_ok=True)
    artifacts = {'models': {}, 'predictions': {}}
    for name, model in models.items():
        model_path = private_output_dir / 'models' / (name + '.joblib')
        # Write only newly created local objects. This program never joblib.load's.
        joblib.dump(model, model_path, compress=3)
        artifacts['models'][name] = {'file': str(model_path.relative_to(PRIVATE_ROOT.resolve())),
                                     'sha256': _hash_bytes(model_path.read_bytes()), 'bytes': model_path.stat().st_size}
        artifacts['predictions'][name] = {}
        for split, records in predictions[name].items():
            path = private_output_dir / 'predictions' / (name + '_' + split + '.jsonl')
            payload = ''.join(json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n' for row in records).encode('utf-8')
            path.write_bytes(payload)
            artifacts['predictions'][name][split] = {
                'file': str(path.relative_to(PRIVATE_ROOT.resolve())), 'sha256': _hash_bytes(payload), 'n_rows': len(records)}
    by_system = {name: {row['id']: row for row in predictions[name]['test']} for name in SYSTEMS}
    reference = predictions['majority']['test']
    if any(set(index) != set(by_system['majority']) for index in by_system.values()):
        raise AssertionError('systems do not share identical test IDs')
    joint = []
    for row in reference:
        aligned = {name: index[row['id']] for name, index in by_system.items()}
        if any(other['label'] != row['label'] or other['family_id'] != row['family_id'] for other in aligned.values()):
            raise AssertionError('test labels/families disagree across systems')
        joint.append({'id': row['id'], 'label': row['label'], 'family_id': row['family_id'],
                      'predictions': {name: other['prediction'] for name, other in aligned.items()}})
    combined_path = private_output_dir / 'predictions_test.jsonl'
    combined_bytes = ''.join(json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n' for row in joint).encode('utf-8')
    combined_path.write_bytes(combined_bytes)
    artifacts['combined_test_predictions'] = {
        'file': str(combined_path.relative_to(PRIVATE_ROOT.resolve())),
        'sha256': _hash_bytes(combined_bytes), 'n_rows': len(joint), 'systems': list(SYSTEMS)}
    try:
        base_commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=RESEARCH_ROOT.parent,
                                     capture_output=True, text=True, check=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        base_commit = None
    config_bytes = json.dumps(summary['config'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    summary.update({
        'finished_at_utc': datetime.now(timezone.utc).isoformat(),
        'base_commit': base_commit, 'source_sha256': _hash_bytes(Path(__file__).read_bytes()),
        'data_sha256': _hash_bytes(raw), 'config_sha256': _hash_bytes(config_bytes),
        'preparation_manifest': manifest, 'private_artifacts': artifacts,
        'software': {'python': platform.python_version(), 'numpy': _version('numpy'),
                     'scipy': _version('scipy'), 'scikit_learn': _version('scikit-learn'),
                     'torch': _version('torch'), 'joblib': _version('joblib'),
                     'threadpoolctl': _version('threadpoolctl')},
        'hardware': {'platform': platform.platform(), 'processor': platform.processor(),
                     'cpu_thread_limit': THREADS, 'gpu_used': False, 'peak_memory_measured': False},
        'total_wall_seconds': time.perf_counter() - started, 'total_cpu_seconds': time.process_time() - cpu_started,
        'source_level': 'our experiment; newly trained local baselines, not reconstructed old checkpoints',
    })
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--private-output', required=True, type=Path)
    parser.add_argument('--summary', required=True, type=Path)
    parser.add_argument('--manifest', required=True, type=Path)
    args = parser.parse_args()
    summary = run(args.input, args.private_output, args.summary, args.manifest)
    # Do not print raw rows, private predictions, vocabulary or model parameters.
    print(json.dumps({'status': summary['status'], 'summary': str(args.summary),
                      'systems': list(summary['systems']), 'data_sha256': summary['data_sha256'],
                      'total_wall_seconds': summary['total_wall_seconds']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
