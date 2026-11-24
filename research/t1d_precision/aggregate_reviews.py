"""Retain independent labels, prepare anonymous adjudications, and summarize agreement."""
from pathlib import Path
from collections import Counter
import argparse
import csv
import json
import random
import re
import numpy as np

ROOT = Path(__file__).resolve().parent
SEED = 20261117
LABELS = ('valid', 'invalid', 'uncertain')
CAUSES = ('alternative_source_precision', 'reasonable_alternative', 'reference_error', 'true_error', 'unresolved', 'invalid_format')
C_FIELDS = ('primary_cause', 'formula_valid', 'alternative_precision_used')


def read_json(path):
    return json.loads(path.read_text(encoding='utf8'))


def validate_review_response(kind, review_id, response):
    if not isinstance(response, dict):
        raise ValueError('expected object')
    id_key = 'review_id' if kind == 'b' else 'call_id'
    required = {id_key, 'verdict', 'reason'} if kind == 'b' else {id_key, *C_FIELDS, 'reason'}
    if set(response) != required:
        raise ValueError('response fields do not match the requested schema')
    if response.get(id_key) != review_id:
        raise ValueError('anonymous id mismatch')
    if not isinstance(response.get('reason'), str) or not response['reason'].strip():
        raise ValueError('missing reason')
    if kind == 'b':
        if response.get('verdict') not in LABELS:
            raise ValueError('unknown semantic label')
    else:
        if response.get('primary_cause') not in CAUSES:
            raise ValueError('unknown attribution label')
        if response.get('formula_valid') is not None and type(response.get('formula_valid')) is not bool:
            raise ValueError('formula_valid must be bool or null')
        if type(response.get('alternative_precision_used')) is not bool:
            raise ValueError('alternative_precision_used must be bool')


def parse_review(kind, review_id, adjudication=False):
    folder = ('adjudicate_' if adjudication else 'review_') + kind
    path = ROOT / 'raw' / folder / f'{review_id}.txt'
    if not path.exists():
        return {'status': 'missing'}
    raw = path.read_text(encoding='utf8')
    text = raw.strip()
    if text.startswith('```') and text.endswith('```'):
        text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.I)[:-3].strip()
    try:
        response = json.loads(text)
        validate_review_response(kind, review_id, response)
        return {'status': 'ok', 'response': response, 'raw_file': path.relative_to(ROOT).as_posix()}
    except (ValueError, TypeError) as exc:
        return {'status': 'invalid_format', 'error': str(exc), 'raw_file': path.relative_to(ROOT).as_posix()}


def kappa_from_matrix(matrix):
    matrix = np.asarray(matrix, dtype=float)
    n = matrix.sum()
    if n == 0:
        return None
    observed = np.trace(matrix) / n
    expected = (matrix.sum(0) * matrix.sum(1)).sum() / n**2
    return float((observed - expected) / (1 - expected)) if expected < 1 else None


def draws_for_pages(rows, draws):
    pages = sorted({r['page_id'] for r in rows})
    if not pages:
        return pages, np.empty((draws, 0)), {}
    rng = np.random.default_rng(SEED)
    weights = rng.multinomial(len(pages), np.full(len(pages), 1 / len(pages)), size=draws)
    return pages, weights, {p: i for i, p in enumerate(pages)}


def ratio_summary(rows, predicate, draws=10000):
    pages, weights, indices = draws_for_pages(rows, draws)
    if not rows:
        return {'n': 0, 'count': 0, 'estimate': None, 'ci95': None, 'pages': 0}
    den = np.zeros(len(pages))
    num = den.copy()
    for r in rows:
        i = indices[r['page_id']]
        den[i] += 1
        num[i] += bool(predicate(r))
    boot_den = weights @ den
    boot = (weights @ num) / boot_den
    return {'n': len(rows), 'count': int(num.sum()), 'estimate': float(num.sum() / den.sum()),
            'ci95': np.quantile(boot, [.025, .975]).tolist(), 'pages': len(pages)}


def agreement_summary(rows, labels, key, draws):
    matrix = np.zeros((len(labels), len(labels)), dtype=int)
    for r in rows:
        matrix[labels.index(r['first'][key]), labels.index(r['second']['response'][key])] += 1
    result = ratio_summary(rows, lambda r: r['first'][key] == r['second']['response'][key], draws)
    result.update(labels=list(labels), confusion_matrix=matrix.tolist(), kappa=kappa_from_matrix(matrix), kappa_ci95=None)
    if rows:
        pages, weights, indices = draws_for_pages(rows, draws)
        by_page = np.zeros((len(pages), len(labels)**2))
        for r in rows:
            a = labels.index(r['first'][key])
            b = labels.index(r['second']['response'][key])
            by_page[indices[r['page_id']], a * len(labels) + b] += 1
        samples = (weights @ by_page).reshape(draws, len(labels), len(labels))
        n = samples.sum((1, 2))
        observed = np.trace(samples, axis1=1, axis2=2) / n
        expected = (samples.sum(1) * samples.sum(2)).sum(1) / n**2
        ok = expected < 1
        vals = (observed[ok] - expected[ok]) / (1 - expected[ok])
        result['kappa_ci95'] = np.quantile(vals, [.025, .975]).tolist() if len(vals) else None
        result['kappa_valid_bootstrap_draws'] = int(len(vals))
    return result


def display_reason(original):
    """Remove only explicit review-history framing, never source arguments."""
    rules = (
        (r"^Adopt the independent review's more cautious classification\.\s*", 'procedural opening sentence'),
        (r"Adopt the independent review's unresolved classification:\s*", 'procedural classification preface'),
        (r'^Adopt the independent review after rechecking\s+', 'procedural preface; following source locator retained'),
        (r'^Adopt the independent review:\s*', 'procedural opening preface'),
        (r'\s*Original root and independent judgments are retained\.$', 'record-retention sentence'),
    )
    displayed, removals = original, []
    for pattern, description in rules:
        def remove(match):
            removals.append({'removed_text': match.group(), 'reason': description})
            return ''
        displayed = re.sub(pattern, remove, displayed)
    displayed = displayed.strip()
    if not displayed:
        displayed, removals = original, []
    limitations = []
    # A classification instruction intertwined with a material interpretation
    # is not removed automatically. It stays visible, with a provenance-level
    # limitation, rather than silently changing the original reasoning.
    if re.search(r'\b(?:adopt|retain)\b.*\b(?:validity|classification|judgment|flag)\b|\b(?:independent|first|second|third|previous|prior|root)\s+(?:review|judgment|classification)', displayed, re.I):
        limitations.append('Possible procedural or judgment-history wording retained because it is intertwined with substantive interpretation; complete origin blinding is not assured.')
    return {'original_reason': original, 'display_reason': displayed,
            'removed_fragments': removals, 'blindness_limitations': limitations}


def adjudication_prompt(kind, row):
    review_id = row['review_id']
    display_records = [dict(source_round='first', **display_reason(row['first']['reason'])),
                       dict(source_round='second', **display_reason(row['second']['response']['reason']))]
    rng = random.Random(SEED + int(review_id[1:]) + (1000 if kind == 'c' else 0))
    rng.shuffle(display_records)
    reasons = [r['display_reason'] for r in display_records]
    row['adjudication_reason_blinding'] = {
        'display_copy_changed': any(r['removed_fragments'] for r in display_records),
        'complete_origin_blinding_not_assured': any(r['blindness_limitations'] for r in display_records),
    }
    provenance_path = ROOT / 'private/adjudication_reason_display' / kind / f'{review_id}.json'
    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    provenance = {'review_id': review_id, 'kind': kind, 'display_order': display_records}
    provenance_text = json.dumps(provenance, ensure_ascii=False, indent=2) + '\n'
    if provenance_path.exists() and provenance_path.read_text(encoding='utf8') != provenance_text:
        raise ValueError(f'Adjudication reason display mapping changed: {review_id}')
    if not provenance_path.exists():
        provenance_path.write_text(provenance_text, encoding='utf8', newline='\n')
    original = (ROOT / 'prompts' / f'review_{kind}' / f'{review_id}.txt').read_text(encoding='utf8')
    text = original + '\nTWO SOURCE INTERPRETATIONS TO CONSIDER\n'
    text += 'The order is random. Evaluate these reasons against the supplied source and give your own judgment using the same JSON schema. Their order carries no priority.\n'
    text += json.dumps(reasons, ensure_ascii=False, indent=2) + '\n'
    path = ROOT / 'prompts' / f'adjudicate_{kind}' / f'{review_id}.txt'
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding='utf8') != text:
        raise ValueError(f'Adjudication prompt changed: {review_id}')
    if not path.exists():
        path.write_text(text, encoding='utf8', newline='\n')


def collect(kind):
    rows = read_json(ROOT / 'private' / f'review_{kind}_map.json')
    for r in rows:
        r['second'] = parse_review(kind, r['review_id'])
        r['disagreement'] = None
        r['third'] = {'status': 'not_required'}
        if r.get('first') and r['second']['status'] == 'ok':
            keys = ('verdict',) if kind == 'b' else C_FIELDS
            changed = [key for key in keys if r['first'].get(key) != r['second']['response'].get(key)]
            r['disagreement'] = bool(changed)
            r['disagreement_fields'] = changed
            if changed:
                adjudication_prompt(kind, r)
                r['third'] = parse_review(kind, r['review_id'], adjudication=True)
    return rows


def majority_valid(r):
    if r['second']['status'] != 'ok':
        return None
    labels = [r['first']['verdict'], r['second']['response']['verdict']]
    if r['disagreement']:
        if r['third']['status'] != 'ok':
            return None
        labels.append(r['third']['response']['verdict'])
    return labels.count('valid') >= 2


def summarize_b(rows, draws):
    witnesses = [r for r in rows if r['group'] == 'witness']
    pairs = [r for r in witnesses if r['second']['status'] == 'ok']
    stable = [r for r in rows if r['group'] == 'control' and r['second']['status'] == 'ok']
    majority = [dict(r, majority_valid=majority_valid(r)) for r in witnesses if majority_valid(r) is not None]
    strict = lambda r: r['first']['verdict'] == 'valid' and r['second']['response']['verdict'] == 'valid'
    strict_rate = ratio_summary(pairs, strict, draws)
    majority_rate = ratio_summary(majority, lambda r: r['majority_valid'], draws)
    return {
        'expected_witness': 196, 'expected_control': 60, 'first_valid_n': sum(r['first']['verdict'] == 'valid' for r in witnesses),
        'agreement': agreement_summary(pairs, LABELS, 'verdict', draws),
        'strict_valid_n': strict_rate['count'] if len(pairs) == 196 else None,
        'strict_valid_fraction': strict_rate,
        'majority_valid_n': majority_rate['count'] if len(majority) == 196 else None,
        'majority_valid_fraction': majority_rate,
        'second_label_counts': {
            'witness': dict(Counter(r['second']['response']['verdict'] for r in pairs)),
            'control': dict(Counter(r['second']['response']['verdict'] for r in stable)),
        },
        'second_invalid_or_uncertain': {
            'witness': ratio_summary(pairs, lambda r: r['second']['response']['verdict'] != 'valid', draws),
            'control': ratio_summary(stable, lambda r: r['second']['response']['verdict'] != 'valid', draws),
        },
        'retained_denominator_test': 1147,
        'strict_fraction_of_test': strict_rate['count'] / 1147 if len(pairs) == 196 else None,
        'strict_fraction_of_test_ci95': [x * 196 / 1147 for x in strict_rate['ci95']] if len(pairs) == 196 else None,
        'majority_fraction_of_test': majority_rate['count'] / 1147 if len(majority) == 196 else None,
        'majority_fraction_of_test_ci95': [x * 196 / 1147 for x in majority_rate['ci95']] if len(majority) == 196 else None,
        'stable_first_labels_available': False,
        'majority_convention': 'Only disagreements receive a third judgment; two agreeing original judgments already establish a majority. Stable controls have no first judgment and are excluded from paired agreement and retention counts.',
    }


def summarize_c(rows, draws):
    pairs = [r for r in rows if r['second']['status'] == 'ok']
    agreed = [r for r in pairs if r['first']['primary_cause'] == r['second']['response']['primary_cause']]
    result = {
        'expected': 68, 'agreement': agreement_summary(pairs, CAUSES, 'primary_cause', draws),
        'all_fields_agreement': ratio_summary(pairs, lambda r: not r['disagreement'], draws),
        'first_cause_counts': dict(Counter(r['first']['primary_cause'] for r in rows)),
        'second_cause_counts': dict(Counter(r['second']['response']['primary_cause'] for r in pairs)),
        'strict_cause_counts': dict(Counter(r['first']['primary_cause'] for r in agreed)),
        'first_label_source': 'T1C final source attribution: review_*.json overlaid with adjudication.json; this preserves the prior final published categories rather than reusing its unadjudicated preliminary labels.',
    }
    for cause in ('reference_error', 'reasonable_alternative'):
        result[f'{cause}_strict_fraction_of_all_reviewed'] = ratio_summary(
            pairs, lambda r: r['first']['primary_cause'] == cause and r['second']['response']['primary_cause'] == cause, draws)
        result[f'{cause}_fraction_of_agreed_causes'] = ratio_summary(agreed, lambda r: r['first']['primary_cause'] == cause, draws)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-incomplete', action='store_true')
    parser.add_argument('--draws', type=int, default=10000)
    args = parser.parse_args()
    all_rows = {'b': collect('b'), 'c': collect('c')}
    result = {'seed': SEED, 'bootstrap_draws': args.draws, 'bootstrap_unit': 'document/page; resample all judgments on a page together', 'complete': True}
    records = []
    for kind, rows in all_rows.items():
        second_bad = [r['review_id'] for r in rows if r['second']['status'] != 'ok']
        third_bad = [r['review_id'] for r in rows if r['disagreement'] and r['third']['status'] != 'ok']
        complete = not second_bad and not third_bad
        result['complete'] &= complete
        result[f'review_{kind}'] = (summarize_b if kind == 'b' else summarize_c)(rows, args.draws)
        result[f'review_{kind}'].update(
            complete=complete,
            second_status_counts=dict(Counter(r['second']['status'] for r in rows)),
            second_missing_or_invalid=second_bad,
            disagreements=[r['review_id'] for r in rows if r['disagreement']],
            third_missing_or_invalid=third_bad,
            third_status_counts=dict(Counter(r['third']['status'] for r in rows)),
            adjudication_display_reason_changed_ids=[r['review_id'] for r in rows if r.get('adjudication_reason_blinding', {}).get('display_copy_changed')],
            adjudication_origin_blinding_limitation_ids=[r['review_id'] for r in rows if r.get('adjudication_reason_blinding', {}).get('complete_origin_blinding_not_assured')],
        )
        for r in rows:
            key = 'verdict' if kind == 'b' else 'primary_cause'
            record = {k: r.get(k) for k in ('review_id', 'id', 'page_id', 'group', 'call_id', 'disagreement')}
            record.update(kind=kind, first_label=(r.get('first') or {}).get(key),
                          second_status=r['second']['status'], second_label=r['second'].get('response', {}).get(key),
                          third_status=r['third']['status'], third_label=r['third'].get('response', {}).get(key),
                          first_reason=(r.get('first') or {}).get('reason'),
                          second_reason=r['second'].get('response', {}).get('reason'),
                          third_reason=r['third'].get('response', {}).get('reason'))
            records.append(record)
    # The complete status is explicit even when an interim run is requested.
    (ROOT / 'review_results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8', newline='\n')
    with (ROOT / 'per_review.csv').open('w', encoding='utf8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    (ROOT / 'per_review.jsonl').write_text(''.join(json.dumps({'kind': kind, **r}, ensure_ascii=False) + '\n' for kind, rows in all_rows.items() for r in rows), encoding='utf8', newline='\n')
    print(json.dumps({'complete': result['complete'], **{kind: {
        'second': result[f'review_{kind}']['second_status_counts'],
        'disagreements': len(result[f'review_{kind}']['disagreements']),
        'third_pending': len(result[f'review_{kind}']['third_missing_or_invalid']),
    } for kind in ('b', 'c')}}, ensure_ascii=False))
    if not result['complete'] and not args.allow_incomplete:
        raise SystemExit('Independent reviews or required adjudications remain incomplete.')


if __name__ == '__main__':
    main()
