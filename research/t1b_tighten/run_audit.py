"""T1B three-stage audit; review decisions are explicit, versioned inputs."""
import argparse
from collections import Counter
from fractions import Fraction as F
import hashlib
import copy
import json
from pathlib import Path
import sys
from prepare import HERE, T1, table_facts
from exact_solver import solve_range, verify_result
sys.path.insert(0,str(T1))
from interval_core import eval_scalar

def load_inputs(partial=False):
    packets=[]; reviews=[]
    for suffix in ('a','b'):
        packets += json.loads((HERE/f'packets_{suffix}.json').read_text(encoding='utf8'))
        path=HERE/f'review_{suffix}.json'
        if path.exists():reviews += json.loads(path.read_text(encoding='utf8'))
    lookup={r['id']:r for r in reviews}
    assert len(lookup)==len(reviews),'duplicate reviews'
    if not partial:
        assert len(lookup)==len(packets)==196
        assert all(r['verdict'] in ('valid','invalid','uncertain') for r in reviews)
        assert all(r['context_reviewed'] for r in reviews)
    return packets,lookup

def native_box(audit):
    return {k:tuple(F(b[end]['exact']) for end in ('lo','hi')) for k,b in audit['input_intervals'].items()}

def acceptance(audit):
    y=F(str(audit['exe_ans'])); h=abs(y)/100
    return y-h,y+h

def build_model(packet,review,stage):
    audit=packet['audit']; box=native_box(audit); eq=[]; inventory=[]
    if stage==0:return box,eq,inventory
    for d in review['duplicates']:
        k=d['variable']; low,high=F(d['lo']),F(d['hi'])
        assert k in box and low<=high
        old=box[k]; box[k]=(max(old[0],low),min(old[1],high))
        inventory.append({'type':'duplicate_intersection',**d,'before':list(map(str,old)),'after':list(map(str,box[k]))})
    if stage==1:return box,eq,inventory
    allfacts=table_facts(packet['document'],allow_percent=True)
    extra={k:tuple(map(F,v)) for k,v in review.get('extra_bounds',{}).items()}
    # Only bring table facts connected to reviewed relations or source links.
    used={k for e in review['equations'] for k in e['terms']}
    for d in review['duplicates']:
        if d.get('location') in allfacts:used.add(d['location'])
    for k in sorted(used):
        if k in box:continue
        if k in extra:box[k]=extra[k]
        elif k in allfacts:
            v,h=allfacts[k]; box[k]=(v-h,v+h)
        else:raise ValueError(f'{packet["id"]}: unknown constraint variable {k}')
    # A table operand and that same source cell are one fact, including percent
    # scaling. Do not infer identity from equal values in different locations.
    for variable,source in audit['input_provenance'].items():
        loc=source['location']
        if loc in used and loc in box:
            if loc not in allfacts:
                raise ValueError(f'{packet["id"]}: source identity needs explicit parsed units for {loc}')
            v,h=allfacts[loc]; scale=F(source['half'])/h
            assert scale*v==F(source['value'])
            relation={variable:F(1),loc:-scale};eq.append(relation)
            inventory.append({'type':'source_identity','terms':{k:str(v) for k,v in relation.items()},'reason':loc})
    for d in review['duplicates']:
        loc=d.get('location')
        if loc in used and loc in box:
            scale=F(d['scale'])
            relation={d['variable']:F(1),loc:-scale};eq.append(relation)
            inventory.append({'type':'duplicate_identity','terms':{k:str(v) for k,v in relation.items()},'reason':d['reason']})
    for e in review['equations']:
        terms={k:F(v) for k,v in e['terms'].items() if F(v)}
        assert terms and all(k in box for k in terms)
        eq.append(terms);inventory.append({'type':'reviewed_sum',**e})
    return box,eq,inventory

def solve_stage(packet,review,stage):
    bounds,equations,inventory=build_model(packet,review,stage)
    if any(lo>hi for lo,hi in bounds.values()):
        return {'status':'inconsistent_disclosures','inventory':inventory,'bounds':{k:list(map(str,v)) for k,v in bounds.items()},'equations':[]}
    result=solve_range(bounds,equations,packet['audit']['steps'],acceptance(packet['audit']))
    assert verify_result(bounds,equations,packet['audit']['steps'],acceptance(packet['audit']),result)
    result['verification_passed']=True
    result['bounds']={k:list(map(str,v)) for k,v in bounds.items()}
    result['equations']=[{k:str(v) for k,v in e.items()} for e in equations]
    result['inventory']=inventory
    envelope=result['enclosure']; band=acceptance(packet['audit'])
    result['gold_excluded']=bool(envelope and (F(envelope['hi'])<band[0] or F(envelope['lo'])>band[1]))
    return result

def inside_witness(stage,steps,band):
    """A second, feasible accepted assignment prevents gold-incompatible
    documents being counted as rounding ambiguity. Exact bisection is a
    witness search only; failure does not certify absence."""
    box={k:tuple(map(F,v)) for k,v in stage['bounds'].items()}
    equations=[{k:F(v) for k,v in e.items()} for e in stage['equations']]
    def feasible(p):
        return (all(lo==hi or lo<p[k]<hi for k,(lo,hi) in box.items()) and
                all(sum((coef*p[k] for k,coef in e.items()),F(0))==0 for e in equations))
    candidates=[]
    for field in ('feasible_point','strict_interior_point','witness'):
        if stage.get(field):candidates.append({k:F(v) for k,v in stage[field].items()})
    candidates += [{k:F(v) for k,v in t['point'].items()} for t in stage.get('extrema',{}).values()]
    candidates.append({k:(lo+hi)/2 for k,(lo,hi) in box.items()})
    interior=stage.get('strict_interior_point')
    if interior:
        interior={k:F(v) for k,v in interior.items()}
        candidates += [{k:(F(999999)*p[k]+interior[k])/1000000 for k in p} for p in candidates[:]]
    below=[];above=[]
    for p in candidates:
        if not feasible(p):continue
        try:value=eval_scalar(steps,p)
        except (ValueError,ZeroDivisionError):continue
        if band[0]<=value<=band[1]:return {'point':{k:str(v) for k,v in p.items()},'value':str(value)}
        (below if value<band[0] else above).append(p)
    if below and above:
        left,right=below[0],above[0]
        for _ in range(100):
            middle={k:(left[k]+right[k])/2 for k in left}
            try:value=eval_scalar(steps,middle)
            except (ValueError,ZeroDivisionError):break
            if band[0]<=value<=band[1] and feasible(middle):return {'point':{k:str(v) for k,v in middle.items()},'value':str(value)}
            if value<band[0]:left=middle
            else:right=middle
    return None

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--partial',action='store_true');args=parser.parse_args()
    packets,reviews=load_inputs(args.partial);out=HERE/'results';out.mkdir(exist_ok=True)
    rows=[]
    for i,packet in enumerate(packets):
        review=reviews.get(packet['id'])
        if not review or review['verdict'] not in ('valid','invalid','uncertain'):continue
        audit=packet['audit']; band=acceptance(audit)
        # Freshly re-evaluate every original witness before any new model.
        w={k:F(v['exact']) for k,v in audit['relative_1pct']['witness'].items()}
        assert all(lo<w[k]<hi for k,(lo,hi) in native_box(audit).items())
        value=eval_scalar(audit['steps'],w)
        assert not band[0]<=value<=band[1]
        row={'id':packet['id'],'category':audit['category'],'question':audit['question'],
             'program':audit['program'],'steps':audit['steps'],'acceptance':list(map(str,band)),
             'sample40':packet['sample40'],'review_verdict':review['verdict'],'review_reason':review['reason'],
             'original_witness_reverified':True,'stages':{}}
        for stage,name in enumerate(('original','duplicates','sums')):
            row['stages'][name]=solve_stage(packet,review,stage)
        final=row['stages']['sums']
        row['inside_witness']=inside_witness(final,audit['steps'],band) if final['status'] not in ('infeasible','inconsistent_disclosures') else None
        row['additional_output_disclosures']=review.get('direct_output_bounds',[])
        if review['verdict']=='invalid':row['final']='semantic_invalid'
        elif review['verdict']=='uncertain':row['final']='semantic_uncertain'
        elif final.get('gold_excluded'):row['final']='reference_incompatible'
        elif row['additional_output_disclosures']:row['final']='unresolved_additional_output_constraint'
        elif final['status']=='witnessed_outside':row['final']='retained' if row['inside_witness'] else 'unresolved_no_accepted_witness'
        elif final['status']=='certified_inside':
            row['final']='determined_by_duplicates' if row['stages']['duplicates']['status']=='certified_inside' else 'determined_by_sums'
        else:row['final']=final['status']
        if review.get('optional_sensitivity_equations'):
            stronger=copy.deepcopy(review)
            stronger['equations']+=stronger['optional_sensitivity_equations']
            row['optional_sensitivity']={
                'extra_assumptions':review['optional_sensitivity_equations'],
                'result':solve_stage(packet,stronger,2),
                'used_in_primary_count':False}
        rows.append(row)
        if (i+1)%20==0:print(f'{i+1}/{len(packets)} processed',flush=True)
    summary={'n_cohort':len(packets),'n_reviewed_processed':len(rows),'n_test':1147,
             'stage_status':{name:dict(Counter(r['stages'][name]['status'] for r in rows)) for name in ('original','duplicates','sums')},
             'stage_gold_excluded':{name:sum(r['stages'][name].get('gold_excluded',False) for r in rows) for name in ('original','duplicates','sums')},
             'final':dict(Counter(r['final'] for r in rows)),
             'sample40':dict(Counter(r['review_verdict'] for r in rows if r['sample40'])),
             'method_final':dict(Counter(r['stages']['sums'].get('method','unavailable') for r in rows)),
             'exact_final_ranges':sum(r['stages']['sums'].get('range_exact',False) for r in rows),
             'by_category':{c:dict(Counter(r['final'] for r in rows if r['category']==c)) for c in sorted({r['category'] for r in rows})},
             'review_sha256':{part:hashlib.sha256((HERE/f'review_{part}.json').read_bytes()).hexdigest() for part in ('a','b') if (HERE/f'review_{part}.json').exists()}}
    retained=summary['final'].get('retained',0)
    summary['retained_percent_test']=100*retained/1147
    summary['gate']='retain' if len(rows)==196 and retained>=58 else ('downgrade' if len(rows)==196 else 'incomplete')
    suffix='_partial' if args.partial else ''
    (out/f'per_question{suffix}.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf8')
    (out/f'summary{suffix}.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
