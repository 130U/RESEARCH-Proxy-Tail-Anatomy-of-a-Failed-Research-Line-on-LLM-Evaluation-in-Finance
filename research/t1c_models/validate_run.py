"""Audit the complete frozen experiment and write a SHA-256 evidence manifest."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
import numpy
import sympy
import prepare
import score

ROOT = Path(__file__).resolve().parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--t1-dir', type=Path, default=ROOT.parents[2]/'proxy-tail/research/t1_rounding')
    args = ap.parse_args()
    sample = json.loads((ROOT/'private/sample.json').read_text(encoding='utf8'))
    calls = [json.loads(x) for x in (ROOT/'calls.jsonl').read_text(encoding='utf8').splitlines()]
    scored = [json.loads(x) for x in (ROOT/'scores.jsonl').read_text(encoding='utf8').splitlines()]
    expected = {f'Q{i:03}' for i in range(1,393)}
    assert len(sample) == len(calls) == len(scored) == 392
    for records in (sample, calls, scored):
        assert {r['call_id'] for r in records} == expected
    assert len({r['id'] for r in sample}) == 392
    assert {p.stem for p in (ROOT/'raw').glob('Q*.txt')} == expected
    assert Counter(r['group'] for r in sample) == {'witness':196, 'control':196}
    pairs = defaultdict(list)
    for r in sample: pairs[r['pair_id']].append(r)
    assert len(pairs) == 196
    for pair in pairs.values():
        assert len(pair)==2 and {r['group'] for r in pair}=={'witness','control'}
        assert pair[0]['category']==pair[1]['category']
    t1 = [json.loads(x) for x in (args.t1_dir/'results/per_question.jsonl').read_text(encoding='utf8').splitlines()]
    witnesses = {r['id'] for r in t1 if r['split']=='test' and r.get('relative_1pct',{}).get('status')=='witnessed_outside'}
    assert witnesses == {r['id'] for r in sample if r['group']=='witness'}
    assert all(r['relative_1pct']['status']=='certified_inside' for r in sample if r['group']=='control')
    docs = {r['id']:r for r in json.loads((args.t1_dir/'data/finqa/test.json').read_text(encoding='utf8'))}
    official = score.load_module('audit_finqa_official',args.t1_dir/'data/finqa/evaluate.py')
    scores = {r['call_id']:r for r in scored}
    for r in sample:
        d=docs[r['id']]
        table=d.get('table_ori',d['table'])
        document='\n'.join(d['pre_text'])+'\n\nTABLE\n'+'\n'.join(' | '.join(row) for row in table)+'\n\n'+'\n'.join(d['post_text'])
        prompt=prepare.PROMPT.replace('{document}',document).replace('{question}',d['qa']['question'])
        assert (ROOT/'inputs'/f'{r["call_id"]}.txt').read_text(encoding='utf8')==prompt
        invalid,value=official.eval_program(official.program_tokenization(r['program']),d['table'])
        assert not invalid and value==r['exe_ans'], r['call_id']
        out=scores[r['call_id']]
        assert (out['id'],out['group'],out['pair_id'])==(r['id'],r['group'],r['pair_id'])
        assert out.get('response')==score.read_response(ROOT/'raw'/f'{r["call_id"]}.txt')
        assert (out['expression_scores']['display'] is None)==(score.display_target(r) is None)
    for c in calls:
        assert c['fork_turns']=='none' and c['status']=='completed'
        assert c['agent_path'].endswith('/solve_'+c['call_id'].lower())
        fmt='%Y-%m-%d %H:%M:%S UTC'
        assert datetime.strptime(c['completed_utc'],fmt)>=datetime.strptime(c['started_utc'],fmt)
    assert len({c['model'] for c in calls})==1
    results=json.loads((ROOT/'results.json').read_text(encoding='utf8'))
    assert results['complete'] and results['n']==392 and not results['unreviewed_expression_errors']
    assert not results['missing_second_source_review'] and not results['unadjudicated_disagreements']
    source_paths=['interval_core.py','results/per_question.jsonl','data/finqa/test.json','data/finqa/evaluate.py','data/finqa/LICENSE']
    files={}
    for p in sorted(ROOT.rglob('*')):
        rel=p.relative_to(ROOT).as_posix()
        if not p.is_file() or '__pycache__' in p.parts or p.suffix=='.tmp' or rel=='integrity.json' or rel.startswith('private/') and rel!='private/sample.json':continue
        files[rel]=digest(p)
    manifest={'complete':True,'questions':392,'matched_pairs':196,'fresh_sessions':392,
              'prompt_reconstruction_matches':392,'official_gold_execution_matches':392,
              'analysis_runtime':{'python':sys.version,'numpy':numpy.__version__,'sympy':sympy.__version__},
              'model_conditions':sorted({c['model'] for c in calls}),
              'source_sha256':{name:digest(args.t1_dir/name) for name in source_paths},'artifact_sha256':files}
    (ROOT/'integrity.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps({k:v for k,v in manifest.items() if not k.endswith('sha256')},indent=2))

if __name__=='__main__':main()
