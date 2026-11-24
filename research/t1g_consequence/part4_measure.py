"""Reviewed duplicate disclosures: exact program source replacement.

Each substitution changes one semantic input. Other displayed inputs remain
fixed; a univariate rational range is stronger than merely using an interval
enclosure. Does not call an answer-generating model.
"""
from __future__ import annotations
import ast,csv,gzip,json,sys,re
from collections import Counter,defaultdict
from fractions import Fraction as F
from pathlib import Path
import sympy as sp
from part4_duplicates import ROOT,OLD,SCALE,number,contexts,review_stratum,jsonl
sys.path.insert(0,str(OLD))
from analyze import bind,PROGRAM

# AI semantic review of every member of the two explicitly defined strata.
# IDs refer to the full semantic/unit scan, never to a numeric proximity list.
SINGLE_YES=set('''p12275 p12408 p12410 p14503 p18038 p18260
p24124 p24717 p25357 p25453 p27164 p27180 p27196 p29461 p29640
p30928 p32834 p34233 p34236 p34970 p35496 p36064 p37866 p39116
p39719 p41426 p41427 p42076 p42112 p43054 p43209 p43462 p44774
p44805 p48164 p48513 p49803 p50005'''.split())
COPULA_YES=set('''p03393 p08107 p08316 p08326 p09269 p09726 p10481 p10532
p11766 p11768 p11823 p12122 p12277 p12291 p12294 p12329 p12332
p12423 p12436 p12468 p12483 p12486 p12647 p12761 p12790 p12958
p12968 p13635 p14408 p14720 p18756 p18804 p18822 p18834 p19297
p20091 p20093 p20148 p20548
p24173 p25065 p25345 p25355 p25365 p26673 p26705 p26736 p29801
p30434 p32017 p32069 p32131 p32185 p32246 p32299 p33776 p33779
p35438 p38465 p38471 p40065 p40504 p40525 p42138 p42162 p42184
p42221 p42877 p43832 p43904 p43991 p44013 p44265 p44290 p44316
p44384 p44402 p44833 p44856 p45821 p46253 p46292 p46783 p46829
p46854 p48875 p49835 p49859'''.split())
UNRESOLVED={'p02283':'Original issue amount and year-end balance of the same security; there is no evidence yet that the period is the same.','p12933':"The full text's retained interests may be broader in scope than the table's interest-only; the quantities cannot be identified as the same from the names alone."}
REASONS={
'p12603':'The table gives the net carrying amount after the allowance for loan losses; the full text gives fair value.',
'p12650':'2015 pre-tax earnings of an adjacent business segment; cannot be bound across segments to this table.',
'p37885':"The full text's 1.7m is the gross impairment, with a separate recovery of 1.0m; the table's 651k is the net amount.",
'p39462':"The full text's three years are 2019, 2018, 2017 in that order; 102.4m belongs to 2018, not 2017.",
'p40065':'2019 income tax expense in the table and 2019 income tax expense in the full text; the unit is established by the header in thousands; any precision incompatibility is kept.',
'p42076':'The same 2018 fair-value adjustment of contingent consideration for the Brink acquisition; 450k and 0.5m sit on the boundary of the coarse box and were not filtered out.',
'p24717':'A footnote states explicitly that 2018 plant start-up costs were reclassified; the table still lists the original 2018 Plant start-up costs, and footnote (2) refers to the same item.',
}

def loadrows(path):
    if path.suffix=='.gz':
        with gzip.open(path,'rt',encoding='utf8') as f:return [json.loads(x) for x in f if x.strip()]
    return [json.loads(x) for x in path.read_text(encoding='utf8').splitlines() if x.strip()]

def old_review():
    candidates=list(csv.DictReader((OLD/'duplicate_precision_test_candidates.csv').open(encoding='utf8',newline='')))
    reviews=[]
    for r in csv.DictReader((OLD/'duplicate_precision_test_review_part1.csv').open(encoding='utf8',newline='')):
        c=candidates[int(r['candidate_pair'])-1];reviews.append((c,r['confirmed_same_fact'],r['reason']))
    for r in csv.DictReader((OLD/'duplicate_precision_test_review_part2.csv').open(encoding='utf8',newline='')):
        c=candidates[int(r['candidate_row'])-1];reviews.append((c,r['confirmed_same_fact'],r['reason']))
    return reviews

def reviewed():
    rows=loadrows(ROOT/'part4_candidates.jsonl.gz');index=defaultdict(list)
    for r in rows:index[(r['document_id'],r['row'],r['column'],r['table_unit'],r['text_location'],r['text_raw'])].append(r)
    for r in rows:
        stratum=review_stratum(r)
        if stratum:
            r['review_stratum']=stratum
            if r['pair_id'] in SINGLE_YES|COPULA_YES:
                r['status']='confirmed';r['reason']=REASONS.get(r['pair_id'],"Checked: same metric, period, and scope; the original table unit/sentence is in this row's evidence.")
            elif r['pair_id'] in UNRESOLVED:
                r['status']='unresolved';r['reason']=UNRESOLVED[r['pair_id']]
            else:
                r['status']='rejected';r['reason']=REASONS.get(r['pair_id'],'The amount named in the full text is a sub-item, a change amount, or a different metric/period or convention, and differs from the table quantity; the rejection is not based on the numeric difference.')
    imported=[]
    for c,status,reason in old_review():
        key=(c['filename'],int(c['row']),int(c['column']),c['table_unit_candidate'],c['text_location'],c['text_mention'])
        for r in index.get(key,[]):
            r['legacy_review']=True;r['legacy_review_reason']=reason
            if r['status']=='unreviewed':
                r['status']='confirmed' if status in ('true','yes') else 'rejected' if status in ('false','no') else 'unresolved'
                r['review_stratum']='legacy_T1_overlap_selected';r['reason']=reason
            imported.append(r['pair_id'])
    for r in rows:
        if r['status']=='confirmed':
            r['text_sign_normalization']=-1 if F(r['table_value'])<0 else 1
            r['signed_text_value']=str(F(r['text_value'])*r['text_sign_normalization'])
            # Explicit expense/loss/cash-use magnitudes are signed to the table
            # accounting convention after semantic review, not for matching.
            tv,pv=F(r['table_value']),F(r['signed_text_value']);th,ph=F(r['table_half']),F(r['text_half'])
            coarse,fine,ch=(tv,pv,th) if th>ph else (pv,tv,ph)
            r['fine_source_center_in_coarse_source_box']=coarse-ch<=fine<=coarse+ch
            r['source_boxes_intersect']=abs(tv-pv)<=th+ph
    jsonl(ROOT/'part4_reviewed_pairs.jsonl',[r for r in rows if r['status']!='unreviewed'])
    jsonl(ROOT/'part4_confirmed_pairs.jsonl',[r for r in rows if r['status']=='confirmed'])
    return rows

def program_expression(steps,values,variable):
    x=sp.Symbol('z',real=True);out=[]
    def val(t):
        if t==variable:return x
        if t in values:return sp.Rational(values[t])
        if t.startswith('#'):return out[int(t[1:])]
        if t.startswith('const_'):t=t[6:].replace('m1','-1')
        if t.endswith('%'):return sp.Rational(t[:-1])/100
        return sp.Rational(t)
    for op,a,b in steps:
        aa,bb=val(a),val(b)
        out.append({'add':lambda:aa+bb,'subtract':lambda:aa-bb,'multiply':lambda:aa*bb,'divide':lambda:aa/bb,'exp':lambda:aa**bb}[op]())
    return x,sp.cancel(out[-1])

def exact_range(expr,x,lo,hi):
    lo,hi=sp.Rational(lo),sp.Rational(hi)
    num,den=sp.fraction(expr)
    if sp.degree(den,x)>0 and any(lo<=z<=hi for z in sp.Poly(den,x).real_roots()):raise ValueError('coarse_box_contains_pole')
    dnum=sp.fraction(sp.cancel(sp.diff(expr,x)))[0]
    points=[lo,hi]
    if dnum!=0:points += [z for z in sp.Poly(dnum,x).real_roots() if lo<z<hi]
    ys=[expr.subs(x,p) for p in points]
    return min(ys),max(ys)

FINQA_MANUAL=set('''DXC/2018/page_56.pdf-1 DXC/2018/page_56.pdf-2 DXC/2018/page_56.pdf-3
GS/2013/page_63.pdf-1 MSI/2007/page_70.pdf-2 MSI/2007/page_70.pdf-3
MSI/2008/page_69.pdf-1 UNP/2011/page_24.pdf-2 MSI/2009/page_65.pdf-1
MSI/2009/page_65.pdf-2 MSI/2009/page_69.pdf-2 MSI/2009/page_69.pdf-3'''.split())
TATQA_MANUAL=set('''d0523c72-fe3c-4238-b564-aeb1baee3bff
2f68d64d-b509-4961-9d86-9a04afb7c35c e9ee1e78-8957-4be8-a10e-672ec4fe6dbe
55fde486-8d32-4749-9664-c256b7e0181d a06acbd3-4272-45db-8b75-3c373b244425
640f0a84-b1bf-44aa-92ae-84259399a208 08dd24d2-263e-404a-8a13-4f93034ef8f0
5d4b2ee2-c89b-47c6-bfca-1351f95947b9 2b0c326b-d144-4522-a918-4f509aa789f3
bc43b597-d752-448b-924d-21543a3880ec ce2cada8-d0e1-4334-a86e-9acc76f73cf8'''.split())

def ast_steps(expression):
    steps=[]
    def parse(n):
        if isinstance(n,ast.Name) and n.id=='manual':return 'manual'
        if isinstance(n,ast.Constant):return str(F(str(n.value)))
        if isinstance(n,ast.UnaryOp):
            t=parse(n.operand)
            if isinstance(n.op,ast.USub):steps.append(('subtract','0',t));return '#'+str(len(steps)-1)
            return t
        if isinstance(n,ast.BinOp):
            a,b=parse(n.left),parse(n.right);op={ast.Add:'add',ast.Sub:'subtract',ast.Mult:'multiply',ast.Div:'divide'}[type(n.op)]
            steps.append((op,a,b));return '#'+str(len(steps)-1)
        raise ValueError('invalid_manual_expression')
    parse(ast.parse(expression,mode='eval').body);return steps

def manual_binding(c,q,r):
    qid=q.get('id',q.get('uid'));tv=number(r['table_raw'])[0]
    if c['dataset']=='finqa':
        prog=q['qa']['program']
        if qid=='GS/2013/page_63.pdf-1':prog='add(911507, 938555), divide(#0, const_2)'
        steps=[(op,a.strip(),b.strip()) for op,a,b in PROGRAM.findall(prog)]
        tokens={t for _,a,b in steps for t in (a,b) if not t.startswith(('#','const_'))}
        target=next((t for t in tokens if not t.endswith('%') and F(t)==tv),None);mode='table'
        if target is None:
            target=next((t for t in tokens if not t.endswith('%') and F(t)==F(r['signed_text_value'])/SCALE[r['text_unit']]),None);mode='text'
        if target is None:return None
        loc=f"table_{r['row']}:{r['column']}" if mode=='table' else 'manual-text'
        prov={'manual':dict(value=str(F(target)),half='0',location=loc,context=r['text'] if mode=='text' else r['row_label'])}
        steps=[(op,'manual' if a==target else a,'manual' if b==target else b) for op,a,b in steps]
        return dict(id=qid,split=c['split'],question=q['qa']['question'],program=q['qa']['program'],steps=steps,input_provenance=prov,binding_method='manual_source_role_other_inputs_fixed')
    raw=q['derivation'].replace(',','').replace('$','').replace('£','').replace('€','')
    regex=r'(?<![\w.])'+re.escape(str(abs(tv)))+r'(?![\w.])'
    if not re.search(regex,raw):return None
    raw=re.sub(regex,'manual',raw);steps=ast_steps(raw)
    prov={'manual':dict(value=str(abs(tv)),half='0',location=r['table_location'],raw=r['table_raw'])}
    x,expr=program_expression(steps,{'manual':abs(tv)},'manual');center=expr.subs(x,sp.Rational(abs(tv)));gold=sp.Rational(str(q['answer']))
    if q['scale']=='percent' and abs(center*100-gold)<abs(center-gold):steps.append(('multiply','#'+str(len(steps)-1),'100'))
    return dict(id=qid,split=c['split'],question=q['question'],program=q['derivation'],steps=steps,input_provenance=prov,binding_method='manual_source_role_other_inputs_fixed')

def bindings(rows):
    result=defaultdict(list);fail=[]
    for c in contexts():
        if c['dataset']!='finqa':continue
        for q in c['questions']:
            try:
                steps,_,prov,_=bind(q)
                result[('finqa',c['id'])].append(dict(id=q['id'],split=q['split'],question=q['qa']['question'],program=q['qa']['program'],steps=steps,input_provenance=prov))
            except Exception as e:fail.append(dict(id=q['id'],reason=str(e)))
    for q in loadrows(ROOT/'part3_corrected_per_question.jsonl'):
        result[('tatqa',q['table_id'])].append(q)
    pairs=defaultdict(list)
    for r in rows:
        if r['status']=='confirmed':pairs[r['dataset'],r['document_id']].append(r)
    manual_log=[]
    for c in contexts():
        for q in c['questions']:
            qid=q.get('id',q.get('uid'))
            if qid=='PNC/2014/page_111.pdf-1':
                for r in pairs[c['dataset'],c['id']]:
                    if r['pair_id'] not in ('p19818','p19821'):continue
                    steps=[('subtract','manual','2.6')] if r['pair_id']=='p19818' else [('subtract','2.6','manual')]
                    rr=dict(id=qid,split=c['split'],question=q['qa']['question'],program=q['qa']['program'],steps=steps,input_provenance={'manual':dict(value='13/5',half='1/20',location='manual-distinct-period-role',context=r['text'],pair_id=r['pair_id'])},binding_method='manual_separate_year_roles')
                    result[c['dataset'],c['id']].append(rr);manual_log.append(dict(pair_id=r['pair_id'],**rr))
                continue
            if qid not in FINQA_MANUAL|TATQA_MANUAL:continue
            for r in pairs[c['dataset'],c['id']]:
                rr=manual_binding(c,q,r)
                if rr:
                    # The targeted formula/source was read explicitly above.
                    result[c['dataset'],c['id']].append(rr);manual_log.append(dict(pair_id=r['pair_id'],**rr))
    jsonl(ROOT/'part4_manual_bindings.jsonl',manual_log)
    jsonl(ROOT/'part4_binding_exclusions.jsonl',fail)
    return result

def measure(rows):
    bound=bindings(rows);results=[];exclusions=[];seen={}
    for r in rows:
        if r['status']!='confirmed':continue
        related=bound[r['dataset'],r['document_id']];matched=[]
        for q in related:
            prov=q['input_provenance'];values={k:F(p['value']) for k,p in prov.items()}
            for name,p in prov.items():
                if p.get('pair_id') and p['pair_id']!=r['pair_id']:continue
                loc=p['location'];tableloc=f"table_{r['row']}:{r['column']}" if r['dataset']=='finqa' else r['table_location']
                native_table=number(r['table_raw'])[0];native_text=number(r['text_raw'].split()[0])[0]
                mode=None
                if loc==tableloc:
                    mode='table';factor=F(SCALE[r['table_unit']]);tableval=F(r['table_value'])/factor;textval=F(r['signed_text_value'])/factor
                    if values[name]==-tableval:tableval=-tableval;textval=-textval
                    if values[name]!=tableval:continue
                    original=tableval;alternative=textval;oh=F(r['table_half'])/factor;ah=F(r['text_half'])/factor
                elif r['dataset']=='finqa' and p.get('context')==r['text'] and abs(values[name])==abs(native_text):
                    mode='text';factor=F(SCALE[r['text_unit']]);textval=F(r['signed_text_value'])/factor;tableval=F(r['table_value'])/factor
                    if values[name]==-textval:tableval=-tableval;textval=-textval
                    if values[name]!=textval:continue
                    original=textval;alternative=tableval;oh=F(r['text_half'])/factor;ah=F(r['table_half'])/factor
                elif r['dataset']=='tatqa' and loc==r['text_location']+':'+str(r['text_offset']):
                    mode='text';factor=F(SCALE[r['text_unit']]);textval=abs(F(r['signed_text_value'])/factor);tableval=abs(F(r['table_value'])/factor)
                    if values[name]!=textval:continue
                    original=textval;alternative=tableval;oh=F(r['text_half'])/factor;ah=F(r['table_half'])/factor
                if not mode:continue
                matched.append(q['id']);key=(r['dataset'],q['id'],r['row_label'].strip().lower(),tuple(r['table_years']),str(original),str(alternative),str(ah))
                if key in seen:seen[key]['pair_ids'].append(r['pair_id']);continue
                try:
                    x,expr=program_expression(q['steps'],values,name)
                    coarse,fine,ch=(original,alternative,oh) if oh>ah else (alternative,original,ah)
                    cy,fy=expr.subs(x,sp.Rational(coarse)),expr.subs(x,sp.Rational(fine))
                    lo,hi=exact_range(expr,x,coarse-ch,coarse+ch)
                    relative=abs(cy-fy)/abs(fy) if fy else sp.oo if cy else sp.Integer(0)
                    out=dict(dataset=r['dataset'],split=q['split'],question_id=q['id'],question=q['question'],pair_ids=[r['pair_id']],input_variable=name,original_source=mode,original_input=str(original),alternative_input=str(alternative),coarse_input=str(coarse),fine_input=str(fine),coarse_half=str(ch),expression=str(expr),fine_answer=str(fy),coarse_answer=str(cy),relative_difference=str(relative),relative_difference_float=float(relative) if relative!=sp.oo else None,over_1pct=bool(relative>sp.Rational(1,100)),coarse_range_lo=str(lo),coarse_range_hi=str(hi),fine_answer_in_coarse_range=bool(lo<=fy<=hi),range_method='exact_univariate_rational_range_other_inputs_fixed',new_independent_scan=r.get('review_stratum')!='legacy_T1_overlap_selected')
                    results.append(out);seen[key]=out
                except Exception as e:exclusions.append(dict(pair_id=r['pair_id'],question_id=q['id'],reason=str(e)))
        r['analyzable_question_ids']=sorted(set(matched))
        r['question_binding_status']='matched' if matched else 'no_unique_bound_arithmetic_input_for_this_pair'
    jsonl(ROOT/'part4_confirmed_pairs.jsonl',[r for r in rows if r['status']=='confirmed'])
    jsonl(ROOT/'part4_question_results.jsonl',results);jsonl(ROOT/'part4_substitution_exclusions.jsonl',exclusions)
    joint=dict(dataset='finqa',question_id='PNC/2014/page_111.pdf-1',pair_ids=['p19818','p19821'],original_program='subtract(2.6, 2.6)',separate_role_fine_program='subtract(2.616, 2.572)',coarse_answer='0',fine_answer='11/250',relative_difference_to_fine='1',coarse_joint_range=['-1/10','1/10'],fine_answer_contained=True,note='Both year roles are substituted at the same time; supplementary only, not added to the single-input substitution denominator.')
    (ROOT/'part4_two_role_case.json').write_text(json.dumps(joint,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return results

def summary(rows,results):
    out={'scan':json.loads((ROOT/'part4_scan_counts.json').read_text()),'reviewed':dict(Counter(r['status'] for r in rows)),'by_dataset':{}}
    for dataset in ('finqa','tatqa'):
        rr=[r for r in rows if r['dataset']==dataset];pairs=[r for r in rr if r['status']=='confirmed'];qq=[q for q in results if q['dataset']==dataset]
        independent=[r for r in pairs if r.get('review_stratum')!='legacy_T1_overlap_selected'];iq=[q for q in qq if q['new_independent_scan']]
        finite=sorted(q['relative_difference_float'] for q in qq if q['relative_difference_float'] is not None)
        def quant(p):
            if not finite:return None
            pos=(len(finite)-1)*p;i=int(pos);return finite[i]+(finite[min(i+1,len(finite)-1)]-finite[i])*(pos-i)
        out['by_dataset'][dataset]=dict(semantic_reviewed=sum(r['status']!='unreviewed' for r in rr),confirmed_pairs=len(pairs),independent_confirmed_pairs=len(independent),legacy_only_confirmed_pairs=len(pairs)-len(independent),pair_fine_center_contained=sum(r['fine_source_center_in_coarse_source_box'] for r in pairs),independent_pair_fine_center_contained=sum(r['fine_source_center_in_coarse_source_box'] for r in independent),nonintersecting_confirmed_pair_ids=[r['pair_id'] for r in pairs if not r['source_boxes_intersect']],pairs_with_bound_questions=sum(bool(r.get('analyzable_question_ids')) for r in pairs),substitutions=len(qq),unique_questions=len({q['question_id'] for q in qq}),over_1pct=sum(q['over_1pct'] for q in qq),over_1pct_rate=sum(q['over_1pct'] for q in qq)/len(qq) if qq else None,coarse_answer_range_contains_fine=sum(q['fine_answer_in_coarse_range'] for q in qq),independent_substitutions=len(iq),independent_over_1pct=sum(q['over_1pct'] for q in iq),zero_fine_nonzero_coarse=sum(q['relative_difference_float'] is None for q in qq),relative_difference_quantiles={str(p):quant(p) for p in [0,.25,.5,.75,.9,.95,1]})
    (ROOT/'part4_summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(out,ensure_ascii=False,indent=2))
    if results:
        with (ROOT/'part4_question_results.csv').open('w',encoding='utf8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)

if __name__=='__main__':
    rows=reviewed();results=measure(rows);summary(rows,results)
