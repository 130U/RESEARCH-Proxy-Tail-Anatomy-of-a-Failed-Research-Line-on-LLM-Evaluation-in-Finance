"""Extract verbatim JSON objects from retained raw arrays; never repair judgments."""
from pathlib import Path
from collections import Counter
import argparse
import json
import re

from aggregate_reviews import validate_review_response

ROOT = Path(__file__).resolve().parent


def array_spans(raw):
    """Return object values and exact source substrings, tolerating only fences."""
    start = len(raw) - len(raw.lstrip())
    end = len(raw.rstrip())
    opening = re.match(r'```(?:json)?\s*', raw[start:end], flags=re.I)
    if opening:
        start += opening.end()
        if not raw[start:end].endswith('```'):
            raise ValueError('unclosed code fence')
        end -= 3
    body = raw[start:end]
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON object key')
            result[key] = value
        return result
    parsed = json.loads(body, object_pairs_hook=unique_keys)
    if not isinstance(parsed, list):
        raise ValueError('batch response is not a JSON array')
    decoder = json.JSONDecoder()
    pos = 0
    while pos < len(body) and body[pos].isspace():
        pos += 1
    assert body[pos] == '['
    pos += 1
    result = []
    for expected in parsed:
        while body[pos].isspace():
            pos += 1
        begin = pos
        value, pos = decoder.raw_decode(body, pos)
        assert value == expected
        result.append({'value': value, 'text': body[begin:pos], 'source_char_span': [start+begin, start+pos]})
        while pos < len(body) and body[pos].isspace():
            pos += 1
        if pos < len(body) and body[pos] == ',':
            pos += 1
    return result


def split_batch(batch):
    group, item_group, batch_id = batch['batch_group'], batch['item_group'], batch['batch_id']
    kind = item_group.rsplit('_', 1)[1]
    id_key = 'review_id' if kind == 'b' else 'call_id'
    source = ROOT / 'raw' / group / f'{batch_id}.txt'
    call_file = ROOT / 'calls' / group / f'{batch_id}.json'
    report = {'batch_group': group, 'batch_id': batch_id, 'expected_ids': batch['item_ids'],
              'source_raw_file': source.relative_to(ROOT).as_posix(), 'status': 'missing', 'items': []}
    if not source.exists():
        return report
    if not call_file.exists():
        report.update(status='source_call_missing')
        return report
    call = json.loads(call_file.read_text(encoding='utf8'))
    if call.get('tool_use_observed') or call.get('status') != 'completed':
        report.update(status='source_call_not_completed_or_protocol_violation', source_call_status=call.get('status'))
        return report
    try:
        spans = array_spans(source.read_bytes().decode('utf8'))
    except (ValueError, AssertionError, IndexError) as exc:
        report.update(status='invalid_batch_format', error=str(exc), missing_ids=batch['item_ids'])
        return report
    ids = [span['value'].get(id_key) if isinstance(span['value'], dict) else None for span in spans]
    counts = Counter(x for x in ids if isinstance(x, str))
    expected = set(batch['item_ids'])
    report.update(status='processed', returned_n=len(spans), duplicate_ids=sorted(x for x, n in counts.items() if n > 1),
                  unexpected_ids=sorted(x for x in counts if x not in expected), missing_ids=sorted(expected-set(counts)))
    for index, span in enumerate(spans):
        item, review_id = span['value'], ids[index]
        state = {'array_index': index, 'review_id': review_id, 'source_char_span': span['source_char_span']}
        report['items'].append(state)
        if not isinstance(review_id, str) or review_id not in expected:
            state['status'] = 'missing_or_unexpected_id'; continue
        if counts[review_id] != 1:
            state['status'] = 'duplicate_id'; continue
        try:
            validate_review_response(kind, review_id, item)
        except ValueError as exc:
            state.update(status='invalid_item_format', error=str(exc)); continue
        target = ROOT / 'raw' / item_group / f'{review_id}.txt'
        record_path = ROOT / 'calls' / item_group / f'{review_id}.json'
        record = {
            'group': item_group, 'id': review_id, 'status': 'derived_from_batch',
            'fresh_individual_session': False, 'fresh_source_session': call.get('fresh_session'),
            'source_batch_group': group, 'source_batch_id': batch_id,
            'source_call_file': call_file.relative_to(ROOT).as_posix(),
            'source_raw_file': source.relative_to(ROOT).as_posix(),
            'source_array_index': index, 'source_char_span': span['source_char_span'],
            'derivation': 'Verbatim JSON-object substring from the retained raw batch response. No judgment values or prose repaired.',
            **{key: call.get(key) for key in ('thread_id', 'model', 'reasoning_effort', 'started_utc', 'completed_utc', 'tool_use_observed')},
        }
        if target.exists():
            if target.read_bytes().decode('utf8') != span['text'] or not record_path.exists():
                state['status'] = 'existing_response_conflict'; continue
            existing = json.loads(record_path.read_text(encoding='utf8'))
            if existing.get('source_raw_file') != record['source_raw_file'] or existing.get('source_array_index') != index:
                state['status'] = 'existing_provenance_conflict'; continue
            state['status'] = 'already_extracted'; continue
        target.parent.mkdir(parents=True, exist_ok=True)
        record_path.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(span['text'].encode('utf8'))
        record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf8', newline='\n')
        state['status'] = 'extracted'
    good = {r['review_id'] for r in report['items'] if r['status'] in ('extracted', 'already_extracted')}
    report['unusable_expected_ids'] = sorted(expected-good)
    report['complete'] = not report['unusable_expected_ids'] and not report['unexpected_ids']
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--groups', default='review_b_batch,review_c_batch,adjudicate_b_batch,adjudicate_c_batch')
    args = parser.parse_args()
    results = []
    for group in args.groups.split(','):
        mapping_path = ROOT / 'private' / f'{group}_map.json'
        if not mapping_path.exists():
            continue
        for batch in json.loads(mapping_path.read_text(encoding='utf8')):
            results.append(split_batch(batch))
    (ROOT / 'review_batch_extraction.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf8', newline='\n')
    print(json.dumps({'batches': len(results), 'batch_status': dict(Counter(r['status'] for r in results)),
                      'item_status': dict(Counter(item['status'] for r in results for item in r['items']))}, ensure_ascii=False))


if __name__ == '__main__':
    main()
