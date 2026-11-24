"""Score original answers and expressions, certify attainable outputs, retain evidence.

No model calls. The only executed input is an allowlisted arithmetic AST; never eval().
"""
from __future__ import annotations
import argparse
import ast
import csv
import importlib.util
import itertools
import json
import math
import re
import sys
from collections import Counter
from decimal import Decimal
from fractions import Fraction as F
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OPS={ast.Add:'add',ast.Sub:'subtract',ast.Mult:'multiply',ast.Div:'divide',ast.Pow:'exp'}

def fraction(s):
    return F(Decimal(str(s).strip().replace(',','').replace('−','-')))

def parse_expression(s):
    s=str(s).strip().replace('−','-').replace('×','*').replace('÷','/')
    if len(s)>2000: raise ValueError('expression too long')
    tree=ast.parse(s,mode='eval').body
    def visit(n):
        if isinstance(n,ast.Constant) and type(n.value) in (int,float):
            return ('number',fraction(ast.get_source_segment(s,n)))
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.UAdd,ast.USub)):
            inner=visit(n.operand)
            if inner[0]=='number': return ('number',inner[1] if isinstance(n.op,ast.UAdd) else -inner[1])
            return inner if isinstance(n.op,ast.UAdd) else ('subtract',('number',F(0)),inner)
        if isinstance(n,ast.BinOp) and type(n.op) in OPS:
            left,right=visit(n.left),visit(n.right)
            if isinstance(n.op,ast.Pow) and (right[0]!='number' or right[1].denominator!=1 or abs(right[1])>12):
                raise ValueError('unsupported exponent')
            return (OPS[type(n.op)],left,right)
        raise ValueError('unsupported expression node: '+type(n).__name__)
    return visit(tree)

def run_tree(t,cast=F,substitutions=None):
    if t[0]=='number':
        return substitutions.get(t[1],cast(t[1])) if substitutions else cast(t[1])
    a,b=run_tree(t[1],cast,substitutions),run_tree(t[2],cast,substitutions)
    return {'add':lambda:a+b,'subtract':lambda:a-b,'multiply':lambda:a*b,'divide':lambda:a/b,'exp':lambda:a**b}[t[0]]()

def decimal_literal(x):
    # AST literals originate from finite decimals. Normalizing factors do too.
    d=Decimal(x.numerator)/Decimal(x.denominator)
    return format(d,'f')

def dsl_tokens(t):
    steps=[]
    def walk(x):
        if x[0]=='number': return decimal_literal(x[1])
        a,b=walk(x[1]),walk(x[2])
        k=len(steps)
        steps.append([x[0]+'(',a,b,')'])
        return '#'+str(k)
    result=walk(t)
    if not steps: steps.append(['add(',result,'0',')'])
    return [token for s in steps for token in s]+['EOF']

def percent_to_execution(row):
    """Fixed reference-encoding rule, never examines model correctness."""
    if row['call_id']=='Q003': return F(1),'average of displayed percentage-point tax rates; source table header'
    if '%' in row['answer'] and row.get('display_factor'):
        return F(row['display_factor']['exact']), 'T1 verified percent display factor'
    steps=row['steps']
    if any(op=='multiply' and 'const_100' in (a,b) for op,a,b in steps):
        # If a later divide by 100 exists, it restores fraction units.
        if steps[-1][0]=='divide' and steps[-1][2]=='const_100': return F(1,100),'terminal divide by 100'
        return F(1),'explicit gold multiplication by 100'
    # Subtracting displayed interest rates produces percentage points.
    if all(op in ('add','subtract') for op,_,_ in steps) and all('%' in p['raw'] for p in row['input_provenance'].values()):
        return F(1),'add/subtract displayed percentages'
    if row['call_id']=='Q245': return F(1),'source text percentages, difference in percentage points'
    return F(1,100),'fraction/ratio convention; no percentage-point encoding'

def is_percent(unit):
    return bool(re.search(r'percent|percentage|%',unit.lower()))

def scale_response(row,unit,overrides):
    if row['call_id'] in overrides:
        spec=overrides[row['call_id']]
        if 'reference_money_magnitude' in spec:
            u=unit.lower()
            if not re.search(r'dollar|usd|\$',u):raise ValueError('monetary conversion requires an explicitly monetary response unit')
            magnitude=10**9 if 'billion' in u else 10**6 if 'million' in u else 1000 if 'thousand' in u else 1
            return F(magnitude)/F(spec['reference_money_magnitude']),spec['reason']
        return F(spec['response_factor']),spec['reason']
    if is_percent(unit): return percent_to_execution(row)
    terminal=row['steps'][-1]
    if terminal[0]=='multiply' and 'const_1000000' in terminal[1:] and 'million' in unit.lower():
        return F(1000000),'response explicitly in millions; reference terminal conversion is to dollars'
    return F(1),'response uses numeric units of reference calculation (review explicit unit differences)'

def read_response(path):
    raw=path.read_text(encoding='utf8').strip()
    body=re.sub(r'^```(?:json)?\s*|\s*```$','',raw).strip()
    obj=json.loads(body)
    if not isinstance(obj,dict) or not all(k in obj for k in ('answer','unit','expression','explanation')):
        raise ValueError('missing response fields')
    return obj

def display_target(row):
    text=row['answer'].strip().replace(',','')
    text=re.sub(r'^\$\s*','',text)
    text=re.sub(r'\s+(?:million|billion|thousand)(?:\s+dollars)?$','',text,flags=re.I)
    if not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)\s*%?',text): return None
    pct=text.endswith('%')
    text=text.rstrip('%').strip()
    places=max(0,-Decimal(text).as_tuple().exponent)
    factor=percent_to_execution(row)[0] if pct or row['call_id'] in ('Q021','Q046') else F(1)
    # Missing % sign in a small set of human labels is a reference issue;
    # keep the written label, and do not silently repair its units.
    return fraction(text),places,factor

def round_places(x,places):
    power=F(10)**places
    return F(round(x*power))/power

def significant_digits(s):
    s=str(s).strip().replace(',','').lower()
    if not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?',s): return None
    mantissa=s.split('e')[0].lstrip('+-').replace('.','').lstrip('0')
    return len(mantissa) if mantissa else 1

def json_number(v): return {'exact':str(v),'decimal':float(v)}

def attainable(row,y,core):
    box={k:core.Interval(F(v['lo']['exact']),F(v['hi']['exact'])) for k,v in row['input_intervals'].items()}
    steps=row['steps']; center={k:v.midpoint for k,v in box.items()}
    enclosure=core.eval_interval(steps,box) # certifies no pole over this entire box
    hit=enclosure.lo<=y<=enclosure.hi
    out={'outer_hit':hit,'certified':False,'certificate':None}
    if not hit:return out
    midpoint=core.eval_scalar(steps,center)
    if y==midpoint:
        out.update(certified=True,certificate={'kind':'exact_center','inputs':{k:str(v) for k,v in center.items()}})
        return out
    names=sorted(box)
    points=[(midpoint,center)]
    shrink=F(10**12-1,10**12)
    for signs in itertools.product((-1,1),repeat=len(names)):
        p={k:box[k].midpoint+s*shrink*box[k].halfwidth for k,s in zip(names,signs)}
        points.append((core.eval_scalar(steps,p),p))
    lo,hi=min(points,key=lambda p:p[0]),max(points,key=lambda p:p[0])
    if lo[0]<=y<=hi[0]:
        out.update(certified=True,certificate={'kind':'continuous_segment_IVT','target':str(y),
          'left':{'value':str(lo[0]),'inputs':{k:str(v) for k,v in lo[1].items()}},
          'right':{'value':str(hi[0]),'inputs':{k:str(v) for k,v in hi[1].items()}},
          'continuity':'whole-box interval execution succeeds; every denominator excludes zero'})
    return out

def symbolic_match(row,tree,factor):
    import sympy as sp
    env={k:sp.Symbol(k) for k in row['input_provenance']}
    sub={F(p['value']):env[k] for k,p in row['input_provenance'].items()}
    if len(sub)!=len(env): return None  # same number in distinct semantic roles
    cast=lambda f:sp.Rational(f.numerator,f.denominator)
    pred=run_tree(tree,cast,sub)*cast(factor)
    prior=[]
    def arg(a):
        if a in env:return env[a]
        if a.startswith('#'):return prior[int(a[1:])]
        if a.startswith('const_'):a=a[6:].replace('m','-').replace('_','.')
        return cast(F(a))
    for op,a,b in row['steps']:
        x,z=arg(a),arg(b)
        prior.append({'add':lambda:x+z,'subtract':lambda:x-z,'multiply':lambda:x*z,'divide':lambda:x/z,'exp':lambda:x**z}[op]())
    return sp.cancel(pred-prior[-1])==0

def precision(row,answer,core):
    # Certified OUTER bound gives a conservative error-order budget, not a claim
    # of identical leading digits or an exact count of meaningful digits.
    e=row['relative_1pct']['enclosure']
    if not e:return {}
    lo,hi=F(e['lo']['exact']),F(e['hi']['exact'])
    c=F(row['center']['exact']); sig=significant_digits(answer)
    # T1A exact two-input growth theorem: R=(|a|*hb+|b|*ha)/(|a|*(|a|-ha)*|g|).
    # Accept either sign of (b-a)/a or b/a-1; a sign reversal preserves relative radius.
    st=row['steps'];growth=None
    if len(st) in (2,3):
        op,b,a=st[0]
        if op=='subtract' and st[1][:2]==['divide','#0'] and st[1][2] in (a,b):
            base=st[1][2];growth=(base,b if base==a else a)
        if op=='divide' and st[1]==['subtract','#0','const_1']:growth=(a,b)
        if op=='divide' and st[1]==['subtract','const_1','#0']:growth=(a,b)
        if len(st)==3 and not (st[2][0]=='multiply' and '#1' in st[2][1:] and 'const_100' in st[2][1:]):growth=None
    growth_budget=None;first_order_budget=None;bound_kind='T1 conservative outer interval'
    if growth and all(k in row['input_intervals'] for k in growth):
        a_name,b_name=growth
        a=F(row['input_provenance'][a_name]['value']);b=F(row['input_provenance'][b_name]['value'])
        ha=F(row['input_provenance'][a_name]['half']);hb=F(row['input_provenance'][b_name]['half'])
        if a_name!=b_name and abs(a)>ha and a!=b:
            radius=(abs(a)*hb+abs(b)*ha)/(abs(a)*(abs(a)-ha)*abs(b/a-1))
            eps=float(radius);growth_budget=-math.log10(eps)
            first_order_budget=-math.log10(float(radius*(1-ha/abs(a))))
            bound_kind='T1A exact growth relative radius'
        else:growth=None
    if not c or lo<=0<=hi:return {'reported_significant_digits':sig,'error_order_digits':None,'excess_digits':None}
    if growth_budget is None:eps=float(max(abs(lo-c),abs(hi-c))/abs(c))
    budget=-math.log10(eps) if eps>0 else None
    # A rounded k-significant-digit value has worst-case relative error at most
    # 5*10^-k; use this conventional threshold and state it explicitly.
    k=max(0,math.floor(math.log10(5/eps))) if eps>0 else None
    return {'reported_significant_digits':sig,'relative_radius_bound':eps,'bound_kind':bound_kind,
            't1a_precision_budget':growth_budget,'error_order_digits':budget,
            't1a_first_order_budget':first_order_budget,
            'excess_over_t1a_budget':sig-growth_budget if sig is not None and growth_budget is not None else None,
            'excess_over_t1a_first_order_budget':sig-first_order_budget if sig is not None and first_order_budget is not None else None,
            'conservative_significant_digit_budget':k,'excess_digits':max(0,sig-k) if sig is not None and k is not None else None}

def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec)
    sys.modules[name]=mod; spec.loader.exec_module(mod); return mod

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--t1-dir',type=Path,default=ROOT.parents[2]/'proxy-tail/research/t1_rounding')
    args=ap.parse_args()
    core=load_module('t1c_interval_core',args.t1_dir/'interval_core.py')
    official=load_module('t1c_finqa_official',args.t1_dir/'data/finqa/evaluate.py')
    rows=json.loads((ROOT/'private/sample.json').read_text(encoding='utf8'))
    override_path=ROOT/'unit_overrides.json'
    overrides=json.loads(override_path.read_text(encoding='utf8')) if override_path.exists() else {}
    alt_path=ROOT/'alternative_values.json'
    alternatives=json.loads(alt_path.read_text(encoding='utf8')) if alt_path.exists() else []
    output=[]
    for r in rows:
        path=ROOT/'raw'/f'{r["call_id"]}.txt'
        if not path.exists(): continue
        o={k:r[k] for k in ('call_id','id','group','pair_id','category','question','answer','exe_ans','program')}
        o['page_id']=r['id'].rsplit('-',1)[0]
        dt=display_target(r)
        o['reference_display']=None if dt is None else {'target':str(dt[0]),'places':dt[1],'factor':str(dt[2]),
               'gold_center_rounds_to_human_answer':round_places(F(r['center']['exact'])/dt[2],dt[1])==round_places(dt[0],dt[1])}
        try:
            obj=read_response(path);o['response']=obj
            factor,why=scale_response(r,obj['unit'],overrides)
            o['normalization']={'factor':str(factor),'reason':why}
            y=fraction(obj['answer'])*factor
            tree=parse_expression(obj['expression'])
            exact=run_tree(tree)*factor
            normalized_tree=tree if factor==1 else ('multiply',tree,('number',factor))
            tokens=dsl_tokens(normalized_tree)
            invalid,execution_value=official.eval_program(tokens,[])
            if invalid:raise ValueError('official executor rejected arithmetic program')
            o.update(parse_status='ok',printed=json_number(y),expression_value=json_number(exact),
                     official_program=tokens,official_execution_value=execution_value,
                     same_source_symbolic_formula=symbolic_match(r,tree,factor))
            gold=F(str(r['exe_ans']))
            for name,value,official_value in [('printed',y,round(float(y),5)),('expression',exact,execution_value)]:
                o[name+'_scores']={'official':official_value==r['exe_ans'],
                   'relative_1pct':abs(value-gold)<=abs(gold)/100 if gold else value==0,
                   'display':None if dt is None else round_places(value/dt[2],dt[1])==round_places(dt[0],dt[1])}
                o[name+'_compatibility']=attainable(r,value,core)
            emitted_places=-Decimal(str(obj['answer']).replace(',','')).as_tuple().exponent
            o['printed_matches_expression_rounding']=round_places(exact/factor,emitted_places)==y/factor
            o['printed_only_rejection']=not o['printed_scores']['official'] and o['expression_scores']['official']
            o['output_quantization_only']=o['printed_only_rejection'] and o['printed_matches_expression_rounding']
            o['printed_arithmetic_discrepancy']=not o['printed_matches_expression_rounding'] and round(float(y),5)!=execution_value
            o['alternative_value_matches']=[a for a in alternatives if a['call_id']==r['call_id'] and F(a['alternative_value_exact'])==exact]
            o['precision']=precision(r,obj['answer'],core)
        except Exception as e:
            o['parse_status']='error';o['parse_error']=type(e).__name__+': '+str(e)
            for track in ('printed','expression'):
                o[track+'_scores']={'official':False,'relative_1pct':False,'display':None if dt is None else False}
        output.append(o)
    (ROOT/'scores.jsonl').write_text(''.join(json.dumps(o,ensure_ascii=False)+'\n' for o in output),encoding='utf8',newline='\n')
    print(json.dumps({'completed':len(output),'parse_status':dict(Counter(o['parse_status'] for o in output)),
      'official_expression_correct':sum(o.get('expression_scores',{}).get('official',False) for o in output)},indent=2))
    fields=['call_id','id','group','category','parse_status','question','answer','exe_ans','program','model_answer','unit','expression','normalization_factor','same_source_symbolic_formula','printed_official','expression_official','printed_1pct','expression_1pct','printed_display','expression_display','printed_box','expression_box','output_quantization_only']
    with (ROOT/'scores.csv').open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for o in output:
            flat={k:o[k] for k in fields if k in o}; response=o.get('response',{})
            flat.update(model_answer=response.get('answer'),unit=response.get('unit'),expression=response.get('expression'),normalization_factor=o.get('normalization',{}).get('factor'))
            for track in ('printed','expression'):
                for rule,key in [('official','official'),('1pct','relative_1pct'),('display','display')]:flat[track+'_'+rule]=o.get(track+'_scores',{}).get(key)
                flat[track+'_box']=o.get(track+'_compatibility',{}).get('certified')
            w.writerow(flat)

if __name__=='__main__':main()
