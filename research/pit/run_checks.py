"""Finite PIT construction checks and explicit limits; no financial training."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

from research.local.world import generate
from research.pit.pipeline import (FrozenConfig, build_at_cutoff, canonical_history,
    upsert, tombstone, world_adapter, naive_full_log_vocabulary_then_filter,
    naive_full_log_latest_duplicate_then_filter, naive_full_log_size_selects_historical)
from research.pit.seed_checks import run_checks as seed_checks


ROOT = Path(__file__).resolve().parents[1]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def frozen_design():
    return {'world_seed':20261115,'companies':4,'quarters':10,
            'pipeline_seeds':[11,130,2026],'cutoffs':[-5,-2,0,2,4],
            'configs':[
                FrozenConfig(),
                FrozenConfig(lexical_threshold=(1,1),sample_limit=21,
                             development_fraction=(1,3),
                             tokenizer_candidates=((16,1),(32,1),(32,2)),
                             capacity_penalty=(1,10000))],
            'contamination_seed':20261115,'planted_wrong_times':3}


def compare_all_artifacts(left, right):
    if set(left) != set(right):
        raise AssertionError('stable artifact names changed')
    unequal = [name for name in left if left[name] != right[name]]
    if unequal:
        raise AssertionError('future interference in ' + ','.join(unequal))
    return len(left)


def future_variants(base, all_events, cutoff):
    first = base[0]
    revision = upsert(first['document_id'],'future-revision',cutoff+1,
                      'entirely future text xyzzy',record_time=cutoff-5,
                      source='excluded-source',core=True,label='future-label',
                      metadata={'future_rank':99})
    deletion = tombstone(first['document_id'],'future-delete',cutoff+1,record_time=cutoff-7)
    duplicate = upsert('future-copy','future-copy-event',cutoff+1,first['payload']['text'])
    # Opaque bodies are intentional: only legal future headers are in the domain.
    opaque = {'document_id':'opaque','event_id':first['event_id'],
              'knowledge_time':cutoff+1,'payload':object()}
    return {'existing_future':all_events,
            'reordered_future':list(reversed(all_events)),
            'future_revision_metadata':base+[revision],
            'future_tombstone':base+[deletion],
            'future_duplicate':base+[duplicate],
            'future_opaque_body_reused_id':base+[opaque],
            'combined_future':base+[revision,deletion,duplicate,opaque]}


def positive_controls():
    old = [upsert('a','a-v1',0,'old alpha'),upsert('b','b-v1',0,'old beta')]
    unseen = upsert('c','c-v1',1,'unseen future omega')
    duplicate = upsert('copy','copy-v1',1,'old alpha')
    cases = []
    for name, function, extension in [
        ('vocabulary_before_projection',naive_full_log_vocabulary_then_filter,unseen),
        ('latest_duplicate_before_projection',naive_full_log_latest_duplicate_then_filter,duplicate),
        ('full_log_length_selects_old_document',naive_full_log_size_selects_historical,unseen)]:
        before, after = function(old,0), function(old+[extension],0)
        if before == after:
            raise AssertionError('positive control failed to detect ' + name)
        cases.append({'case':name,'before':before,'after':after,'future_interference':True})
    return cases


def metadata_gap():
    path = ROOT/'data/source_audit.json'
    raw = path.read_bytes()
    report = json.loads(raw)
    rows = report['records']
    counts = []
    for year in (2015,2020,2025):
        cutoff = f'{year}-12-31'
        counts.append({'cutoff':cutoff,
                       'claimed_release_on_or_before':sum(r['manifest_published_date']<=cutoff for r in rows),
                       'declared_local_retrieval_on_or_before':sum(r['retrieved_at_declared'][:10]<=cutoff for r in rows),
                       'historical_byte_version_proven':sum(r['historical_byte_version_proven'] and r['manifest_published_date']<=cutoff for r in rows)})
    return {'source':'previous fixed nonrandom 10-document saved-source metadata audit',
            'source_sha256':digest(raw),'n':len(rows),'counts':counts,
            'interpretation':'missing historical-byte evidence is not evidence that the content was unavailable then',
            'limitation':'not a new source audit, not a random population sample, not a real-text pipeline run'}


def run():
    started = time.perf_counter()
    design = frozen_design()
    world = generate(seed=design['world_seed'],companies=design['companies'],quarters=design['quarters'])
    events = world_adapter(world)
    comparisons = byte_checks = 0
    cases = []
    nonempty_development_cases = 0
    for config_index, config in enumerate(design['configs']):
        for seed in design['pipeline_seeds']:
            for cutoff in design['cutoffs']:
                base = [e for e in events if e['knowledge_time'] <= cutoff]
                expected = build_at_cutoff(base,cutoff=cutoff,config=config,seed=seed)
                selection = json.loads(expected['tokenizer_candidates.json'])
                nonempty_development_cases += bool(selection['development_document_ids'])
                for name, extension in future_variants(base,events,cutoff).items():
                    actual = build_at_cutoff(extension,cutoff=cutoff,config=config,seed=seed)
                    byte_checks += compare_all_artifacts(expected,actual)
                    comparisons += 1
                cases.append({'configuration_index':config_index,'seed':seed,'cutoff':cutoff,
                              'visible_events':len(base),
                              'development_documents':len(selection['development_document_ids']),
                              'selected_candidate_index':selection['selected_index'],
                              'artifact_digest_manifest':json.loads(expected['artifact_hashes.json']),
                              'future_variants_compared':7})
    if nonempty_development_cases == 0:
        raise AssertionError('suite failed to exercise historical development selection')

    contaminated = generate(seed=design['contamination_seed'],companies=4,quarters=10,
                            contamination=design['planted_wrong_times'])
    observed = world_adapter(contaminated)
    visible_ids = {doc.document_id for doc in canonical_history(observed,cutoff=0).documents}
    # Only this oracle reads latent time; the learner adapter does not.
    wrong_ids = {row['id'] for row in contaminated if row['recorded_time']<=0<row['available_time']}
    if len(wrong_ids) != design['planted_wrong_times'] or not wrong_ids <= visible_ids:
        raise AssertionError('contamination oracle identity mismatch')
    observed_artifacts = build_at_cutoff(observed,cutoff=0)
    plus_future = observed + [upsert('later','later-event',1,'later harmless observation')]
    compare_all_artifacts(observed_artifacts,build_at_cutoff(plus_future,cutoff=0))
    config_json = {**design,'configs':[asdict(config) for config in design['configs']]}
    result = {'scope':'finite mathematical and implementation checks; no mainline model training',
              'design':config_json,'comparisons':comparisons,'stable_byte_comparisons':byte_checks,
              'artifact_count_per_comparison':len(observed_artifacts),
              'nonempty_development_base_cases':nonempty_development_cases,'base_cases':cases,
              'known_bad_pipeline_positive_controls':positive_controls(),
              'timestamp_truth_counterexample':{
                  'planted_wrong_record_times':len(wrong_ids),
                  'wrong_time_records_admitted':len(wrong_ids & visible_ids),
                  'future_append_invariance_still_passes':True,
                  'conclusion':'record-relative noninterference does not certify true availability'},
              'seed_independence_counterexample':seed_checks(),
              'local_metadata_evidence_gap':metadata_gap(),
              'python':sys.version,'platform':platform.platform(),
              'gpu_used':False,'model_training_performed':False,'peak_memory_measured':False,
              'source_hashes':{name:digest((ROOT/name).read_bytes()) for name in
                  ('pit/pipeline.py','pit/run_checks.py','pit/seed_checks.py','local/world.py','pit/PROTOCOL.md')},
              'elapsed_seconds':time.perf_counter()-started,
              'limitations':['finite suite does not prove universal program correctness',
                             'clock truth, frozen external choices and completeness remain external premises',
                             'byte equality checked directly; digests only index the artifacts',
                             'no real-text model, performance evaluation, historical certificate or novelty verification']}
    destination = ROOT/'pit/results.json'
    destination.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    return result


if __name__ == '__main__':
    result = run()
    print(json.dumps({key:result[key] for key in ('comparisons','stable_byte_comparisons',
          'nonempty_development_base_cases','timestamp_truth_counterexample','elapsed_seconds')},indent=2))
