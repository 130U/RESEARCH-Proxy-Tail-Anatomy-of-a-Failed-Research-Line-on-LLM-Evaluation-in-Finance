"""Group frozen anonymous materials without revealing earlier labels or groups."""
from pathlib import Path
import argparse
import json
import re

ROOT = Path(__file__).resolve().parent
CONFIG = {
    'review_b': ('T', 16), 'review_c': ('U', 16),
    'adjudicate_b': ('V', 8), 'adjudicate_c': ('W', 8),
}


def split_packet(path):
    text = path.read_text(encoding='utf8')
    header, body = text.split('\nMATERIAL\n', 1)
    if '\nTWO SOURCE INTERPRETATIONS TO CONSIDER\n' in body:
        material, tail = body.split('\nTWO SOURCE INTERPRETATIONS TO CONSIDER\n', 1)
        # The second line is a fixed instruction; only the two randomly
        # ordered reasons themselves become part of this material.
        _, reasons = tail.split('\n', 1)
        material = json.loads(material)
        material['source_interpretations_random_order'] = json.loads(reasons)
    else:
        material = json.loads(body)
    return header, material


def batch_header(header, adjudication=False):
    if 'Return only JSON with exactly these fields:' in header:
        header = header.replace('Return only JSON with exactly these fields:',
            'Return only a JSON array, with one object for each supplied material in the supplied order. Each object must use exactly these fields:')
    elif 'Return only one JSON object with the requested fields, using the anonymous call_id supplied below.' in header:
        header = header.replace('Return only one JSON object with the requested fields, using the anonymous call_id supplied below.',
            'Return only a JSON array, with one object for each supplied material in the supplied order, using its anonymous call_id and the requested fields.')
    else:
        raise ValueError('Unrecognized frozen review schema instruction')
    header += '\nAssess each material independently. Do not infer a common answer or prevalence from the batch. Do not combine items or omit any item.\n'
    if adjudication:
        header += 'Each material includes two source interpretations in random order. Evaluate their reasons against that material and give your own judgment. Their order carries no priority.\n'
    return header


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--groups', default=','.join(CONFIG))
    args = parser.parse_args()
    summary = {}
    for group in args.groups.split(','):
        prefix, size = CONFIG[group]
        source_files = sorted((ROOT / 'prompts' / group).glob('*.txt'))
        batch_group = group + '_batch'
        mapping_path = ROOT / 'private' / f'{batch_group}_map.json'
        existing = json.loads(mapping_path.read_text(encoding='utf8')) if mapping_path.exists() else []
        assigned = {item for batch in existing for item in batch['item_ids']}
        remaining = [path for path in source_files if path.stem not in assigned]
        mapping = list(existing)
        for offset in range(0, len(remaining), size):
            sources = remaining[offset:offset+size]
            packets = [split_packet(path) for path in sources]
            if len({header for header, _ in packets}) != 1:
                raise ValueError(f'Mismatched substantive rubric in {group}')
            batch_id = f'{prefix}{len(mapping)+1:03}'
            header = batch_header(packets[0][0], group.startswith('adjudicate'))
            prompt = header + '\nMATERIALS\n' + json.dumps([material for _, material in packets], ensure_ascii=False, indent=2) + '\n'
            target = ROOT / 'prompts' / batch_group / f'{batch_id}.txt'
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and target.read_text(encoding='utf8') != prompt:
                raise ValueError(f'Refusing to change frozen batch {batch_id}')
            if not target.exists():
                target.write_text(prompt, encoding='utf8', newline='\n')
            mapping.append({'batch_id': batch_id, 'batch_group': batch_group, 'item_group': group,
                            'item_ids': [path.stem for path in sources],
                            'source_prompts': [path.relative_to(ROOT).as_posix() for path in sources],
                            'characters': len(prompt), 'whitespace_words': len(prompt.split())})
        mapping_path.parent.mkdir(parents=True, exist_ok=True)
        mapping_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + '\n', encoding='utf8', newline='\n')
        summary[batch_group] = {'batches': len(mapping), 'items': sum(len(x['item_ids']) for x in mapping),
                                'max_characters': max((x['characters'] for x in mapping), default=0),
                                'max_whitespace_words': max((x['whitespace_words'] for x in mapping), default=0)}
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
