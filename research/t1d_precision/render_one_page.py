"""Render the requested compact result page only from a complete results.json."""
from pathlib import Path
import argparse
import json

ROOT = Path(__file__).resolve().parent


def estimate(summary, percent=False, decimals=2):
    value = summary.get('estimate') if summary else None
    if value is None:
        return '—'
    scale = 100 if percent else 1
    suffix = '%' if percent else ''
    digits = 1 if percent else decimals
    point_digits = 2 if percent and min(abs(100*value-80), abs(100*value-90)) < .05 else digits
    text = f'{scale*value:.{point_digits}f}{suffix}'
    interval = summary.get('ci95')
    if interval is not None:
        text += f' [{scale*interval[0]:.{digits}f}{suffix}, {scale*interval[1]:.{digits}f}{suffix}]'
    return text


def kappa(summary):
    return estimate({'estimate': summary.get('kappa'), 'ci95': summary.get('kappa_ci95')})


def percentage_point_change(summary):
    value = summary.get('estimate') if summary else None
    if value is None:
        return '—'
    text = f'{100*value:+.1f} percentage points'
    interval = summary.get('ci95')
    if interval is not None:
        text += f' [{100*interval[0]:+.1f}, {100*interval[1]:+.1f}]'
    return text


def require_complete(result):
    if not (result.get('complete') and result.get('inference_complete') and result.get('semantic_review_complete')):
        raise ValueError('Main inference or mandatory semantic review is incomplete; ONE_PAGE must not be rendered.')
    reviews = result.get('semantic_reviews', {})
    if not reviews.get('complete') or not all(reviews.get(name, {}).get('complete') for name in ('review_b', 'review_c')):
        raise ValueError('The embedded semantic review summary is incomplete.')
    for condition in ('A', 'B', 'C'):
        expected = result['sample']['expected_by_condition'][condition]
        if result['summary_table'][condition]['available_n'] != expected:
            raise ValueError('Primary response counts do not match the frozen design.')
    b = reviews['review_b']
    if b.get('first_valid_n') != 139 or not isinstance(b.get('strict_valid_n'), int) or not isinstance(b.get('majority_valid_n'), int):
        raise ValueError('The requested 139-to-strict-retention comparison is unavailable.')
    if not 0 <= b['strict_valid_n'] <= 139 or not b['strict_valid_n'] <= b['majority_valid_n'] <= 196:
        raise ValueError('Inconsistent strict/majority retention counts.')
    if result['precision_decision']['status'] not in ('classified', 'exclusions_above_10pct'):
        raise ValueError('The frozen decision rule has not been evaluated.')


def render_one_page(result):
    require_complete(result)
    table = result['summary_table']
    lines = ['| | Condition A: not asked | Condition B: asked | Condition C: asked and taught |', '|---|---:|---:|---:|']
    rows = [
        ('Scorable responses', None, False),
        ('Median claimed digits', 'claimed_digits', False),
        ('Median true reliable digits', 'true_digits', False),
        ('Share over-reporting by more than one digit', 'overreported', True),
        ('Share of intervals "accurate"', 'width_accurate', True),
        ('Share of intervals "too narrow"', 'width_narrow', True),
        ('1% judgment accuracy', 'onepct_accuracy', True),
    ]
    for label, metric, percent in rows:
        values = []
        for condition in ('A', 'B', 'C'):
            summary = table[condition]
            if metric is None:
                values.append(f'{summary["scorable_n"]}/{summary["available_n"]}; {estimate(summary["scorable_fraction"], percent=True)}')
            else:
                values.append(estimate(summary['metrics'].get(metric), percent=percent))
        lines.append('| ' + ' | '.join([label, *values]) + ' |')
    lines.extend(['', 'Brackets in the table are 95% intervals from 10,000 bootstrap draws over the fixed 237 page clusters; the first row also gives the scorable fraction. For A, "claimed digits" means only the literally printed digits. The previous round\'s 16/12 digits are the group medians for the 144 growth questions with the same source and the same formula.', ''])

    decision = result['precision_decision']
    if decision['status'] == 'classified':
        lines.append(f'Under the threshold fixed before execution (interval-accurate share ≥80% and 1% judgment accuracy ≥90%), this round is classified as **{decision["classification"]}**.')
    else:
        exclusions = []
        for condition in ('A', 'B', 'C'):
            s = table[condition]
            if s['available_n'] and s['excluded_n'] / s['available_n'] > .1:
                exclusions.append(f'{condition} excluded {s["excluded_n"]}/{s["available_n"]}')
        causes = {condition: table[condition]['exclusion_reasons'] for condition in ('A', 'B', 'C') if table[condition]['excluded_n']}
        reasons = '; '.join(f'{condition}: ' + ', '.join(f'{reason}={count}' for reason, count in sorted(values.items())) for condition, values in causes.items())
        lines.append('Triggered the preset exception in the task: ' + '; '.join(exclusions) + ', above 10%; the exclusion reasons are reported first and the three-way classification is not forced for now. ' + reasons + '.')
    paired = result['paired_C_minus_B']['all_scorable']['all']
    metrics = paired['metrics']
    if paired['paired_scorable_n']:
        lines.append(f'Same-question pairing C−B: interval-accurate share {percentage_point_change(metrics["width_accurate"])}; 1% judgment accuracy {percentage_point_change(metrics["onepct_accuracy"])}. '
                     f'For {paired["truth_transition"]["truth_changed"]["count"]}/{paired["paired_scorable_n"]} questions the true 1% status changed with the formula or source; the difference cannot be read as a pure causal effect of precision awareness.')
    else:
        lines.append('No question has scorable responses on both sides; the paired C−B difference was not estimated.')
    if result['sample']['C_design'] == 'half':
        extra = result['sample'].get('extra_C_n', 0)
        lines.append(f'C uses the 98 pairs (196 questions) drawn and fixed before execution; the {extra} extra C responses are kept but do not enter the main analysis.')

    reviews = result['semantic_reviews']
    rb, rc = reviews['review_b'], reviews['review_c']
    stable = rb['second_invalid_or_uncertain']['control']
    witness = rb['second_invalid_or_uncertain']['witness']
    strict = rb['strict_valid_n']
    lines.extend(['', f'Main semantic-review figure: **139 → {strict}** (valid in both rounds); valid by majority: {rb["majority_valid_n"]}. '
                  f'Two-round agreement on the 196 witness questions {estimate(rb["agreement"], percent=True)}, κ={kappa(rb["agreement"])}. '
                  f'Second-round invalid/uncertain: stable questions {stable["count"]}/{stable["n"]} ({estimate(stable, percent=True)}), '
                  f'witness questions {witness["count"]}/{witness["n"]} ({estimate(witness, percent=True)}).'])
    ref = rc['reference_error_strict_fraction_of_all_reviewed']
    alt = rc['reasonable_alternative_strict_fraction_of_all_reviewed']
    ref_agreed = rc['reference_error_fraction_of_agreed_causes']
    alt_agreed = rc['reasonable_alternative_fraction_of_agreed_causes']
    lines.append(f'The 68 T1C rejection cases: two-round attribution agreement {estimate(rc["agreement"], percent=True)}, κ={kappa(rc["agreement"])}; '
                 f'among the {ref_agreed["n"]} cases where both rounds agree on the attribution, "reference error" {ref_agreed["count"]}/{ref_agreed["n"]} ({estimate(ref_agreed, percent=True)}), '
                 f'"defensible alternative convention" {alt_agreed["count"]}/{alt_agreed["n"]} ({estimate(alt_agreed, percent=True)}); '
                 f'as strict counts over all reviewed cases, the two categories are {ref["count"]}/{ref["n"]} and {alt["count"]}/{alt["n"]}.')
    blind_limits = sorted(set(rb.get('adjudication_origin_blinding_limitation_ids', []) + rc.get('adjudication_origin_blinding_limitation_ids', [])))
    if blind_limits:
        lines.append(f'In round three, {len(blind_limits)} reasons were kept because process wording could not be safely separated from the substantive argument, so source blinding is limited; this does not affect the main count of "valid in both rounds".')

    secondary = result.get('secondary_B')
    if secondary and secondary.get('inference_complete'):
        ss = secondary['summary']
        model = ', '.join(secondary.get('model_counts', {})) or 'another model tier'
        effort = ', '.join(secondary.get('reasoning_effort_counts', {}))
        source = model + (' / ' + effort if effort else '')
        lines.extend(['', f'Independent rerun of B ({source}): {ss["scorable_n"]}/{ss["available_n"]} scorable, '
                      f'interval accurate {estimate(ss["metrics"]["width_accurate"], percent=True)}, '
                      f'over-reporting by more than one digit {estimate(ss["metrics"]["overreported"], percent=True)}, '
                      f'1% judgment accuracy {estimate(ss["metrics"]["onepct_accuracy"], percent=True)}; not mixed into the main conclusion.'])
    elif secondary and secondary.get('status') != 'not_run':
        lines.extend(['', f'The other-tier B run did not finish; only {secondary.get("available_n", 0)}/{secondary.get("expected_n", 392)} analyzable responses were saved, so it is not treated as a complete rerun or included in the main conclusion.'])

    lines.extend(['', 'Interpretation limits: A\'s printed digits are not the same as an active statement of reliable precision; B was already reminded that the numbers are rounded, so it measures whether the model can compute after the reminder. Every truth value follows the response\'s own formula. FinQA is public, so training exposure may exist; the absence of interval labels does not mean contamination has been ruled out. The exact service version for A was not exposed, and B/C ran at different times, so cross-condition comparisons keep the service-condition limitation.'])
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results', type=Path, default=ROOT / 'results.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'ONE_PAGE.md')
    args = parser.parse_args()
    result = json.loads(args.results.read_text(encoding='utf8'))
    try:
        text = render_one_page(result)
    except (KeyError, TypeError, ValueError) as exc:
        raise SystemExit(f'Refusing final one-page output: {exc}') from exc
    args.output.write_text(text, encoding='utf8', newline='\n')
    print(json.dumps({'written': str(args.output), 'complete': True, 'characters': len(text)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
