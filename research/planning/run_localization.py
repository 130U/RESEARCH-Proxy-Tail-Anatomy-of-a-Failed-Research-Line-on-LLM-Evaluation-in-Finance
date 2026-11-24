"""Run only the frozen round-8 artificial localization comparisons, offline.

No training, real audits, network, or private input. Existing threshold_results
and PDF files are read-only. All 48 planned rows are written before work begins;
the worker atomically updates them, so a wall-time limit cannot drop hard cases.
Run from the repository root: python -m research.planning.run_localization
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from math import comb
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time

from research.planning.total_count_design import (
    Budget, BudgetExceeded, optimal_design, risk_dp, risk_greedy,
)
from research.planning.threshold_design import rectangle_design, risk as direct_threshold_risk


DIRECTORY = Path(__file__).resolve().parent
REPOSITORY = DIRECTORY.parent.parent
OUTPUT = DIRECTORY / 'localization_results.json'
ALPHA = Fraction(1, 20)
WALL_SECONDS = 60
BUDGET = Budget()
SOURCE_FILES = [
    DIRECTORY / 'LOCALIZATION_PROTOCOL.md',
    DIRECTORY / 'total_count_design.py',
    DIRECTORY / 'test_total_count_design.py',
    DIRECTORY / 'test_run_localization.py',
    Path(__file__),
    DIRECTORY / 'threshold_design.py',
    DIRECTORY / 'threshold_results.json',
]


def _hashes():
    return {str(p.relative_to(REPOSITORY)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in SOURCE_FILES}


def _write(value):
    temporary = OUTPUT.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    # Windows readers/sync scanners can briefly deny atomic replacement. Retry
    # only explicit access/sharing/locking codes, for at most 0.775 s of sleep.
    # Persistent denials and every unrelated error still propagate; the old
    # committed JSON is never reported as the new completed state.
    delays = (0.025, 0.05, 0.1, 0.2, 0.4)
    for attempt in range(len(delays)+1):
        try:
            temporary.replace(OUTPUT)
            return
        except OSError as error:
            if getattr(error, 'winerror', None) not in {5, 32, 33} or attempt == len(delays):
                raise
            time.sleep(delays[attempt])


def _ceil(value):
    return -(-value.numerator // value.denominator)


def _planned_rows():
    rows = []
    for r in (2, 3, 4, 5, 6):
        for N in (2, 5, 10, 20):
            rows.append(dict(case_id=f'threshold-r{r}-N{N}', family='threshold',
                             N=N, d=2*r-1, k=r, status='pending'))
    for d in (2, 3, 4, 5, 6, 8, 12, 20):
        rows.append(dict(case_id=f'and-d{d}-N2', family='and', N=2, d=d, k=d, status='pending'))
    for L in (1, 2, 5, 10):
        for N in (2, 5, 10, 20):
            rows.append(dict(case_id=f'star-L{L}-N{N}', family='star', N=N, d=L+1,
                             leaves=L, k=2, status='pending'))
    for N in (4, 8, 16, 32):
        r = N*N
        rows.append(dict(case_id=f'sharpness-N{N}', family='sharpness_bounds',
                         N=N, d=2*r-1, k=r, r=r, status='pending'))
    assert len(rows) == 48
    return rows


def _certified_design(samples, risk, source):
    assert risk <= ALPHA
    return dict(samples=list(samples), audit_count=sum(samples), cost_exact=str(sum(samples)),
                risk_exact=str(risk), optimality='exact optimum in stated fixed-allocation class',
                evidence_source=source)


def _frozen_thresholds():
    data = json.loads((DIRECTORY/'threshold_results.json').read_text(encoding='utf-8'))
    expected = {(r, N) for r in (2, 3, 4, 5, 6) for N in (2, 5, 10, 20)}
    indexed = {(row['threshold'], row['layer_population']): row for row in data['rows']}
    if len(data['rows']) != 20 or set(indexed) != expected or Fraction(data['alpha_exact']) != ALPHA:
        raise ValueError('frozen threshold scope/alpha does not match round-8 protocol')
    return indexed


def _threshold_baselines(row, frozen):
    r, N, d = row['k'], row['N'], row['d']
    old = frozen[(r, N)]
    if old['layers'] != d or old['total_population'] != N*d:
        raise ValueError('frozen population metadata mismatch')
    direct_samples = old['direct']['samples']
    direct_risk = direct_threshold_risk(N, direct_samples, r)
    if direct_risk != Fraction(old['direct']['risk_exact']) or sum(direct_samples) != old['direct']['cost']:
        raise ValueError('frozen direct risk/cost mismatch')
    direct = _certified_design(direct_samples, direct_risk,
                               'threshold_results.json: imported optimum; returned allocation risk recomputed')
    old_box = old['rectangle']
    box_samples, bounds = old_box['samples'], old_box['count_upper_box']
    if len(box_samples) != d or len(bounds) != d or sum(b > 0 for b in bounds) >= r:
        raise ValueError('frozen count box is not safe for the threshold target')
    risks = []
    for bound, n in zip(bounds, box_samples):
        if not 0 <= bound <= N or not 0 <= n <= N:
            raise ValueError('invalid frozen box or allocation')
        if bound < N:
            available = N-bound-1
            risks.append(Fraction(comb(available, n), comb(N, n)) if n <= available else Fraction(0))
    box_risk = max(risks, default=Fraction(0))
    closed = rectangle_design(N, d, r, ALPHA)
    if sum(box_samples) != old_box['cost'] or old_box['cost'] != closed['cost'] or box_risk != Fraction(old_box['risk_exact']):
        raise ValueError('frozen box cost/risk disagrees with exact strongest-box formula')
    box = _certified_design(box_samples, box_risk, 'frozen JSON plus strongest joint-zero box formula')
    balanced = old['balanced']
    balanced_risk = risk_greedy((N,)*d, balanced['samples'], r)
    if balanced_risk != Fraction(balanced['risk_exact']) or sum(balanced['samples']) != balanced['cost']:
        raise ValueError('frozen balanced total-count interpretation mismatch')
    row['old_balanced_total_count'] = dict(samples=balanced['samples'], cost_exact=str(balanced['cost']),
                                          risk_exact=str(balanced_risk), optimality='balanced class only')
    return direct, box


def _simple_baselines(row):
    N, d = row['N'], row['d']
    if row['family'] == 'and':
        samples = [N] + [0]*(d-1)
        direct_risk = direct_threshold_risk(N, samples, d)
        source = 'localization_value.md LV5: census one stratum is direct and box optimal'
    else:
        required = _ceil(N*(1-ALPHA))
        samples = [required] + [0]*(d-1)
        direct_risk = Fraction(N-required, N)
        source = 'localization_value.md section 7: center-clean gate is direct and box optimal'
    direct = _certified_design(samples, direct_risk, source)
    box = _certified_design(samples, direct_risk, source)
    row['simple_local_clean_gate'] = dict(samples=samples, cost_exact=str(sum(samples)),
                                         risk_exact=str(direct_risk), optimal=True)
    return direct, box


def _sharpness(row):
    N, r, d = row['N'], row['r'], row['d']
    factor = Fraction(N-1, N)
    count, value = 0, Fraction(1)
    while value > ALPHA:
        count += 1
        value *= factor
    assert 1 <= count <= r
    assert factor**(count-1) > ALPHA and value <= ALPHA
    direct_upper = r+count-1
    total_lower = 2*N*N-N
    total_upper = d
    total_risk = factor**r
    assert total_risk <= ALPHA
    ratio_lower = Fraction(total_lower, direct_upper)
    ratio_upper = Fraction(d, r)
    box_cost = r * _ceil(N*(1-ALPHA))
    assert ratio_lower <= ratio_upper < 2
    assert box_cost > total_upper
    return dict(status='bounds_only', k_N=count,
                direct_feasible_design=dict(compressed_samples=[dict(sample_size=0, strata=r-count),
                                                                 dict(sample_size=1, strata=direct_upper)],
                                            cost_exact=str(direct_upper), risk_exact=str(value)),
                total_count_feasible_design=dict(compressed_samples=[dict(sample_size=1, strata=d)],
                                                 cost_exact=str(total_upper), risk_exact=str(total_risk)),
                direct_optimum_lower_exact=str(r), direct_optimum_upper_exact=str(direct_upper),
                total_count_optimum_lower_exact=str(total_lower), total_count_optimum_upper_exact=str(total_upper),
                box_optimum_cost_exact=str(box_cost), strong_simple_choice_certified='total_count',
                strong_simple_optimum_lower_exact=str(total_lower),
                strong_simple_optimum_upper_exact=str(total_upper),
                total_over_direct_ratio_lower_exact=str(ratio_lower),
                total_over_direct_ratio_upper_exact=str(ratio_upper),
                ratio_semantics='bounds on the ratio of globally optimal costs, not a ratio of selected allocations',
                bounds_source='localization_value.md LV4, r=N^2 path; finite constructions and inequalities',
                globally_exact_costs_computed=False,
                warning='Bounds only; the exact design optimizer is deliberately not run at these dimensions.')


def _compute(row, frozen):
    if row['family'] == 'sharpness_bounds':
        return _sharpness(row)
    direct, box = (_threshold_baselines(row, frozen) if row['family'] == 'threshold'
                   else _simple_baselines(row))
    row['direct'] = direct
    row['box'] = box
    row['every_stratum_in_a_minimal_harmful_configuration'] = True
    total = optimal_design((row['N'],)*row['d'], row['k'], ALPHA, budget=BUDGET)
    assert total['status'] == 'optimal'
    independent_risk = risk_dp((row['N'],)*row['d'], total['samples'], row['k'], budget=BUDGET)
    if independent_risk != Fraction(total['risk_exact']) or independent_risk > ALPHA:
        raise ValueError('returned total-count allocation fails independent DP risk check')
    if sum(total['samples']) != Fraction(total['cost_exact']):
        raise ValueError('total-count unit cost mismatch')
    total['returned_risk_verified_by_independent_dp'] = True
    if row['family'] == 'and':
        kappa, miss = 0, Fraction(1)
        while miss > ALPHA:
            kappa += 1
            miss /= 2
        d = row['d']
        expected = d+1 if d < kappa else (d+kappa+1)//2
        if Fraction(total['cost_exact']) != expected:
            raise ValueError('AND optimum disagrees with the independent closed form')
        row['and_closed_form'] = dict(kappa=kappa, cost_exact=str(expected), matches=True)
    direct_cost = Fraction(direct['cost_exact'])
    box_cost = Fraction(box['cost_exact'])
    total_cost = Fraction(total['cost_exact'])
    simple_cost = min(box_cost, total_cost)
    if direct_cost > simple_cost:
        raise ValueError('computed direct optimum exceeds a valid simple baseline')
    return dict(status='optimal_comparison', total_count=total,
                strong_simple_cost_exact=str(simple_cost),
                strong_simple_choice='tie' if box_cost == total_cost else 'box' if box_cost < total_cost else 'total_count',
                direct_saving_vs_total_exact=str((total_cost-direct_cost)/total_cost),
                direct_saving_vs_strong_simple_exact=str((simple_cost-direct_cost)/simple_cost),
                total_over_direct_ratio_exact=str(total_cost/direct_cost),
                strong_simple_over_direct_ratio_exact=str(simple_cost/direct_cost))


def _worker():
    state = json.loads(OUTPUT.read_text(encoding='utf-8'))
    frozen = _frozen_thresholds()
    for row in state['cases']:
        row['status'] = 'running'
        _write(state)
        started = time.perf_counter()
        try:
            row.update(_compute(row, frozen))
        except BudgetExceeded as error:
            row.update(status='budget_exceeded', error=str(error), globally_exact_costs_computed=False)
        except Exception as error:
            row.update(status='error', error_type=type(error).__name__, error=str(error))
        row['elapsed_seconds'] = round(time.perf_counter()-started, 6)
        _write(state)
    return 0


def _summarize(rows):
    families = {}
    for family in ('threshold', 'and', 'star'):
        group = [row for row in rows if row['family'] == family]
        complete = [row for row in group if row['status'] == 'optimal_comparison']
        summary = dict(planned=len(group), complete=len(complete),
                       strict_direct_gain_vs_total=sum(Fraction(row['direct_saving_vs_total_exact']) > 0 for row in complete),
                       strict_direct_gain_vs_strong_simple=sum(Fraction(row['direct_saving_vs_strong_simple_exact']) > 0 for row in complete))
        if len(complete) == len(group):
            for comparator in ('total', 'strong_simple'):
                values = [Fraction(row[f'direct_saving_vs_{comparator}_exact']) for row in complete]
                summary[f'median_saving_vs_{comparator}_exact'] = str(statistics.median(values))
                summary[f'maximum_saving_vs_{comparator}_exact'] = str(max(values))
        families[family] = summary
    return families


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        return _worker()
    started = time.perf_counter()
    state = dict(status='running', research_status='exploratory artificial mathematical comparisons',
                 created_utc=datetime.now(timezone.utc).isoformat(), alpha_exact=str(ALPHA),
                 target_accuracy_interval_exact=['9/10', '1'], unit_costs=True,
                 real_audit_performed=False, model_trained=False, network_used=False,
                 protocol='research/planning/LOCALIZATION_PROTOCOL.md',
                 runtime=dict(python=platform.python_version(), platform=platform.platform()),
                 budget=dict(wall_seconds=WALL_SECONDS, per_exact_optimization=asdict(BUDGET),
                             peak_memory_measured=False, peak_memory_bytes=None),
                 source_sha256=_hashes(), cases=_planned_rows(),
                 proof_note_at_start=dict(path='research/theory/localization_value.md',
                     sha256=hashlib.sha256((REPOSITORY/'research/theory/localization_value.md').read_bytes()).hexdigest(),
                     role='supporting derivation under concurrent editorial review; not read as executable input'),
                 limitations=[
                     'All populations, vote structures and contamination hypotheses are artificial mathematical inputs.',
                     'Total-count optimum is over fixed stratified uniform zero-finding procedures, not adaptive audits.',
                     'The simple comparator is chosen before audit results: min(strongest safe box, strongest total-count gate).',
                     'Sharpness rows contain bounds and feasible constructions, not computed global optima.',
                     'This extension is exploratory; original threshold cases and favorable comparisons were already seen.',
                     'No historical certificate, model utility, novelty, or G0/G1 passage follows from these checks.'])
    _write(state)
    worker_timed_out = False
    return_code = None
    worker_error = ''
    try:
        run = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'research.planning.run_localization', '--worker'],
                             cwd=REPOSITORY, capture_output=True, text=True, encoding='utf-8',
                             timeout=max(0.1, WALL_SECONDS-(time.perf_counter()-started)-1),
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        return_code = run.returncode
        worker_error = run.stderr.strip()
    except subprocess.TimeoutExpired:
        worker_timed_out = True
    state = json.loads(OUTPUT.read_text(encoding='utf-8'))
    for row in state['cases']:
        if row['status'] in {'pending', 'running'}:
            row.update(status='budget_exceeded' if worker_timed_out else 'worker_failed',
                       error='whole-run wall budget exhausted' if worker_timed_out else worker_error,
                       globally_exact_costs_computed=False)
    state['elapsed_seconds'] = round(time.perf_counter()-started, 6)
    state['wall_timeout'] = worker_timed_out
    state['worker_return_code'] = return_code
    state['source_sha256_after'] = _hashes()
    state['sources_unchanged_during_run'] = state['source_sha256'] == state['source_sha256_after']
    state['summaries'] = _summarize(state['cases'])
    completed = all(row['status'] in {'optimal_comparison', 'bounds_only'} for row in state['cases'])
    state['status'] = 'complete' if completed and state['sources_unchanged_during_run'] else 'incomplete_or_changed_inputs'
    if worker_error:
        state['worker_error'] = worker_error
    _write(state)
    temporary = OUTPUT.with_suffix('.json.tmp')
    if temporary.exists():
        temporary.unlink()
    print(json.dumps(dict(status=state['status'], cases=len(state['cases']),
                          elapsed_seconds=state['elapsed_seconds'], wall_timeout=worker_timed_out,
                          statuses={status: sum(row['status'] == status for row in state['cases'])
                                    for status in sorted({row['status'] for row in state['cases']})},
                          summaries=state['summaries']), ensure_ascii=False, indent=2))
    return 0 if state['status'] == 'complete' else 2


if __name__ == '__main__':
    raise SystemExit(main())
