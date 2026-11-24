"""TAT-QA point-only binding and preregistered distribution prediction.

This module never constructs a rounding interval or evaluates box extrema.
The frozen forecast uses marginal precision/output distributions, not observed
per-question mantissas. Exact measurement lives in a different module.
"""
from __future__ import annotations
import ast, csv, json, math, re
from collections import Counter
from decimal import Decimal
from fractions import Fraction as F
from pathlib import Path
import sympy as sp

ROOT=Path(__file__).resolve().parent
NUM=re.compile(r'(?<![A-Za-z0-9_.])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|(?<![\w.])\.\d+')
SCALE={'thousand':1000,'million':1000000,'billion':1000000000}

def decimal_info(raw):
    d=Decimal(raw.replace(',','')); h=F(1,2)*F(10)**d.as_tuple().exponent
    sig=len(raw.replace(',','').replace('.','').lstrip('0')) or 1
    return F(d),h,sig

def sources(context,q):
    result=[]
    for i,row in enumerate(context['table']['table']):
        for j,cell in enumerate(row):
            hits=list(NUM.finditer(cell))
            if len(hits)!=1: continue
            hit=hits[0];v,h,k=decimal_info(hit.group())
            if 1900<=v<=2100 and not ('.' in hit.group() or '%' in cell): continue
            result.append(dict(value=str(v),half=str(h),sig=k,raw=cell,location=f'table:{i}:{j}',type='table'))
    selected={str(x) for x in q.get('rel_paragraphs',[])}
    for p in context['paragraphs']:
        if selected and str(p['order']) not in selected: continue
        for hit in NUM.finditer(p['text']):
            v,h,k=decimal_info(hit.group())
            if 1900<=v<=2100 and '.' not in hit.group(): continue
            result.append(dict(value=str(v),half=str(h),sig=k,raw=hit.group(),location=f"paragraph:{p['order']}:{hit.start()}",type='text'))
    return result

def bind(context,q,split):
    deriv=q['derivation'].strip().replace('−','-').replace('–','-').replace('×','*').replace('÷','/').replace('[','(').replace(']',')').replace('$','').replace('£','').replace('€','')
    if not deriv: raise ValueError('empty_derivation')
    if any(c in deriv for c in '<>='): raise ValueError('non_arithmetic_derivation')
    src=sources(context,q); literals={}; locations={}; prov={}; expr_parts=[];pos=0
    for match in NUM.finditer(deriv):
        expr_parts.append(deriv[pos:match.start()]);raw=match.group();value,_,_=decimal_info(raw)
        after=deriv[match.end():];unit=re.match(r'\s*(thousand|million|billion)s?\b',after,re.I)
        factor=F(SCALE[unit.group(1).lower()]) if unit else F(1)
        end=match.end()+(unit.end() if unit else 0)
        pct=re.match(r'\s*%',deriv[end:]);factor*=F(1,100) if pct else 1
        if pct:end+=pct.end()
        candidates=[s for s in src if F(s['value'])==value]
        table_candidates=[s for s in candidates if s['type']=='table']
        if table_candidates:candidates=table_candidates
        key=(value,factor)
        if key in literals: token=literals[key]
        elif not candidates:
            if value not in {0,1,2,3,4,5,6,7,8,9,10,12,100,1000,1000000,1000000000}:raise ValueError('source_not_found')
            token=str(value*factor)
        else:
            if len(candidates)!=1:raise ValueError('source_identity_ambiguous')
            source=candidates[0]; loc=source['location']
            if loc not in locations:
                name=f'x{len(prov)}';locations[loc]=name
                prov[name]={**source,'value':str(value),'half':source['half']}
            token=locations[loc]
            if factor!=1:token=f'({token}*{factor})'
        literals[key]=token;expr_parts.append(token);pos=end
    expr_parts.append(deriv[pos:]);prepared=''.join(expr_parts)
    if re.search(r'[A-WYZa-wyz_]',prepared):raise ValueError('unsupported_expression_text')
    names={k:sp.Symbol(k) for k in prov};steps=[]
    def add(op,left,right):
        steps.append((op,left,right));return '#'+str(len(steps)-1)
    def parse(node):
        if isinstance(node,ast.Name) and node.id in names:return node.id
        if isinstance(node,ast.Constant) and isinstance(node.value,(int,float)):
            return str(F(str(node.value)))
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.USub,ast.UAdd)):
            arg=parse(node.operand);return add('subtract','0',arg) if isinstance(node.op,ast.USub) else arg
        if isinstance(node,ast.BinOp) and isinstance(node.op,(ast.Add,ast.Sub,ast.Mult,ast.Div)):
            return add({ast.Add:'add',ast.Sub:'subtract',ast.Mult:'multiply',ast.Div:'divide'}[type(node.op)],parse(node.left),parse(node.right))
        raise ValueError('unsupported_ast')
    try: out=parse(ast.parse(prepared,mode='eval').body)
    except (SyntaxError,ValueError): raise ValueError('unsupported_ast')
    if not prov:raise ValueError('no_bound_inputs')
    vals={k:F(v['value']) for k,v in prov.items()}
    def run(symbolic=False):
        outs=[]
        def val(token):return (names[token] if symbolic else vals[token]) if token in names else outs[int(token[1:])] if token.startswith('#') else sp.Rational(token) if symbolic else F(token)
        for op,a,b in steps:
            aa,bb=val(a),val(b);outs.append({'add':lambda:aa+bb,'subtract':lambda:aa-bb,'multiply':lambda:aa*bb,'divide':lambda:aa/bb}[op]())
        return outs[-1]
    center=run();expression=sp.cancel(run(True));gold=F(str(q['answer']))
    factor=F(1)
    if q['scale']=='percent':
        # TAT-QA formulas mix percent-point literals with unitless fractions.
        # Choose only documented percent normalization, never fitted scaling.
        factor=min((F(1),F(100)),key=lambda z:abs(center*z-gold))
    elif re.search(r'\b(thousand|million|billion)',deriv,re.I):factor=F(1,SCALE.get(q['scale'],1))
    if factor!=1:
        steps.append(('multiply','#'+str(len(steps)-1),str(factor)));expression*=sp.Rational(factor);center*=factor
    base=dict(id=q['uid'],table_id=context['table']['uid'],split=split,question=q['question'],derivation=q['derivation'],scale=q['scale'],gold=str(gold),center=str(center),steps=steps,input_provenance=prov,expression=str(expression),output_factor=str(factor))
    kind='other';prediction_group=None;params={}
    if len(names)==2:
        for a in names:
            b=next(n for n in names if n!=a);aa,bb=names[a],names[b]
            slope=sp.cancel(sp.diff(expression,bb)*aa);offset=sp.cancel(expression-slope*bb/aa)
            if not slope.free_symbols and not offset.free_symbols and slope:
                if offset and sp.cancel(slope+offset)==0:
                    kind='growth';r=vals[b]/vals[a]
                    if r>0 and r!=1:
                        prediction_group='growth';params=dict(r=float(r),ka=prov[a]['sig'],kb=prov[b]['sig'],baseline=a)
                    break
                if offset==0:
                    kind='ratio';r=abs(vals[b]/vals[a])
                    if r:
                        prediction_group='ratio';params=dict(r=float(r),ka=prov[a]['sig'],kb=prov[b]['sig'],baseline=a)
                    break
    derivatives={k:sp.diff(expression,s) for k,s in names.items()}
    if all(not v.free_symbols for v in derivatives.values()):
        radius=sum(abs(F(str(v)))*F(prov[k]['half']) for k,v in derivatives.items())
        kind='difference' if any(v<0 for v in derivatives.values()) else 'sum'
        prediction_group=kind;params=dict(radius=str(radius),magnitude=str(abs(center)))
    if kind=='other':
        if any(op=='divide' for op,_,_ in steps):kind='ratio_other'
        elif any(op=='subtract' for op,_,_ in steps):kind='difference_other'
    base.update(category=kind,prediction_group=prediction_group,prediction_parameters=params)
    return base

def prepare():
    rows=[];excluded=[];counts=Counter()
    for split in ['train','dev','test']:
        data=json.loads((ROOT/'data/tatqa'/f'{split}.json').read_text(encoding='utf-8'))
        for context in data:
            for q in context['questions']:
                if q['answer_type']!='arithmetic':continue
                counts[split]+=1
                try: rows.append(bind(context,q,split))
                except Exception as e:
                    reason=str(e) if isinstance(e,ValueError) else type(e).__name__
                    excluded.append(dict(id=q['uid'],split=split,question=q['question'],derivation=q.get('derivation'),reason=reason))
    for filename,data in [('tatqa_bound_points.jsonl',rows),('tatqa_excluded.jsonl',excluded)]:
        (ROOT/filename).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in data),encoding='utf-8')
    print(json.dumps(dict(total=dict(counts),bound=len(rows),excluded=dict(Counter(x['reason'] for x in excluded)),categories=dict(Counter(r['category'] for r in rows)))))
    return rows

def mantissa_probability(r,ka,kb,kind,tau=.01):
    """Analytical loguniform integral; no observed mantissa is an argument."""
    ha=.5*10.**(1-ka);points=[1.,10.]
    for e in range(math.floor(math.log10(r))-1,math.floor(math.log10(10*r))+2):
        x=10.**e/r
        if 1<x<10:points.append(x)
    points=sorted(set(points));mass=0
    denominator=abs(r-1) if kind=='growth' else r
    for left,right in zip(points,points[1:]):
        mid=(left+right)/2;hb=.5*10.**(math.floor(math.log10(r*mid))-kb+1)
        boundary=ha+(hb+r*ha)/(tau*denominator)
        mass+=math.log10(min(right,max(left,boundary))/left)
    return mass

def predict(rows):
    result={};curve=[]
    for group in ['growth','difference','ratio','sum']:
        sub=[r for r in rows if r['prediction_group']==group];n=len(sub)
        if not n:continue
        if group in ('growth','ratio'):
            pairs=Counter((r['prediction_parameters']['ka'],r['prediction_parameters']['kb']) for r in sub)
            outputs=Counter(r['prediction_parameters']['r'] for r in sub)
            total=sum(nk*ng*mantissa_probability(r,ka,kb,group) for (ka,kb),nk in pairs.items() for r,ng in outputs.items())/(n*n)
            for k in sorted(set(ka for ka,kb in pairs)):
                selected={p:c for p,c in pairs.items() if p[0]==k};nk=sum(selected.values())
                prob=sum(c*ng*mantissa_probability(r,ka,kb,group) for (ka,kb),c in selected.items() for r,ng in outputs.items())/(nk*n)
                curve.append(dict(category=group,k=k,n=nk,prediction=prob))
            signatures=dict(precision_pairs={f'{a},{b}':c for (a,b),c in pairs.items()},output_ratio_marginal={str(g):c for g,c in outputs.items()})
        else:
            radii=Counter(F(r['prediction_parameters']['radius']) for r in sub)
            magnitudes=Counter(F(r['prediction_parameters']['magnitude']) for r in sub)
            total=sum(nr*ny*(rad>y/100) for rad,nr in radii.items() for y,ny in magnitudes.items())/(n*n)
            signatures=dict(radius_marginal={str(v):c for v,c in radii.items()},answer_magnitude_marginal={str(v):c for v,c in magnitudes.items()})
        result[group]=dict(n=n,prediction=total,statistics=signatures)
    n=sum(v['n'] for v in result.values());overall=sum(v['n']*v['prediction'] for v in result.values())/n
    summary=dict(stage='prediction_only_no_measured_intervals',bound=len(rows),forecast_supported=n,unsupported=len(rows)-n,prediction=overall,by_category=result,curve=curve)
    (ROOT/'part3_prediction.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# TAT-QA frozen prediction: measurement not yet computed','',
      'Source level: our experiment (point values, displayed precision, and answer distribution only; no TAT-QA rounding-box range had been computed when this file was generated).',
      '',f'Input: the official pinned TAT-QA version `870accc41953dcde885aabeb963d94aabdc0fbc3`, train/dev/test_gold. 6,960 arithmetic questions; {len(rows)} conservatively bound; the prediction definition covers {n}.',
      '', '| Type | Questions | Predicted 1% out-of-tolerance rate |','|---|---:|---:|']
    for k,v in result.items():lines.append(f"| {k} | {v['n']} | {v['prediction']:.6%} |")
    lines.extend([f'| Total (population the prediction applies to) | {n} | {overall:.6%} |','',
      'Growth rates follow T1a: the empirical joint distribution of significant-digit pairs is taken as independent of the growth-magnitude marginal, the base-period mantissa is log-uniform on [1,10), and the exact two-number growth rule is integrated. Ratios use the same mantissa model with the ratio magnitude fixed, integrating the error rule for same-sign absolute quantities. The prediction function does not receive per-question mantissas.',
      '', 'The radius of differences and linear sums is determined by the displayed half last-digit units and the known linear coefficients; the empirical distribution of radii is mixed independently with the empirical distribution of absolute answer values to compute the share with R > 0.01 |y|, without reading the per-question correspondence. The independence in this extension is an assumption; no parameter was fitted.',
      '', f'Another {len(rows)-n} bound non-standard/nonlinear questions have no frozen population prediction; they are still audited later and reported separately. Passing the threshold on the applicable population must not be written up as all arithmetic questions passing.',
      '', 'The main comparison uses the same applicable population, first defining the 1% tolerance on the program center value (the prediction assumes the standard answer equals the value computed from the displayed numbers), and also reports a sensitivity result with the annotated answer as the center. Output magnitude is converted only by percent/explicit units; offsets between the annotation and the center are kept.',
      '', 'Source binding: each number in a formula corresponds to a single table cell; when there is no table match, a single number in the relevant paragraph is used. Identical formula numbers share a variable only when they correspond to a single source; duplicate sources or precision conflicts are excluded. Formula numbers without a source that are 0–10, 12, 100, or decimal unit multiples are treated as explicit structural constants; the rest are excluded. This convention is a conditional rounding audit and does not claim that all integers were actually rounded.',
      '', 'Acceptance, frozen: the population prediction and the measurement differ by no more than 5 percentage points, and the first-order decision agreement rate on the same population is at least 95%. Per-operation-type differences, the fully bound population, and coverage of all arithmetic questions are all reported at the same time.'])
    (ROOT/'part3_prediction.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:{kk:vv for kk,vv in v.items() if kk!='statistics'} for k,v in result.items()}));print('OVERALL',n,overall)

if __name__=='__main__':predict(prepare())
