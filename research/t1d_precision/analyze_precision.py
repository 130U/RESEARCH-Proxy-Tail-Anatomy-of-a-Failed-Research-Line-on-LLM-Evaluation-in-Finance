"""Frozen T1D metrics and paired document-cluster bootstrap; no model calls."""
from pathlib import Path
from collections import Counter
import argparse
import json
import math
import numpy as np

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[2]
SEED = 20261117


def read_jsonl(path):
    return [json.loads(s) for s in path.read_text(encoding='utf8').splitlines() if s.strip()]


def finite(value):
    return value is not None and isinstance(value, (int, float, bool)) and math.isfinite(value)


class ClusterBootstrap:
    def __init__(self, pages, draws=10000, seed=SEED):
        self.pages = sorted(set(pages))
        self.page_index = {page: i for i, page in enumerate(self.pages)}
        self.draws = draws
        self.seed = seed
        self.weights = np.random.default_rng(seed).multinomial(
            len(self.pages), np.full(len(self.pages), 1 / len(self.pages)), size=draws
        )

    def summarize(self, rows, field, statistic='mean', return_draws=False):
        eligible = [r for r in rows if finite(r.get(field))]
        values = np.array([r[field] for r in eligible], dtype=float)
        result = {'n': len(eligible), 'estimate': None, 'ci95': None, 'pages': len({r['page_id'] for r in eligible}),
                  'statistic': statistic, 'bootstrap_valid_draws': 0}
        if not eligible:
            return (result, np.full(self.draws, np.nan)) if return_draws else result
        if statistic == 'mean':
            numerator = np.zeros(len(self.pages))
            denominator = numerator.copy()
            for row, value in zip(eligible, values):
                index = self.page_index[row['page_id']]
                numerator[index] += value
                denominator[index] += 1
            boot_den = self.weights @ denominator
            boot_num = self.weights @ numerator
            boot = np.divide(boot_num, boot_den, out=np.full(self.draws, np.nan), where=boot_den > 0)
            result['estimate'] = float(values.mean())
            if all(isinstance(r[field], bool) for r in eligible):
                result['count'] = int(values.sum())
        elif statistic == 'median':
            order = np.argsort(values, kind='stable')
            values = values[order]
            page_cols = np.array([self.page_index[eligible[i]['page_id']] for i in order])
            # Expand page multiplicities into row multiplicities; no parametric
            # approximation replaces the actual median in a resampled cluster set.
            row_weights = self.weights[:, page_cols]
            cumulative = np.cumsum(row_weights, axis=1)
            totals = cumulative[:, -1]
            left_order = np.maximum(0, (totals - 1) // 2)
            right_order = totals // 2
            left = np.argmax(cumulative > left_order[:, None], axis=1)
            right = np.argmax(cumulative > right_order[:, None], axis=1)
            boot = (values[left] + values[right]) / 2
            boot = np.where(totals > 0, boot, np.nan)
            result['estimate'] = float(np.median(values))
        else:
            raise ValueError(statistic)
        valid = boot[np.isfinite(boot)]
        result['bootstrap_valid_draws'] = int(len(valid))
        result['ci95'] = np.quantile(valid, [.025, .975]).tolist() if len(valid) else None
        return (result, boot) if return_draws else result


COMMON_METRICS = {
    'claimed_digits': ('claimed_digits', 'median'),
    'true_digits': ('d_star', 'median'),
    'digit_error': ('e', 'median'),
    'within_one_digit': ('within_one_digit', 'mean'),
    'overreported': ('overreported', 'mean'),
    'first_order_accuracy': ('first_order_correct', 'mean'),
    'always_certain_accuracy': ('always_certain_correct', 'mean'),
}
INTERVAL_METRICS = {
    'interval_width_ratio': ('r', 'median'),
    'width_accurate': ('width_accurate', 'mean'),
    'width_narrow': ('width_narrow', 'mean'),
    'width_wide': ('width_wide', 'mean'),
    'coverage': ('coverage', 'mean'),
    'onepct_accuracy': ('onepct_correct', 'mean'),
    'uncertain_recognition': ('onepct_correct', 'mean'),
    'certain_recognition': ('onepct_correct', 'mean'),
    'self_contradiction': ('self_contradiction', 'mean'),
}


def metric_rows(rows, name):
    if name == 'uncertain_recognition':
        return [r for r in rows if r.get('truth_1pct') is False]
    if name == 'certain_recognition':
        return [r for r in rows if r.get('truth_1pct') is True]
    return rows


def condition_summary(rows, condition, bootstrap):
    eligible = [r for r in rows if r['scorable']]
    result = {
        'available_n': len(rows), 'scorable_n': len(eligible),
        'excluded_n': len(rows) - len(eligible),
        'exclusion_reasons': dict(Counter(r['exclusion_reason'] for r in rows if not r['scorable'])),
        'scorable_fraction': bootstrap.summarize(rows, 'scorable'),
        'numeric_printed_digits': bootstrap.summarize(rows, 'printed_digits', 'median'),
        'metrics': {},
    }
    for name, (field, statistic) in COMMON_METRICS.items():
        result['metrics'][name] = bootstrap.summarize(eligible, field, statistic)
    if condition != 'A':
        for name, (field, statistic) in INTERVAL_METRICS.items():
            result['metrics'][name] = bootstrap.summarize(metric_rows(eligible, name), field, statistic)
        result['reported_zero_width_n'] = sum(r.get('r') == 0 for r in eligible)
        result['true_uncertain_n'] = sum(r.get('truth_1pct') is False for r in eligible)
        result['true_certain_n'] = sum(r.get('truth_1pct') is True for r in eligible)
        result['self_contradiction_unavailable_n'] = sum(r.get('self_contradiction') is None for r in eligible)
    return result


def strata(rows):
    yield 'all', rows
    for group in ('witness', 'control'):
        yield 'group/' + group, [r for r in rows if r['group'] == group]
    for category in ('growth', 'ratio', 'difference', 'sum', 'other'):
        yield 'category/' + category, [r for r in rows if r['category'] == category]


def paired_summary(rows_b, rows_c, bootstrap):
    b_map = {r['call_id']: r for r in rows_b if r['scorable']}
    c_map = {r['call_id']: r for r in rows_c if r['scorable']}
    ids = sorted(set(b_map) & set(c_map))
    b = [b_map[key] for key in ids]
    c = [c_map[key] for key in ids]
    result = {'paired_scorable_n': len(ids), 'paired_pages': len({r['page_id'] for r in b}), 'metrics': {}}
    transitions = [dict(page_id=rb['page_id'],
                        truth_changed=rb['truth_1pct'] != rc['truth_1pct'],
                        became_certain=rb['truth_1pct'] is False and rc['truth_1pct'] is True,
                        became_uncertain=rb['truth_1pct'] is True and rc['truth_1pct'] is False,
                        printed_expression_changed=rb['expression'] != rc['expression'])
                   for rb, rc in zip(b, c)]
    result['truth_transition'] = {
        'labels': ['uncertain', 'certain'],
        'counts_B_rows_C_columns': [[sum(rb['truth_1pct'] == x and rc['truth_1pct'] == y for rb, rc in zip(b, c)) for y in (False, True)] for x in (False, True)],
        **{key: bootstrap.summarize(transitions, key) for key in ('truth_changed', 'became_certain', 'became_uncertain', 'printed_expression_changed')},
        'limitation': 'Different expressions and source choices can change true precision; these contrasts are not a pure causal effect on precision awareness. Printed-expression differences need not imply mathematically different formulas.',
    }
    for name, (field, statistic) in {**COMMON_METRICS, **INTERVAL_METRICS}.items():
        # A metric must be defined on both responses for paired contrasts.
        valid = [i for i in range(len(ids)) if finite(b[i].get(field)) and finite(c[i].get(field))]
        if name in ('uncertain_recognition', 'certain_recognition'):
            common_truth = name == 'certain_recognition'
            valid = [i for i in valid if b[i]['truth_1pct'] == common_truth and c[i]['truth_1pct'] == common_truth]
        mb = metric_rows([b[i] for i in valid], name)
        mc = metric_rows([c[i] for i in valid], name)
        observed_b, draws_b = bootstrap.summarize(mb, field, statistic, return_draws=True)
        observed_c, draws_c = bootstrap.summarize(mc, field, statistic, return_draws=True)
        diff = draws_c - draws_b
        diff = diff[np.isfinite(diff)]
        result['metrics'][name] = {
            'estimate': None if observed_b['estimate'] is None or observed_c['estimate'] is None else observed_c['estimate'] - observed_b['estimate'],
            'ci95': np.quantile(diff, [.025, .975]).tolist() if len(diff) else None,
            'B': observed_b, 'C': observed_c, 'paired_metric_defined_n': len(valid),
            'bootstrap_valid_draws': int(len(diff)),
            'eligibility': ('Both responses have the same requested true certainty class.' if name in ('uncertain_recognition', 'certain_recognition') else 'Metric defined on both responses to the same question.'),
        }
    return result


def decision(summary, inference_complete):
    if not inference_complete:
        return {'status': 'pending_inference', 'classification': None}
    # The task's exception precedes the forced three-way classification.
    excluded = {c: summary[c]['excluded_n'] / summary[c]['available_n'] for c in ('A', 'B', 'C')}
    if any(excluded[c] > .1 for c in ('B', 'C')):
        return {'status': 'exclusions_above_10pct', 'classification': None,
                'excluded_fraction': excluded,
                'reason': 'At least one elicited condition excludes more than 10%; report causes first as required by the task.'}
    def passes(c):
        metrics = summary[c]['metrics']
        return metrics['width_accurate']['estimate'] >= .8 and metrics['onepct_accuracy']['estimate'] >= .9
    classification = 'the model already knows' if passes('B') else 'it learns from one sentence' if passes('C') else 'it does not learn even when taught'
    return {'status': 'classified', 'classification': classification, 'excluded_fraction': excluded,
            'B_meets_both_thresholds': passes('B'), 'C_meets_both_thresholds': passes('C'),
            'thresholds': {'width_accurate': .8, 'onepct_accuracy': .9},
            'wording_caveat': 'Condition B already tells the model that figures are rounded; its label means capability after this reminder, not spontaneous awareness.'}


def secondary_b_summary(rows, expected_ids, bootstrap, calls_root=None):
    """Optional other-model B replication, never pooled into the primary trial."""
    observed = {r['call_id'] for r in rows}
    complete = observed == expected_ids
    calls = []
    for path in sorted((calls_root or ROOT / 'calls/B_secondary').glob('*.json')):
        calls.append(json.loads(path.read_text(encoding='utf8')))
    result = {
        'condition': 'B_secondary', 'prompt_condition': 'B', 'expected_n': len(expected_ids),
        'available_n': len(rows), 'inference_complete': complete,
        'status': 'complete' if complete else 'partial_or_running' if rows or calls else 'not_run',
        'excluded_from_primary_A_B_C': True,
        'missing_responses': sorted(expected_ids-observed),
        'model_counts': dict(Counter(r.get('model') or 'not_recorded' for r in rows)),
        'reasoning_effort_counts': dict(Counter(r.get('reasoning_effort') or 'not_recorded' for r in rows)),
        'call_status_counts': dict(Counter(r.get('status', 'unknown') for r in calls)),
        'called_model_counts': dict(Counter(r.get('model') or 'not_recorded' for r in calls)),
        'summary': None, 'by_subset': {},
        'threshold_check': {'status': 'pending_inference', 'meets_B_thresholds': None},
        'scope': 'The unchanged B prompt on the original 392 questions, using another model. Metrics use its own source-bound expressions and the same 237-page resampling frame. It does not change the primary three-way conclusion.',
    }
    if rows:
        for subset in ('all_scorable', 'official_correct'):
            selected = rows if subset == 'all_scorable' else [r for r in rows if r.get('official_expression_correct') is True]
            result['by_subset'][subset] = {
                name: condition_summary(group_rows, 'B_secondary', bootstrap) for name, group_rows in strata(selected)
            }
        result['summary'] = result['by_subset']['all_scorable']['all']
    if complete:
        summary = result['summary']
        excluded_fraction = summary['excluded_n'] / summary['available_n']
        if excluded_fraction > .1:
            result['threshold_check'] = {'status': 'exclusions_above_10pct', 'meets_B_thresholds': None,
                                         'excluded_fraction': excluded_fraction}
        else:
            width = summary['metrics']['width_accurate']['estimate']
            accuracy = summary['metrics']['onepct_accuracy']['estimate']
            result['threshold_check'] = {'status': 'evaluated', 'meets_B_thresholds': width >= .8 and accuracy >= .9,
                                         'excluded_fraction': excluded_fraction,
                                         'thresholds': {'width_accurate': .8, 'onepct_accuracy': .9},
                                         'limitation': 'This secondary run contains B only; it cannot establish whether teaching the rule would change this model\'s result.'}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-incomplete', action='store_true')
    parser.add_argument('--c-design', choices=('full', 'half'), default='full')
    parser.add_argument('--draws', type=int, default=10000)
    args = parser.parse_args()
    sample = json.loads((WORKSPACE / 'proxy-tail-t1c/research/t1c_models/private/sample.json').read_text(encoding='utf8'))
    pages = sorted({r['id'].rsplit('-', 1)[0] for r in sample})
    assert len(sample) == 392 and len(pages) == 237
    ids = {r['call_id'] for r in sample}
    c_ids = ids if args.c_design == 'full' else set(json.loads((ROOT / 'private/c_half_ids.json').read_text(encoding='utf8')))
    expected = {'A': ids, 'B': ids, 'C': c_ids}
    all_rows = read_jsonl(ROOT / 'per_response.jsonl')
    keys = [(r['condition'], r['call_id']) for r in all_rows]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate condition/question responses')
    if any(condition not in {*expected, 'B_secondary'} or key not in ids for condition, key in keys):
        raise ValueError('Scored responses do not match the original frozen sample')
    extra_c = [r for r in all_rows if r['condition'] == 'C' and r['call_id'] not in c_ids]
    secondary_rows = [r for r in all_rows if r['condition'] == 'B_secondary']
    rows = [r for r in all_rows if r['condition'] in expected and (r['condition'] != 'C' or r['call_id'] in c_ids)]
    missing = {c: sorted(expected[c] - {r['call_id'] for r in rows if r['condition'] == c}) for c in expected}
    inference_complete = not any(missing.values())
    reviews_path = ROOT / 'review_results.json'
    reviews = json.loads(reviews_path.read_text(encoding='utf8')) if reviews_path.exists() else {'complete': False}
    bootstrap = ClusterBootstrap(pages, args.draws)
    report = {
        'complete': inference_complete and bool(reviews.get('complete')),
        'complete_scope': 'Primary A/B/C and mandatory semantic reviews; optional secondary_B has separate completion status.',
        'inference_complete': inference_complete, 'semantic_review_complete': bool(reviews.get('complete')),
        'sample': {'original_questions': 392, 'original_pairs': 196, 'page_clusters': len(pages),
                   'expected_by_condition': {c: len(v) for c, v in expected.items()}, 'C_design': args.c_design,
                   'extra_C_n': len(extra_c), 'extra_C_ids_retained_outside_primary_analysis': sorted(r['call_id'] for r in extra_c)},
        'bootstrap': {'draws': args.draws, 'seed': SEED, 'sampling_frame_pages': len(pages),
                      'method': 'Percentile bootstrap; uniformly resample the original 237 pages with replacement, keeping all responses on a drawn page together. Same draws for every subgroup and paired contrast. Counts are observed counts, not estimated sample sizes.'},
        'missing_responses': missing, 'by_condition': {}, 'summary_table': {},
        'paired_C_minus_B': {}, 'semantic_reviews': reviews,
    }
    for condition in ('A', 'B', 'C'):
        condition_rows = [r for r in rows if r['condition'] == condition]
        report['by_condition'][condition] = {}
        for subset in ('all_scorable', 'official_correct'):
            base = condition_rows if subset == 'all_scorable' else [r for r in condition_rows if r.get('official_expression_correct') is True]
            report['by_condition'][condition][subset] = {
                name: condition_summary(group_rows, condition, bootstrap) for name, group_rows in strata(base)
            }
        report['summary_table'][condition] = report['by_condition'][condition]['all_scorable']['all']
    b_rows = [r for r in rows if r['condition'] == 'B']
    c_rows = [r for r in rows if r['condition'] == 'C']
    for subset in ('all_scorable', 'official_correct'):
        selected_b = b_rows if subset == 'all_scorable' else [r for r in b_rows if r.get('official_expression_correct') is True]
        selected_c = c_rows if subset == 'all_scorable' else [r for r in c_rows if r.get('official_expression_correct') is True]
        report['paired_C_minus_B'][subset] = {}
        c_strata = dict(strata(selected_c))
        for name, grouped_b in strata(selected_b):
            report['paired_C_minus_B'][subset][name] = paired_summary(grouped_b, c_strata[name], bootstrap)
    report['precision_decision'] = decision(report['summary_table'], inference_complete)
    report['secondary_B'] = secondary_b_summary(secondary_rows, ids, bootstrap)
    report['interpretation_limits'] = [
        'A records printed significant digits, not an explicit assertion of reliable digits; trailing zeros are counted literally.',
        'B explicitly reminds the model that displayed figures are rounded. It tests elicited calculation after a reminder.',
        'Truth is the certified rounding-box range of each response\'s own source-bound expression, not the gold calculation. It does not impose additional accounting identities.',
        'The first-order comparator is T1A\'s local derivative radius on the same source-bound expression; it generalizes the simple equal-unit difference/growth rule and is not an exact range certificate.',
        'First-order and always-certain baselines are reported separately on each condition\'s identical eligible questions and expressions. B/C may choose different expressions and hence have different truth labels.',
        'Paired C-minus-B uses questions scorable in both conditions; the official-correct version additionally requires official correctness in both. Paired uncertain/certain recognition uses only questions with that same truth class in both conditions; separate unpaired condition summaries keep each condition\'s own truth class.',
        'Nonpositive true width, zero expression center, unresolved binding and malformed outputs are reported separately rather than forced into precision metrics.',
        'FinQA is public; training exposure is possible. The benchmark does not supply interval labels, but the effect of exposure on this experiment is not established.',
        'Optional B_secondary results are separate from every primary A/B/C metric, paired contrast, figure and three-way classification.',
    ]
    (ROOT / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf8', newline='\n')
    print(json.dumps({'complete': report['complete'], 'inference_complete': inference_complete,
                      'semantic_review_complete': report['semantic_review_complete'],
                      'available': {c: report['summary_table'][c]['available_n'] for c in ('A', 'B', 'C')},
                      'scorable': {c: report['summary_table'][c]['scorable_n'] for c in ('A', 'B', 'C')},
                      'secondary_B_status': report['secondary_B']['status'], 'secondary_B_available': len(secondary_rows),
                      'decision': report['precision_decision']}, ensure_ascii=False))
    if not report['complete'] and not args.allow_incomplete:
        raise SystemExit('Responses or semantic adjudications are incomplete; final delivery is not ready.')


if __name__ == '__main__':
    main()
