"""Join printed-change matches to existing T1c/T1d responses; no model calls.

Re-run after part1_questions.json changes. T1d condition A reuses T1c and is
counted once. Selection is numeric evidence, not a claim about private reasoning.
"""
from __future__ import annotations
import csv,json
from collections import Counter
from decimal import Decimal
from fractions import Fraction as F
from pathlib import Path

ROOT=Path(__file__).resolve().parent
WORKSPACE=ROOT.parents[2]

def load_jsonl(path):return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
def exact(value):
    if value is None:return None
    if isinstance(value,dict):value=value.get('exact')
    try:return F(str(value))
    except (ValueError,TypeError,ZeroDivisionError):return None

def official_equal(a,b):
    return None if a is None or b is None else round(float(a),5)==round(float(b),5)

def classify(value,printed,recomputed):
    if value is None:return 'unparsed','no_numeric_value'
    p=value==printed;r=value==recomputed
    if p or r:return ('both' if p and r else 'printed' if p else 'recomputed'),'exact_expression'
    p=official_equal(value,printed);r=official_equal(value,recomputed)
    if p or r:return ('both' if p and r else 'printed' if p else 'recomputed'),'same_official_5decimal_value'
    return 'other','neither_exact_nor_officially_equal'

def main():
    candidates=json.loads((ROOT/'part1_questions.json').read_text(encoding='utf-8'))
    cpath=WORKSPACE/'proxy-tail-t1c/research/t1c_models/scores.jsonl'
    dpath=WORKSPACE/'proxy-tail-t1d/research/t1d_precision/per_response.jsonl'
    c=load_jsonl(cpath);d=load_jsonl(dpath);answers={}
    for item in c:
        answers[(item['id'],'A')]=dict(id=item['id'],condition='A',model='T1c original run; serving identity unavailable',
            answer=item.get('response',{}).get('answer'),expression=item.get('response',{}).get('expression'),
            normalized_answer=exact(item.get('printed')),normalized_expression=exact(item.get('expression_value')),
            official_expression_correct=item.get('expression_scores',{}).get('official'),
            official_answer_correct=item.get('printed_scores',{}).get('official'),
            call_id=item.get('call_id'),source=str(cpath))
    for item in d:
        condition=item.get('condition','unknown');key=(item['id'],condition)
        # A is exactly the T1c response carried into T1d, not an independent run.
        if condition=='A' and key in answers:continue
        factor=exact(item.get('official_normalization',{}).get('factor','1'))
        value=exact(item.get('answer'));expression=exact(item.get('center'))
        value=value*factor if value is not None and factor is not None else None
        expression=expression*factor if expression is not None and factor is not None else None
        answers[key]=dict(id=item['id'],condition=condition,model=item.get('model'),answer=item.get('answer'),expression=item.get('expression'),
            normalized_answer=value,normalized_expression=expression,
            official_expression_correct=item.get('official_expression_correct'),official_answer_correct=None,
            call_id=item.get('call_id'),source=str(dpath))
    rows=[];finqa=[q for q in candidates if q['dataset']=='finqa'];affected=[q for q in finqa if q.get('official_disagrees')]
    for q in finqa:
        printed=exact(q['printed_in_answer_unit']);recomputed=exact(q['recomputed']);gold=exact(q['gold'])
        for (qid,condition),answer in answers.items():
            if qid!=q['id']:continue
            chosen,method=classify(answer['normalized_expression'],printed,recomputed)
            # If parsing failed, reported answer is weaker evidence and marked so.
            if chosen=='unparsed':chosen,method=classify(answer['normalized_answer'],printed,recomputed);method='reported_answer:'+method
            rows.append(dict(id=qid,split=q['split'],question=q['question'],kind=q['kind'],printed_raw=q['printed_raw'],
                printed_in_answer_unit=str(printed),recomputed=str(recomputed),gold=str(gold),
                officially_affected=bool(q.get('official_disagrees')),relative_1pct_affected=bool(q.get('relative_1pct_disagrees')),
                row_mismatch=bool(q.get('row_mismatch')),condition=condition,model=answer['model'],
                answer=answer['answer'],expression=answer['expression'],
                normalized_answer=str(answer['normalized_answer']) if answer['normalized_answer'] is not None else None,
                normalized_expression=str(answer['normalized_expression']) if answer['normalized_expression'] is not None else None,
                selected_value=chosen,selection_evidence=method,
                official_expression_correct=answer['official_expression_correct'],
                official_answer_correct=answer['official_answer_correct'] if answer['official_answer_correct'] is not None else official_equal(answer['normalized_answer'],gold),
                source=answer['source'],call_id=answer['call_id']))
    ids={q['id'] for q in rows};affected_ids={q['id'] for q in rows if q['officially_affected']}
    summary=dict(source_level='our_experiment_existing_responses_only',candidate_finqa_pairs=len(finqa),candidate_finqa_unique_questions=len({q['id'] for q in finqa}),
        affected_finqa_pairs=len(affected),affected_finqa_unique_questions=len({q['id'] for q in affected}),
        existing_sample_unique_questions=len({key[0] for key in answers}),existing_unique_responses=len(answers),
        matched_unique_questions=len(ids),affected_matched_unique_questions=len(affected_ids),matched_responses=len(rows),
        selections=dict(Counter(r['selected_value'] for r in rows if r['officially_affected'])),
        official_outcomes=dict(Counter(str(r['official_expression_correct']) for r in rows if r['officially_affected'])),
        reused_A_deduplicated=True,rows=rows)
    (ROOT/'part1_existing_responses.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    fields=list(rows[0]) if rows else ['id','split','question','kind','printed_raw','printed_in_answer_unit','recomputed','gold','officially_affected','relative_1pct_affected','row_mismatch','condition','model','answer','expression','normalized_answer','normalized_expression','selected_value','selection_evidence','official_expression_correct','official_answer_correct','source','call_id']
    with (ROOT/'part1_existing_responses.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    text=(f'# Part One: intersection with existing answers\n\nSource level: our experiment, reusing existing T1c/T1d answers; no new model calls.\n\n'
        f'Part One currently matches {len(finqa)} FinQA question–printed-value pairs ({len({q["id"] for q in finqa})} distinct questions), of which {len({q["id"] for q in affected})} disagree under official scoring. '
        f'The intersection with the original 392-question sample is **{len(ids)} questions**; the intersection with officially affected questions is **{len(affected_ids)} questions**, with {len(rows)} matched answers in total.'
        '\n\nT1d condition A reuses T1c and has been deduplicated; B, C, and B_secondary are each kept. The selected-value label first compares the exact value of the normalized expression, then the FinQA official five-decimal execution value. Equal numbers show only that the results agree; they do not prove which cell the model actually read.'
        '\n\nIf the intersection is zero, these existing answers cannot answer "does the model choose the printed value or the recomputed value on affected questions", nor can they be used to assert that the model does not show this behavior.'
        '\n\nAfter `part1_questions.json` is updated, rerun `part1_existing_responses.py` to refresh the results.\n')
    (ROOT/'part1_existing_responses.md').write_text(text,encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
