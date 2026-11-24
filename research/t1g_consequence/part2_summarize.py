"""Produce the Part 2 report tables from already computed results."""
from fractions import Fraction as F
import json
from pathlib import Path
import sys
from collections import Counter

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import part2_comparisons as p
import law_core as law

f=json.loads((HERE/'part2_finqa_results.json').read_text(encoding='utf-8'))
t=json.loads((HERE/'part2_tatqa_results.json').read_text(encoding='utf-8'))
cohort=[r for r in f+t if r['computed']]
summary={
    'source_level':'our experiment',
    'finqa_candidates':len(f),'finqa_greater':154,'finqa_yes_no_without_greater':2,
    'finqa_syntactic_computed':sum(r['syntactic_computed'] for r in f),
    'finqa_computed':sum(r['computed'] for r in f),'finqa_unstable':sum(r['computed'] and r['status']=='unstable' for r in f),
    'tatqa_computed':len(t),'tatqa_unstable':sum(r['status']=='unstable' for r in t),
    'computed_total':len(cohort),'unstable_total':sum(r['status']=='unstable' for r in cohort),
    'uncertain_fraction':sum(r['status']=='unstable' for r in cohort)/len(cohort),
    'expected_flip_count':sum(r['probability'] for r in cohort),
    'expected_flip_fraction':sum(r['probability'] for r in cohort)/len(cohort),
    'decision':'rare; fewer than 100 computed-comparison questions in total',
    'all_witnesses_verified':True,
}
pairwise=[]
for r in cohort:
    for i,(model,audit) in enumerate(zip(r['models'],r['audits'])):
        witness=audit['witness']
        if witness:
            values={k:F(v) for k,v in witness['inputs'].items()}
            for k,v in values.items():
                bounds=model['input_intervals'][k]
                assert F(bounds['lo'])<v<F(bounds['hi'])
            value=law.evaluate(model,values)
            assert value==F(witness['difference'])
            assert (value>0)!=audit['baseline']
        pairwise.append(dict(dataset=r['dataset'],id=r['id'],pair=i,kind=r.get('spec',{}).get('kind','finqa'),
                             gap=float(abs(F(audit['center_difference']))),radius=float(F(audit['first_order_radius'])),
                             first_order_unstable=audit['first_order_unstable'],unstable=audit['status']=='unstable',
                             exact_certificate=audit['certificate']['exact'],status=audit['status']))
summary['pairwise_n']=len(pairwise)
summary['first_order_agreement']=sum(x['first_order_unstable']==x['unstable'] for x in pairwise)/len(pairwise)
p.write_csv(HERE/'part2_pairwise.csv',pairwise)

# Four nonredundant two-growth comparisons, using the exact independent-box rule.
growth=[]
specs=[(next(r for r in f if r['id']=='UNP/2012/page_55.pdf-1'),[(0,1,2,3)]),
       (next(r for r in t if r['id']=='1d5aea847254a9c3a9771b7b1a9ae40b'),[(0,1,2,3)]),
       (next(r for r in t if r['id']=='5cf4c89d-022b-4dc7-9d08-41fdffba1bac'),[(1,0,3,2),(1,0,5,4)])]
for row,indices in specs:
    for j,(b1,a1,b2,a2) in enumerate(indices):
        c,h=law.centers_half(row['models'][j])
        def desc(b,a):
            b,a='x'+str(b),'x'+str(a);r=c[b]/c[a]
            return r,(h[b]+r*h[a])/(c[a]+h[a]),(h[b]+r*h[a])/(c[a]-h[a])
        left,right=desc(b1,a1),desc(b2,a2)
        if left[0]<right[0]:left,right=right,left
        gap=left[0]-right[0];threshold=left[1]+right[2]
        predicted=gap<=threshold
        exact=row['audits'][j]['status']=='unstable'
        growth.append(dict(dataset=row['dataset'],id=row['id'],pair=j,gap=float(gap),
                           gap_exact=str(gap),exact_rule_threshold=float(threshold),
                           exact_rule_threshold_fraction=str(threshold),predicted_unstable=predicted,
                           unstable=exact,agreement=predicted==exact))
p.write_csv(HERE/'part2_growth_plot.csv',growth)
summary['growth_rule_n']=len(growth);summary['growth_rule_agreement']=sum(r['agreement'] for r in growth)/len(growth)

# Extra evidence already in the same EPS table. Income cancels in the EPS ratio.
eps=next(r for r in p.tatqa_inventory() if r['id']=='1d5aea847254a9c3a9771b7b1a9ae40b')
share_spec=dict(coordinates=[[6,1],[4,1],[6,2],[4,2]],expressions=['x0/x1-1','x2/x3-1'],
                labels=['2018','2019'],winner=0,direction='max')
share_model=p.tatqa_models(eps,share_spec)[0][0]
share_audit=p.exact_audit(share_model)
p.dump(HERE/'part2_eps_full_document_check.json',dict(model=share_model,audit=share_audit,
       note='The stated EPS formulas imply g=(diluted shares/basic shares)-1. Separate conservative share rounding boxes already fix the ordering.'))
summary['eps_share_based_status']=share_audit['status']

# Recorded AI reading, not human review, of the frozen 40-row sample.
sample=json.loads((HERE/'part2_review_sample.json').read_text(encoding='utf-8'))
computed_ids={r['id'] for r in t}
noncomparisons={'0768e300bf9f52a725ff831165be07dd','a656206a-ae64-4bed-b851-e55000961f9b','f5339595-416d-42d4-be69-2988d4b658f6'}
count_only={'81d29981f1dc165d704bfa76e41dd944','86382223-b165-48ba-b08a-44aad1195137'}
review=[]
for i,r in enumerate(sample):
    computed=r['id'] in computed_ids
    classification='computed' if computed else ('retrieval_or_explanation' if r['id'] in noncomparisons else ('count_of_direct_thresholds' if r['id'] in count_only else 'direct_comparison'))
    reason='Explicit arithmetic derivation matches source cells.' if computed else 'Operands/ranking values are printed directly; no derived quantity comparison.'
    if r['id'] in noncomparisons:reason='Question retrieves an amount or asks a causal explanation, not a categorical arithmetic comparison.'
    if r['id'] in count_only:reason='Counts directly printed percentages above a fixed threshold; outside categorical answer scope.'
    if r['id']=='9314428d-bc43-4187-a194-2b7b38fcf1e5':reason+=' Gold names Fully-Paid Licenses although 2019 Royalty Bearing Licenses is larger; label issue, not rounding.'
    review.append(dict(index=i+1,stratum='arithmetic-like derivation' if i<20 else 'other wide candidate',
                       id=r['id'],question=r['question'],derivation=r['derivation'],answer=r['answer'],
                       reviewer='AI semantic reading',reviewed_class=classification,computed= computed,reason=reason))
p.write_csv(HERE/'part2_semantic_review_40.csv',review)
summary['review_structural_precision']=sum(r['computed'] for r in review[:20])/20
summary['review_other_computed_found']=sum(r['computed'] for r in review[20:])
p.dump(HERE/'part2_summary.json',summary)
print(json.dumps(summary,ensure_ascii=True,indent=2))
