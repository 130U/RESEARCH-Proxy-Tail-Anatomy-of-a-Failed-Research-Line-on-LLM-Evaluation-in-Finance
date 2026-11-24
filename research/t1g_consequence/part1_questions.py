"""Link header-derived changes to source-bound standard QA expressions."""
from part1_changes import *
import sys, sympy as sp, ast
sys.path.insert(0,str(OLD))
import analyze as t1
sys.path.insert(0,str(OLD/'data/tatqa'))
import tatqa_utils
# Load the actual official scalar normalization function without its unrelated
# pandas reporting dependency. Its body is unchanged from the pinned source.
metric_ast=ast.parse((OLD/'data/tatqa/tatqa_metric.py').read_text(encoding='utf-8'))
metric_ns=dict(vars(tatqa_utils))
exec(compile(ast.Module(body=[n for n in metric_ast.body if isinstance(n,ast.FunctionDef) and n.name=='get_answer_str'],type_ignores=[]),'<official TAT-QA get_answer_str>','exec'),metric_ns)
official_answer_str=metric_ns['get_answer_str']

def symbolic(steps,prov):
    names={k:sp.Symbol(k) for k in prov};out=[]
    def get(s):
        if s in names:return names[s]
        if str(s).startswith('#'):return out[int(s[1:])]
        return sp.Rational(str(s).replace('const_m1','-1').replace('const_',''))
    for op,a,b in steps:
        aa,bb=get(a),get(b)
        if op=='add':v=aa+bb
        elif op=='subtract':v=aa-bb
        elif op=='multiply':v=aa*bb
        elif op=='divide':v=aa/bb
        else:raise ValueError('unsupported')
        out.append(v)
    return sp.cancel(out[-1]),names

def row_expression(q,r,table,ds,unique=True):
    """Source-row-limited fallback; admits only two unique numeric cell values.

    This does not certify overall semantics; both cells must occur uniquely in
    the full table and the expression must be algebraically identical to their
    change. Other literals remain constants, and every candidate stays auditable.
    """
    a,b=sp.symbols('A B');mapped={}
    for key,sym in [('base',a),('new',b)]:
        nn=number(r[key+'_raw']);v=nn['value'];unit=nn['unit'];rawv=v/unit
        occurrences=[(i,j) for i,row in enumerate(table) for j,c in enumerate(row) if number(c) and number(c)['value']/number(c)['unit']==rawv]
        if unique and len(occurrences)!=1:return None
        mapped[rawv]=sym/unit
        if '%' in r[key+'_raw']:mapped[rawv/100]=sym/(unit*100)
    if len(mapped)<2:return None
    if ds=='finqa':
        out=[]
        def get(tok):
            tok=tok.strip()
            if tok.startswith('#'):return out[int(tok[1:])]
            if tok.startswith('const_'):return sp.Rational(tok.replace('const_m1','-1').replace('const_',''))
            val=F(tok[:-1])/100 if tok.endswith('%') else F(tok);return mapped.get(val,sp.Rational(str(val)))
        for op,u,v in t1.PROGRAM.findall(q['program']):
            if op not in ['add','subtract','multiply','divide']:return None
            u,v=get(u),get(v);out.append({'add':lambda:u+v,'subtract':lambda:u-v,'multiply':lambda:u*v,'divide':lambda:u/v}[op]())
        if not out:return None
        expr=out[-1]
    else:
        import ast
        deriv=q['derivation'].replace(',','').replace('−','-').replace('×','*').replace('÷','/').replace('$','').replace('%','/100')
        def parse(n):
            if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)):
                v=F(str(n.value));return mapped.get(v,sp.Rational(str(v)))
            if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.USub):
                if isinstance(n.operand,ast.Constant):
                    v=-F(str(n.operand.value));return mapped.get(v,-parse(n.operand))
                return -parse(n.operand)
            if isinstance(n,ast.BinOp):
                u,v=parse(n.left),parse(n.right)
                if isinstance(n.op,ast.Add):return u+v
                if isinstance(n.op,ast.Sub):return u-v
                if isinstance(n.op,ast.Mult):return u*v
                if isinstance(n.op,ast.Div):return u/v
            raise ValueError('unsupported')
        try:expr=parse(ast.parse(deriv,mode='eval').body)
        except Exception:return None
        # Use the derivation convention for a dimensionless growth fraction.
        if q['scale']=='percent' and sp.cancel(expr/((b-a)/a)) in [1,-1]:expr*=100
    if expr.free_symbols!={a,b}:return None
    ref=b-a if r['kind']=='amount' else 100*(b/a-1)
    factor=sp.cancel(expr/ref)
    if factor.free_symbols:return None
    return factor

def main():
    allrows=json.loads((HERE/'part1_rows_all.json').read_text(encoding='utf-8'))
    bydoc=defaultdict(list)
    for r in allrows:
        if r['status']=='compatible':bydoc[r['dataset'],r['doc_id']].append(r)
    finqa={r['id']:r for r in map(json.loads,(OLD/'results/per_question.jsonl').read_text(encoding='utf-8').splitlines())}
    tatqa={r['id']:r for r in map(json.loads,(HERE/'tatqa_bound_points.jsonl').read_text(encoding='utf-8').splitlines())}
    results=[];denoms=[];bindings=[]
    for ds in ['finqa','tatqa']:
        for d in documents(ds):
            for q in d['questions']:
                prog=q.get('program',q.get('derivation',''))
                question=q['question']
                # Broad question-defined denominator does not depend on successful binding.
                keyword_change=bool(re.search(r'change|increas|decreas|growth|grew|declin|reduc|differen|\brise|\brisen|\bfell|\bfall',question,re.I))
                if ds=='finqa':
                    steps=[(op,u.strip(),v.strip()) for op,u,v in t1.PROGRAM.findall(prog)]
                    change=t1.category(steps) in ['growth','difference'] if steps else False
                else:
                    change=bool(re.search(r'[\d)%]\s*[-−–]|[-−–]\s*\(',prog))
                arithmetic=q.get('answer_type','arithmetic')=='arithmetic' and q.get('exe_ans','') not in ['yes','no']
                if change and arithmetic:denoms.append(dict(dataset=ds,id=q['id'],split=q['split'],question=question,program=prog,keyword_change=keyword_change))
                if not (change and arithmetic and bydoc[ds,d['doc_id']]):continue
                record=(finqa if ds=='finqa' else tatqa).get(q['id'])
                usable=record is not None and (ds!='finqa' or record.get('status')=='analyzed')
                try:e,names=symbolic(record['steps'],record['input_provenance']) if usable else (None,{})
                except Exception:e,names=None,{}
                p=record['input_provenance'] if usable else {}
                for r in bydoc[ds,d['doc_id']]:
                    loc_a=f"table_{r['row']}:{r['base_col']}" if ds=='finqa' else f"table:{r['row']}:{r['base_col']}"
                    loc_b=f"table_{r['row']}:{r['new_col']}" if ds=='finqa' else f"table:{r['row']}:{r['new_col']}"
                    a=next((names[k] for k,v in p.items() if v['location']==loc_a),None)
                    b=next((names[k] for k,v in p.items() if v['location']==loc_b),None)
                    binding='previous_source_binding'
                    if a is None or b is None:
                        factor=row_expression(q,r,d['table'],ds);binding='unique_table_cell_fallback'
                        if q['id']=='3c51553e-bb48-4a48-954f-768f8421ad28' and r['label'].lower()=='net assets':
                            factor=row_expression(q,r,d['table'],ds,unique=False)
                            binding='semantic_override_question_explicitly_names_net_assets_not_equity'
                        if factor is None:
                            potential=row_expression(q,r,d['table'],ds,unique=False)
                            if potential is not None and not potential.free_symbols:
                                bindings.append(dict(dataset=ds,id=q['id'],row=r['row'],label=r['label'],question=question,program=prog,factor=str(potential),reason='numeric_formula_matches_but_source_ambiguous'))
                            continue
                    else:
                        if ds=='tatqa':
                            a*=1 if F(r['base'])>=0 else -1;b*=1 if F(r['new'])>=0 else -1
                        ref=b-a if r['kind']=='amount' else (b/a-1)*100
                        factor=sp.cancel(e/ref)
                    if factor.free_symbols or factor not in [1,-1,sp.Rational(1,100),sp.Rational(-1,100),100,-100]:continue
                    cv=F(r['printed'])*F(str(factor));center=F(r['center'])*F(str(factor))
                    gold=F(str(q['exe_ans'])) if ds=='finqa' else F(str(q['answer']))
                    out=dict(dataset=ds,id=q['id'],doc_id=d['doc_id'],split=q['split'],question=question,program=prog,row=r['row'],label=r['label'],kind=r['kind'],base_raw=r['base_raw'],new_raw=r['new_raw'],printed_raw=r['change_raw'],factor=str(factor),printed_in_answer_unit=str(cv),recomputed=str(center),gold=str(gold),
                        relative_1pct_disagrees=abs(cv-gold)>abs(gold)/100,
                        printed_precision_disagrees=rounded(center,2*F(r['printed_half'])*abs(F(str(factor))))!=cv,
                        row_mismatch=r['mismatch'],binding=binding)
                    if ds=='finqa':
                        out['official_disagrees']=round(float(cv),5)!=q['exe_ans']
                        out['recomputed_official_pass']=round(float(center),5)==q['exe_ans']
                        acc=t1.display_acceptance(q['answer'],center)
                        if acc:
                            interval,fac=acc
                            out['human_display_disagrees']=not interval.lo<=cv<=interval.hi
                        else:out['human_display_disagrees']=None
                    else:
                        # Official scalar arithmetic normalization: round to 2 decimals,
                        # multiply declared scale, format %.4f, then normalize the number.
                        def official(v):return official_answer_str([str(float(v))],q['scale'])
                        out['official_disagrees']=official(cv)!=official(gold)
                        out['recomputed_official_pass']=official(center)==official(gold)
                        out['scale']=q['scale']
                    results.append(out)
    csvout(HERE/'part1_question_denominators.csv',denoms);csvout(HERE/'part1_questions.csv',results);dump(HERE/'part1_questions.json',results)
    csvout(HERE/'part1_question_binding_exclusions.csv',bindings)
    summary={}
    for ds in ['finqa','tatqa']:
        rr=[r for r in results if r['dataset']==ds];den=[r for r in denoms if r['dataset']==ds]
        def cnt(field):return len({r['id'] for r in rr if r.get(field)})
        summary[ds]=dict(change_question_denominator=len(den),matched_questions=len({r['id'] for r in rr}),official_disagree=cnt('official_disagrees'),official_rate=cnt('official_disagrees')/len(den),relative_1pct_disagree=cnt('relative_1pct_disagrees'),printed_precision_disagree=cnt('printed_precision_disagrees'),human_display_disagree=cnt('human_display_disagrees'),
            recomputation_pass_and_print_fail=len({r['id'] for r in rr if r['official_disagrees'] and r['recomputed_official_pass']}))
    dump(HERE/'part1_question_summary.json',summary);print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
