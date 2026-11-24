"""T1D: exact model-expression precision, with explicit source bindings.

No inference calls. Prior answers and reference data are read only. A numeric
match only generates source candidates; ambiguous identities require an
explicit reviewed binding in binding_overrides.json. Gold operands are never
used for binding. Output precision stays in the response's stated units.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import itertools
import json
import math
import re
import sys
from collections import Counter
from decimal import Decimal
from fractions import Fraction as F
from pathlib import Path

# Importing read-only prior-round modules must not create cache files there.
sys.dont_write_bytecode = True

import sympy as sp

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[2]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def exact(x):
    return F(Decimal(str(x).strip().replace(',', '').replace('−', '-')))


def dumpable(x):
    if isinstance(x, F):
        return str(x)
    if isinstance(x, dict):
        return {k: dumpable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [dumpable(v) for v in x]
    return x


def log_ratio(numerator, denominator):
    # Avoid conversion overflow/underflow for exact rational arithmetic.
    value = abs(numerator / denominator)
    return math.log10(value.numerator) - math.log10(value.denominator)


def numeric_nodes(tree, parent=None, side=None, sibling=None, depth=0):
    if tree[0] == 'number':
        return [{'value': tree[1], 'parent': parent, 'side': side,
                 'sibling': sibling, 'depth': depth}]
    if tree[0] not in ('add', 'subtract', 'multiply', 'divide'):
        raise ValueError('expression_operator_not_in_fixed_prompt')
    return (numeric_nodes(tree[1], tree[0], 'left', tree[2], depth+1) +
            numeric_nodes(tree[2], tree[0], 'right', tree[1], depth+1))


def parse_model_expression(expression, prior):
    # Financial source displays use thousands separators. Recognize only
    # correctly grouped digits; never turn an arbitrary comma tuple into a
    # valid arithmetic expression by deleting every comma.
    grouped = re.compile(r'(?<![\w.,])\d{1,3}(?:,\d{3})+(?:\.\d+)?(?![\w.,])')
    normalized = grouped.sub(lambda match: match.group().replace(',', ''), str(expression))
    if ',' in normalized:
        raise ValueError('malformed_thousands_separator_in_expression')
    return prior.parse_expression(normalized)


def source_catalog(document, t1):
    # The selected/gold source list is deliberately discarded.
    _, full = t1.source_numbers(document)
    result = []
    for item in full:
        result.append({
            'location': item['loc'], 'raw': item['raw'],
            'value': item['value'], 'half': item['half'],
            'context': item['context'], 'text': item['text'],
            'percent': item['percent'],
        })
    return result


def quantity_kind(source):
    """Conservative lexical cases; uncertain contracts await source review."""
    # Some FinQA table headers omit a space at a line break ("ofShares").
    # Restore that lexical boundary before identifying explicit count labels.
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', source['context']).lower()
    # The task explicitly treats counts, years/dates, contractual terms exact.
    count_label = r'\b(number\s*of|headcount|employees|stores|facilities|members|units sold|shares|securitiesremaining)\b'
    money_label = r'\b(cost|expense|revenue|income|cash|liabilit|asset|payment|benefit|price|proceeds|dollar)'
    if source['location'].startswith('table_'):
        if re.search(count_label, text) and not re.search(money_label, text):
            return 'exact', 'Table row explicitly labels a count; task treats counts as exact.'
    else:
        # A sentence ending "for the years 2011 and 2010" does not make every
        # money/rate figure in that sentence an exact time quantity.
        position = int(source['location'].rsplit(':', 1)[1])
        tail = source['text'][position:position+len(source['raw'])+65].lower()
        raw_pattern = re.escape(source['raw'].strip()).replace(r'\ ', r'\s*')
        if re.match(r'\s*'+raw_pattern+r'\s+(?:employees|stores|facilities|members|days|months|years)\b', tail):
            return 'exact', 'Source figure is immediately followed by an explicit count/time noun.'
        if re.match(r'\s*'+raw_pattern+r'\s+(?:(?:million|thousand|billion)\s+)?(?:common\s+)?shares\b', tail):
            return 'exact', 'Source figure explicitly states a share count; task treats counts as exact.'
    if re.search(r'contractual|exercise price|strike price|coupon|par value|'
                 r'dividend.*per.*share|per.*share.*dividend|useful life|vesting', text):
        return 'review', 'Potential contractual or defined term needs explicit source review.'
    return 'rounded', 'Unique displayed source figure; rounding half-unit taken from its written precision.'


def obvious_constant(node, expression, response, question):
    value, parent, side = node['value'], node['parent'], node['side']
    wording = (response.get('explanation', '') + ' ' + question).lower()
    if value == 0:
        return 'Exact arithmetic zero.'
    if value in (F(1), F(-1)) and parent == 'multiply':
        return 'Exact arithmetic multiplicative identity/sign without a displayed source conflict.'
    if value == 1 and parent in ('add', 'subtract') and node['sibling'][0] == 'divide':
        return 'Exact one plus/minus a ratio in a growth or percentage conversion.'
    if abs(value) in (F(100), F(1000), F(10**6), F(10**9)) and parent in ('multiply', 'divide'):
        unit = str(response.get('unit', '')).lower()
        if abs(value) == 100 and ('percent' in unit or '%' in unit or re.search(r'percent|rate', wording)):
            return 'Exact percentage conversion factor.'
        if re.search(r'million|billion|thousand|dollar|usd|\$', unit + ' ' + wording):
            return 'Exact decimal magnitude conversion factor.'
    if value.denominator == 1 and 2 <= value <= 12 and parent == 'divide' and side == 'right':
        def summands(t):
            if t[0] == 'add':
                return summands(t[1])+summands(t[2])
            return 1
        if re.search(r'averag|\bmean\b', wording) and summands(node['sibling']) == value:
            return 'Exact average divisor matches the number of additive observations in the numerator.'
        if value == 12 and re.search(r'annual|month|year', wording):
            return 'Exact months-per-year conversion.'
    return None


class BindingFailure(Exception):
    def __init__(self, problems, partial):
        super().__init__('source_binding_unresolved')
        self.problems, self.partial = problems, partial


class ScoringFailure(ValueError):
    def __init__(self, reason, detail):
        super().__init__(reason)
        self.detail = detail


def numeric_field(response, name):
    try:
        return exact(response[name])
    except Exception as error:
        raise ScoringFailure(name + '_not_numeric',
                             type(error).__name__ + ': ' + str(error)) from error


def bind_tree(tree, catalog, response, question, override):
    nodes = numeric_nodes(tree)
    bindings, pending, symbols = [], [], {}
    # Overrides are per numeric occurrence n0,n1,...; repeated facts can use
    # a shared fact_id. Every override must state a source location or exact
    # constant judgment plus a human-readable reason.
    override_nodes = override.get('nodes', {})
    by_loc = {s['location']: s for s in catalog}
    for index, node in enumerate(nodes):
        key = f'n{index}'
        value = node['value']
        selected, exact_reason, factor, fact_id = None, None, F(1), None
        candidates = []
        for source in catalog:
            if source['value'] == value:
                candidates.append((source, F(1)))
        if not candidates:
            # Accounting negatives may be used as a positive loss magnitude.
            for source in catalog:
                if source['value'] == -value and value != 0:
                    candidates.append((source, F(-1)))
        spec = override_nodes.get(key)
        if spec:
            if not spec.get('reason'):
                raise ValueError('binding_override_requires_reason')
            if spec.get('exact') is True:
                exact_reason = spec['reason']
                if spec.get('location'):
                    selected = by_loc.get(spec['location'])
                    if selected is None:
                        raise ValueError('override_source_location_not_found')
                    factor = F(spec.get('factor', '1'))
                    if selected['value'] * factor != value:
                        raise ValueError('override_source_value_mismatch')
            else:
                selected = by_loc.get(spec.get('location'))
                if selected is None:
                    raise ValueError('override_source_location_not_found')
                factor = F(spec.get('factor', '1'))
                if selected['value'] * factor != value:
                    raise ValueError('override_source_value_mismatch')
            fact_id = spec.get('fact_id')
        else:
            constant = obvious_constant(node, response['expression'], response, question)
            # Constants in arithmetic roles may also coincidentally occur in
            # the document. No prior/gold operand data resolves this choice.
            structural_average = constant and constant.startswith('Exact average divisor')
            structural_ratio_identity = (value == 1 and node['parent'] == 'subtract'
                                         and node['sibling'][0] == 'divide')
            terminal_percent = (value == 100 and node['parent'] == 'multiply' and node['depth'] == 1
                                and re.search(r'percent|%', str(response.get('unit','')), re.I))
            if constant and (not candidates or structural_average or structural_ratio_identity or terminal_percent):
                exact_reason = constant
            elif not candidates and value.denominator == 1 and 1900 <= value <= 2100 and re.search(r'year|date|period', question, re.I):
                exact_reason = 'Exact calendar year explicitly used in the time question.'
            else:
                # Duplicate lexical presentations with identical context and
                # precision represent the same explicitly repeated statement.
                identities = {}
                for source, scale in candidates:
                    identity = (re.sub(r'\s+', ' ', source['context'].lower()).strip(),
                                source['value'], source['half'])
                    identities.setdefault(identity, (source, scale))
                if len(identities) == 1:
                    selected, factor = next(iter(identities.values()))
                    kind, why = quantity_kind(selected)
                    if kind == 'exact':
                        exact_reason = why
                    elif kind == 'review':
                        pending.append({'node': key, 'value': str(value), 'reason': why,
                                        'candidates': dumpable([s for s, _ in candidates])})
                        continue
                else:
                    pending.append({'node': key, 'value': str(value),
                                    'reason': 'ambiguous_source_identity' if identities else 'no_displayed_source_or_obvious_constant',
                                    'candidates': dumpable([s for s, _ in candidates])})
                    continue
        if exact_reason:
            bindings.append({'node': key, 'literal': str(value), 'exact': True,
                             'value': str(value), 'half': '0', 'reason': exact_reason,
                             'factor': str(factor),
                             'source_value': str(selected['value']) if selected else None,
                             'location': selected['location'] if selected else None,
                             'raw': selected['raw'] if selected else None,
                             'context': selected['context'] if selected else None})
            continue
        fact_id = fact_id or selected['location']
        # The source-valued variable is shared before any sign/unit factor.
        if fact_id in symbols:
            prior = symbols[fact_id]
            if (prior['center'], prior['half']) != (selected['value'], selected['half']):
                raise ValueError('shared_fact_inconsistent_display_precision')
        else:
            symbols[fact_id] = {'name': f'x{len(symbols)}', 'center': selected['value'],
                                'half': selected['half'], 'location': selected['location']}
        bindings.append({'node': key, 'literal': str(value), 'exact': False,
                         'variable': symbols[fact_id]['name'], 'fact_id': fact_id,
                         'value': str(selected['value']), 'half': str(selected['half']),
                         'factor': str(factor), 'location': selected['location'],
                         'raw': selected['raw'], 'context': selected['context'],
                         'reason': spec['reason'] if spec else quantity_kind(selected)[1]})
    if pending:
        raise BindingFailure(pending, bindings)
    binding_map = {b['node']: b for b in bindings}
    position, steps = 0, []

    def compile_node(t):
        nonlocal position
        if t[0] == 'number':
            binding = binding_map[f'n{position}']; position += 1
            if binding['exact']:
                return binding['value']
            variable, scale = binding['variable'], F(binding['factor'])
            if scale == 1:
                return variable
            steps.append(['multiply', variable, str(scale)])
            return '#' + str(len(steps)-1)
        left, right = compile_node(t[1]), compile_node(t[2])
        steps.append([t[0], left, right])
        return '#' + str(len(steps)-1)

    output = compile_node(tree)
    if not output.startswith('#'):
        steps.append(['add', output, '0'])
    intervals = {s['name']: {'lo': str(s['center']-s['half']),
                            'hi': str(s['center']+s['half'])} for s in symbols.values()}
    return steps, intervals, bindings


def certified_range(steps, intervals, law):
    # The T1A evaluator treats repeated variables as the same fact. A success
    # requires a monotonicity or coordinatewise-linear-fractional certificate.
    row = {'steps': steps, 'input_intervals': intervals}
    if not intervals:
        center = law.evaluate(row, {})
        return center, center, center, F(0), 'all_exact_inputs'
    cert = law.range_certificate(row)
    if not cert['exact']:
        raise ValueError('exact_range_not_certified')
    centers, _ = law.centers_half(row)
    center = law.evaluate(row, centers)
    _, first_order_radius, _ = law.gradient_radius(row)
    return center, cert['lo'], cert['hi'], first_order_radius, cert['method']


def read_raw(path):
    raw = path.read_text(encoding='utf8').strip()
    body = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw).strip()
    def unique_keys(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ScoringFailure('duplicate_json_key', 'Repeated object key: ' + key)
            value[key] = item
        return value
    try:
        value = json.loads(body, object_pairs_hook=unique_keys)
    except json.JSONDecodeError as error:
        raise ScoringFailure('malformed_json', str(error)) from error
    if not isinstance(value, dict):
        raise ValueError('response_is_not_json_object')
    return value


def score_one(sample, document, condition, path, modules, overrides):
    prior, source, law, official = modules
    out = {k: sample[k] for k in ('call_id', 'id', 'pair_id', 'group', 'category')}
    out.update(condition=condition, page_id=sample['id'].rsplit('-', 1)[0],
               scorable=False, parse_status='error', exclusion_reason=None,
               official_expression_correct=None, raw_file=str(path))
    pending = None
    try:
        response = read_raw(path)
        required = {'answer', 'unit', 'expression', 'explanation'}
        if condition != 'A':
            required |= {'low', 'high', 'reliable_digits'}
        if not required <= response.keys():
            raise ValueError('missing_response_fields')
        out['response'] = response
        out['json_schema_exact'] = set(response) == required and all(isinstance(response[k], str) for k in required)
        out.update(answer=response['answer'], unit=response['unit'], expression=response['expression'])
        answer = numeric_field(response, 'answer')
        try:
            tree = parse_model_expression(response['expression'], prior)
            numeric_nodes(tree)
        except Exception as error:
            raise ScoringFailure('expression_parse_error',
                                 type(error).__name__ + ': ' + str(error)) from error
        display_places = -Decimal(str(response['answer']).replace(',', '')).as_tuple().exponent
        out['answer_matches_expression_rounding'] = prior.round_places(prior.run_tree(tree), display_places) == answer
        out['printed_digits'] = prior.significant_digits(response['answer'])
        out['parse_status'] = 'ok'
        normalized_factor, why = prior.scale_response(sample, response['unit'], overrides['units'])
        normalized = tree if normalized_factor == 1 else ('multiply', tree, ('number', normalized_factor))
        invalid, official_value = official.eval_program(prior.dsl_tokens(normalized), [])
        out['official_expression_correct'] = not invalid and official_value == sample['exe_ans']
        out['official_normalization'] = {'factor': str(normalized_factor), 'reason': why}
        out['official_execution_value'] = official_value
        if condition != 'A':
            low, high = numeric_field(response, 'low'), numeric_field(response, 'high')
            digits_raw = str(response['reliable_digits']).strip()
            if not re.fullmatch(r'\d+', digits_raw):
                raise ValueError('reliable_digits_not_nonnegative_integer')
            digits = int(digits_raw)
            out.update(low=str(low), high=str(high), reliable_digits=digits,
                       reported_interval_reversed=high < low)
        key = condition + '/' + sample['call_id']
        spec = overrides['bindings'].get(key, {})
        # An explicitly reviewed identical arithmetic expression can share a
        # binding across conditions, without sharing any model output.
        if not spec:
            spec = overrides['bindings'].get(sample['call_id'], {})
        if not spec and condition != 'A':
            previous = overrides['bindings'].get('A/' + sample['call_id'], {})
            if previous.get('expression') and parse_model_expression(previous['expression'], prior) == tree:
                spec = previous
                out['binding_reused_from'] = 'A/' + sample['call_id']
        if spec.get('expression') and parse_model_expression(spec['expression'], prior) != tree:
            raise ValueError('binding_override_expression_mismatch')
        catalog = source_catalog(document, source)
        steps, intervals, bindings = bind_tree(tree, catalog, response, document['qa']['question'], spec)
        out.update(bindings=bindings, model_steps=steps, model_input_intervals=intervals)
        out['source_literal_rescaled'] = any(b.get('location') and abs(F(b['factor'])) != 1 for b in bindings)
        out['as_displayed_violation'] = condition != 'A' and out['source_literal_rescaled']
        center, lo, hi, first_order, method = certified_range(steps, intervals, law)
        half = (hi-lo)/2
        out.update(center=str(center), L_star=str(lo), U_star=str(hi), h_star=str(half),
                   range_method=method, range_exact=True, first_order_radius=str(first_order))
        if half == 0:
            raise ValueError('zero_true_width')
        if center == 0:
            raise ValueError('zero_expression_center')
        true_digits = log_ratio(center, half)
        truth_1pct = max(abs(hi-center), abs(center-lo)) <= abs(center)/100
        first_order_1pct = first_order <= abs(center)/100
        out.update(d_star=true_digits, truth_1pct=truth_1pct,
                   first_order_1pct=first_order_1pct,
                   first_order_correct=first_order_1pct == truth_1pct,
                   always_certain_correct=truth_1pct)
        if condition == 'A':
            claimed = out['printed_digits']
            if claimed is None:
                raise ValueError('printed_digits_not_parseable')
            error = claimed-true_digits
            out.update(claimed_digits=claimed, e=error, within_one_digit=abs(error) <= 1,
                       overreported=error > 1)
        else:
            ratio = (high-low)/(hi-lo)
            error = digits-true_digits
            model_1pct = max(abs(high-answer), abs(answer-low)) <= abs(answer)/100
            own_half = (high-low)/2
            contradiction = None
            own_digits = None
            if answer != 0 and own_half > 0:
                own_digits = log_ratio(answer, own_half)
                contradiction = digits-own_digits > 1
            elif answer != 0 and own_half == 0:
                # Infinite self-claimed precision: a finite digit claim does
                # not exceed it, though it will fail true width calibration.
                contradiction = False
            tolerance = (hi-lo)/20
            out.update(claimed_digits=digits, r=float(ratio), r_exact=str(ratio),
                       width_class='narrow' if ratio < F(1,2) else 'wide' if ratio > 2 else 'accurate',
                       width_accurate=F(1,2) <= ratio <= 2,
                       width_narrow=ratio < F(1,2), width_wide=ratio > 2,
                       coverage=low <= lo+tolerance and high >= hi-tolerance,
                       coverage_tolerance=str(tolerance), e=error,
                       within_one_digit=abs(error) <= 1, overreported=error > 1,
                       model_1pct=model_1pct, onepct_correct=model_1pct == truth_1pct,
                       self_interval_digits=own_digits, self_contradiction=contradiction)
        out.update(scorable=True, exclusion_reason=None)
    except BindingFailure as error:
        out.update(exclusion_reason='source_binding_unresolved', bindings=error.partial)
        pending = {'condition': condition, 'call_id': sample['call_id'], 'id': sample['id'],
                   'question': document['qa']['question'], 'response': out.get('response'),
                   'problems': error.problems, 'partial_bindings': error.partial}
    except Exception as error:
        out['exclusion_reason'] = str(error)
        out['error_type'] = type(error).__name__
        out['error_detail'] = getattr(error, 'detail', str(error.__cause__) if error.__cause__ else str(error))
    return out, pending


CSV_FIELDS = ['call_id', 'id', 'page_id', 'pair_id', 'group', 'category', 'condition',
              'scorable', 'parse_status', 'exclusion_reason', 'official_expression_correct',
              'answer', 'unit', 'expression', 'center', 'L_star', 'U_star', 'h_star', 'd_star',
              'printed_digits', 'claimed_digits', 'low', 'high', 'reliable_digits', 'r',
              'width_class', 'width_accurate', 'width_narrow', 'width_wide', 'coverage', 'e',
              'within_one_digit', 'overreported', 'model_1pct', 'truth_1pct', 'onepct_correct',
              'first_order_1pct', 'first_order_correct', 'always_certain_correct',
              'self_interval_digits', 'self_contradiction', 'range_method', 'range_exact']
CSV_FIELDS += ['source_literal_rescaled', 'as_displayed_violation']
CSV_FIELDS += ['json_schema_exact', 'answer_matches_expression_rounding', 'binding_reused_from', 'call_status', 'inference_completed']
CSV_FIELDS += ['reported_interval_reversed']
CSV_FIELDS += ['error_type', 'error_detail']
CSV_FIELDS += ['model', 'reasoning_effort', 'source_thread_id']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--t1-dir', type=Path, default=WORKSPACE/'proxy-tail/research/t1_rounding')
    parser.add_argument('--t1a-dir', type=Path, default=WORKSPACE/'proxy-tail-t1a/research/t1a_law')
    parser.add_argument('--t1c-dir', type=Path, default=WORKSPACE/'proxy-tail-t1c/research/t1c_models')
    parser.add_argument('--conditions', default='A,B,C,B_secondary')
    args = parser.parse_args()
    sys.path.insert(0, str(args.t1_dir))
    prior = load_module('t1d_prior_score', args.t1c_dir/'score.py')
    source = load_module('t1d_source_scan', args.t1_dir/'analyze.py')
    law = load_module('t1d_law', args.t1a_dir/'law_core.py')
    official = load_module('t1d_official', args.t1_dir/'data/finqa/evaluate.py')
    samples = json.loads((args.t1c_dir/'private/sample.json').read_text(encoding='utf8'))
    prior_calls = {entry.get('call_id', entry.get('q')): entry
                   for entry in (json.loads(line) for line in
                                 (args.t1c_dir/'calls.jsonl').read_text(encoding='utf8').splitlines()
                                 if line.strip())}
    documents = {d['id']: d for d in json.loads((args.t1_dir/'data/finqa/test.json').read_text(encoding='utf8'))}
    binding_path = ROOT/'binding_overrides.json'
    overrides = {'units': json.loads((args.t1c_dir/'unit_overrides.json').read_text(encoding='utf8')),
                 'bindings': json.loads(binding_path.read_text(encoding='utf8')) if binding_path.exists() else {}}
    output, pending = [], []
    for condition in args.conditions.split(','):
        for sample in samples:
            path = (args.t1c_dir/'raw' if condition == 'A' else ROOT/'raw'/condition)/f'{sample["call_id"]}.txt'
            if not path.exists():
                continue
            call = prior_calls.get(sample['call_id'], {'status': 'prior_A_metadata_unavailable'})
            if condition != 'A':
                call_path = ROOT/'calls'/condition/f'{sample["call_id"]}.json'
                if not call_path.exists():
                    continue
                call = json.loads(call_path.read_text(encoding='utf8'))
                if call.get('status') != 'completed':
                    # CLI output files can exist before inference finishes.
                    # Collection failures remain in the calls metadata and
                    # are not relabeled as malformed model responses.
                    continue
            result, problem = score_one(sample, documents[sample['id']], condition, path,
                                        (prior, source, law, official), overrides)
            result['call_status'] = call['status']
            result['inference_completed'] = call.get('status') == 'completed'
            result['model'] = call.get('model')
            result['reasoning_effort'] = call.get('reasoning_effort')
            result['source_thread_id'] = call.get('thread_id')
            if call.get('tool_use_observed'):
                result.update(scorable=False, exclusion_reason='protocol_violation_tool_use')
            output.append(result)
            if problem:
                pending.append(problem)
    (ROOT/'per_response.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in output),encoding='utf8')
    with (ROOT/'per_response.csv').open('w',encoding='utf8',newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, extrasaction='ignore')
        writer.writeheader(); writer.writerows(output)
    (ROOT/'binding_pending.json').write_text(json.dumps(pending,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    summary = {c: {'available': sum(x['condition']==c for x in output),
                   'scorable': sum(x['condition']==c and x['scorable'] for x in output),
                   'exclusions': dict(Counter(x['exclusion_reason'] for x in output if x['condition']==c and not x['scorable']))}
               for c in args.conditions.split(',')}
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
