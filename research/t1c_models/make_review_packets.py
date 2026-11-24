"""Create group-blind source/meaning review packets; never alters raw answers."""
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser();p.add_argument('--parts',type=int,default=3)
    p.add_argument('--exclude-reviewed',action='append',type=Path,default=[]);a=p.parse_args()
    excluded={r['call_id'] for path in a.exclude_reviewed for r in json.loads(path.read_text(encoding='utf8'))}
    rows=[json.loads(s) for s in (ROOT/'scores.jsonl').read_text(encoding='utf8').splitlines()]
    docs={r['id']:r for r in json.loads((ROOT/'private/documents.json').read_text(encoding='utf8'))}
    packets=[]
    for r in rows:
        if r.get('expression_scores',{}).get('official') is True:continue
        if r['call_id'] in excluded:continue
        doc=docs[r['id']]
        packets.append({'call_id':r['call_id'],'question':r['question'],
            'pre_text':doc['pre_text'],'table':doc.get('table_ori',doc['table']),'post_text':doc['post_text'],
            'human_answer':r['answer'],'reference_program':r['program'],'reference_execution_value':r['exe_ans'],
            'model_response':r.get('response'),'model_normalization':r.get('normalization'),
            'model_expression_value':r.get('expression_value'),'parse_error':r.get('parse_error'),
            'instructions':'Judge the model formula against the source and question. Do not assume the reference is correct. Group and interval flags are deliberately withheld.'})
    (ROOT/'private/review_packets').mkdir(exist_ok=True)
    for i in range(a.parts):
        out=packets[i::a.parts]
        (ROOT/'private/review_packets'/f'part_{i+1}.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    print({'review_total':len(packets),'parts':[len(packets[i::a.parts]) for i in range(a.parts)]})

if __name__=='__main__':main()
