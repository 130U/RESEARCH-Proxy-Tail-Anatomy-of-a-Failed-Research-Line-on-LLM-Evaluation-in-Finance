"""Re-run immutable T1 rules, then apply explicit reviewed inclusion corrections.

This does not repair gold programs or write into research/t1_rounding.
"""
import json
from collections import Counter
from pathlib import Path
import sys
from prepare import HERE,T1
sys.path.insert(0,str(T1))
from analyze import analyze_one

def main():
    reviews={r['id']:r for part in ('a','b') for r in json.loads((HERE/f'review_{part}.json').read_text(encoding='utf8'))}
    raw=json.loads((T1/'data/finqa/test.json').read_text(encoding='utf8'))
    rows=[]
    for q in raw:
        r=analyze_one(q,'test')
        baseline=r.get('relative_1pct',{}).get('status',r['status'])
        review=reviews.get(q['id'])
        correction=None
        if review and review['verdict']!='valid':
            correction={'rule':'require_verified_source_quantity_and_program_semantics','verdict':review['verdict'],'reason':review['reason']}
        rows.append({'id':q['id'],'t1_status':baseline,'t1_reason':r.get('reason'),
                     'review_correction':correction,'eligible_for_t1b':bool(review and correction is None)})
    assert len(rows)==1147
    witnessed={r['id'] for r in rows if r['t1_status']=='witnessed_outside'}
    assert witnessed==set(reviews),'Original T1 cohort changed on fresh re-run'
    out=HERE/'results';out.mkdir(exist_ok=True)
    (out/'t1_replay.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf8')
    report={'n_all':len(rows),'baseline':dict(Counter(r['t1_status'] for r in rows)),
            'review_verdicts':dict(Counter(r['verdict'] for r in reviews.values())),
            'n_original_witnesses':len(witnessed),'n_semantically_eligible':sum(r['eligible_for_t1b'] for r in rows),
            'scope':'T1 source/parser re-run all1147; semantic corrections reviewed for196 original positives only; no extrapolation to other951.'}
    (out/'t1_replay_summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
