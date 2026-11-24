"""Freeze the matched FinQA sample and gold-free single-question prompts."""
from pathlib import Path
import argparse
import collections
import json
import random
import shutil

ROOT = Path(__file__).resolve().parent
PROMPT = '''Solve the financial question using only the document below. Give a final numerical answer, its unit, and a brief arithmetic expression showing your calculation. Do not use external sources or tools. Your expression must use numbers and arithmetic operators (+, -, *, /, parentheses) and evaluate to your answer in the stated unit. Do not include explanatory prose outside the JSON.
Return JSON with exactly these fields:
{"answer": "numerical value as a string", "unit": "unit, or percent, ratio, times, years, etc.", "expression": "arithmetic expression", "explanation": "one brief sentence"}

DOCUMENT
{document}

QUESTION
{question}
'''

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--t1-dir', type=Path, default=ROOT.parents[2] / 'proxy-tail/research/t1_rounding')
    a = p.parse_args()
    t1 = [json.loads(s) for s in (a.t1_dir/'results/per_question.jsonl').read_text(encoding='utf8').splitlines()]
    docs = {r['id']: r for r in json.loads((a.t1_dir/'data/finqa/test.json').read_text(encoding='utf8'))}
    tests = [r for r in t1 if r['split']=='test' and r['status']=='analyzed']
    witnessed = sorted([r for r in tests if r['relative_1pct']['status']=='witnessed_outside'], key=lambda r:r['id'])
    stable = collections.defaultdict(list)
    for r in sorted(tests, key=lambda r:r['id']):
        if r['relative_1pct']['status']=='certified_inside':
            stable[r['category']].append(r)
    rng = random.Random(20261116)
    for category in sorted(stable):
        rng.shuffle(stable[category])
    paired = []
    for i, r in enumerate(witnessed,1):
        control = stable[r['category']].pop()
        paired.extend([dict(pair_id=f'P{i:03}',group='witness',**r),dict(pair_id=f'P{i:03}',group='control',**control)])
    assert len(witnessed)==196 and len({r['id'] for r in paired})==392
    rng.shuffle(paired)
    (ROOT/'inputs').mkdir(exist_ok=True)
    (ROOT/'raw').mkdir(exist_ok=True)
    (ROOT/'private').mkdir(exist_ok=True)
    for i,r in enumerate(paired,1):
        r['call_id']=f'Q{i:03}'
        d=docs[r['id']]
        table=d.get('table_ori',d['table'])
        document='\n'.join(d['pre_text'])+'\n\nTABLE\n'+'\n'.join(' | '.join(row) for row in table)+'\n\n'+'\n'.join(d['post_text'])
        (ROOT/'inputs'/f'{r["call_id"]}.txt').write_text(PROMPT.replace('{document}',document).replace('{question}',d['qa']['question']),encoding='utf8',newline='\n')
    (ROOT/'private/sample.json').write_text(json.dumps(paired,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    (ROOT/'private/documents.json').write_text(json.dumps([docs[r['id']] for r in paired],ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
    (ROOT/'prompt.txt').write_text(PROMPT,encoding='utf8',newline='\n')
    shutil.copyfile(a.t1_dir/'data/finqa/LICENSE',ROOT/'inputs/LICENSE')
    print(json.dumps({'n':len(paired),'group_category':dict(collections.Counter(r['group']+'/'+r['category'] for r in paired))},indent=2))

if __name__=='__main__':main()
