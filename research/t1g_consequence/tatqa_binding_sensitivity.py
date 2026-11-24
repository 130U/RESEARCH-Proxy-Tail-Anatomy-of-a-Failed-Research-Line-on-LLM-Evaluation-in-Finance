"""Post-freeze semantic sensitivity: explicit structural constants stay exact.

The frozen forecast and original results are never overwritten. This records
the discovered number-to-source collision in means and growth baselines.
The same frozen prediction population (IDs) is retained for comparison.
"""
from __future__ import annotations
import copy,json,re
from fractions import Fraction as F
from collections import Counter
from pathlib import Path
from tatqa_exact_core import range_certificate,classify_range,gradient_radius,evaluate
from tatqa_measure import witnesses,fstr,write_csv,load
ROOT=Path(__file__).resolve().parent

def repair(row):
    row=copy.deepcopy(row);p=row['input_provenance'];changes=[];steps=[]
    question=row['question'].lower()
    for i,(op,a,b) in enumerate(row['steps']):
        olda,oldb=a,b
        if (op=='divide' and re.search(r'\baverage\b|\bmean\b',question)
                and b in p and F(p[b]['value']).denominator==1 and 2<=F(p[b]['value'])<=12):
            b=p[b]['value'];reason='mean_divisor_is_exact_count'
        elif (op=='subtract' and re.search(r'percent|growth|change|increase|decrease|proportion',question)
                and b in p and F(p[b]['value'])==1 and a.startswith('#')
                and row['steps'][int(a[1:])][0]=='divide'):
            b='1';reason='unit_growth_baseline_is_exact'
        elif (op=='subtract' and re.search(r'percent|proportion|share',question)
                and a in p and F(p[a]['value'])==1 and b.startswith('#')
                and row['steps'][int(b[1:])][0]=='divide'):
            a='1';reason='unit_complement_baseline_is_exact'
        else:reason=None
        if reason:changes.append(dict(step=i,old=[op,olda,oldb],new=[op,a,b],reason=reason))
        steps.append([op,a,b])
    if changes:
        used={v for op,a,b in steps for v in (a,b) if v in p}
        row['input_provenance']={k:v for k,v in p.items() if k in used};row['steps']=steps
    return row,changes

def main():
    original=load(ROOT/'part3_per_question.jsonl');results=[];changes=[]
    for old in original:
        row,edits=repair(old)
        if edits:
            row['input_intervals']={k:dict(lo=str(F(p['value'])-F(p['half'])),hi=str(F(p['value'])+F(p['half']))) for k,p in row['input_provenance'].items()}
            center,radius,gradient=gradient_radius(row);assert center==F(row['center'])
            cert=range_certificate(row);gold=F(row['gold'])
            cs=classify_range(cert,center,F(1,100));gs=classify_range(cert,gold,F(1,100))
            row.update(range=cert,first_order_radius=radius,gradient=gradient,center_status=cs,gold_status=gs,
                center_first_order=radius>abs(center)/100,gold_first_order=abs(center-gold)+radius>abs(gold)/100,
                center_witness=witnesses(row,center,cs),gold_witness=witnesses(row,gold,gs),
                min_sig=min(p['sig'] for p in row['input_provenance'].values()))
            changes.append(dict(id=row['id'],question=row['question'],derivation=row['derivation'],forecast_member=bool(row['prediction_group']),edits=edits,old_center_status=old['center_status'],new_center_status=cs,old_gold_status=old['gold_status'],new_gold_status=gs))
        results.append(fstr(row))
    (ROOT/'part3_corrected_per_question.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in results),encoding='utf-8')
    (ROOT/'part3_binding_corrections.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in changes),encoding='utf-8')
    frozen=json.loads((ROOT/'part3_prediction.json').read_text(encoding='utf-8'))
    def summ(rows,pred=None):
        n=len(rows);cs=sum(r['center_status']=='outside' for r in rows);gs=sum(r['gold_status']=='outside' for r in rows)
        return dict(n=n,center_outside=cs,gold_outside=gs,center_rate=cs/n,gold_rate=gs/n,
            center_accuracy=sum(r['center_first_order']==(r['center_status']=='outside') for r in rows)/n,
            gold_accuracy=sum(r['gold_first_order']==(r['gold_status']=='outside') for r in rows)/n,
            prediction=pred,center_error_pp=100*(pred-cs/n) if pred is not None else None,gold_error_pp=100*(pred-gs/n) if pred is not None else None)
    summary=dict(corrected_questions=len(changes),corrected_forecast_members=sum(x['forecast_member'] for x in changes),
        correction_types=dict(Counter(e['reason'] for x in changes for e in x['edits'])),
        all_bound=summ(results),frozen_forecast_population=summ([r for r in results if r['prediction_group']],frozen['prediction']),
        by_frozen_category={c:summ([r for r in results if r['category']==c],frozen['by_category'].get(c,{}).get('prediction')) for c in sorted(set(r['category'] for r in results))})
    (ROOT/'part3_binding_sensitivity_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    compact=[{k:r[k] for k in ['id','split','category','prediction_group','center','gold','min_sig','center_status','gold_status','center_first_order','gold_first_order','first_order_radius']}|dict(range_exact=r['range']['exact'],range_method=r['range']['method'],lo=r['range']['lo'],hi=r['range']['hi']) for r in results]
    write_csv(ROOT/'part3_corrected_per_question.csv',compact)
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
