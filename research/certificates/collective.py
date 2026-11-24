"""Bound accuracy and macro-F1 under a shared budget of changed shard heads.

The mathematical adversary can change each selected head's predictions freely
on the fixed finite evaluation set. This relaxes retraining realizability and
therefore gives sound outer bounds, not a claim every witness can be trained.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
from itertools import combinations
import json
from math import comb, inf, nextafter
from pathlib import Path

from research.local.audit import audit_upper, reachable


class BudgetExceeded(ValueError):
    """No certificate is returned if an exact search budget is exhausted."""


def integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def validate(votes, labels, classes, budget):
    if not integer(classes) or classes < 2 or not integer(budget) or budget < 0:
        raise ValueError('classes >=2 and budget >=0 must be integers')
    if not votes or not labels or len(votes) != len(labels) or not votes[0]:
        raise ValueError('nonempty rectangular votes and one label per example required')
    m = len(votes[0])
    if any(len(row) != m for row in votes):
        raise ValueError('all examples must have the same ordered shard IDs')
    if not all(integer(x) and 0 <= x < classes for row in votes for x in row):
        raise ValueError('vote classes must be integer indices')
    if not all(integer(x) and 0 <= x < classes for x in labels):
        raise ValueError('true labels must be integer class indices')
    return len(votes), m, min(budget, m)


def interval(lower, upper):
    lower, upper = Fraction(lower), Fraction(upper)
    if lower > upper:
        raise ValueError('inverted interval')
    lo, hi = float(lower), float(upper)
    if Fraction(lo) > lower: lo = nextafter(lo, -inf)
    if Fraction(hi) < upper: hi = nextafter(hi, inf)
    return dict(lower=lo, upper=hi, lower_exact=str(lower), upper_exact=str(upper))


def metric_values(true_support, true_positive, predicted):
    """Fixed-K macro-F1: a class with both counts zero contributes zero."""
    classes = len(true_support)
    n = sum(true_support)
    accuracy = Fraction(sum(true_positive), n)
    macro = sum((Fraction(2*t, a+p) if a+p else Fraction(0)
                 for a,t,p in zip(true_support,true_positive,predicted)), Fraction(0))/classes
    return accuracy, macro


def candidates_for_subset(votes, changed, classes):
    changed = set(changed)
    size = len(changed)
    result = []
    for row in votes:
        counts = [sum(v == c for i,v in enumerate(row) if i not in changed) for c in range(classes)]
        choices = [c for c in range(classes) if all(
            counts[c]+size >= counts[d]+int(d < c) for d in range(classes) if d != c)]
        if not choices:
            raise AssertionError('a voting outcome must exist')
        result.append(choices)
    return result


def component_bounds(candidates, labels, classes):
    """Cheap outer envelope; per-class extremizers need not coincide."""
    support = [labels.count(c) for c in range(classes)]
    low_terms, high_terms = [], []
    for c in range(classes):
        tp_low = sum(y == c and choices == [c] for y,choices in zip(labels,candidates))
        tp_high = sum(y == c and c in choices for y,choices in zip(labels,candidates))
        fp_low = sum(y != c and choices == [c] for y,choices in zip(labels,candidates))
        fp_high = sum(y != c and c in choices for y,choices in zip(labels,candidates))
        low_den = support[c]+tp_low+fp_high
        high_den = support[c]+tp_high+fp_low
        low_terms.append(Fraction(2*tp_low,low_den) if low_den else Fraction(0))
        high_terms.append(Fraction(2*tp_high,high_den) if high_den else Fraction(0))
    n = len(labels)
    acc_low = Fraction(sum(choices == [y] for y,choices in zip(labels,candidates)),n)
    acc_high = Fraction(sum(y in choices for y,choices in zip(labels,candidates)),n)
    return {'accuracy': (acc_low,acc_high), 'macro_f1': (sum(low_terms)/classes,sum(high_terms)/classes)}, None


def exact_bounds(candidates, labels, classes, max_states):
    """Enumerate sufficient-count states, not independent class optima.

    Each state is (TP_0,...,TP_K-1, predicted_0,...,predicted_K-1).
    Exact only within the stated candidate-product relaxation.
    """
    states = {(0,)*(2*classes)}
    peak = 1
    for y, choices in zip(labels,candidates):
        updated = set()
        for state in states:
            for c in choices:
                next_state = list(state)
                next_state[classes+c] += 1
                next_state[c] += int(c == y)
                updated.add(tuple(next_state))
                if len(updated) > max_states:
                    raise BudgetExceeded('exact count-state budget exceeded; no partial certificate returned')
        states = updated
        peak = max(peak,len(states))
    support = [labels.count(c) for c in range(classes)]
    low, high = [Fraction(1),Fraction(1)],[Fraction(0),Fraction(0)]
    for state in states:
        values = metric_values(support,state[:classes],state[classes:])
        low = [min(a,b) for a,b in zip(low,values)]
        high = [max(a,b) for a,b in zip(high,values)]
    return dict(accuracy=(low[0],high[0]),macro_f1=(low[1],high[1])),dict(peak=peak,final=len(states))


def certify(votes, labels, classes=3, budget=1, method='component', max_subsets=100000, max_states=100000):
    labels = list(labels)
    n,m,budget = validate(votes,labels,classes,budget)
    if method not in ('component','exact'):
        raise ValueError('method must be component or exact')
    if not all(integer(x) and x >= 1 for x in (max_states,max_subsets)):
        raise ValueError('positive integer search limits required')
    subsets = comb(m,budget)
    if subsets > max_subsets:
        raise BudgetExceeded('subset budget exceeded; no partial certificate returned')
    def bound(candidates):
        return (component_bounds(candidates,labels,classes) if method == 'component'
                else exact_bounds(candidates,labels,classes,max_states))
    counts = [[row.count(c) for c in range(classes)] for row in votes]
    independent = [reachable(count,budget) for count in counts]
    pointwise,pointwise_states = bound(independent)
    collective = {'accuracy': [Fraction(1),Fraction(0)], 'macro_f1': [Fraction(1),Fraction(0)]}
    extremizers = {metric:{'lower':None,'upper':None} for metric in collective}
    peak_states = 0
    for changed in combinations(range(m),budget):
        current,state_count = bound(candidates_for_subset(votes,changed,classes))
        if state_count: peak_states = max(peak_states,state_count['peak'])
        for metric,(lo,hi) in current.items():
            if extremizers[metric]['lower'] is None or lo < collective[metric][0]:
                collective[metric][0] = lo; extremizers[metric]['lower'] = list(changed)
            if extremizers[metric]['upper'] is None or hi > collective[metric][1]:
                collective[metric][1] = hi; extremizers[metric]['upper'] = list(changed)
    return dict(status='conditional_mathematical_certificate',method=method,
                exactness='exact for arbitrary selected-head outputs' if method=='exact' else 'outer envelope from separate class extrema',
                n_examples=n,n_heads=m,classes=classes,affected_heads_budget=budget,
                tie_rule='smallest class index',empty_class_f1=0,
                independent={metric:interval(*v) for metric,v in pointwise.items()},
                collective={metric:interval(*v) for metric,v in collective.items()},
                endpoint_subsets=extremizers,subsets_enumerated=subsets,
                exact_states=dict(pointwise=pointwise_states,collective_peak=peak_states) if method=='exact' else None,
                arithmetic='exact fractions with outward-rounded binary64 display',
                assumptions=['same fixed evaluation points and true labels for clean and observed models',
                             'same ordered shard IDs across every vote row',
                             'at most budget heads may differ jointly across the evaluation set',
                             'all unselected heads and shared preprocessing/backbone are unchanged'],
                limitations=['head-budget premise is not verified by this checker',
                             'not a timestamp, parsing, or population generalization certificate',
                             'selected heads allowed arbitrary outputs: outer relaxation of retraining',
                             'no assertion that supplied votes came from a trained language model'])


def certify_from_audit(votes, labels, population, sample_size, findings, alpha='1/20', classes=3,
                       method='component', max_subsets=100000, max_states=100000):
    """Combine exact fixed-n audit inversion with both deterministic envelopes.

    All claims remain conditional on supplied audit and training assumptions.
    This routine checks arithmetic, not whether an audit was really random.
    """
    a=Fraction(str(alpha))
    upper=audit_upper(population,sample_size,findings,a)
    result=certify(votes,labels,classes,upper,method,max_subsets,max_states)
    result['status']='conditional_fixed_population_audit_certificate'
    result['audit']=dict(population=population,sample_size=sample_size,findings=findings,
                         alpha_exact=str(a),contamination_upper=upper,
                         joint_coverage_at_least_exact=str(1-a),
                         probability_space='uniform fixed-size audit of frozen finite document population',
                         evidence_status='supplied audit summary; not independently verified')
    result['assumptions'] += [
        'audit sample uniform without replacement, fixed n and perfectly adjudicated',
        'population, model, head mapping and evaluation set fixed before audit',
        'deleting one contaminated stable-ID document affects at most one head',
        'trusted core, tokenizer and shared preprocessing are historically valid',
        'clean comparator deletes future content under historically measurable selection rules']
    result['joint_claim']='both fixed-test clean-comparator metrics lie in their collective intervals on the same audit-coverage event'
    result['limitations'] += ['not a claim of independently established clean training provenance',
                              'not an anytime-valid audit or future-population guarantee',
                              'no extra alpha split needed for these two consequences of the same event']
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--method',choices=['component','exact'],default='component')
    parser.add_argument('--max-subsets',type=int,default=100000)
    parser.add_argument('--max-states',type=int,default=100000)
    args=parser.parse_args()
    raw=args.input.read_bytes(); source=json.loads(raw)
    if source.get('input_kind') != 'head_predictions':
        raise ValueError('input_kind must be head_predictions; class-count matrices are not interchangeable')
    votes=source['votes_by_example_and_head']
    if 'audit' in source:
        if 'budget' in source: raise ValueError('choose audit-derived budget or explicit head budget, not both')
        a=source['audit']
        result=certify_from_audit(votes,source['labels'],a['population'],a['sample_size'],a['findings'],
                                 a.get('alpha','1/20'),source.get('classes',3),args.method,args.max_subsets,args.max_states)
    else:
        result=certify(votes,source['labels'],source.get('classes',3),source['budget'],args.method,args.max_subsets,args.max_states)
    result['input_sha256']=hashlib.sha256(raw).hexdigest()
    result['checker_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__ == '__main__': main()
