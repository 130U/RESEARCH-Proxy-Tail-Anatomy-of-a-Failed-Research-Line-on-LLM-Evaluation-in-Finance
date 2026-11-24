"""Independent replay of saved proofs: never calls an optimizer."""
import hashlib
import copy
import json
from fractions import Fraction as F
from prepare import HERE
from run_audit import load_inputs,build_model,acceptance
from exact_solver import verify_result
from interval_core import eval_scalar

def main():
    packets,reviews=load_inputs();lookup={p['id']:p for p in packets}
    out=HERE/'results';summary=json.loads((out/'summary.json').read_text(encoding='utf8'))
    for part,expected in summary['review_sha256'].items():
        assert hashlib.sha256((HERE/f'review_{part}.json').read_bytes()).hexdigest()==expected,'Review changed after solving'
    rows=[json.loads(s) for s in (out/'per_question.jsonl').read_text(encoding='utf8').splitlines()]
    assert {r['id'] for r in rows}==set(lookup)
    proofs=0;paired=0;optional=0
    for row in rows:
        packet=lookup[row['id']];review=reviews[row['id']]
        for i,name in enumerate(('original','duplicates','sums')):
            bounds,eq,inventory=build_model(packet,review,i);result=row['stages'][name]
            assert result['bounds']=={k:list(map(str,v)) for k,v in bounds.items()}
            assert result['equations']==[{k:str(v) for k,v in e.items()} for e in eq]
            assert verify_result(bounds,eq,row['steps'],acceptance(packet['audit']),result)
            proofs+=1
        if row['final']=='retained':
            witness=row['inside_witness'];assert witness is not None
            p={k:F(v) for k,v in witness['point'].items()}
            assert set(p)==set(bounds)
            assert all(lo==hi or lo<p[k]<hi for k,(lo,hi) in bounds.items())
            assert all(sum((v*p[k] for k,v in e.items()),F(0))==0 for e in eq)
            result=eval_scalar(row['steps'],p);lo,hi=acceptance(packet['audit'])
            assert lo<=result<=hi and str(result)==witness['value']
            assert row['stages']['sums']['status']=='witnessed_outside'
            paired+=1
        if row.get('optional_sensitivity'):
            stronger=copy.deepcopy(review)
            stronger['equations']+=stronger['optional_sensitivity_equations']
            bounds,eq,_=build_model(packet,stronger,2)
            assert verify_result(bounds,eq,row['steps'],acceptance(packet['audit']),row['optional_sensitivity']['result'])
            optional+=1
    report={'questions':len(rows),'stage_proofs_verified_without_optimizer':proofs,
            'paired_inside_outside_witnesses_verified':paired,
            'optional_sensitivity_proofs_verified':optional,'pass':True}
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
