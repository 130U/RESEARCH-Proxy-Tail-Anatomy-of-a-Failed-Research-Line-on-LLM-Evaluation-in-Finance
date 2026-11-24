import csv, json, sys, shutil
from datetime import datetime, timezone
from pathlib import Path
PRIVATE = Path(__file__).resolve().parent
OUT = PRIVATE.parent / 'proxy-tail/research/absolute_scoring'
SCHEDULE = {r['call_id']:r for r in csv.DictReader((OUT/'schedule.csv').open(encoding='utf-8'))}
BATCHES = {}
for row in csv.DictReader((OUT/'batches.csv').open(encoding='utf-8')):
    BATCHES.setdefault(row['input_key'], set()).add(row['id'])
def now(): return datetime.now(timezone.utc).isoformat()
def unique_object(pairs):
    result={}
    for key,value in pairs:
        if key in result: raise ValueError('Duplicate JSON key: '+key)
        result[key]=value
    return result
def update_progress():
    completed = {p.stem for p in (OUT/'raw_scores').glob('*.json')}
    main=sum(SCHEDULE[c]['kind']=='main' for c in completed)
    control=len(completed)-main
    remaining=[c for c in SCHEDULE if c not in completed]
    (OUT/'progress.md').write_text(f'# Absolute-scoring run progress\n\nUpdated (UTC): {now()}\n\nSaved and validated {len(completed)}/250 calls; main experiment {main}/200, controls {control}/50.\nSaved {40*len(completed)} ID scores (repeats are not new independent headlines).\nNext call to run: {remaining[0] if remaining else "none, scoring complete"}.\n\nThis page reports only execution progress and does not judge the research conclusion in advance.\n',encoding='utf-8')
    return {'completed':len(completed),'main':main,'control':control,'next':remaining[:3]}
action=sys.argv[1]
if action=='start':
    cid, task = sys.argv[2:4]
    row=SCHEDULE[cid]
    dest=OUT/'raw_scores'/f'{cid}.json'
    if dest.exists(): raise RuntimeError('Completed output exists')
    response=PRIVATE/row['input_key']/'response.json'
    attempt=1
    log=OUT/'calls.jsonl'
    if log.exists():
        attempt+=sum(json.loads(l)['call_id']==cid for l in log.read_text(encoding='utf-8').splitlines())
    if response.exists():
        archive=response.with_name(f'previous_before_{cid}_attempt{attempt}.json')
        if archive.exists(): raise RuntimeError('Archive exists')
        response.rename(archive)
    record={'call_id':cid,'input_key':row['input_key'],'agent_task':task,'model':'gpt-6-sol','reasoning_effort':'low','started_utc':now(),'attempt':attempt}
    (PRIVATE/f'pending_{cid}.json').write_text(json.dumps(record,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(record,ensure_ascii=False))
elif action=='finish':
    for cid in sys.argv[2:]:
        pending=PRIVATE/f'pending_{cid}.json'
        record=json.loads(pending.read_text(encoding='utf-8'))
        source=PRIVATE/record['input_key']/'response.json'
        dest=OUT/'raw_scores'/f'{cid}.json'
        record['completed_utc']=now()
        try:
            raw=source.read_bytes()
            scores=json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique_object)
            assert type(scores) is dict and set(scores)==BATCHES[record['input_key']]
            assert len(scores)==40 and all(type(v) is int and 0<=v<=100 for v in scores.values())
            if dest.exists(): raise RuntimeError('Refuse to overwrite completed score')
            dest.write_bytes(raw)
            record.update(status='valid',output=f'raw_scores/{cid}.json',score_count=40)
        except Exception as e:
            record.update(status='invalid_or_missing',error=f'{type(e).__name__}: {e}')
        with (OUT/'calls.jsonl').open('a',encoding='utf-8',newline='\n') as f:
            f.write(json.dumps(record,ensure_ascii=False)+'\n')
        pending.unlink()
        print(json.dumps(record,ensure_ascii=False))
    print(json.dumps(update_progress()))
elif action=='progress': print(json.dumps(update_progress()))
