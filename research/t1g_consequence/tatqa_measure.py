"""Exact audit, executable only after the point-only prediction commit.

tatqa_exact_core is an unchanged copy of T1a law_core (task/t1a, 3b29bfe).
It preserves repeated-input dependence and certifies coordinatewise rational
extrema; this wrapper adds complete rational input witnesses and paired reports.
"""
from __future__ import annotations
import csv,json,subprocess
from collections import Counter
from fractions import Fraction as F
from itertools import product
from pathlib import Path
from tatqa_exact_core import range_certificate,classify_range,gradient_radius,evaluate

ROOT=Path(__file__).resolve().parent

def load(path):return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines()]
def fstr(obj):
    if isinstance(obj,F):return str(obj)
    if isinstance(obj,dict):return {str(k):fstr(v) for k,v in obj.items()}
    if isinstance(obj,(list,tuple)):return [fstr(x) for x in obj]
    return obj
def write_csv(path,rows):
    with path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def witnesses(row,reference,classification):
    if classification!='outside':return None
    centers={k:F(v['value']) for k,v in row['input_provenance'].items()}
    half={k:F(v['half']) for k,v in row['input_provenance'].items()}
    if abs(evaluate(row,centers)-reference)>abs(reference)/100:
        return dict(values=centers,value=evaluate(row,centers),kind='center_already_outside')
    # Strictly interior, with progressively closer approach for narrow violations.
    for shrink in [F(999,1000),F(999999,1000000),F(999999999999,1000000000000)]:
        for signs in product((-1,1),repeat=len(centers)):
            vals={k:centers[k]+s*half[k]*shrink for k,s in zip(centers,signs)}
            try:value=evaluate(row,vals)
            except ZeroDivisionError:continue
            if abs(value-reference)>abs(reference)/100:
                assert all(abs(vals[k]-centers[k])<half[k] for k in centers)
                return dict(values=vals,value=value,kind='strict_interior_corner')
    # Closed half-ULP model permits endpoints; distinguish these rare cases.
    for signs in product((-1,1),repeat=len(centers)):
        vals={k:centers[k]+s*half[k] for k,s in zip(centers,signs)}
        try:value=evaluate(row,vals)
        except ZeroDivisionError:continue
        if abs(value-reference)>abs(reference)/100:return dict(values=vals,value=value,kind='closed_box_corner')
    raise AssertionError(('outside_without_witness',row['id'],str(reference)))

def measure():
    status=subprocess.run(['git','show','0c68d8a:research/t1g_consequence/part3_prediction.json'],cwd=ROOT.parents[1],capture_output=True,text=True,encoding='utf-8')
    if status.returncode:raise RuntimeError('Required frozen prediction commit not found')
    frozen=json.loads(status.stdout)
    if frozen!=json.loads((ROOT/'part3_prediction.json').read_text(encoding='utf-8')):raise RuntimeError('Prediction differs from frozen commit')
    rows=load(ROOT/'tatqa_bound_points.jsonl');results=[]
    for row in rows:
        row['input_intervals']={k:dict(lo=str(F(p['value'])-F(p['half'])),hi=str(F(p['value'])+F(p['half']))) for k,p in row['input_provenance'].items()}
        center,radius,gradient=gradient_radius(row);assert center==F(row['center'])
        cert=range_certificate(row);gold=F(row['gold'])
        cs=classify_range(cert,center,F(1,100));gs=classify_range(cert,gold,F(1,100))
        result={**row,'range':cert,'first_order_radius':radius,'gradient':gradient,'center_status':cs,'gold_status':gs,
            'center_first_order':radius>abs(center)/100,'gold_first_order':abs(center-gold)+radius>abs(gold)/100,
            'center_witness':witnesses(row,center,cs),'gold_witness':witnesses(row,gold,gs),
            'min_sig':min(p['sig'] for p in row['input_provenance'].values())}
        results.append(fstr(result))
    (ROOT/'part3_per_question.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in results),encoding='utf-8')
    compact=[{k:r[k] for k in ['id','split','category','prediction_group','center','gold','min_sig','center_status','gold_status','center_first_order','gold_first_order','first_order_radius']}|dict(range_exact=r['range']['exact'],range_method=r['range']['method'],lo=r['range']['lo'],hi=r['range']['hi']) for r in results]
    write_csv(ROOT/'part3_per_question.csv',compact)
    def summarize(sub,prediction=None):
        n=len(sub);cc=Counter(r['center_status'] for r in sub);gc=Counter(r['gold_status'] for r in sub)
        ccorrect=sum(r['center_first_order']==(r['center_status']=='outside') for r in sub if r['center_status']!='unresolved')
        gcorrect=sum(r['gold_first_order']==(r['gold_status']=='outside') for r in sub if r['gold_status']!='unresolved')
        return dict(n=n,exact_ranges=sum(r['range']['exact'] for r in sub),center_counts=dict(cc),gold_counts=dict(gc),
            center_rate=cc['outside']/n if n else None,gold_rate=gc['outside']/n if n else None,
            center_first_order_accuracy=ccorrect/(n-cc['unresolved']) if n>cc['unresolved'] else None,
            gold_first_order_accuracy=gcorrect/(n-gc['unresolved']) if n>gc['unresolved'] else None,
            prediction=prediction,center_error_pp=100*(prediction-cc['outside']/n) if prediction is not None else None,
            gold_error_pp=100*(prediction-gc['outside']/n) if prediction is not None else None)
    supported=[r for r in results if r['prediction_group']]
    summary=dict(prediction_commit='0c68d8a',total_arithmetic=6960,bound_total=summarize(results),forecast_population=summarize(supported,frozen['prediction']),by_category={},by_split={})
    for category in sorted(set(r['category'] for r in results)):
        sub=[r for r in results if r['category']==category];pred=frozen['by_category'].get(category,{}).get('prediction')
        # Predicted category and measured group may differ for excluded zero growth.
        summary['by_category'][category]=summarize(sub,pred)
    for split in ['train','dev','test']:summary['by_split'][split]=summarize([r for r in results if r['split']==split])
    summary['first_order_disagreements']=[{k:r[k] for k in ['id','category','center_status','gold_status','center_first_order','gold_first_order','center','gold','first_order_radius']} for r in results if r['center_first_order']!=(r['center_status']=='outside') or r['gold_first_order']!=(r['gold_status']=='outside')]
    (ROOT/'part3_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # Diagram panel data use the canonical growth baseline precision in both sets.
    curves=[]
    for item in frozen['curve']:
        if item['category']!='growth':continue
        k=item['k'];sub=[r for r in results if r['prediction_group']=='growth' and r['prediction_parameters']['ka']==k]
        curves.append(dict(dataset='TAT-QA',k=k,n=len(sub),observed=sum(r['center_status']=='outside' for r in sub)/len(sub),predicted=item['prediction']))
    finqa_root=ROOT.parents[2]/'proxy-tail-t1a/research/t1a_law/results'
    bs=json.loads((finqa_root/'benford_summary.json').read_text(encoding='utf-8'))
    for item in bs['by_k_a']:curves.append(dict(dataset='FinQA',k=item['k_a'],n=item['n'],observed=item['observed_center_rate'],predicted=item['marginal_prediction']))
    write_csv(ROOT/'part3_growth_precision_plot.csv',curves)
    # All operations: matched display precision and first-order prediction.
    allcurves=[]
    for k in sorted(set(r['min_sig'] for r in results)):
        sub=[r for r in results if r['min_sig']==k]
        allcurves.append(dict(dataset='TAT-QA',k=k,n=len(sub),observed=sum(r['center_status']=='outside' for r in sub)/len(sub),first_order=sum(r['center_first_order'] for r in sub)/len(sub)))
    t1=load(ROOT.parents[2]/'proxy-tail/research/t1_rounding/results/per_question.jsonl');t1a={r['id']:r for r in load(finqa_root/'per_question.jsonl')}
    for k in sorted(set(r['min_sig'] for r in t1 if r.get('status')=='analyzed')):
        sub=[t1a[r['id']] for r in t1 if r.get('status')=='analyzed' and r['min_sig']==k]
        allcurves.append(dict(dataset='FinQA',k=k,n=len(sub),observed=sum(r['exact_status']=='outside' for r in sub)/len(sub),first_order=sum(r['first_order_prediction']=='outside' for r in sub)/len(sub)))
    write_csv(ROOT/'part3_all_precision_plot.csv',allcurves)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return summary

if __name__=='__main__':measure()
