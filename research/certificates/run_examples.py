"""Run frozen, constructed vote examples; no model training or downloads."""
import hashlib
import json
from pathlib import Path
import platform
import time

from research.certificates.collective import certify


def main():
    started=time.perf_counter()
    cases=[dict(name='shared_budget_strict_improvement',votes=[[0,1],[1,0],[0,1],[1,0]],labels=[0,0,1,1],classes=2,budget=1),
           dict(name='component_optima_incompatible',votes=[[1,1,1,2,2],[1,1,1,1,1],[2,2,2,2,2]],labels=[0,1,2],classes=3,budget=1),
           dict(name='no_contamination_perfect',votes=[[0,0,1],[1,1,2],[2,2,0]],labels=[0,1,2],classes=3,budget=0),
           dict(name='all_heads_change',votes=[[0,0,1],[1,1,2],[2,2,0]],labels=[0,1,2],classes=3,budget=3)]
    records=[]
    for case in cases:
        for method in ('component','exact'):
            tick=time.perf_counter()
            result=certify(case['votes'],case['labels'],case['classes'],case['budget'],method)
            records.append(dict(name=case['name'],method=method,result=result,elapsed_seconds=time.perf_counter()-tick))
    root=Path('research/experiments/collective_metrics'); root.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(cases,sort_keys=True,indent=2).encode('utf-8')
    (root/'constructed_inputs.json').write_bytes(raw)
    data=dict(source_level='our_experiment_mathematical_constructed_examples',
              data_sha256=hashlib.sha256(raw).hexdigest(),base_commit='8e4dd0b33c95ac2ac1a6015eba6f2dfafe5c1254',
              checker_sha256=hashlib.sha256(Path('research/certificates/collective.py').read_bytes()).hexdigest(),
              python=platform.python_version(),platform=platform.platform(),processor=platform.processor(),
              elapsed_seconds=time.perf_counter()-started,records=records,
              status='conditional_component_verified; real_model_and_timestamp_premises_unverified')
    (root/'results.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# Collective statistic envelope: actual computation results','',
           'Source of all numbers: our experiment (constructed vote matrices, not real models). Actual computation time %.4f seconds.'%data['elapsed_seconds'],'',
           '| Input | Method | Per-point accuracy | Collective accuracy | Per-point macro-F1 | Collective macro-F1 |','|---|---|---|---|---|---|']
    def show(x):return '['+x['lower_exact']+', '+x['upper_exact']+']'
    for row in records:
        r=row['result']; independent=r['independent']; collective=r['collective']
        lines.append('| '+ ' | '.join([row['name'],row['method'],show(independent['accuracy']),show(collective['accuracy']),
                                       show(independent['macro_f1']),show(collective['macro_f1'])])+' |')
    lines+=['','The first example shows that the jointly-affected-heads constraint can strictly tighten the bounds; the second shows that taking per-class F1 extremes separately gives only an outer envelope, and joint reachability cannot be claimed.',
            '"exact" means exact within the relaxation model in which, for a fixed set, the selected heads can freely change all outputs; it does not mean the real training process can realize every endpoint.',
            'The statistic includes all K fixed classes; a class with zero support and zero predictions contributes 0; classes must not be dropped dynamically after each perturbation.',
            'An actual deployment must first prove separately that the trusted core and the shared components are not changed by contamination, and then set the affected-head budget from a valid audit. These input premises were not verified in this experiment.',
            'This round does not pass G0 or G1 on this basis, and does not claim that the collective poisoning certificate or the macro-F1 optimization is new theory.',
            'The program refuses to output when the state budget or the subset budget is exhausted; the exponential/combinatorial complexity of the current implementation limits large-scale use.']
    (root/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=data['status'],cases=len(cases),methods=2,
                          elapsed_seconds=data['elapsed_seconds'],report=str(root/'report.md'))))


if __name__=='__main__':main()
