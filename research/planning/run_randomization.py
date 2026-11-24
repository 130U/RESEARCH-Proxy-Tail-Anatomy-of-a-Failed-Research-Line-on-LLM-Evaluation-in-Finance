"""Offline round-9 exact comparisons; no training, network or real audits."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import platform
import statistics
import time

from research.planning.randomized_audit import (
    randomized_risk, pooled_srs_risk,
    minimum_randomized_audits, minimum_pooled_audits,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUTPUT = HERE / 'randomization_results.json'
ALPHA = Fraction(1, 20)
WALL_SECONDS = 30
SOURCES = [Path(__file__), HERE/'randomized_audit.py',
           HERE/'test_randomized_audit.py', HERE/'RANDOMIZATION_PROTOCOL.md',
           HERE/'localization_results.json']


def hashes():
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in SOURCES}


def write_output(data):
    temporary = OUTPUT.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    delays = (0.025, 0.05, 0.1, 0.2, 0.4)
    for attempt in range(len(delays)+1):
        try:
            temporary.replace(OUTPUT)
            return
        except OSError as error:
            if getattr(error, 'winerror', None) not in {5, 32, 33} or attempt == len(delays):
                raise
            time.sleep(delays[attempt])


def planned():
    old = json.loads((HERE/'localization_results.json').read_text(encoding='utf-8'))
    if old['status'] != 'complete' or Fraction(old['alpha_exact']) != ALPHA:
        raise ValueError('round-8 source must be complete with matching alpha')
    expected = {f'threshold-r{r}-N{N}' for r in (2,3,4,5,6) for N in (2,5,10,20)}
    expected |= {f'and-d{d}-N2' for d in (2,3,4,5,6,8,12,20)}
    expected |= {f'sharpness-N{N}' for N in (4,8,16,32)}
    selected = [row for row in old['cases'] if row['family'] != 'star']
    if len(selected) != 32 or {r['case_id'] for r in selected} != expected:
        raise ValueError('round-9 frozen scope mismatch')
    rows = []
    for old_row in selected:
        row = {k: old_row[k] for k in ('case_id','family','N','d','k')}
        row['status'] = 'pending'
        if old_row['family'] == 'sharpness_bounds':
            if old_row['status'] != 'bounds_only':
                raise ValueError('sharp rows must remain bounds only for fixed quotas')
            row['fixed_direct_cost_bounds'] = [int(old_row['direct_optimum_lower_exact']),
                                               int(old_row['direct_optimum_upper_exact'])]
            row['fixed_simple_portfolio_cost_bounds'] = [int(old_row['strong_simple_optimum_lower_exact']),
                                                         int(old_row['strong_simple_optimum_upper_exact'])]
            row['fixed_costs_exact'] = False
        else:
            if old_row['status'] != 'optimal_comparison':
                raise ValueError('fixed quota comparison not complete')
            c = int(old_row['direct']['cost_exact'])
            p = int(old_row['strong_simple_cost_exact'])
            row['fixed_direct_cost_bounds'] = [c, c]
            row['fixed_simple_portfolio_cost_bounds'] = [p, p]
            row['fixed_costs_exact'] = True
        rows.append(row)
    return rows


def solve(row):
    N, d, r = row['N'], row['d'], row['k']
    for name, search, risk in (
        ('randomized_optimal', minimum_randomized_audits, randomized_risk),
        ('pooled_srs_optimal', minimum_pooled_audits, pooled_srs_risk),
    ):
        m = search(N, d, r, ALPHA)
        value = risk(N, d, r, m)
        previous = risk(N, d, r, m-1) if m else None
        if value > ALPHA or (previous is not None and previous <= ALPHA):
            raise AssertionError('returned integer audit budget is not minimal')
        row[name] = dict(audits=m, risk_exact=str(value),
                         previous_audits_risk_exact=None if previous is None else str(previous))
    m, pooled = row['randomized_optimal']['audits'], row['pooled_srs_optimal']['audits']
    if not m <= pooled or not m <= row['fixed_direct_cost_bounds'][1]:
        raise AssertionError('larger design class has higher claimed optimum')
    q, t = divmod(m, N)
    row['randomized_optimal']['construction'] = dict(full_strata=q, partial_documents=t,
        selection='uniform random ordered distinct strata; uniform documents in the partial stratum')
    row['saving_vs_pooled_exact'] = str(Fraction(pooled-m, pooled))
    lo, hi = row['fixed_direct_cost_bounds']
    row['saving_vs_fixed_direct_bounds_exact'] = [str(Fraction(lo-m,lo)), str(Fraction(hi-m,hi))]
    row['status'] = 'complete'


def table(data):
    lines = ['# Arbitrary random quotas: complete 32-cell results', '',
             'All inputs are hand-made homogeneous threshold structures, α=1/20; all zero findings must output the fixed interval, and the true bad set is fixed in advance.',
             'The randomized method is minimax optimal within the restricted output class; pooled is optimal within the whole-population SRS class. The fixed-quota sharp rows keep their bounds.',
             'Sources: [JSON](randomization_results.json), [protocol](RANDOMIZATION_PROTOCOL.md), [proof](../theory/randomized_audit.md).',
             f"JSON SHA256: `{hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}`.", '',
             '| Case | d | r | N | Randomized optimum | pooled optimum | Fixed direct optimum or bounds | Fixed simple-combination optimum or bounds | Randomized-method risk (approx.) |',
             '|---|---:|---:|---:|---:|---:|---|---|---:|']
    for row in data['cases']:
        if row['status'] != 'complete':
            lines.append(f"| {row['case_id']} | {row['d']} | {row['k']} | {row['N']} | {row['status']} | — | — | — | — |")
            continue
        def display(bounds):
            return str(bounds[0]) if bounds[0] == bounds[1] else f'[{bounds[0]},{bounds[1]}]'
        lines.append(f"| {row['case_id']} | {row['d']} | {row['k']} | {row['N']} | "
                     f"{row['randomized_optimal']['audits']} | {row['pooled_srs_optimal']['audits']} | "
                     f"{display(row['fixed_direct_cost_bounds'])} | {display(row['fixed_simple_portfolio_cost_bounds'])} | "
                     f"{float(Fraction(row['randomized_optimal']['risk_exact'])):.8f} |")
    lines += ['', 'Exact risks and the risks with one document fewer are in the JSON; decimals are for display only and are not used for decisions. The 16 star structures are asymmetric and are explicitly outside the scope of this theorem.',
              'Relative gains only describe the hand-made structures and the specified output convention; they are not a natural-model certificate, originality, or a G0/G1 pass.']
    (HERE/'randomization_table.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')


def main():
    start = time.perf_counter()
    data = dict(status='running', created_utc=datetime.now(timezone.utc).isoformat(),
                research_status='exploratory artificial mathematical comparisons', alpha_exact=str(ALPHA),
                output_contract='All zero findings must output fixed I; any finding outputs the full range.',
                sampling_class='arbitrary distributions on distinct m-document audit subsets; truth fixed before randomization',
                network_used=False, real_audit_performed=False, model_trained=False,
                runtime=dict(python=platform.python_version(), platform=platform.platform()),
                budget=dict(wall_seconds=WALL_SECONDS, peak_memory_measured=False),
                source_sha256=hashes(), cases=planned())
    write_output(data)
    try:
        for row in data['cases']:
            if time.perf_counter()-start > WALL_SECONDS:
                raise TimeoutError('round-9 wall budget exceeded; pending rows retained')
            tick = time.perf_counter()
            solve(row)
            row['elapsed_seconds'] = round(time.perf_counter()-tick, 6)
        data['source_sha256_after'] = hashes()
        data['sources_unchanged_during_run'] = data['source_sha256_after'] == data['source_sha256']
        if not data['sources_unchanged_during_run']:
            raise RuntimeError('executable inputs changed during the run')
        data['summaries'] = {}
        for family in ('threshold','and','sharpness_bounds'):
            subset = [row for row in data['cases'] if row['family'] == family]
            savings = [Fraction(row['saving_vs_pooled_exact']) for row in subset]
            data['summaries'][family] = dict(cases=len(subset),
                strict_gain_vs_pooled=sum(value>0 for value in savings),
                median_saving_vs_pooled_exact=str(statistics.median(savings)),
                strict_gain_vs_fixed_direct_lower=sum(row['randomized_optimal']['audits'] < row['fixed_direct_cost_bounds'][0] for row in subset))
        data['status'] = 'complete'
    except Exception as error:
        data['status'] = 'failed'
        data['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        data['elapsed_seconds'] = round(time.perf_counter()-start, 6)
        write_output(data)
        table(data)
    print(json.dumps(dict(status=data['status'], rows=len(data['cases']), elapsed_seconds=data['elapsed_seconds'],
                          summaries=data['summaries']), ensure_ascii=False))


if __name__ == '__main__':
    main()
