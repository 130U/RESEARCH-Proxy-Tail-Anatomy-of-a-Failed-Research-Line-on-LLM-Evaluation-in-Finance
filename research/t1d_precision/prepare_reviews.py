"""Prepare frozen anonymous packets; source data and prior judgments stay read-only."""
from pathlib import Path
import json
import random

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[2]
T1 = WORKSPACE / 'proxy-tail/research/t1_rounding'
T1B = WORKSPACE / 'proxy-tail-t1b/research/t1b_tighten'
T1C = WORKSPACE / 'proxy-tail-t1c/research/t1c_models'
SEED = 20261117

SEMANTIC_RUBRIC = '''Independently assess the supplied financial question, reference calculation and source bindings. Use only the supplied material; do not use external sources, code or tools. Do not assume that either the reference calculation or the source binding is correct.

Check all three issues:
1. Does each bound input refer to the right entity, metric, period, sign and unit in the document?
2. Is treating each bound input as a rounded financial quantity justified? Exact counts, dates, years, contractual terms and defined constants are exact; an aggregate amount or a measured average can be rounded. Decide from the source, not merely from the number of printed digits. An explicitly rounded scaled count is different from an exact item count.
3. Does the reference calculation answer the question with the appropriate meaning, denominator and units?

Use "valid" only when all three are supported. Use "invalid" when a definite binding, quantity-type or calculation error is established. Use "uncertain" when the excerpt is insufficient or genuinely ambiguous. Give one concise source-specific reason. Do not calculate uncertainty intervals.

Return only JSON with exactly these fields:
{"review_id":"the supplied anonymous id","verdict":"valid, invalid, or uncertain","reason":"one source-specific sentence"}
'''


def read_json(path):
    return json.loads(path.read_text(encoding='utf8'))


def read_jsonl(path):
    return [json.loads(s) for s in path.read_text(encoding='utf8').splitlines() if s.strip()]


def write_frozen(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding='utf8') != text:
            raise ValueError(f'Refusing to change a frozen review packet: {path}')
    else:
        path.write_text(text, encoding='utf8', newline='\n')


def document(doc):
    # Zero-based locations match the upstream binder's table and combined text indices.
    return {
        'pre_text': [{'location': f'text_{i}', 'text': s} for i, s in enumerate(doc['pre_text'])],
        'table': [{'row_index': i, 'cells': row} for i, row in enumerate(doc.get('table_ori', doc['table']))],
        'post_text': [{'location': f'text_{i + len(doc["pre_text"])}', 'text': s} for i, s in enumerate(doc['post_text'])],
        'location_convention': 'All indices are zero-based. table_i:j identifies row i and column j. text_i:k identifies character offset k in combined pre_text + post_text item i after source HTML normalization.',
    }


def first_c_reviews():
    reviews = {}
    for path in sorted(T1C.glob('review_*.json')):
        for row in read_json(path):
            if row['call_id'] in reviews:
                raise ValueError('Duplicate original C judgment')
            reviews[row['call_id']] = dict(row, original_review_file=path.name)
    for row in read_json(T1C / 'adjudication.json'):
        reviews[row['call_id']] = dict(reviews[row['call_id']], **row)
        reviews[row['call_id']]['final_override_file'] = 'adjudication.json'
    return reviews


def main():
    rows = read_jsonl(T1 / 'results/per_question.jsonl')
    tests = [r for r in rows if r.get('split') == 'test' and r.get('status') == 'analyzed']
    witness = sorted([r for r in tests if r['relative_1pct']['status'] == 'witnessed_outside'], key=lambda r: r['id'])
    stable = sorted([r for r in tests if r['relative_1pct']['status'] == 'certified_inside'], key=lambda r: r['id'])
    assert len(witness) == 196 and len(stable) == 532
    rng = random.Random(SEED)
    controls = rng.sample(stable, 60)
    cohort = [('witness', r) for r in witness] + [('control', r) for r in controls]
    rng.shuffle(cohort)
    docs = {r['id']: r for r in read_json(T1 / 'data/finqa/test.json')}
    previous_b = {}
    for filename in ('review_a.json', 'review_b.json'):
        for r in read_json(T1B / filename):
            assert r['id'] not in previous_b
            previous_b[r['id']] = dict(r, original_review_file=filename)
    assert set(previous_b) == {r['id'] for r in witness}
    mapping_b = []
    for i, (group, r) in enumerate(cohort, 1):
        review_id = f'R{i:03}'
        doc = docs[r['id']]
        provenance = {
            key: {k: v[k] for k in ('program_token', 'raw', 'location', 'context') if k in v}
            for key, v in r['input_provenance'].items()
        }
        packet = {
            'review_id': review_id, 'document': document(doc),
            'question': doc['qa']['question'], 'reference_program': r['program'],
            'reference_program_convention': '#k means the output of zero-based operation k; const_* are exact constants.',
            'input_bindings': provenance,
        }
        text = SEMANTIC_RUBRIC + '\nMATERIAL\n' + json.dumps(packet, ensure_ascii=False, indent=2) + '\n'
        write_frozen(ROOT / 'prompts/review_b' / f'{review_id}.txt', text)
        mapping_b.append({
            'review_id': review_id, 'id': r['id'], 'page_id': r['id'].rsplit('-', 1)[0],
            'group': group, 'category': r['category'], 'first': previous_b.get(r['id']),
        })

    scores = read_jsonl(T1C / 'scores.jsonl')
    rejected = sorted([r for r in scores if r.get('expression_scores', {}).get('official') is False], key=lambda r: r['call_id'])
    assert len(rejected) == 68
    rng_c = random.Random(SEED)
    rng_c.shuffle(rejected)
    first_c = first_c_reviews()
    c_rubric = (T1C / 'REVIEW_RUBRIC.md').read_text(encoding='utf8')
    # Preserve the prior substantive rubric, remove study/orchestration references from the prompt.
    c_start = c_rubric.index('For each call, report')
    c_end = c_rubric.index('\nThese judgments audit')
    c_rubric = c_rubric[c_start:c_end].strip()
    c_prompt = 'Independently assess the supplied financial question and model response. Use only this material; do not use external sources, code or tools.\n\n' + c_rubric + '\n\nReturn only one JSON object with the requested fields, using the anonymous call_id supplied below.\n'
    mapping_c = []
    for i, r in enumerate(rejected, 1):
        review_id = f'S{i:03}'
        doc = docs[r['id']]
        packet = {
            'call_id': review_id, 'document': document(doc), 'question': r['question'],
            'human_answer': r['answer'], 'reference_program': r['program'],
            'reference_execution_value': r['exe_ans'],
            'model_response': r.get('response'),
        }
        text = c_prompt + '\nMATERIAL\n' + json.dumps(packet, ensure_ascii=False, indent=2) + '\n'
        write_frozen(ROOT / 'prompts/review_c' / f'{review_id}.txt', text)
        mapping_c.append({
            'review_id': review_id, 'call_id': r['call_id'], 'id': r['id'], 'page_id': r['page_id'],
            'group': r['group'], 'first': first_c[r['call_id']],
        })
    for name, value in [('review_b_map.json', mapping_b), ('review_c_map.json', mapping_c)]:
        write_frozen(ROOT / 'private' / name, json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'review_b': len(mapping_b), 'review_b_witness': 196, 'review_b_control': 60, 'review_c': len(mapping_c), 'seed': SEED}))


if __name__ == '__main__':
    main()
