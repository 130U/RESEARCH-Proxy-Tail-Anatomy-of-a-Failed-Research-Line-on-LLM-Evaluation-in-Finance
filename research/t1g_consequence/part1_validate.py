"""Arithmetic invariants and all stored row extrema, without model calls."""
from part1_changes import *
import sys,importlib.util

def main():
    assert probability_between(F(100),F(110),F(1,2),F(1,2),'amount',F(19,2),F(21,2))==F(3,4)
    assert probability_between(F(100),F(110),F(1,2),F(1,2),'amount',F(9),F(11))==1
    rows=json.loads((HERE/'part1_rows_all.json').read_text(encoding='utf-8'));checked=0
    for r in rows:
        if r.get('box_status') not in ['compatible','nonintersection']:continue
        a,b,c=map(F,[r['base'],r['new'],r['printed']]);ha,hb,hc=map(F,[r['base_half'],r['new_half'],r['printed_half']])
        fn=(lambda x,y:y-x) if r['kind']=='amount' else (lambda x,y:100*(y/x-1))
        values=[fn(x,y) for x,y in product([a-ha,a+ha],[b-hb,b+hb])]
        assert min(values)==F(r['lo']) and max(values)==F(r['hi'])
        for k in ['low_witness','high_witness']:
            w=r[k];value=fn(F(w['base']),F(w['new']))
            assert value==F(r['lo'] if k=='low_witness' else r['hi'])
        assert (max(min(values),c-hc)<=min(max(values),c+hc))==(r['box_status']=='compatible')
        assert 0<=r['mismatch_probability']<=1
        checked+=1
    spec=importlib.util.spec_from_file_location('official_finqa',OLD/'data/finqa/evaluate.py');official=importlib.util.module_from_spec(spec);spec.loader.exec_module(official)
    qr=json.loads((HERE/'part1_questions.json').read_text(encoding='utf-8'));score_n=0
    for r in qr:
        if r['dataset']!='finqa':continue
        value=float(F(r['printed_in_answer_unit']));err,output=official.eval_program(official.program_tokenization(f'add({value}, const_0)'),[])
        assert not err and (output!=float(F(r['gold'])))==r['official_disagrees'];score_n+=1
    result=dict(row_extrema_and_witnesses_checked=checked,official_finqa_scores_checked=score_n,uniform_difference_probability_exact='1/4',status='passed')
    dump(HERE/'part1_validation.json',result);print(result)

if __name__=='__main__':main()
