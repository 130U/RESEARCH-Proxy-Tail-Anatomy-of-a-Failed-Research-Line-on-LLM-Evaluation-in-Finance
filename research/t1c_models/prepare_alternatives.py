"""Transfer prior same-fact source reviews without examining model responses."""
import argparse
import csv
import itertools
import json
import re
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
from score import ROOT,load_module

def main():
    p=argparse.ArgumentParser();p.add_argument('--t1-dir',type=Path,default=ROOT.parents[2]/'proxy-tail/research/t1_rounding');a=p.parse_args()
    core=load_module('t1c_alt_core',a.t1_dir/'interval_core.py')
    rows=json.loads((ROOT/'private/sample.json').read_text(encoding='utf8'));byid={r['id']:r for r in rows}
    changes=defaultdict(list)
    with (a.t1_dir/'duplicate_precision_test_substitutions_part1.csv').open(encoding='utf8') as f:
        for s in csv.DictReader(f):
            if s['question_id'] in byid:
                changes[s['question_id']].append({'old':s['old_operand'],'new':s['new_operand'],
                    'prior_review':'part1 candidate '+s['candidate_pair'],'direction':s['source_direction']})
    with (a.t1_dir/'duplicate_precision_test_review_part2.csv').open(encoding='utf8') as f:
        for r in csv.DictReader(f):
            if r['confirmed_same_fact'] not in ('yes','true'):continue
            for s in json.loads(r['coarse_substitution_checks'] or '[]'):
                if s['question_id'] not in byid:continue
                old,new=s['single_operand_substitution'].split(' -> ')
                if F(old)==F(new):continue
                changes[s['question_id']].append({'old':old,'new':new,'prior_review':'part2 candidate '+r['candidate_row'],
                    'direction':'coarse_for_fine','source_reason':r['reason']})
    result=[]
    for qid,cs in changes.items():
        r=byid[qid]; steps=[(op,x.strip(),y.strip()) for op,x,y in re.findall(r'(\w+)\(([^,]+),\s*([^)]*)\)',r['program'])]
        for flags in itertools.product((False,True),repeat=len(cs)):
            if not any(flags):continue
            selected=[c for c,flag in zip(cs,flags) if flag]
            substitution={c['old']:F(c['new']) for c in selected}
            value=core.eval_scalar(steps,substitution)
            result.append({'call_id':r['call_id'],'id':qid,'substitutions':selected,
                'alternative_value_exact':str(value),'alternative_value_decimal':float(value),
                'source':'T1 fixed prior source-identity reviews; not by itself proof that a model used these sources'})
    (ROOT/'alternative_values.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    print(len(result),'alternative calculations across',len(changes),'selected questions')

if __name__=='__main__':main()
