"""Aggregate fixed-test source-native baseline predictions without publishing rows."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

from research.evaluation.evaluate import cluster_bootstrap

LABEL_NAMES = ('negative', 'neutral', 'positive')
MODEL_NAMES = ('majority', 'word', 'char', 'entity_only')
PREDICTION_KEYS = {'majority':'majority', 'word':'word_tfidf_lr',
                   'char':'char_tfidf_lr', 'entity_only':'entity_only_tfidf_lr'}


def load_jsonl(path):
    raw = path.read_bytes()
    return [json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()], hashlib.sha256(raw).hexdigest()


def validate_predictions(predictions, prepared_rows):
    expected = {r['id']:r for r in prepared_rows if r['split'] == 'test'}
    if not expected or len(expected) != sum(r['split'] == 'test' for r in prepared_rows):
        raise ValueError('nonempty unique frozen test rows required')
    found = set()
    for row in predictions:
        identity = row.get('id')
        if identity in found or identity not in expected:
            raise ValueError('unexpected or duplicate prediction ID')
        found.add(identity)
        reference = expected[identity]
        if row.get('label') != reference['label'] or row.get('family_id') != reference['family_id']:
            raise ValueError('prediction truth/group differs from frozen test manifest')
        if row['label'] not in LABEL_NAMES or not row.get('family_id'):
            raise ValueError('source labels and lexical family IDs are required')
        if set(row.get('predictions',{})) != set(PREDICTION_KEYS.values()):
            raise ValueError('all four frozen baseline predictions required on each test row')
        if any(row['predictions'][name] not in LABEL_NAMES for name in PREDICTION_KEYS.values()):
            raise ValueError('unexpected source-task prediction label')
    if found != set(expected):
        raise ValueError('predictions do not cover the full frozen test split')


def evaluate(predictions, prepared_rows, repetitions=10000, seed=130):
    validate_predictions(predictions, prepared_rows)
    def rows_for(name, baseline=None):
        rows = []
        for row in predictions:
            item = {'id':row['id'],'family_id':row['family_id'],'label':row['label'],
                    'prediction':row['predictions'][PREDICTION_KEYS[name]]}
            if baseline is not None:
                item['baseline_prediction'] = row['predictions'][PREDICTION_KEYS[baseline]]
            rows.append(item)
        return rows
    paired = cluster_bootstrap(rows_for('char','word'), repetitions, seed, label_names=LABEL_NAMES)
    systems = {'char':paired['systems']['prediction'], 'word':paired['systems']['baseline_prediction']}
    for name in ('majority','entity_only'):
        single = cluster_bootstrap(rows_for(name), repetitions, seed, label_names=LABEL_NAMES)
        systems[name] = single['systems']['prediction']
    return {
        'task':'source-native entity sentiment, not investment stance',
        'label_names':list(LABEL_NAMES),'n_test_rows':len(predictions),
        'n_lexical_clusters':paired['n_clusters'],'repetitions':repetitions,'seed':seed,
        'nominal_confidence_level':.95,'primary_comparison':'char minus word test macro-F1',
        'primary_macro_f1_difference':paired['paired_difference']['macro_f1'],
        'prediction_key_mapping':PREDICTION_KEYS,
        'paired_secondary_differences':paired['paired_difference'], 'systems':systems,
        'estimand':'entity-row-weighted metrics; entire lexical components resampled jointly',
        'cluster_basis':'normalized exact and token-Jaccard lexical components, not audited semantic events',
        'limitations':[
            'approximate percentile bootstrap conditional on fixed training, development selection and predictions',
            'lexical clusters do not establish independent representative events or temporal generalization',
            'nominal intervals do not include training/selection uncertainty or unknown cross-cluster dependence',
            'secondary/per-class intervals are descriptive and not multiplicity-adjusted',
            'source-task benchmark evidence, not a historical, semantic-parsing or deployment-risk certificate'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--predictions', type=Path, required=True)
    parser.add_argument('--rows', type=Path, default=Path('research/private/real_baseline/rows.jsonl'))
    parser.add_argument('--manifest', type=Path, default=Path('research/real_baseline/aggregate_manifest.json'))
    parser.add_argument('--output', type=Path, default=Path('research/experiments/real_baseline/bootstrap_summary.json'))
    args = parser.parse_args()
    started = time.perf_counter()
    rows, rows_hash = load_jsonl(args.rows)
    manifest_bytes = args.manifest.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest['private_artifact_fingerprints']['rows.jsonl']['sha256'] != rows_hash:
        raise ValueError('prepared row bytes differ from frozen manifest')
    predictions, predictions_hash = load_jsonl(args.predictions)
    result = evaluate(predictions, rows)
    result['source_rows_sha256'] = rows_hash
    result['private_predictions_sha256'] = predictions_hash
    result['aggregate_manifest_sha256'] = hashlib.sha256(manifest_bytes).hexdigest()
    result['source_code_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result['elapsed_seconds'] = time.perf_counter()-started
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'rows':result['n_test_rows'],'clusters':result['n_lexical_clusters'],
                      'primary_difference':result['primary_macro_f1_difference'],
                      'elapsed_seconds':result['elapsed_seconds']},indent=2))


if __name__ == '__main__': main()
