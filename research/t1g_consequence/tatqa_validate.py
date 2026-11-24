"""Meaningful consistency checks for exact boxes and joint witnesses."""
from __future__ import annotations
import json,csv
from fractions import Fraction as F
from pathlib import Path
from collections import Counter
from tatqa_exact_core import evaluate,range_certificate,gradient_radius,classify_range
from tatqa_measure import load,write_csv
ROOT=Path(__file__).resolve().parent

def validate():
    rows=load(ROOT/'part3_corrected_per_question.jsonl');nw=0;kinds=Counter()
    for row in rows:
        c=F(row['center']);g=F(row['gold']);lo=F(row['range']['lo']);hi=F(row['range']['hi'])
        centers={k:F(v['value']) for k,v in row['input_provenance'].items()}
        assert evaluate(row,centers)==c
        assert lo<=c<=hi
        for label,reference in [('center',c),('gold',g)]:
            outside=lo<reference-abs(reference)/100 or hi>reference+abs(reference)/100
            assert (row[label+'_status']=='outside')==outside
            witness=row[label+'_witness']
            assert bool(witness)==outside
            if witness:
                values={k:F(v) for k,v in witness['values'].items()}
                assert all(abs(values[k]-centers[k])<=F(row['input_provenance'][k]['half']) for k in centers)
                assert evaluate(row,values)==F(witness['value'])
                assert abs(F(witness['value'])-reference)>abs(reference)/100
                kinds[witness['kind']]+=1;nw+=1
    # Shared-source algebra must not create rounding uncertainty for x/x.
    identity=dict(steps=[['divide','x','x']],input_intervals={'x':{'lo':'199/2','hi':'201/2'}})
    cert=range_certificate(identity);assert cert['exact'] and cert['lo']==cert['hi']==1
    center,radius,_=gradient_radius(identity);assert center==1 and radius==0
    # Near-cancellation has a genuine joint witness and an exact linear range.
    cancel=dict(steps=[['subtract','x','y']],input_intervals={'x':{'lo':'199/2','hi':'201/2'},'y':{'lo':'197/2','hi':'199/2'}})
    cert=range_certificate(cancel);assert cert['exact'] and cert['lo']==0 and cert['hi']==2
    assert classify_range(cert,F(1),F(1,100))=='outside'
    summary=dict(corrected_rows_checked=len(rows),joint_witnesses_checked=nw,witness_types=dict(kinds),dependency_identity_passed=True,cancellation_passed=True,
        large_gold_offsets=sum(abs(F(r['center'])-F(r['gold']))>abs(F(r['gold']))/100 for r in rows),
        percent_reference_normalized=sum(r['scale']=='percent' for r in rows))
    (ROOT/'part3_validation.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    # Use centered outcomes consistently for the all-operations plot.
    plot=[]
    for k in sorted(set(r['min_sig'] for r in rows)):
        sub=[r for r in rows if r['min_sig']==k]
        plot.append(dict(dataset='TAT-QA corrected',k=k,n=len(sub),observed=sum(r['center_status']=='outside' for r in sub)/len(sub),first_order=sum(r['center_first_order'] for r in sub)/len(sub)))
    finqa=ROOT.parents[2]/'proxy-tail-t1a/research/t1a_law/results/per_question.jsonl'
    t1=load(ROOT.parents[2]/'proxy-tail/research/t1_rounding/results/per_question.jsonl');t1a={r['id']:r for r in load(finqa)}
    def ef(v):return F(v['exact'])
    for k in sorted(set(r['min_sig'] for r in t1 if r.get('status')=='analyzed')):
        sub=[t1a[r['id']] for r in t1 if r.get('status')=='analyzed' and r['min_sig']==k]
        observed=sum(ef(r['lo'])<ef(r['center'])-abs(ef(r['center']))/100 or ef(r['hi'])>ef(r['center'])+abs(ef(r['center']))/100 for r in sub)/len(sub)
        plot.append(dict(dataset='FinQA',k=k,n=len(sub),observed=observed,first_order=sum(r['centered_first_order_prediction']=='outside' for r in sub)/len(sub)))
    write_csv(ROOT/'part3_all_precision_corrected_plot.csv',plot)
    print(json.dumps(summary,indent=2))

if __name__=='__main__':validate()
