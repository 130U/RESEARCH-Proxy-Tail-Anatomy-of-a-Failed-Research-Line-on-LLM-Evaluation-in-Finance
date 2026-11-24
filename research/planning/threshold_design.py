"""Exact fixed zero-finding designs for a symmetric r-of-h impact family.

Artificial mathematical inputs only. No audit is performed and no model is
trained. Optimality is restricted to fixed per-layer sample sizes, equal costs,
and uniform sampling without replacement inside each layer.
"""
from fractions import Fraction
from itertools import combinations_with_replacement
from math import comb
from pathlib import Path
import hashlib
import json
import platform
import time

from research.certificates.collective import BudgetExceeded


def validate(population, layers, threshold, alpha):
    for value in (population, layers, threshold):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError('positive integer population, layers and threshold required')
    if threshold > layers:
        raise ValueError('threshold must not exceed layers')
    if isinstance(alpha, bool) or not isinstance(alpha, (int, str, Fraction)):
        raise ValueError('alpha must be exact, not float/bool')
    try:
        a = Fraction(alpha)
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError('invalid alpha') from error
    if not 0 < a < 1:
        raise ValueError('alpha must lie strictly between zero and one')
    return a


def risk(population, samples, threshold):
    """Worst zero-detection probability over all minimally bad layer sets."""
    if isinstance(population, bool) or not isinstance(population, int) or population < 1:
        raise ValueError('positive integer population required')
    if not samples or isinstance(threshold, bool) or not isinstance(threshold, int) or not 1 <= threshold <= len(samples):
        raise ValueError('valid nonempty design and threshold required')
    if any(isinstance(n, bool) or not isinstance(n, int) or not 0 <= n <= population for n in samples):
        raise ValueError('sample sizes must be integers in [0,population]')
    numerator = 1
    for n in sorted(samples)[:threshold]:
        numerator *= population - n
    return Fraction(numerator, population ** threshold)


def balanced_design(population, layers, threshold, alpha='1/20'):
    a = validate(population, layers, threshold, alpha)
    lo, hi = 0, population
    denominator = population ** threshold
    while lo < hi:
        mid = (lo + hi) // 2
        if (population-mid) ** threshold * a.denominator <= a.numerator * denominator:
            hi = mid
        else:
            lo = mid + 1
    samples = [lo] * layers
    return dict(samples=samples, cost=sum(samples), risk_exact=str(risk(population, samples, threshold)),
                optimality='minimum within balanced designs only')


def rectangle_design(population, layers, threshold, alpha='1/20'):
    """Exact minimum among safe count boxes required to cover themselves.

    At most threshold-1 layers may have a positive count bound. All remaining
    layers must certify zero contamination. The joint-zero box risk is a max,
    not a Bonferroni sum. A rule promising only the final metric interval, not
    the box, belongs to the broader direct class instead.
    """
    a = validate(population, layers, threshold, alpha)
    required = Fraction(population) * (1-a)
    n = -(-required.numerator // required.denominator)
    samples = [0] * (threshold-1) + [n] * (layers-threshold+1)
    box = [population] * (threshold-1) + [0] * (layers-threshold+1)
    return dict(samples=samples, count_upper_box=box, cost=sum(samples),
                risk_exact=str(Fraction(population-n, population)),
                optimality='global among fixed joint-zero safe count-box procedures')


def bonferroni_design(population, layers, threshold, alpha='1/20'):
    """Exact optimum for the more conservative sum-budget box class."""
    a = validate(population, layers, threshold, alpha)
    allowed = population*a
    omitted = allowed.numerator // allowed.denominator
    constrained = layers-threshold+1
    samples = [0]*(threshold-1) + [population-omitted] + [population]*(constrained-1)
    return dict(samples=samples, cost=sum(samples), risk_sum_exact=str(Fraction(omitted,population)),
                optimality='global among safe count boxes using a Bonferroni sum')


def optimal_design(population, layers, threshold, alpha='1/20', max_tuples=500000):
    """Global equal-cost optimum via sorted-coordinate reduction.

    Only the r smallest sample sizes affect risk. In an optimum, all h-r
    others can equal the r-th smallest, so enumerate nondecreasing r-tuples.
    No incomplete enumeration result is returned as a certificate.
    """
    a = validate(population, layers, threshold, alpha)
    if isinstance(max_tuples, bool) or not isinstance(max_tuples, int) or max_tuples < 1:
        raise ValueError('positive integer tuple budget required')
    total = comb(population+threshold, threshold)
    if total > max_tuples:
        raise BudgetExceeded('sorted allocation budget exceeded; no partial optimum returned')
    incumbent = balanced_design(population, layers, threshold, a)
    best_cost, best_samples = incumbent['cost'], incumbent['samples']
    denominator = population ** threshold
    evaluated = 0
    for prefix in combinations_with_replacement(range(population+1), threshold):
        cost = sum(prefix[:-1]) + (layers-threshold+1) * prefix[-1]
        if cost >= best_cost:
            continue
        numerator = 1
        for n in prefix:
            numerator *= population - n
        evaluated += 1
        if numerator * a.denominator <= a.numerator * denominator:
            best_cost = cost
            best_samples = list(prefix) + [prefix[-1]] * (layers-threshold)
    return dict(samples=best_samples, cost=best_cost,
                risk_exact=str(risk(population, best_samples, threshold)),
                optimality='global among fixed equal-cost per-layer uniform designs',
                sorted_tuples_enumerated=total, risks_evaluated_after_cost_pruning=evaluated)


def main():
    started = time.perf_counter()
    rows = []
    # Frozen in impact_budget.md before this experiment was run.
    for threshold in (2, 3, 4, 5, 6):
        for population in (2, 5, 10, 20):
            layers = 2*threshold-1
            direct = optimal_design(population, layers, threshold)
            rectangle = rectangle_design(population, layers, threshold)
            balanced = balanced_design(population, layers, threshold)
            bonferroni = bonferroni_design(population, layers, threshold)
            saving = Fraction(rectangle['cost']-direct['cost'], rectangle['cost'])
            rows.append(dict(layer_population=population, layers=layers, threshold=threshold,
                             total_population=population*layers, direct=direct, rectangle=rectangle,
                             balanced=balanced, bonferroni=bonferroni, saving_fraction_exact=str(saving),
                             saving_fraction=float(saving)))
    sources = [Path(__file__), Path(__file__).with_name('impact_budget.md')]
    result = dict(status='mathematical_design_experiment', alpha_exact='1/20',
                  target_accuracy_interval_exact=['9/10', '1'],
                  votes='artificial unanimous correct heads; one fixed evaluation point',
                  real_audit_performed=False, trained_model=False,
                  python=platform.python_version(), platform=platform.platform(),
                  elapsed_seconds=time.perf_counter()-started, rows=rows,
                  negative_control_two_layer_and=dict(population_per_layer=20,
                      direct=optimal_design(20, 2, 2), rectangle=rectangle_design(20, 2, 2)),
                  source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                  limitations=[
                      'No historical provenance, annotation, or model quality is certified.',
                      'Risk is worst probability of all-zero findings under a bad configuration, not audit success probability.',
                      'Optimality excludes adaptive, nonuniform-within-layer, randomized-allocation and unequal-cost designs.',
                      'Rectangle comparator must cover its reported count box, not just the downstream metric.',
                      'Structural separation does not establish originality.'])
    output = Path(__file__).with_name('threshold_results.json')
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(cases=len(rows), elapsed_seconds=result['elapsed_seconds'],
                         maximum_saving=max(r['saving_fraction'] for r in rows),
                         minimum_saving=min(r['saving_fraction'] for r in rows)), indent=2))


if __name__ == '__main__':
    main()
