"""Render the executed local study without inventing missing measurements."""
import json
from pathlib import Path


def main():
    base=Path('research/experiments/local_foundations')
    r=json.loads((base/'results.json').read_text(encoding='utf-8'))
    audit=json.loads((base/'audit_results.json').read_text(encoding='utf-8'))
    parameters=sorted({x['parameter_count'] for x in r['results']})
    contrast=[x['result']['paired_difference']['macro_f1'] for x in r['paired_main_contrast']]
    # Narrative below is a snapshot of the frozen first experiment. Refuse to
    # silently reuse its interpretation after a changed experiment.
    if not (r['config']['steps']==250 and len(r['config']['seeds'])==3 and
            all(x['estimate']==0 and x['lower']==0 and x['upper']==0 for x in contrast) and
            all(x['metrics']['systems']['prediction']['macro_f1']['estimate']==1
                for x in r['results'] if x['mode'] in ('original_ce','edited_ce','permissions')) and
            all(v['estimate']==0 for x in r['results'] if x['mode'] in ('edited_ce','permissions')
                for v in x['permission_violations'].values()) and
            all(x['metrics']['systems']['prediction']['macro_f1']['estimate']<1
                for x in r['results'] if x['mode']=='shuffled_permissions')):
        raise ValueError('Changed experiment: review narrative before rendering a new report')
    lines=['# Local foundations experiment results', '', 'Date: 2026-11-15. Source level of all numbers: **our experiment (local_foundations)**.', '',
           '## Actual execution and reproduction', '',
           f"CPU; Python {r['python']}, PyTorch {r['torch']}, NumPy {r['numpy']}. Four configurations × three seeds plus one determinism rerun, total time {r['elapsed_seconds']:.2f} seconds; 0 GPU memory, peak RAM not measured.", '',
           f"The data are {r['train_families']} training families and {r['test_families']} test families from later quarters; resampling is by whole company clusters ({r['inference_clusters']} companies); data SHA256 `{r['data_sha256']}`.", '',
           f'Model parameter count: {parameters}, randomly initialized mean embedding + MLP. The training vocabulary comes only from the training families and the predefined edits. No pretraining, GPU, external downloads or private data. 250 full-batch updates per configuration; the same seed gives the same initial weights.', '',
           '```powershell', 'python -m unittest research.local.test_foundations research.local.test_audit -v',
           'python -m research.local.audit','python -m research.local.ablation','python -m research.local.write_report','```','',
           '## Four-configuration, three-seed ablation', '',
           '| Seed | Configuration | Macro-F1 [95% bootstrap CI] | INV violation rate [CI] | LBL violation rate [CI] | REL violation rate [CI] |',
           '|---:|---|---|---|---|---|']
    def fmt(m): return f"{m['estimate']:.4f} [{m['lower']:.4f}, {m['upper']:.4f}]"
    for x in r['results']:
        v=x['permission_violations']
        lines.append(f"| {x['seed']} | {x['mode']} | {fmt(x['metrics']['systems']['prediction']['macro_f1'])} | {fmt(v['INV'])} | {fmt(v['LBL'])} | {fmt(v['REL'])} |")
    lines += ['', 'INV: TV > 0.05; LBL: the predicted label differs before and after the edit; REL: the log-odds change for an edit that truly changes the label is < 0.5. UP constrains only the metric axis and is not imposed on stance; FREE adds no constraint.', '',
              '**The main contrast is permissions − edited_ce**: for all three seeds the macro-F1 difference is 0 and the paired bootstrap interval is [0,0]; full per-class P/R/F1, accuracy, paired results and violation-rate intervals are in `results.json`. This does not prove that the population difference is exactly zero: the test set is saturated, and resampling cannot produce errors that were never observed. A bootstrap interval for 0 violations is also not an exact upper confidence bound on the error rate.', '',
              'The original CE is unstable under some irrelevant appends, but CE with edits is already enough to remove the violations observed in this example; the gain cannot be attributed to the permission term. The shuffled configuration makes errors, but that cannot independently prove that correct permissions add value. In particular, when shuffling assigns REL to an INV/LBL pair whose true labels are the same, the log-odds difference is always 0, so the loss becomes a constant with zero gradient; shuffling also changes the effective gradient composition, so it is not an equal-strength, purely semantic mismatch control. The next version should pre-register a control that can separate permission semantics from effective regularization strength.', '',
              'The explicit stance verbs in this grammar make the task too easy. **Negative conclusion: the current testbed cannot support "the permission loss gives a gain", and cannot serve as evidence that a new model is effective.** The test set will not be tuned further on the basis of this result; the next round should add implicit comparison baselines, negation scope and holder/target binding in a frozen new task, and hold out unused templates/companies/periods.', '',
              f"Determinism check: seed {r['determinism']['seed']}, {r['determinism']['mode']}, retrained weights bitwise equal: {r['determinism']['bitwise_equal']}. This covers only this setting on this machine; it does not guarantee bitwise equality for the old 24M model or across hardware.", '',
              '## Exact audit computation (mathematical inputs, not actual EDGAR scale)', '',
              '| N | n | x | α | Exact K_u | Smallest possible m with favourable ties | Smallest possible m with strict margin |', '|---:|---:|---:|---:|---:|---:|---:|']
    for x in audit['audit_grid']:
        lines.append(f"| {x['N']} | {x['n']} | {x['x']} | {x['alpha']} | {x['upper']} | {x['tie_favourable_min_m']} | {x['strict_margin_min_m']} |")
    lines += ['', 'The minimum shard counts only describe the threshold at which certification is possible under extreme vote patterns such as unanimous votes; they are not the certification coverage a real model would reach. When the sampling fraction of the finite population is high, the 3N/n approximation is clearly too loose. When every item is checked and zero mislabels are found, K_u=0.', '',
              'The implementation compares integer binomial coefficients with a rational α and does not rely on floating-point CDF thresholds. Statistics are summed in the exact rational representation of the input numbers and the binary64 endpoints are rounded outward, while the fractional endpoints are also stored; float inputs are interpreted by their exact binary value. Coverage was checked exhaustively for all N,n,K with N≤12; for three-class votes with m≤6, all reachable replacements were enumerated exhaustively and checked one by one against the reachable-label algorithm. Small-domain exhaustion is an implementation check; the global conclusions rely on the theoretical proofs.', '',
              '## Synthetic world data card', '',
              'Company × quarter, with integer-currency accounting identities (assets = liabilities + equity, revenue = cost + profit); company prices contain independent shocks and announcement effects; author stance is an independent latent variable and is not the same as the revenue direction. Each family stores the text, holder, target, unit/scale, true/recorded time, five kinds of edits and their ground truth. Time is a quarter index relative to the cutoff, not a historical date.', '',
              'Contamination sets the recorded time to 0 only for documents whose true availability time is >0. Output is byte-identical under a fixed seed; the exact k and the accounting identities are checked by tests. The price process is only a simulated environment and supports no investment inference. In this ablation k=0; the contamination mechanism is verified in separate tests and is not mixed into the evaluation task.', '',
              'The text uses only three template sets, the only unit is USD, and real filing restatements / multiple currencies / complex comparison baselines are not simulated. The generator is a controllable test rig; it cannot estimate the parsing error rate on natural text, the real contamination rate, or real investment performance.', '',
              '## Gate status', '',
              'The WP0.5 core mechanism is implemented and tested; template transfer is not verified. The WP0.2 offline smoke test is complete; conclusions on real/harder tasks are missing. The WP0.1 cluster intervals for the old 24M model and the three real baselines are not done. **G0 not passed; no decision on G1 yet.**']
    (base/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__': main()
