"""Full-split nomination without a value-distance/interval-compatibility filter.

Explicitly scaled prose versus table cells; semantic decisions are independent
annotations, never a nearest-number heuristic. Locations are zero based.
"""
from __future__ import annotations
import csv, gzip, html, json, re, sys
from collections import Counter, defaultdict
from decimal import Decimal
from fractions import Fraction as F
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parents[2]/'proxy-tail'/'research'/'t1_rounding'
SCALE={'thousand':1000,'million':1000000,'billion':1000000000,'percent':1}
STOP=set('total net other and the for of in to at as a s year years december january balance amount ended fiscal related during costs cost expense expenses cash per'.split())
MENTION=re.compile(r'(?<![\w.])(?P<num>[+-]?(?:\d[\d,]*(?:\.\d+)?|\.\d+))\s*(?P<unit>billion|million|thousand|percent|%)(?:s)?(?!\w)',re.I)
YEAR=re.compile(r'\b(?:19|20)\d{2}\b')

def clean(s):
    return html.unescape(re.sub(r'<[^>]+>','',re.sub(r'<sup>.*?</sup>','',str(s),flags=re.I))).replace('\u00a0',' ').replace('−','-')

def words(s):
    return {w[:-1] if w.endswith('s') else w for w in re.findall(r'[a-z]+',clean(s).lower()) if len(w)>2 and w not in STOP}

def number(s):
    s=clean(s).strip().replace(',','').replace('$','').replace('£','').replace('€','').strip()
    if s.startswith('(') and s.endswith(')'):s='-'+s[1:-1].strip()
    pct=s.endswith('%');s=s.rstrip('%').strip()
    if not re.fullmatch(r'[+-]?(?:\d+(?:\.\d+)?|\.\d+)',s):return None
    d=Decimal(s);return F(d),F(1,2)*F(10)**d.as_tuple().exponent,pct

def contexts():
    allq={};seen=set()
    for split in ['train','dev','test']:
        for item in json.loads((OLD/'data/finqa'/f'{split}.json').read_text(encoding='utf-8')):
            allq[item['id']]={**item,'split':split}
    grouped=defaultdict(list)
    for q in allq.values():grouped[q['filename']].append(q)
    for page,qs in grouped.items():
        for q in qs:
            # Same page may have variant excerpts; union exact document views.
            view=json.dumps([q['table_ori'],q['pre_text'],q['post_text']],sort_keys=True)
            key=(page,view)
            if key in seen:continue
            seen.add(key)
            yield dict(dataset='finqa',id=page,split=q['split'],table=q['table_ori'],texts=[(f'pre_text[{i}]',x) for i,x in enumerate(q['pre_text'])]+[(f'post_text[{i}]',x) for i,x in enumerate(q['post_text'])],questions=qs)
    for split in ['train','dev','test']:
        for c in json.loads((ROOT/'data/tatqa'/f'{split}.json').read_text(encoding='utf-8')):
            yield dict(dataset='tatqa',id=c['table']['uid'],split=split,table=c['table']['table'],texts=[(f"paragraph:{p['order']}",p['text']) for p in c['paragraphs']],questions=c['questions'])

def unit_hints(c):
    hints=[]
    for i,row in enumerate(c['table']):
        for j,cell in enumerate(row):
            for u in ('thousand','million','billion'):
                if re.search(r'\b'+u+r's?\b',clean(cell),re.I):hints.append((u,f'table:{i}:{j}: {clean(cell)}'))
    if not hints:
        for loc,t in c['texts']:
            for m in re.finditer(r'\b(?:in|dollars in|amounts in|expressed in)\s+(thousands?|millions?|billions?)\b',t,re.I):
                hints.append((m.group(1).lower().rstrip('s'),f'{loc}: {t[max(0,m.start()-30):m.end()+45]}'))
    if not hints and c['dataset']=='tatqa':
        # Non-ratio, table-only arithmetic with dataset-provided output units.
        for q in c['questions']:
            if q.get('answer_type')=='arithmetic' and q.get('answer_from')=='table' and q.get('scale') in SCALE and q['scale']!='percent' and not re.search(r'[/÷]',q.get('derivation','')):
                hints.append((q['scale'],f"question-scale:{q['uid']}:{q.get('derivation','')}"))
    return sorted(set(hints))

def sentence(text,start,end):
    # Decimal periods never split sentences.
    boundaries=[m for m in re.finditer(r'(?<!\d)\.(?!\d)|;|\n',text)]
    left=max([0]+[m.end() for m in boundaries if m.end()<=start]);right=min([len(text)]+[m.start() for m in boundaries if m.start()>=end])
    return text[left:right].strip(),start-left,end-left

def nominate():
    found={};counts=Counter();pages=defaultdict(set)
    for c in contexts():
        counts[c['dataset']+'_views']+=1;pages[c['dataset']].add(c['id'])
        hints=unit_hints(c);units=sorted({u for u,_ in hints})
        mentions=[]
        for loc,text in c['texts']:
            for m in MENTION.finditer(text):
                u=m.group('unit').lower();u='percent' if u=='%' else u
                n=number(m.group('num'))
                if n:
                    seg,a,b=sentence(text,m.start(),m.end())
                    mentions.append((loc,text,m,seg,a,b,u,n))
        for i,row in enumerate(c['table']):
            if not i or not row:continue
            label=clean(row[0]);tokens=words(label)
            if not tokens:continue
            for j,cell in enumerate(row[1:],1):
                n=number(cell)
                if not n:continue
                header=' | '.join(clean(rr[j]) for rr in c['table'][:i] if j<len(rr) and (YEAR.search(clean(rr[j])) or '%' in clean(rr[j])))
                years=set(YEAR.findall(label+' '+header))
                if YEAR.fullmatch(str(n[0])) and not years:continue
                us=['percent'] if n[2] or '%' in header and not units else units
                for u in us:
                    value,half=n[0]*SCALE[u],n[1]*SCALE[u]
                    for loc,text,m,seg,a,b,mu,mn in mentions:
                        if (u=='percent')!=(mu=='percent'):continue
                        shared=tokens&words(seg)
                        if not shared or half==mn[1]*SCALE[mu]:continue
                        key=(c['dataset'],c['id'],i,j,u,loc,m.start(),m.group())
                        if key in found:continue
                        py=set(YEAR.findall(seg));year_state='matching' if years&py else 'unmatched' if years and py else 'not_explicit'
                        tableloc=f'table:{i}:{j}'
                        qs=[]
                        for q in c['questions']:
                            deriv=q.get('qa',q).get('program',q.get('derivation',''))
                            literals=[number(v) for v in re.findall(r'(?<![#\w.])[+-]?(?:\d[\d,]*(?:\.\d+)?|\.\d+)',deriv)]
                            if any(v and abs(v[0]) in {abs(n[0]),abs(mn[0])} for v in literals):qs.append(q.get('id',q.get('uid')))
                        found[key]=dict(dataset=c['dataset'],split=c['split'],document_id=c['id'],row=i,column=j,row_label=label,header=header,table_location=tableloc,table_raw=cell,table_unit=u,unit_evidence=[h for hu,h in hints if hu==u],unit_ambiguous=len(units)>1,text_location=loc,text_offset=m.start(),text_raw=m.group(),text_unit=mu,sentence=seg,text=text,shared_words=sorted(shared),metric_word_coverage=len(shared)/len(tokens),year_state=year_state,table_years=sorted(years),text_years=sorted(py),table_value=str(value),text_value=str(mn[0]*SCALE[mu]),table_half=str(half),text_half=str(mn[1]*SCALE[mu]),possible_question_ids=sorted(set(qs)),status='unreviewed',reason='')
    rows=sorted(found.values(),key=lambda r:(r['dataset'],r['document_id'],r['row'],r['column'],r['text_location'],r['text_offset']))
    for i,r in enumerate(rows,1):r['pair_id']=f'p{i:05d}'
    counts.update({k+'_documents':len(v) for k,v in pages.items()})
    return rows,dict(counts)

def jsonl(path,rows):
    if path.suffix=='.gz':
        with gzip.open(path,'wt',encoding='utf8') as f:
            for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    else:path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')

def strict_candidate(r):
    if r['unit_ambiguous'] or r['year_state']!='matching' or len(r['table_years'])!=1:return False
    if len(r['shared_words'])<2 or r['metric_word_coverage']<.99:return False
    seg=r['sentence']; raw=r['text_raw'];starts=[m.start() for m in re.finditer(re.escape(raw),seg)]
    if len(starts)!=1:return False
    start=starts[0];end=start+len(raw)
    ms=list(MENTION.finditer(seg)); ys=list(YEAR.finditer(seg))
    # Explicit respectively construction assigns years by textual list order.
    if 'respectively' in seg.lower() and len(ms)==len(ys) and len(ms)>1:
        yr=ys[next(i for i,m in enumerate(ms) if m.start()==start)].group()
    else:
        yr=min(ys,key=lambda y:min(abs(y.end()-start),abs(y.start()-end))).group()
    if yr!=r['table_years'][0]:return False
    prefix=seg[max(0,start-55):start].lower()
    if re.search(r'(?:increas|decreas|declin|reduc|rose|fell|change|higher|lower|improv|growth)[a-z]*\s+(?:of\s+|by\s+)?[£$€ ]*$',prefix):return False
    if re.search(r'\b(?:excluding|included|excluding|included|comprised|including|less|except|of which)\b',seg,re.I) and not re.search(r'\b(?:exclud|includ)',r['row_label'],re.I):return False
    return True

def review_stratum(r):
    if not strict_candidate(r):return None
    s=r['sentence'];n=len(list(MENTION.finditer(s)))
    if n==1:return 'one_scaled_mention'
    pos=s.find(r['text_raw']);prefix=s[max(0,pos-220):pos]
    last=prefix[max([0]+[m.end() for m in MENTION.finditer(prefix)]):]
    if re.search(r'(?:was|were|totaled|totalled|amounted to)\s*[$£€ ]*$',last,re.I) and words(r['row_label'])<=words(last):return 'local_copula_assertion'
    return None

def main():
    rows,counts=nominate();jsonl(ROOT/'part4_candidates.jsonl.gz',rows)
    counts.update({k+'_candidates':v for k,v in Counter(r['dataset'] for r in rows).items()})
    (ROOT/'part4_scan_counts.json').write_text(json.dumps(counts,indent=2)+'\n',encoding='utf-8')
    shortlist=[r for r in rows if strict_candidate(r)]
    jsonl(ROOT/'part4_semantic_shortlist.jsonl',shortlist)
    jsonl(ROOT/'part4_single_mention_review.jsonl',[r for r in rows if review_stratum(r)=='one_scaled_mention'])
    jsonl(ROOT/'part4_copula_review.jsonl',[r for r in rows if review_stratum(r)=='local_copula_assertion'])
    print(json.dumps(counts));print('SEMANTIC SHORTLIST',len(shortlist),dict(Counter(r['dataset'] for r in shortlist)))
    for r in shortlist[:15]:print(r['pair_id'],r['document_id'],r['row_label'],r['header'],r['table_raw'],r['text_raw'],r['sentence'][:150])

if __name__=='__main__':main()
