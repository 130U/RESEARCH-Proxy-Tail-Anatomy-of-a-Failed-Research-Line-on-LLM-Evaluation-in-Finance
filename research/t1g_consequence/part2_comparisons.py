"""Joint-input rounding audit of comparison answers; no language-model calls.

Run inventory before audit. The audit command is gated by the parent task's
literature review and the separately committed Part 3 prediction.
"""
from __future__ import annotations

import argparse
import ast
import copy
import csv
from fractions import Fraction as F
import importlib.util
from itertools import product
import json
from pathlib import Path
import re
import sys
from collections import Counter
sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]
T1 = WORKSPACE / 'proxy-tail/research/t1_rounding'
T1A = WORKSPACE / 'proxy-tail-t1a/research/t1a_law'
sys.path.insert(0, str(T1))
sys.path.insert(0, str(T1A))

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

binding = module('t1_binding', T1 / 'analyze.py')


def dump(path, rows):
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2,
                               default=lambda x: str(x) if isinstance(x, F) else x), encoding='utf-8')


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w', encoding='utf-8-sig', newline='') as out:
        w = csv.DictWriter(out, fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False, default=str) if isinstance(v, (dict,list,tuple)) else v
                        for k,v in row.items()})


def finqa_inventory():
    rows=[]
    for split in ('train','dev','test'):
        records=json.loads((T1/'data/finqa'/f'{split}.json').read_text(encoding='utf-8'))
        for record in records:
            qa=record['qa']; program=qa.get('program','')
            if 'greater(' not in program and not any(str(qa.get(key,'')).strip().lower() in ('yes','no') for key in ('answer','exe_ans')):
                continue
            steps=[(op,a.strip(),b.strip()) for op,a,b in binding.PROGRAM.findall(program)]
            greater=[(i,a,b) for i,(op,a,b) in enumerate(steps) if op=='greater']
            computed=bool(greater and any(a.startswith('#') or b.startswith('#') for _,a,b in greater))
            unit_only=record['id'] in {'ANET/2017/page_157.pdf-2','AWK/2018/page_162.pdf-2','DISH/2002/page_94.pdf-4','UNP/2014/page_24.pdf-2','AMT/2014/page_160.pdf-4'}
            rows.append(dict(dataset='FinQA',split=split,id=record['id'],question=qa['question'],
                             answer=qa.get('answer'),exe_ans=qa.get('exe_ans'),derivation=program,
                             computed=computed and not unit_only,syntactic_computed=computed,
                             candidate_reason='greater_or_yes_no',record=record))
    return rows


COMP_WORDS=re.compile(r'\b(highest|largest|lowest|smallest|more|less|higher|lower|greater|faster|most|least|exceed(?:ed|s)?|increase(?:d)?|decrease(?:d)?)\b',re.I)
COMPUTED_WORDS=re.compile(r'\b(growth|grew|grow|change|difference|increase|decrease|ratio|margin|rate of|percentage of|percent of)\b',re.I)
ARITH=re.compile(r'[+*/]|\d\s*-\s*\d')

def tatqa_inventory():
    rows=[]
    directory=HERE/'data/tatqa'
    files=sorted(directory.glob('*.json'))
    if not files: files=[T1/'data/tatqa/dev.json']
    for path in files:
        if any(x in path.name.lower() for x in ('metadata','manifest')): continue
        try: records=json.loads(path.read_text(encoding='utf-8'))
        except Exception: continue
        if not isinstance(records,list): continue
        split=path.stem.replace('tatqa_dataset_','')
        for record in records:
            for qa in record.get('questions',[]):
                if 'answer' not in qa: continue
                derivation=qa.get('derivation','')
                marker=bool(re.search(r'[<>≤≥]',derivation))
                nonarith=qa.get('answer_type')!='arithmetic'
                lexical=nonarith and bool(COMP_WORDS.search(qa['question']))
                if not (qa.get('req_comparison') or marker or lexical): continue
                if not nonarith: continue
                computed=bool(ARITH.search(derivation)) or bool(COMPUTED_WORDS.search(qa['question']))
                rows.append(dict(dataset='TAT-QA',split=split,id=qa['uid'],question=qa['question'],
                                 answer=qa['answer'],derivation=derivation,computed=computed,
                                 candidate_reason=';'.join(k for k,v in [('annotation',qa.get('req_comparison')),('operator',marker),('lexical',lexical)] if v),
                                 table_uid=record['table']['uid'],qa=qa,record=record))
    return rows


def finqa_bind(row):
    record=copy.deepcopy(row['record'])
    if row['id']=='PPG/2018/page_85.pdf-1':
        return [make_model('x0-x1',{'x0':dict(value='291',half='1/2',raw='$291',location='table_4:1',context='environmental reserves'),
                                      'x1':dict(value='180',half='1/2',raw='180',location='text_7',context='asbestos reserves')})]
    if row['id']=='ANET/2015/page_156.pdf-1':
        return [make_model('x0*1000000-x1*1000',{'x0':dict(value='43.9',half='1/20',raw='43.9',location='text_9',context='purchase commitments millions'),
                                                  'x1':dict(value='5754',half='1/2',raw='$5,754',location='table_0:1',context='lease commitments thousands')})]
    steps=[(op,a.strip(),b.strip()) for op,a,b in binding.PROGRAM.findall(record['qa']['program'])]
    if sum(op=='greater' for op,_,_ in steps)!=1 or steps[-1][0]!='greater':
        raise ValueError('not_one_final_greater')
    steps[-1]=('subtract',steps[-1][1],steps[-1][2])
    record['qa']['program']=', '.join(f'{op}({a}, {b})' for op,a,b in steps)
    try:
        mapped,inputs,provenance,warnings=binding.bind(record)
    except ValueError:
        return [finqa_fallback(row)]
    result=dict(steps=mapped,input_intervals={k:dict(lo=str(v.lo),hi=str(v.hi)) for k,v in inputs.items()},
                input_provenance=provenance)
    return [result]


def expression_steps(expression):
    steps=[]
    def convert(node):
        if isinstance(node,ast.Name): return node.id
        if isinstance(node,ast.Constant): return str(node.value)
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.USub):
            a=convert(node.operand);steps.append(('multiply',a,'const_m1'));return f'#{len(steps)-1}'
        if isinstance(node,ast.BinOp):
            op={ast.Add:'add',ast.Sub:'subtract',ast.Mult:'multiply',ast.Div:'divide'}[type(node.op)]
            a,b=convert(node.left),convert(node.right);steps.append((op,a,b));return f'#{len(steps)-1}'
        raise ValueError('unsupported_ast')
    out=convert(ast.parse(expression,mode='eval').body)
    if not out.startswith('#'): steps.append(('add',out,'const_0'))
    return steps


def make_model(expression, sources):
    return dict(steps=expression_steps(expression),
                input_intervals={name:dict(lo=str(F(src['value'])-F(src['half'])),hi=str(F(src['value'])+F(src['half']))) for name,src in sources.items()},
                input_provenance=sources)


def finqa_fallback(row):
    record=row['record'];qa=record['qa']; program=qa['program']
    table=record.get('table_ori',record['table'])
    # These two table operators are expanded from their named rows.
    if 'table_' in program:
        wanted=('credit risk','market risk') if 'table_average' in program else ('revisions of previous quantity estimates','accretion of discount')
        src={};groups=[]
        for label in wanted:
            match=[(i,r) for i,r in enumerate(table) if binding.clean(r[0]).strip().lower()==label]
            if len(match)!=1: raise ValueError('table_row_not_unique')
            i,vals=match[0];group=[]
            for j,raw in enumerate(vals[1:],1):
                hits=binding.tokens(raw,f'table_{i}:{j}',label,table=True)
                if len(hits)!=1: raise ValueError('table_operator_non_numeric')
                hit=hits[0];name=f'x{len(src)}';group.append(name)
                src[name]=dict(value=str(hit['value']),half=str(hit['half']),raw=raw,location=hit['loc'],context=label)
            groups.append('('+'+'.join(group)+')'+('/'+str(len(group)) if 'table_average' in program else ''))
        return make_model(groups[0]+'-'+groups[1],src)
    selected,full=binding.source_numbers(record)
    # Include first table row because FinQA sometimes stores data there.
    for j,cell in enumerate(table[0][1:],1): full.extend(binding.tokens(cell,f'table_0:{j}',binding.clean(table[0][0]),table=True))
    if row['id']=='CDW/2014/page_55.pdf-2':
        for i,r in enumerate(table[1:],1):full.extend(binding.tokens(r[0],f'table_{i}:0','dividend amount',table=True))
    src={};mapped={};steps=[]
    for op,a,b in binding.PROGRAM.findall(program):
        if op=='greater':op='subtract'
        if op not in ('add','subtract','multiply','divide'):raise ValueError('unsupported_operation')
        operands=[]
        for token in (a.strip(),b.strip()):
            if token.startswith(('#','const_')):operands.append(token);continue
            if token in mapped:operands.append(mapped[token]);continue
            pct=token.endswith('%');value=F(token.rstrip('%').replace(',',''))
            candidates=[c for c in selected if c['value']==value]
            if not candidates:candidates=[c for c in full if c['value']==value]
            if not candidates and value>0 and f'multiply({token}, const_m1)' in program:
                candidates=[dict(c,value=-c['value']) for c in selected+full if c['value']==-value]
            if not candidates and row['id'] in ('PKG/2006/page_65.pdf-1','UNP/2012/page_30.pdf-1'):
                candidates=[dict(c,value=-c['value']) for c in selected+full if c['value']==-value]
            if not candidates and re.search(r'(?<!\d)'+re.escape(token)+r'(?!\d)',qa['question']):
                candidates=[dict(value=value,half=F(0),raw=token,loc='question:given',context='explicit threshold')]
            if not candidates:raise ValueError('source_not_found_fallback:'+token)
            widths={c['half'] for c in candidates}
            if len(widths)>1:raise ValueError('source_precision_ambiguous_fallback:'+token)
            c=candidates[0];scale=F(1,100) if pct else F(1)
            name=f'x{len(src)}';mapped[token]=name;operands.append(name)
            # Dividends and contractual coupon rates are declared quantities.
            fixed=row['id'] in ('MRO/2007/page_79.pdf-1','CDW/2014/page_55.pdf-2') or (row['id'].startswith('UNP/2011/page_80') and pct)
            src[name]=dict(value=str(value*scale),half='0' if fixed else str(c['half']*scale),raw=c['raw'],location=c['loc'],
                           context=c['context'],binding_note='same-precision multiple candidates; numeric role occurs once or is manually inspected',
                           exact_declared_quantity=fixed)
        steps.append((op,*operands))
    return dict(steps=steps,input_intervals={k:dict(lo=str(F(s['value'])-F(s['half'])),hi=str(F(s['value'])+F(s['half']))) for k,s in src.items()},input_provenance=src)


def exact_audit(model):
    """Return joint range, verified strict interior flip witness, and probability."""
    import law_core as law
    import numpy as np
    from scipy.stats import qmc
    centers,half=law.centers_half(model); names=list(centers)
    center=law.evaluate(model,centers)
    baseline=center>0
    cert=law.range_certificate(model)
    witness=None
    for signs in product((-1,1), repeat=len(names)):
        values={k:centers[k]+s*half[k]*F(999,1000) for k,s in zip(names,signs)}
        try: value=law.evaluate(model,values)
        except ZeroDivisionError: continue
        if (value>0)!=baseline:
            witness=dict(inputs={k:str(v) for k,v in values.items()},difference=str(value),
                         comparison=value>0,interior_fraction='999/1000')
            break
    lo,hi=cert['lo'],cert['hi']
    if witness: status='unstable'
    elif lo is not None and ((baseline and lo>0) or (not baseline and hi<=0)):
        status='stable'
    elif cert['exact'] and baseline and lo==0:
        status='boundary_only'
    else: status='unresolved'
    probs=[]
    for seed in (20261117,20261118):
        uniform=qmc.Sobol(len(names), scramble=True, seed=seed).random_base2(17)
        vals={k:float(centers[k])+(uniform[:,j]*2-1)*float(half[k]) for j,k in enumerate(names)}
        outputs=np.asarray(law.evaluate(model,vals))
        probs.append(float(np.mean((outputs>0)!=baseline)))
    _,radius,gradient=law.gradient_radius(model)
    return dict(center_difference=str(center),baseline=baseline,status=status,certificate={k:str(v) if isinstance(v,F) else v for k,v in cert.items()},
                witness=witness,probability=sum(probs)/2,qmc_replicates=probs,qmc_n_per_replicate=2**17,
                first_order_radius=str(radius),first_order_unstable=abs(center)<radius,
                gradient={k:str(v) for k,v in gradient.items()})


def tatqa_models(row,spec):
    table=row['record']['table']['table'];sources={}
    for i,coord in enumerate(spec['coordinates']):
        if coord is None:
            item=spec['text_sources'][str(i)]
            raw=item['raw'];loc=f"paragraph_{item['paragraph']}";context=next(p['text'] for p in row['record']['paragraphs'] if p['order']==item['paragraph'])
        else:
            r,c=coord;raw=table[r][c];loc=f'table_{r}:{c}';context=table[r][0]
        hits=binding.tokens(raw,loc,context,table=True)
        if len(hits)!=1:raise ValueError(f'cannot parse {loc}: {raw}')
        hit=hits[0]
        sources[f'x{i}']=dict(value=str(hit['value']),half='0' if spec.get('exact_inputs') else str(hit['half']),raw=raw,location=loc,context=context)
    expressions=spec['expressions'];winner=spec['winner']
    if spec['direction'] in ('zero','threshold'):
        exprs=expressions;competitors=spec['labels']
    else:
        exprs=[];competitors=[]
        for i,expression in enumerate(expressions):
            if i==winner:continue
            a,b=expressions[winner],expression
            if spec['direction']=='min': a,b=b,a
            exprs.append('('+a+')-('+b+')');competitors.append(spec['labels'][i])
    return [(make_model(expression,sources),competitor) for expression,competitor in zip(exprs,competitors)]


def joint_probability(models):
    import numpy as np
    import law_core as law
    from scipy.stats import qmc
    centers,half=law.centers_half(models[0]);names=list(centers)
    probs=[]
    for seed in (20261117,20261118):
        uniform=qmc.Sobol(len(names),scramble=True,seed=seed).random_base2(17)
        values={k:float(centers[k])+(uniform[:,j]*2-1)*float(half[k]) for j,k in enumerate(names)}
        flips=np.zeros(2**17,dtype=bool)
        for model in models:
            baseline=law.evaluate(model,centers)>0
            flips |= (np.asarray(law.evaluate(model,values))>0)!=baseline
        probs.append(float(np.mean(flips)))
    return sum(probs)/2,probs


def run_tatqa():
    specs=json.loads((HERE/'part2_tatqa_specs.json').read_text(encoding='utf-8'))
    rows=tatqa_inventory();outputs=[]
    for row in rows:
        if row['id'] not in specs:continue
        spec=specs[row['id']];out={k:v for k,v in row.items() if k not in ('record','qa')}
        out.update(computed=True,spec=spec)
        try:
            pairs=tatqa_models(row,spec);models=[m for m,_ in pairs]
            out['models']=models;out['audits']=[dict(exact_audit(m),competitor=c) for m,c in pairs]
            statuses=[a['status'] for a in out['audits']]
            out['status']='unstable' if 'unstable' in statuses else ('stable' if set(statuses)=={'stable'} else 'unresolved')
            out['probability'],out['qmc_replicates']=joint_probability(models)
            if row['id']=='ce5fc144-7926-472b-9f90-f6fcbc3410e7':
                out['probability']=float(F(29,360));out['probability_exact']='29/360'
                out['probability_method']='Irwin-Hall sum of six uniforms: F_6(2)=(2^6-6)/6!'
            elif row['id']=='1d5aea847254a9c3a9771b7b1a9ae40b':
                from scipy.integrate import dblquad
                # Conditional rectangle area of basic EPS X < (A/B)*Y.
                # A,B are diluted EPS; integrate exactly in X,Y, numerically in A,B.
                def conditional(a,b):
                    k=a/b;l1,u1=2.995,3.005;l2,u2=6.655,6.665
                    pos=lambda z:max(z,0.0)**2
                    return (pos(k*u2-l1)-pos(k*l2-l1)-pos(k*u2-u1)+pos(k*l2-u1))/(2*k*(u1-l1)*(u2-l2))
                value,error=dblquad(lambda a,b:conditional(a,b),6.575,6.585,lambda b:2.955,lambda b:2.965,epsabs=1e-10,epsrel=1e-8)
                out['probability']=value/0.0001;out['probability_quadrature_error']=error/0.0001
                out['probability_method']='analytic conditional rectangle area; adaptive two-dimensional quadrature over denominator intervals'
        except Exception as exc:out.update(status='unsupported',reason=str(exc))
        outputs.append(out)
    dump(HERE/'part2_tatqa_results.json',outputs);write_csv(HERE/'part2_tatqa_results.csv',outputs)
    print(Counter(r['status'] for r in outputs))


def review_sample():
    import random
    rows=tatqa_inventory();rng=random.Random(20261117)
    structural=[r for r in rows if ARITH.search(r['derivation'])]
    remainder=[r for r in rows if r not in structural]
    sample=rng.sample(structural,min(20,len(structural)))+rng.sample(remainder,40-min(20,len(structural)))
    dump(HERE/'part2_review_sample.json',[{k:v for k,v in r.items() if k not in ('record','qa')} for r in sample])
    for r in sample:print(r['id'],r['question'],'|',r['derivation'],'|',r['answer'])


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['inventory','finqa','tatqa','sample']);args=p.parse_args()
    if args.command=='tatqa':return run_tatqa()
    if args.command=='sample':return review_sample()
    if args.command=='inventory':
        rows=finqa_inventory()+tatqa_inventory()
        compact=[{k:v for k,v in r.items() if k not in ('record','qa')} for r in rows]
        specs=json.loads((HERE/'part2_tatqa_specs.json').read_text(encoding='utf-8'))
        for r in compact:
            if r['dataset']=='TAT-QA':
                r['raw_computed_candidate']=r['computed']
                r['computed']=r['id'] in specs
                r['screening_disposition']='confirmed arithmetic comparison' if r['computed'] else 'no computed comparison established by derivation/source screening; not interval-audited'
        dump(HERE/'part2_inventory.json',compact)
        write_csv(HERE/'part2_inventory.csv',compact)
        print({d:sum(r['dataset']==d for r in rows) for d in ('FinQA','TAT-QA')})
    else:
        rows=finqa_inventory(); outputs=[]
        for row in rows:
            out={k:v for k,v in row.items() if k!='record'}
            try:
                models=finqa_bind(row);out['models']=models
                out['audits']=[exact_audit(model) for model in models]
                out['status']=out['audits'][0]['status']
                out['probability']=out['audits'][0]['probability']
                label=str(row.get('exe_ans','')).strip().lower()
                out['center_matches_gold']=out['audits'][0]['baseline']==(label=='yes') if label in ('yes','no') else None
                out['center_matches_human_answer']=out['audits'][0]['baseline']==(str(row.get('answer','')).strip().lower()=='yes') if str(row.get('answer','')).strip().lower() in ('yes','no') else None
                if row['id'] in ('PPG/2018/page_85.pdf-1','ANET/2015/page_156.pdf-1'):
                    out['repair_note']='Official program has no comparison; displayed question reconstructed separately, not an official-program result.'
            except Exception as exc: out.update(status='unsupported',reason=str(exc))
            outputs.append(out)
        dump(HERE/'part2_finqa_results.json',outputs)
        write_csv(HERE/'part2_finqa_results.csv',outputs)
        from collections import Counter
        print(Counter((r['computed'],r['status']) for r in outputs))

if __name__=='__main__': main()
