"""Exact finite counterexample to marginal-only independence of a seed.

This enumerates artificial fair-bit worlds; it is not a financial experiment.
"""
from fractions import Fraction
from itertools import product
import json


def independent(joint):
    left = {x for x, _ in joint}
    right = {y for _, y in joint}
    return all(joint.get((x,y), Fraction()) ==
               sum(p for (a,_),p in joint.items() if a == x) *
               sum(p for (_,b),p in joint.items() if b == y)
               for x in left for y in right)


def run_checks():
    records = []
    for truth_table in product((0,1), repeat=4):
        joint = {}
        for h,b in product((0,1), repeat=2):
            omega = truth_table[2*h+b]
            joint[omega,b] = joint.get((omega,b),Fraction()) + Fraction(1,4)
        marginal = independent(joint)
        conditional = True
        for h in (0,1):
            given_h = {}
            for b in (0,1):
                key = truth_table[2*h+b], b
                given_h[key] = given_h.get(key,Fraction()) + Fraction(1,2)
            conditional &= independent(given_h)
        records.append({'omega_table_order_00_01_10_11':truth_table,
                        'omega_independent_of_future_marginally':marginal,
                        'omega_independent_of_future_given_history':conditional})
    misleading = [r for r in records if r['omega_independent_of_future_marginally']
                  and not r['omega_independent_of_future_given_history']]
    assert len(records) == 16
    assert sum(r['omega_independent_of_future_marginally'] for r in records) == 6
    assert sum(r['omega_independent_of_future_given_history'] for r in records) == 4
    assert {r['omega_table_order_00_01_10_11'] for r in misleading} == {(0,1,1,0),(1,0,0,1)}
    xor_worlds = [{'history':h,'future':b,'seed':h^b,'output':h^(h^b),'probability':'1/4'}
                  for h,b in product((0,1),repeat=2)]
    assert all(r['output'] == r['future'] for r in xor_worlds)
    return {'scope':'all 16 deterministic Boolean seeds in an artificial independent fair-bit world',
            'arithmetic':'exact Fraction probabilities', 'functions_enumerated':16,
            'marginal_independence_passes':6,'conditional_independence_passes':4,
            'marginal_only_counterexamples':misleading,'xor_worlds':xor_worlds,
            'conclusion':'fixed-seed factorization and measurability are distinct from no added future information',
            'limitations':['finite check of a specified counterexample, not a proof for all probability spaces',
                           'no inference about actual seed generation or actual financial data']}


if __name__ == '__main__':
    print(json.dumps(run_checks(),ensure_ascii=False,indent=2))
