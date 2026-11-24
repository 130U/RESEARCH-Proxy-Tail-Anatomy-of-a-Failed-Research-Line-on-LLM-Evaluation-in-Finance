"""Freeze the task's literal prompts and reuse the original 392 documents."""
from pathlib import Path
import json
import random
import re

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[2]
T1C = WORKSPACE / 'proxy-tail-t1c/research/t1c_models'
T1 = WORKSPACE / 'proxy-tail/research/t1_rounding'


def main():
    task = (ROOT / 'TASK.md').read_text(encoding='utf8')
    b = re.search(r'### Prompt B\s*```\s*\n(.*?)\n```', task, re.S).group(1) + '\n'
    rule = re.search(r'### Prompt C.*?```\s*\n(.*?)\n```', task, re.S).group(1)
    paragraph = 'Figures in the document are rounded to the precision shown: a displayed figure may stand for any value that rounds to it. Counts, years, dates and contractual terms are exact.'
    assert b.count(paragraph) == 1
    c = b.replace(paragraph, paragraph + '\n\n' + rule)
    sample = json.loads((T1C / 'private/sample.json').read_text(encoding='utf8'))
    assert len(sample) == 392 and len({r['id'] for r in sample}) == 392
    for condition, prompt in [('B', b), ('C', c)]:
        (ROOT / 'prompts' / condition).mkdir(parents=True, exist_ok=True)
        (ROOT / 'raw' / condition).mkdir(parents=True, exist_ok=True)
        (ROOT / f'prompt_{condition}.txt').write_text(prompt, encoding='utf8', newline='\n')
        for row in sample:
            original = (T1C / 'inputs' / f"{row['call_id']}.txt").read_text(encoding='utf8')
            document, question = original.split('\nDOCUMENT\n', 1)[1].rsplit('\nQUESTION\n', 1)
            # Preserve the source payload verbatim, including its blank line separators.
            payload = prompt.split('\nDOCUMENT\n', 1)[0] + '\nDOCUMENT\n' + document + '\nQUESTION\n' + question
            (ROOT / 'prompts' / condition / f"{row['call_id']}.txt").write_text(payload, encoding='utf8', newline='\n')
    pairs = sorted({r['pair_id'] for r in sample})
    half_pairs = set(random.Random(20261117).sample(pairs, 98))
    (ROOT / 'private').mkdir(exist_ok=True)
    (ROOT / 'private/c_half_ids.json').write_text(json.dumps(sorted(r['call_id'] for r in sample if r['pair_id'] in half_pairs), indent=2) + '\n', encoding='utf8')
    train = json.loads((T1 / 'data/finqa/train.json').read_text(encoding='utf8'))
    pilot = random.Random(20261117).sample(sorted(train, key=lambda r:r['id']), 10)
    assert not {d['id'] for d in pilot} & {r['id'] for r in sample}
    (ROOT / 'prompts/pilot').mkdir(exist_ok=True)
    for i, d in enumerate(pilot, 1):
        document = '\n'.join(d['pre_text']) + '\n\nTABLE\n' + '\n'.join(' | '.join(row) for row in d.get('table_ori',d['table'])) + '\n\n' + '\n'.join(d['post_text'])
        prompt = b if i % 2 else c
        payload = prompt.replace('{document}', document).replace('{question}', d['qa']['question'])
        (ROOT / 'prompts/pilot' / f'P{i:03}.txt').write_text(payload, encoding='utf8', newline='\n')
    (ROOT / '.runtime').mkdir(exist_ok=True)
    print(json.dumps({'B':392,'C':392,'fallback_C':196,'pilot_train':10,'prompt_text':'verbatim task extraction'}))


if __name__ == '__main__':
    main()
