"""Deterministic review packets and numerical sum candidates, never semantic facts."""
import hashlib
import itertools
import json
import random
import re
import sys
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve().parent
T1 = HERE.parent / 't1_rounding'
sys.path.insert(0, str(T1))
from analyze import clean, number, tokens, source_numbers

def duplicate_candidates(packet):
    candidates=[]
    _,facts=source_numbers(packet['document'])
    for variable,iv in packet['audit']['input_intervals'].items():
        lo,hi=F(iv['lo']['exact']),F(iv['hi']['exact'])
        source=packet['audit']['input_provenance'][variable]
        for fact in facts:
            scales=list(map(F,['1','1000','1/1000','1000000','1/1000000','100','1/100']))
            for scale in scales+[-v for v in scales]:
                low,high=sorted(((fact['value']-fact['half'])*scale,(fact['value']+fact['half'])*scale))
                if max(low,lo)<min(high,hi) and (low>lo or high<hi):
                    candidates.append({'variable':variable,'source_location':source['location'],
                       'original_interval':[str(lo),str(hi)],'candidate_location':fact['loc'],
                       'raw':fact['raw'],'scale':str(scale),'interval':[str(low),str(high)],'context':fact['context']})
    return candidates

def cell_number(cell, allow_percent=False):
    s = re.sub(r'<sup>.*?</sup>', '', str(cell), flags=re.I)
    s = clean(s).strip()
    if ('%' in s and not allow_percent) or s in {'', '-', '—', '–', 'n/a', 'N/A'}:
        return None
    s = s.replace('$','').replace('%','').strip()
    s = re.sub(r'\s*(?:pts?|percentage points?)$', '', s, flags=re.I).strip()
    s = re.sub(r'\([a-zA-Z]\)|\[\d+\]', '', s).strip()
    paren = s.startswith('(') and s.endswith(')')
    s = s.strip('()').replace('$', '').strip()
    if not re.fullmatch(r'[-+]?\s*(?:\d[\d,]*(?:\.\d+)?|\.\d+)', s):
        return None
    v, h, _, _ = number(s)
    return (-abs(v) if paren else v), h

def table_facts(q, allow_percent=False):
    facts = {}
    for i,row in enumerate(q['table_ori']):
        for j,cell in enumerate(row[1:],1):
            parsed = cell_number(cell, allow_percent=allow_percent)
            if parsed is not None:
                v,h = parsed
                # Four-digit years in header cells are metadata, not financial facts.
                if i == 0 and 1900 <= v <= 2100 and h == F(1,2):
                    continue
                facts[f'table_{i}:{j}'] = (v,h)
    return facts

def sum_candidates(q):
    table=q['table_ori']; facts=table_facts(q); patterns=set()
    rows=sorted({int(k.split('_')[1].split(':')[0]) for k in facts})
    # Contiguous blocks capture long balance reconciliations and disjoint
    # subsets up to six terms capture subtotal rows amid presentation gaps.
    for target in rows:
        others=[r for r in rows if r!=target]
        sets=set()
        for start in range(len(others)):
            for end in range(start+2,len(others)+1):
                sets.add(tuple(others[start:end]))
        if len(others)<=16:
            for n in range(2,min(6,len(others))+1):
                sets.update(itertools.combinations(others,n))
        for subset in sets:
            patterns.add(tuple(sorted([(target,-1)]+[(r,1) for r in subset])))
        for left,right in itertools.combinations(others,2):
            patterns.add(tuple(sorted([(target,-1),(left,1),(right,-1)])))
            patterns.add(tuple(sorted([(target,-1),(left,-1),(right,1)])))
    result=[]; seen=set()
    for pattern in sorted(patterns):
        if pattern[0][1]<0: pattern=tuple((r,-v) for r,v in pattern)
        if pattern in seen: continue
        seen.add(pattern)
        columns=[]; residuals=[]
        for col in range(1,max(map(len,table))):
            keys=[f'table_{r}:{col}' for r,_ in pattern]
            if not all(k in facts for k in keys): continue
            vals=[facts[k] for k in keys]
            residual=sum(v*coef for (v,h),(r,coef) in zip(vals,pattern))
            width=sum(h*abs(coef) for (v,h),(r,coef) in zip(vals,pattern))
            columns.append(col); residuals.append((residual,width))
        if not columns or any(abs(r)>h for r,h in residuals):continue
        result.append({'rows':{str(r):c for r,c in pattern},'columns':columns,
                       'labels':{str(r):table[r][0] for r,c in pattern},
                       'residuals':[str(r) for r,h in residuals],
                       'allowed_rounding_halfwidths':[str(h) for r,h in residuals]})
    return result

def main():
    source=T1/'results/per_question.jsonl'; raw=T1/'data/finqa/test.json'
    audit=[json.loads(s) for s in source.read_text(encoding='utf8').splitlines()]
    cohort=sorted([q for q in audit if q['split']=='test' and q.get('relative_1pct',{}).get('status')=='witnessed_outside'],key=lambda q:q['id'])
    docs={q['id']:q for q in json.loads(raw.read_text(encoding='utf8'))}
    ids=sorted(random.Random(20261116).sample([q['id'] for q in cohort],40))
    (HERE/'sample40.json').write_text(json.dumps({'seed':20261116,'ids':ids},indent=2),encoding='utf8')
    for part,group in [('a',cohort[:98]),('b',cohort[98:])]:
        packets=[{'id':q['id'],'audit':q,'document':docs[q['id']],'sample40':q['id'] in ids} for q in group]
        (HERE/f'packets_{part}.json').write_text(json.dumps(packets,indent=2),encoding='utf8')
        candidates={q['id']:sum_candidates(docs[q['id']]) for q in group}
        (HERE/f'sum_candidates_{part}.json').write_text(json.dumps(candidates,indent=2),encoding='utf8')
        dup={q['id']:duplicate_candidates(q) for q in packets}
        (HERE/f'duplicate_candidates_{part}.json').write_text(json.dumps({k:v for k,v in dup.items() if v},indent=2),encoding='utf8')
        print(part,len(packets),'questions',sum(map(len,candidates.values())),'numerical relation candidates')
    manifest={'t1_commit':'30acb8d','finqa_commit':'0f16e2867befa6840783e58be38c9efb9229d742','sample_seed':20261116,
              'scope':'FinQA full provided context; not original annual report',
              'input_sha256':{str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,raw)},
              'cohort_ids':[q['id'] for q in cohort]}
    (HERE/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')

if __name__=='__main__':main()
