"""Document-cluster bootstrap and rule-specific, traceable error attribution."""
import argparse
import csv
from collections import Counter
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
RULES=('official','relative_1pct','display')
GROUPS=('witness','control')

def load_reviews(adjudicate=True):
    result={}
    for p in sorted(ROOT.glob('review_*.json')):
        content=json.loads(p.read_text(encoding='utf8'))
        for r in content:
            key=r['call_id']
            if key in result:raise ValueError('duplicate independent review '+key)
            result[key]=r
    p=ROOT/'adjudication.json'
    if p.exists() and adjudicate:
        for r in json.loads(p.read_text(encoding='utf8')):result[r['call_id']]={**result.get(r['call_id'],{}),**r}
    return result

def accepted(row,track,rule):
    return row[track+'_scores'][rule]

def cause(row,track,rule,reviews):
    if accepted(row,track,rule) is not False:return None
    if row['parse_status']!='ok':return reviews.get(row['call_id'],{}).get('primary_cause','invalid_format')
    if track=='printed' and row.get('printed_arithmetic_discrepancy'):return 'printed_arithmetic_error'
    if track=='printed' and accepted(row,'expression',rule):
        return 'output_precision' if row.get('printed_matches_expression_rounding') else 'printed_arithmetic_error'
    if rule=='display' and accepted(row,'expression','official'):return 'human_label_disagreement'
    return reviews.get(row['call_id'],{}).get('primary_cause','unreviewed')

def cluster_bootstrap(rows,track,rule,draws=10000,seed=20261116):
    pages=sorted({r['page_id'] for r in rows});idx={p:i for i,p in enumerate(pages)}
    denominators=np.zeros((len(pages),2));errors=denominators.copy()
    for r in rows:
        result=accepted(r,track,rule)
        if result is None:continue
        i,j=idx[r['page_id']],GROUPS.index(r['group'])
        denominators[i,j]+=1;errors[i,j]+=not result
    if np.any(denominators.sum(0)==0):return None
    rng=np.random.default_rng(seed)
    counts=rng.multinomial(len(pages),np.full(len(pages),1/len(pages)),size=draws)
    den=counts@denominators;num=counts@errors
    rates=num/den;diff=rates[:,0]-rates[:,1]
    ci=np.quantile(diff,[.025,.975]).tolist()
    observed=errors.sum(0)/denominators.sum(0)
    return {'pages':len(pages),'draws':draws,'seed':seed,'error_difference':float(observed[0]-observed[1]),
            'ci95':ci,'difference_threshold_met':bool(observed[0]-observed[1]>.05 and (ci[0]>0 or ci[1]<0))}

def main():
    p=argparse.ArgumentParser();p.add_argument('--allow-incomplete',action='store_true');a=p.parse_args()
    rows=[json.loads(s) for s in (ROOT/'scores.jsonl').read_text(encoding='utf8').splitlines()]
    if len(rows)!=392 and not a.allow_incomplete:raise SystemExit('Expected all 392 responses; use --allow-incomplete for development only')
    reviews=load_reviews()
    original_reviews=load_reviews(adjudicate=False)
    second_reviews={}
    for path in sorted((ROOT/'independent').glob('source_*.json')):
        for item in json.loads(path.read_text(encoding='utf8')):
            if item['call_id'] in second_reviews:raise ValueError('duplicate second review '+item['call_id'])
            second_reviews[item['call_id']]=item
    adjudication_path=ROOT/'adjudication.json'
    adjudicated={r['call_id'] for r in json.loads(adjudication_path.read_text(encoding='utf8'))} if adjudication_path.exists() else set()
    disagreements=[]
    for key,second in second_reviews.items():
        original=original_reviews[key]
        changed=[k for k in ('primary_cause','formula_valid','alternative_precision_used') if original.get(k)!=second.get(k)]
        if changed:disagreements.append({'call_id':key,'fields':changed,'root':original,'independent':second,'final':reviews[key],'adjudicated':key in adjudicated})
    (ROOT/'independent/disagreements.json').write_text(json.dumps(disagreements,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    report={'n':len(rows),'complete':len(rows)==392,'independent_review_n':len(reviews),'group_category':dict(Counter(r['group']+'/'+r['category'] for r in rows)),
            'pages':len({r['page_id'] for r in rows}),'tracks':{},'precision':{}}
    page_sets={g:{r['page_id'] for r in rows if r['group']==g} for g in GROUPS}
    report['page_counts']={g:len(page_sets[g]) for g in GROUPS}
    report['page_counts']['shared']=len(page_sets['witness']&page_sets['control'])
    report['second_source_review_n']=len(second_reviews)
    report['source_review_disagreement_n']=len(disagreements)
    report['unadjudicated_disagreements']=[r['call_id'] for r in disagreements if not r['adjudicated']]
    report['missing_second_source_review']=[r['call_id'] for r in rows if accepted(r,'expression','official') is False and r['call_id'] not in second_reviews]
    for track in ('expression','printed'):
        result={}
        for rule in RULES:
            groups={}
            all_errors=[]
            for group in GROUPS:
                sample=[r for r in rows if r['group']==group and accepted(r,track,rule) is not None]
                rejected=[r for r in sample if not accepted(r,track,rule)]
                all_errors.extend(rejected)
                box=[r for r in rejected if r.get(track+'_compatibility',{}).get('certified')]
                supported=[r for r in rejected if cause(r,track,rule,reviews)=='alternative_source_precision'
                           and reviews.get(r['call_id'],{}).get('formula_valid') is True]
                groups[group]={'n':len(sample),'correct':len(sample)-len(rejected),'errors':len(rejected),
                  'accuracy':(len(sample)-len(rejected))/len(sample) if sample else None,
                  'box_compatible_errors':len(box),'box_compatible_fraction_of_errors':len(box)/len(rejected) if rejected else None,
                  'outer_interval_hit_errors':sum(bool(r.get(track+'_compatibility',{}).get('outer_hit')) for r in rejected),
                  'source_supported_rounding_errors':len(supported),'causes':dict(Counter(cause(r,track,rule,reviews) for r in rejected))}
                groups[group]['alternative_precision_used_in_rejections']=sum(reviews.get(r['call_id'],{}).get('alternative_precision_used') is True for r in rejected)
            broad=sum(bool(r.get(track+'_compatibility',{}).get('certified')) or cause(r,track,rule,reviews)=='alternative_source_precision' for r in all_errors)
            strict=sum(cause(r,track,rule,reviews)=='alternative_source_precision' and reviews.get(r['call_id'],{}).get('formula_valid') is True for r in all_errors)
            bootstrap=cluster_bootstrap(rows,track,rule)
            result[rule]={'groups':groups,'bootstrap':bootstrap,'all_errors':len(all_errors),
                'outer_interval_hit_n':sum(bool(r.get(track+'_compatibility',{}).get('outer_hit')) for r in all_errors),
                'box_or_alternative_n':broad,'box_or_alternative_fraction':broad/len(all_errors) if all_errors else None,
                'source_supported_rounding_n':strict,'source_supported_rounding_fraction':strict/len(all_errors) if all_errors else None,
                'literal_threshold_met':bool(bootstrap and bootstrap['difference_threshold_met'] or all_errors and broad/len(all_errors)>.1),
                'strict_error_attribution_threshold_met':bool(all_errors and strict/len(all_errors)>.1)}
        report['tracks'][track]=result
    for group in GROUPS:
        rs=[r for r in rows if r['group']==group]
        vals={key:[r.get('precision',{}).get(key) for r in rs] for key in ('reported_significant_digits','error_order_digits','excess_digits','t1a_precision_budget','excess_over_t1a_budget','t1a_first_order_budget','excess_over_t1a_first_order_budget')}
        report['precision'][group]={}
        for key,v in vals.items():
            v=[x for x in v if x is not None]
            report['precision'][group][key]={'n':len(v),'median':float(np.median(v)) if v else None,
               'q25':float(np.quantile(v,.25)) if v else None,'q75':float(np.quantile(v,.75)) if v else None}
    report['parse_errors']=[r['call_id'] for r in rows if r['parse_status']!='ok']
    report['reference_display_disagreements']=[r['call_id'] for r in rows if r.get('reference_display') and not r['reference_display']['gold_center_rounds_to_human_answer']]
    report['unreviewed_expression_errors']=[r['call_id'] for r in rows if accepted(r,'expression','official') is False and r['call_id'] not in reviews]
    report['rejected_expression_review']={g:{'group_n':sum(r['group']==g for r in rows),
        'scope':'Only officially rejected expressions are source-reviewed; accepted expressions are not a semantic census.',
        'reviewed_invalid_formulas':sum(r['group']==g and reviews.get(r['call_id'],{}).get('formula_valid') is False for r in rows),
        'unresolved':sum(r['group']==g and reviews.get(r['call_id'],{}).get('primary_cause')=='unresolved' for r in rows),
        'reviewed_true_errors':sum(r['group']==g and reviews.get(r['call_id'],{}).get('primary_cause')=='true_error' for r in rows),
        'valid_formula_rejections':sum(r['group']==g and accepted(r,'expression','official') is False and reviews.get(r['call_id'],{}).get('formula_valid') is True for r in rows)} for g in GROUPS}
    report['precision_same_formula_growth']={}
    for group in GROUPS:
        eligible=[r for r in rows if r['group']==group and r.get('same_source_symbolic_formula') is True
                  and r.get('precision',{}).get('t1a_precision_budget') is not None]
        report['precision_same_formula_growth'][group]={'n':len(eligible),
            'median_reported_digits':float(np.median([r['precision']['reported_significant_digits'] for r in eligible])) if eligible else None,
            'median_t1a_budget':float(np.median([r['precision']['t1a_precision_budget'] for r in eligible])) if eligible else None,
            'median_t1a_first_order_budget':float(np.median([r['precision']['t1a_first_order_budget'] for r in eligible])) if eligible else None,
            'median_excess_first_order':float(np.median([r['precision']['excess_over_t1a_first_order_budget'] for r in eligible])) if eligible else None,
            'median_excess':float(np.median([r['precision']['excess_over_t1a_budget'] for r in eligible])) if eligible else None}
    if report['unreviewed_expression_errors'] and not a.allow_incomplete:
        raise SystemExit('Review these rejected expressions first: '+', '.join(report['unreviewed_expression_errors']))
    if not a.allow_incomplete and (report['missing_second_source_review'] or report['unadjudicated_disagreements']):
        raise SystemExit('Complete independent source review and adjudication before final reporting')
    report['inference_complete']=len(rows)==392
    report['complete']=report['inference_complete'] and not (report['unreviewed_expression_errors'] or report['missing_second_source_review'] or report['unadjudicated_disagreements'])
    (ROOT/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    judgments=[]
    for r in rows:
        review=reviews.get(r['call_id'],{})
        item={k:r[k] for k in ('call_id','id','page_id','group','pair_id','category','question','answer','exe_ans','program','parse_status')}
        item.update(model_answer=r.get('response',{}).get('answer'),model_unit=r.get('response',{}).get('unit'),
          model_expression=r.get('response',{}).get('expression'),formula_valid=review.get('formula_valid'),
          primary_cause=review.get('primary_cause'),review_reason=review.get('reason'),reviewer=review.get('reviewer'),
          alternative_precision_used=review.get('alternative_precision_used'),
          normalization_factor=r.get('normalization',{}).get('factor'),normalization_reason=r.get('normalization',{}).get('reason'))
        for track in ('expression','printed'):
            item[track+'_box_certified']=r.get(track+'_compatibility',{}).get('certified')
            for rule in RULES:
                item[track+'_'+rule]=accepted(r,track,rule)
                item[track+'_'+rule+'_cause']=cause(r,track,rule,reviews)
        item.update({k:r.get('precision',{}).get(k) for k in ('reported_significant_digits','t1a_precision_budget','excess_over_t1a_budget','t1a_first_order_budget','excess_over_t1a_first_order_budget')})
        judgments.append(item)
    with (ROOT/'judgments.csv').open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(judgments[0]));w.writeheader();w.writerows(judgments)
    # Compact console output: all underlying rows and certificates stay in scores.jsonl.
    print(json.dumps({'n':len(rows),'complete':report['complete'],'unreviewed_errors':len(report['unreviewed_expression_errors']),
        'expression':{k:{g:(v['groups'][g]['correct'],v['groups'][g]['n']) for g in GROUPS} for k,v in report['tracks']['expression'].items()}},indent=2))

if __name__=='__main__':main()
