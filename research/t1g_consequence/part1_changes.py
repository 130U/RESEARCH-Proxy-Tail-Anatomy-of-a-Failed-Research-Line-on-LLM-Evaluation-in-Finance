"""Printed changes: header-defined extraction, rational boxes and exact probabilities.

No direction/base/units are chosen by observed agreement. Raw unmatched rows stay in
the output. Run --dataset finqa before the TAT-QA prediction commit if needed.
"""
from pathlib import Path
from fractions import Fraction as F
from collections import Counter, defaultdict
from itertools import product
import argparse, csv, html, json, re, math

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[2]
OLD=WORK/'proxy-tail/research/t1_rounding'
YEARS=re.compile(r'(?<!\d)(?:19|20)\d{2}(?!\d)')
CHANGE=re.compile(r'change|increase|decrease|variance|growth',re.I)
SCALE={'thousand':F(1000),'million':F(10**6),'billion':F(10**9)}

def clean(s):
    return html.unescape(re.sub(r'<[^>]+>','',str(s))).replace('\u2212','-').strip()

def number(s):
    raw=clean(s)
    raw=re.sub(r'\([a-z]\)$','',raw,flags=re.I).strip()
    unit=next((v for k,v in SCALE.items() if re.search(r'\b'+k+r's?\b',raw,re.I)),F(1))
    s=re.sub(r'\b(?:thousand|million|billion)s?\b','',raw,flags=re.I)
    s=re.sub(r'[,$£€%\s]','',s)
    if s.startswith('(') and s.endswith(')'): s='-'+s[1:-1]
    if not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)',s): return None
    places=len(s.split('.')[1]) if '.' in s else 0
    return dict(value=F(s)*unit,half=F(1,2*10**places)*unit,places=places,raw=raw,unit=unit)

def rounded(x,d):
    z=x/d
    if z<0:return -rounded(-x,d)
    return ((2*z.numerator+z.denominator)//(2*z.denominator))*d

def dump(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
def csvout(path,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
        w.writerows({k:json.dumps(v,ensure_ascii=False,default=str) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in rows)

def documents(dataset):
    seen={}
    for split in ['train','dev','test']:
        path=OLD/'data/finqa'/f'{split}.json' if dataset=='finqa' else HERE/'data/tatqa'/f'{split}.json'
        for x in json.loads(path.read_text(encoding='utf-8')):
            key=x['filename'] if dataset=='finqa' else x['table']['uid']
            if key not in seen:
                seen[key]=dict(dataset=dataset,doc_id=key,splits=[],table=x['table_ori'] if dataset=='finqa' else x['table']['table'],
                    texts=x['pre_text']+x['post_text'] if dataset=='finqa' else [p['text'] for p in x['paragraphs']],questions=[])
            obj=seen[key]
            if split not in obj['splits']:obj['splits'].append(split)
            if dataset=='finqa':obj['questions'].append(dict(x['qa'],id=x['id'],split=split))
            else:obj['questions'].extend(dict(q,id=q['uid'],split=split) for q in x['questions'])
    return list(seen.values())

def layouts(doc):
    t=doc['table']; found=[]
    for hi,row in enumerate(t[:5]):
        levels={i:int(YEARS.findall(clean(c))[0]) for i,c in enumerate(row) if len(YEARS.findall(clean(c)))==1 and not CHANGE.search(clean(c)) and '%' not in clean(c)}
        if len(levels)<2:continue
        for ci in range(max(map(len,t))):
            h=clean(row[ci]) if ci<len(row) else ''
            parts=[]
            for r in t[:hi+1]:
                cell=clean(r[ci]) if ci<len(r) else ''
                if not cell:
                    left=next((clean(r[j]) for j in range(min(ci-1,len(r)-1),-1,-1) if clean(r[j])), '')
                    if len(YEARS.findall(left))==2:cell=left
                parts.append(cell)
            context=' '.join(parts)
            pair=YEARS.findall(context)
            global_header=' '.join(clean(c) for r in t[:hi+1] for c in r)
            eligible=bool(CHANGE.search(context)) or (h.strip()=='%' and CHANGE.search(global_header)) or (len(pair)==2 and CHANGE.search(global_header))
            if not eligible or ci in levels:continue
            if re.search(r'market|fx|exchange|assumption|interest rate|basis.point|fair.market',context,re.I):continue
            if len(pair)==2:
                yr=sorted(map(int,pair),reverse=True)
                matching=[next((j for j,y in levels.items() if y==v),None) for v in yr]
                if None in matching:continue
                new,base=matching
            else:
                blocks=[]
                for j in sorted(levels):
                    if blocks and j==blocks[-1][-1]+1:blocks[-1].append(j)
                    else:blocks.append([j])
                preceding=[block for block in blocks if block[-1]<ci]
                block=preceding[-1] if preceding else []
                if len(block)>=2:nearby=sorted(block,key=lambda j:(-levels[j],j))[:2]
                else:nearby=sorted(levels,key=lambda j:(abs(j-ci),j))[:2]
                shortpair=re.search(r'(?<!\d)(\d{2})[-–](\d{2})(?!\d)',context)
                if shortpair:
                    matching=[j for j in levels if str(levels[j])[-2:] in shortpair.groups()]
                    if len(matching)==2:nearby=matching
                new=min(nearby,key=lambda j:(-levels[j],j));base=next(j for j in nearby if j!=new)
            # Formatting '%' may appear only in the first data cell of the column.
            mixed_dollar=any(ci<len(r) and '$' in clean(r[ci]) for r in t[hi+1:])
            pct=bool(re.search(r'%|percent',context,re.I)) or (not mixed_dollar and any(ci<len(r) and '%' in clean(r[ci]) for r in t[hi+1:]))
            if len(YEARS.findall(h))==2 and not mixed_dollar and re.search(r'percent|%',global_header,re.I):pct=True
            found.append(dict(header_row=hi,new_col=new,base_col=base,change_col=ci,kind='percent' if pct else 'amount',header=context,new_year=levels[new],base_year=levels[base]))
    return list({(x['new_col'],x['base_col'],x['change_col']):x for x in found}.values())

def clip(poly,A,B,C):
    """Clip rational polygon to A*x+B*y <= C."""
    result=[]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        dp=A*p[0]+B*p[1]-C;dq=A*q[0]+B*q[1]-C
        if dp<=0:result.append(p)
        if (dp<0<dq) or (dq<0<dp):
            u=dp/(dp-dq);result.append((p[0]+u*(q[0]-p[0]),p[1]+u*(q[1]-p[1])))
    return result

def probability_between(a,b,ha,hb,kind,lo,hi):
    p=[(a-ha,b-hb),(a+ha,b-hb),(a+ha,b+hb),(a-ha,b+hb)]
    if kind=='amount':
        p=clip(p,F(1),F(-1),-lo);p=clip(p,F(-1),F(1),hi)
    else:
        low=1+lo/100;high=1+hi/100
        if a>0:p=clip(p,low,F(-1),F(0));p=clip(p,-high,F(1),F(0))
        else:p=clip(p,-low,F(1),F(0));p=clip(p,high,F(-1),F(0))
    if not p:return F(0)
    area=abs(sum(x*v-y*u for (x,y),(u,v) in zip(p,p[1:]+p[:1])))/2
    return area/(4*ha*hb)

def measure(row):
    a,b,c=[number(row[k]) for k in ['base_raw','new_raw','change_raw']]
    if not all([a,b,c]):return dict(row,status='missing_or_nonnumeric')
    av,bv,cv=a['value'],b['value'],c['value'];ha,hb,hc=a['half'],b['half'],c['half']
    r=dict(row,base=str(av),new=str(bv),printed=str(cv),base_half=str(ha),new_half=str(hb),printed_half=str(hc),base_places=a['places'],new_places=b['places'],printed_places=c['places'])
    if row['kind']=='percent' and av-ha<=0<=av+ha:return dict(r,status='base_touches_zero')
    fn=(lambda x,y:y-x) if row['kind']=='amount' else (lambda x,y:100*(y/x-1))
    corners=[(fn(x,y),x,y) for x,y in product([av-ha,av+ha],[bv-hb,bv+hb])]
    low=min(corners);high=max(corners);lo,hi=low[0],high[0];center=fn(av,bv)
    compatible=max(lo,cv-hc)<=min(hi,cv+hc)
    q=rounded(center,2*hc)
    r.update(status='compatible' if compatible else 'nonintersection',center=str(center),lo=str(lo),hi=str(hi),
        low_witness={'base':str(low[1]),'new':str(low[2])},high_witness={'base':str(high[1]),'new':str(high[2])},
        delta=float(abs(bv-av)/(ha+hb)),equal_precision=ha==hb==hc,
        mismatch=(cv!=center if row['kind']=='amount' else cv!=q),rounded_center=str(q),
        relative_difference=None if cv==0 else float(abs(center-cv)/abs(cv)),
        relative_gt_1pct=abs(center-cv)>abs(cv)/100,
        mismatch_probability=float(1-probability_between(av,bv,ha,hb,row['kind'],q-hc,q+hc)),
        position=None if hi==lo else float((cv-lo)/(hi-lo)))
    return r

def extract(ds):
    rows=[];table_n=0
    for doc in documents(ds):
        ls=layouts(doc)
        if ls:table_n+=1
        for l in ls:
            for ri,r in enumerate(doc['table'][l['header_row']+1:],l['header_row']+1):
                if len(r)<=max(l['new_col'],l['base_col'],l['change_col']):continue
                row=dict(dataset=ds,doc_id=doc['doc_id'],splits=doc['splits'],row=ri,label=clean(r[0]) if l['new_col']!=0 and l['base_col']!=0 else '',**l,
                    base_raw=r[l['base_col']],new_raw=r[l['new_col']],change_raw=r[l['change_col']],raw_row=r)
                if '%' in row['base_raw'] and '%' in row['new_raw']:
                    row['kind']='amount';row['amount_unit']='percentage_points'
                measured=measure(row)
                measured['box_status']=measured['status']
                if re.search(r'adjusted|constant|comp\.|excluding|ias\s*18|organic',row['header'],re.I):
                    measured['status']='different_basis_header'
                rows.append(measured)
    return rows,table_n

def summarize(rows):
    groups={}
    for ds in ['finqa','tatqa']:
        for kind in ['amount','percent']:
            allr=[r for r in rows if r['dataset']==ds and r['kind']==kind];valid=[r for r in allr if r['status']=='compatible']
            small=[r for r in valid if r['delta']<100]
            equal=[r for r in valid if r['equal_precision']]
            groups[f'{ds}_{kind}']=dict(status_counts=dict(Counter(r['status'] for r in allr)),n=len(valid),mismatch=sum(r['mismatch'] for r in valid),
                rate=sum(r['mismatch'] for r in valid)/len(valid) if valid else None,
                predicted_rate=sum(r['mismatch_probability'] for r in valid)/len(valid) if valid else None,
                relative_gt_1pct=sum(r['relative_gt_1pct'] for r in valid),small_delta_n=len(small),small_delta_mismatch=sum(r['mismatch'] for r in small),
                small_delta_rate=sum(r['mismatch'] for r in small)/len(small) if small else None,
                equal_precision_n=len(equal),equal_precision_mismatch=sum(r['mismatch'] for r in equal),
                positions_outside=sum(not 0<=r['position']<=1 for r in valid if r['position'] is not None))
    return groups

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dataset',choices=['finqa','tatqa','all'],default='all');a=ap.parse_args()
    ds=['finqa','tatqa'] if a.dataset=='all' else [a.dataset]
    rows=[]
    for name in ds:
        rs,n=extract(name);rows+=rs;print(name,'candidate tables',n,'rows',len(rs))
    dump(HERE/f'part1_rows_{a.dataset}.json',rows);csvout(HERE/f'part1_rows_{a.dataset}.csv',rows)
    summary=summarize(rows);dump(HERE/f'part1_summary_{a.dataset}.json',summary);print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
