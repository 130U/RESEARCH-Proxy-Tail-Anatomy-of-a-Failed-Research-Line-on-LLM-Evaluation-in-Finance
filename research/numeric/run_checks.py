"""Constructed semantic-envelope study, no natural-language parsing or training."""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

from research.numeric.semantic_envelope import (Interval, Budget, SemanticBranch,
    semantic_envelope, probabilities_at_eta, width_gate, relative_change_interval,
    difference_interval, rescale_interval, robust_label, label_set)

ROOT = Path(__file__).resolve().parents[1]
BUDGET = Budget()
LABELS = ('low','middle','high')


def branch(identity, g, slope=1, offset=0, thresholds=(-1,1), labels=LABELS):
    return SemanticBranch(identity,g,slope,offset,tuple(map(F,thresholds)),
                          target_id='constructed-ordered-response',class_labels=labels)


def envelope(branches):
    return semantic_envelope(branches,BUDGET)


def display(result):
    return {'class_intervals_approximate_display':[[float(x.lower),float(x.upper)] for x in result.class_intervals],
            'certificate':result.to_json()}


def run():
    tick = time.perf_counter()
    cases = {}
    # An interior probability maximum is essential even for one fixed context.
    middle = envelope([branch('wide-logit',Interval(-3,3))])
    endpoint_upper = max(probabilities_at_eta(x,(-1,1),BUDGET)[1].upper for x in (-3,3))
    if middle.extrema[1].maximum.lower <= endpoint_upper:
        raise AssertionError('interior-peak witness did not separate from endpoints')
    cases['interior_middle_peak'] = {**display(middle),
        'endpoint_only_maximum_upper':str(endpoint_upper),
        'certified_interior_peak_minimum':str(middle.extrema[1].maximum.lower)}

    # Two exact but conflicting semantic branches are not numerical error.
    discrete = envelope([branch('context-left',Interval(0,0),offset=-4),
                         branch('context-right',Interval(0,0),offset=4)])
    scalar_hull = envelope([branch('convexified-logit',Interval(-4,4))])
    if discrete.class_intervals[1].width > BUDGET.tolerance:
        raise AssertionError('symmetry should identify the middle probability up to rounding')
    if scalar_hull.extrema[1].maximum.lower <= discrete.extrema[1].maximum.upper:
        raise AssertionError('collapsing disconnected branches must introduce an unattainable peak')
    if width_gate(discrete,F(1,10)).status != 'fail':
        raise AssertionError('wide semantic ambiguity must fail the declared width gate')
    cases['discrete_semantics_with_zero_numeric_radius'] = {
        'finite_union':display(discrete),'scalar_hull_relaxation':display(scalar_hull),
        'gate_010':width_gate(discrete,F(1,10)).to_json(),
        'scope':'middle probability identifiable by symmetry; low/high remain ambiguous'}

    # Same underlying variable: preserving equality is strictly more informative.
    coupled = envelope([branch('same-quantity',Interval(0,0),slope=2)])
    relaxed_g = relative_change_interval(Interval(100,200),Interval(100,200))
    rectangle = envelope([branch('independent-rectangle',relaxed_g,slope=2)])
    if relaxed_g != Interval(F(-1,2),1):
        raise AssertionError('wrong independent ratio range')
    cases['dependency_information'] = {'known_constraint':'x=b in [100,200]',
        'exact_g':Interval(0,0).to_json(),'rectangle_g':relaxed_g.to_json(),
        'preserved_relation':display(coupled),'forgotten_relation':display(rectangle),
        'interpretation':'loss from forgetting a known relation, not intrinsic ambiguity of the original problem'}

    x,b = Interval(90,110),Interval(100,100)
    original_g = relative_change_interval(x,b)
    original = envelope([branch('unit-invariant-tuple',original_g,slope=2)])
    scales = (F(1,1000000),F(1,1000),F(1),F(1000),F(1000000))
    for scale in scales:
        g = relative_change_interval(rescale_interval(x,scale),rescale_interval(b,scale))
        if g != original_g or envelope([branch('unit-invariant-tuple',g,slope=2)]).to_json() != original.to_json():
            raise AssertionError('positive common unit scaling changed a normalized certificate')
    cases['unit_invariance'] = {'scales':[str(s) for s in scales],
        'g':original_g.to_json(),'equal_normalized_features_and_certificates':True,
        'scope':'rational tuples only; no natural-text parser invariance was evaluated'}

    # Individually monotone branches can jump down through a selector.
    eps = F(1,10**6)
    before = envelope([branch('selected-before',Interval(-eps,-eps),offset=4,
                              thresholds=(0,),labels=('low','high'))])
    after = envelope([branch('selected-after',Interval(eps,eps),offset=-4,
                             thresholds=(0,),labels=('low','high'))])
    drop_lower = before.class_intervals[1].lower-after.class_intervals[1].upper
    branch_lipschitz_allowance = (2*eps)/4
    if drop_lower <= branch_lipschitz_allowance:
        raise AssertionError('switching witness must exceed fixed-branch derivative allowance')
    cases['branch_switch'] = {'input_distance':str(2*eps),
        'each_fixed_branch_probability_lipschitz_bound':'1/4',
        'fixed_branch_allowance':str(branch_lipschitz_allowance),
        'certified_output_drop_lower':str(drop_lower),
        'approximate_drop_display':float(drop_lower),
        'scope':'one finite witness; the proof establishes a jump as epsilon tends to zero'}

    agreement = [difference_interval(Interval(110,120),Interval(100,100)),
                 difference_interval(Interval(115,125),Interval(100,105))]
    conflict = [difference_interval(Interval(150,150),Interval(100,100)),
                difference_interval(Interval(150,150),Interval(200,200))]
    if robust_label(agreement) != 'above' or robust_label(conflict) is not None:
        raise AssertionError('symbolic consensus did not match specified comparison semantics')
    cases['symbolic_comparison'] = {
        'agreement_branch_labels':[label_set(v) for v in agreement],
        'agreement_decision':robust_label(agreement),
        'conflicting_baseline_branch_labels':[label_set(v) for v in conflict],
        'conflict_decision':robust_label(conflict),
        'meaning':'exact sign(x-baseline) task; a learned head is not needed when semantics agree'}

    # Freeze all 25 grid cells, not only visually helpful ones.
    widths = (F(1,20),F(1,10),F(1,5))
    radius_values = (F(0),F(1,10),F(1,2),F(1),F(2))
    offsets = (F(0),F(1,4),F(1),F(2),F(4))
    grid = []
    totals = {str(w):{'pass':0,'fail':0,'undetermined':0} for w in widths}
    for radius in radius_values:
        for offset in offsets:
            result = envelope([branch('minus',Interval(-radius,radius),offset=-offset),
                               branch('plus',Interval(-radius,radius),offset=offset)])
            decisions = {str(w):width_gate(result,w).to_json() for w in widths}
            for w in widths:
                totals[str(w)][decisions[str(w)]['status']] += 1
            grid.append({'radius':str(radius),'context_offset_magnitude':str(offset),
                         'decisions':decisions,
                         'approximate_max_width_display':float(width_gate(result,F(1,10)).width_bounds.upper)})
    for w, counts in totals.items():
        counts['guaranteed_accepted_fraction'] = str(F(counts['pass'],len(grid)))
        counts['possible_accepted_fraction_upper'] = str(F(counts['pass']+counts['undetermined'],len(grid)))

    # Probe the numerical decision boundary without claiming a primary scientific gate.
    boundary_bounds = width_gate(middle,F(1,10)).width_bounds
    probe = (boundary_bounds.lower+boundary_bounds.upper)/2
    if boundary_bounds.width <= 0 or width_gate(middle,probe).status != 'undetermined':
        raise AssertionError('an unresolved numerical boundary must not silently pass or fail')
    cases['numerical_boundary_probe'] = {'threshold_rule':'midpoint of computed width enclosure, implementation probe only',
                                        **width_gate(middle,probe).to_json()}

    result = {'status':'conditional numeric component only; no parser or trained-model certificate',
        'budget':{'tolerance_per_extremum':str(BUDGET.tolerance),'max_terms':BUDGET.max_terms,
                  'max_abs_argument':str(BUDGET.max_abs_argument)},
        'cases':cases,'grid':grid,'grid_count':len(grid),'primary_width_gate':'1/10',
        'finite_constructed_population_frontier':totals,
        'frontier_scope':'25 equally weighted declared candidate problems, not empirical population coverage',
        'python':sys.version,'platform':platform.platform(),'gpu_used':False,
        'model_training_performed':False,'natural_text_parsing_performed':False,
        'peak_memory_measured':False,
        'source_hashes':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
                        ('numeric/semantic_envelope.py','numeric/run_checks.py','numeric/PROTOCOL.md')},
        'elapsed_seconds':time.perf_counter()-tick,
        'limitations':['true semantic candidate coverage is unverified',
                       'model probabilities are not certified true class probabilities',
                       'minimal coordinate box relative to supplied branch intervals, not jointly attainable box',
                       'all coefficients are hand-specified mathematical examples; no architecture novelty claim',
                       'finite checks do not prove global parser correctness, usefulness or novelty']}
    (ROOT/'numeric/results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    return result


if __name__ == '__main__':
    result = run()
    print(json.dumps({'grid_count':result['grid_count'],
        'frontier':result['finite_constructed_population_frontier'],
        'branch_switch_drop_lower_approximate':result['cases']['branch_switch']['approximate_drop_display'],
        'elapsed_seconds':result['elapsed_seconds']},indent=2))
