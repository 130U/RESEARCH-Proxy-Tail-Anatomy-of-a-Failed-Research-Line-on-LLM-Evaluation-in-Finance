"""Run offline checks. Add --train to repeat the frozen synthetic smoke study."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--train',action='store_true')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    tests=['research.local.test_foundations','research.local.test_audit','research.evaluation.test_evaluate',
           'research.certificates.test_collective','research.planning.test_audit_frontier',
           'research.planning.test_impact_audit','research.planning.test_threshold_design',
           'research.planning.test_total_count_design',
           'research.planning.test_run_localization',
           'research.planning.test_randomized_audit',
           'research.real_baseline.test_prepare',
           'research.real_baseline.test_train_baselines','research.real_baseline.test_bootstrap_results',
           'research.pit.test_pipeline','research.numeric.test_semantic_envelope']
    if (root/'research/xbrl/test_parse_local.py').exists(): tests.append('research.xbrl.test_parse_local')
    commands=[['-m','unittest',*tests,'-v'], ['-m','research.local.audit'],
              ['research/checks/theory_checks.py','--output','research/checks/results.json'],
              ['-m','research.certificates.run_examples'],['-m','research.planning.audit_frontier'],
              ['-m','research.certificates.collective',
               'research/experiments/collective_metrics/audit_example.json',
               'research/experiments/collective_metrics/audit_certificate.json','--method','exact'],
              ['-m','research.planning.threshold_design'],
              ['research/data/fomc_source_audit.py','--self-test'],
              ['-m','research.pit.run_checks'],
              ['-m','research.numeric.run_checks'], ['-m','research.planning.run_localization'],
              ['-m','research.planning.run_randomization']]
    if args.train: commands += [['-m','research.local.ablation'],['-m','research.local.write_report']]
    logs=[]
    for command in commands:
        tick=time.perf_counter()
        run=subprocess.run([sys.executable,*command],cwd=root,text=True,capture_output=True,encoding='utf-8',errors='replace')
        print(run.stdout); print(run.stderr,file=sys.stderr)
        logs.append(dict(command=[sys.executable,*command],returncode=run.returncode,
                         elapsed_seconds=time.perf_counter()-tick,stdout=run.stdout,stderr=run.stderr))
        if run.returncode:
            (root/'research/reproduction_log.json').write_text(json.dumps(logs,ensure_ascii=False,indent=2),encoding='utf-8')
            raise SystemExit(run.returncode)
    (root/'research/reproduction_log.json').write_text(json.dumps(logs,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':main()
