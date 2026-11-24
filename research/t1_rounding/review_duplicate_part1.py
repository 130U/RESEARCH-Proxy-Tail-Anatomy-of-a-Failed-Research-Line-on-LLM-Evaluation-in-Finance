"""Reproduce calculations for manually reviewed test candidate pairs 1--27.

Semantic labels below are an AI reading of the full benchmark page, not an
automatic same-value inference and not external expert adjudication.
"""
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
import csv
import json
from analyze import PROGRAM, display_acceptance
from interval_core import eval_scalar

HERE=Path(__file__).resolve().parent
# Tuple: confirmed_same_fact, reasoning. Unresolved is deliberately excluded
# from the confirmed lower bound.
REVIEWS={
1:("true","2013 labor-related deemed claim: footnote (1) explicitly refers to the table claim; units established in pre_text[8]."),
2:("false","Table explicitly excludes accrued interest (pre_text[13]); narrative liability includes accrued interest (pre_text[11]). Different metric."),
3:("true","December 3 1999 remaining restructuring accrual. post_text[10] says older merger accruals have no remaining balance, supporting the 1998-program equivalence."),
4:("true","2004 employee separation restructuring expense in both locations."),
5:("false","Table is 2005 employee separation expense; text 0.1 million refers to decrease in 2004 facility-closing liability."),
6:("false","Table is ending 2005 facility-closing liability; narrative is 2004 decrease, not ending balance."),
7:("unresolved","Same security but table is 2010 outstanding amount whereas narrative is original 2007 issuance; unchanged principal not established from this excerpt."),
8:("unresolved","Same security but table is 2009 outstanding amount whereas narrative is original 2007 issuance; not counted as same-period fact."),
9:("false","Table 2019 notes, narrative 2024 notes: different security."),
10:("false","Table 2019 notes carrying value, narrative 2024 notes original principal: different security and basis."),
11:("unresolved","Same 2024 security but table maturity amount at 2017 vs issuance principal in 2014; contractual amount may be exact, no precision inference counted."),
12:("false","Carrying value net of costs is not original principal."),
13:("false","Fair value is not original principal."),
14:("false","Table is December 2017 fair value; narrative explicitly December 2016."),
15:("true","Net sales of the discontinued plastics business in 2009; same business and year."),
16:("false","Narrative 3 billion is excluded credit-card interest/fees; table 3.0 is average credit-card receivables held for sale. Not the same metric."),
17:("true","2018 cost of services excluding depreciation, amortization and restructuring in both locations."),
18:("true","2017 cost of services excluding depreciation, amortization and restructuring in both locations."),
19:("true","2018 SG&A excluding depreciation, amortization and restructuring in both locations."),
20:("true","2017 SG&A excluding depreciation, amortization and restructuring in both locations."),
21:("false","Narrative 2.0 billion is SG&A excluding depreciation; table amount is depreciation and amortization itself."),
22:("true","Narrative directly introduces this table as June 2007 bond issuance amounts. Same original total, possibly exact contractual principal."),
23:("true","Total future operating-lease payments at May 28 2017; table annual components sum to 500.7 million."),
24:("true","Total assets at December 2013 in both table and narrative."),
25:("true","Compensation and benefits expense, year ended December 2014."),
26:("true","Compensation and benefits expense, year ended December 2013."),
27:("true","Compensation and benefits expense, year ended December 2012."),
}
# Each mapping was read against question, gold_inds and original cell labels.
# For a coarser-source gold program, use the finer alternative as well.
SUBSTITUTIONS=[
(1,"AAL/2015/page_114.pdf-1","1733","1700","coarse_for_fine",None),
(3,"ADBE/1999/page_64.pdf-3","772","800","coarse_for_fine",None),
(3,"ADBE/1999/page_64.pdf-2","0.8","0.772","fine_for_coarse",None),
(15,"BLL/2010/page_35.pdf-1","635","634.9","fine_for_coarse",None),
(15,"BLL/2010/page_35.pdf-2","634.9","635","coarse_for_fine",None),
(15,"BLL/2010/page_35.pdf-3","634.9","635","coarse_for_fine",None),
(17,"DXC/2018/page_56.pdf-1","17944","17900","coarse_for_fine",None),
(17,"DXC/2018/page_56.pdf-3","17944","17900","coarse_for_fine",None),
(19,"DXC/2018/page_56.pdf-2","2010","2000","coarse_for_fine",None),
(24,"GS/2013/page_63.pdf-1","911507","911510","coarse_for_fine","add(911507, 938555), divide(#0, 2)"),
(24,"GS/2013/page_63.pdf-2","911507","911510","coarse_for_fine",None),
]

def write(path, rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n')
        w.writeheader();w.writerows(rows)

def main():
    records={x['id']:x for x in json.loads((HERE/'data/finqa/test.json').read_text(encoding='utf-8'))}
    candidates=list(csv.DictReader((HERE/'duplicate_precision_test_candidates.csv').open(encoding='utf-8')))
    substitutions=[]
    for pair,qid,old,new,direction,rewrite in SUBSTITUTIONS:
        qa=records[qid]['qa']
        steps=[(op,a.strip(),b.strip()) for op,a,b in PROGRAM.findall(rewrite or qa['program'])]
        original=eval_scalar(steps,{})
        alternative=eval_scalar(steps,{old:F(new)})
        gold=F(str(qa['exe_ans']))
        assert abs(original-gold)<=F(1,200000),(qid,original,gold)
        band=abs(gold)/100
        display=display_acceptance(qa['answer'],original)
        def dclass(x):
            if display is None:return 'unavailable'
            lo,hi=display[0].lo,display[0].hi
            if x==lo or x==hi:return 'boundary_tie'
            return 'outside' if x<lo or x>hi else 'inside'
        substitutions.append(dict(candidate_pair=pair,question_id=qid,source_direction=direction,original_program=qa['program'],expanded_table_program=rewrite or '',old_operand=old,new_operand=new,gold_answer=qa['answer'],original_result=str(original),alternative_result=str(alternative),original_decimal=float(original),alternative_decimal=float(alternative),nominal_relative_change=float(abs(alternative-original)/abs(original)),original_1pct_inside=abs(original-gold)<=band,alternative_1pct_inside=abs(alternative-gold)<=band,display_original=dclass(original),display_alternative=dclass(alternative)))
    reviewed=[]
    for pair in range(1,28):
        c=candidates[pair-1]
        state,reason=REVIEWS[pair]
        s=[r for r in substitutions if r['candidate_pair']==pair]
        c.update(candidate_pair=pair,confirmed_same_fact=state,question_ids=';'.join(r['question_id'] for r in s),coarse_center_cross_1pct=';'.join(r['question_id'] for r in s if r['source_direction']=='coarse_for_fine' and r['original_1pct_inside'] and not r['alternative_1pct_inside']),coarse_center_cross_display=';'.join(r['question_id'] for r in s if r['source_direction']=='coarse_for_fine' and r['display_original']=='inside' and r['display_alternative']=='outside'),alternative_source_cross_1pct=';'.join(r['question_id'] for r in s if r['original_1pct_inside'] and not r['alternative_1pct_inside']),alternative_source_cross_display=';'.join(r['question_id'] for r in s if r['display_original']=='inside' and r['display_alternative']=='outside'),reason=reason)
        reviewed.append(c)
    write(HERE/'duplicate_precision_test_review_part1.csv',reviewed)
    write(HERE/'duplicate_precision_test_substitutions_part1.csv',substitutions)
    print('Manual candidate labels',Counter(r['confirmed_same_fact'] for r in reviewed))
    print('confirmed pages',len({r['filename'] for r in reviewed if r['confirmed_same_fact']=='true'}))
    print('confirmed affected questions',len(substitutions))
    print('1pct source substitution crossing',sum(r['original_1pct_inside'] and not r['alternative_1pct_inside'] for r in substitutions))
    print('display source substitution crossing',sum(r['display_original']=='inside' and r['display_alternative']=='outside' for r in substitutions))
    for r in substitutions: print(r['question_id'],r['source_direction'],r['original_decimal'],r['alternative_decimal'],r['alternative_1pct_inside'],r['display_alternative'])

if __name__=='__main__':main()
