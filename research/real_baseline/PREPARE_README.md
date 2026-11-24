# Real Phase 0: private data preparation for the original source task

This tool only prepares SEntFiN's original **entity-level sentiment**, with the label order fixed as `negative, neutral, positive`; the labels are not renamed as investment stances. It loads no old model, does no training and accesses no network. The real execution uses this round's [pre-registered protocol and budget](PROTOCOL.md); the executed status is recorded at the end.

## Fixed contract

The input is the local original CSV, with header order strictly `S No.,Title,Decisions,Words`. All lexical connected clusters are first built from the valid headlines, and only after that are labels read to decide retention or quarantine; so labels play no part in similarity, group identity or the split. Even if a label is later quarantined, its valid headline can still connect near-duplicate headlines, so that changes in label status do not split the similarity graph.

Normalization is Unicode NFKC, casefold and whitespace folding, keeping digits. All entities of identical headlines must be in the same cluster; lexical near duplicates use Unicode `\w+` token sets with exact Jaccard≥4/5 and transitive merging. With tokens ordered by global frequency, the safe prefix length is `|X|−ceil(.8|X|)+1`, and candidate pairs are then verified with the integer test `5*intersection≥4*union`. If the similarity reaches the threshold, the earliest common token must fall in the prefixes of both sets; otherwise the intersection would be smaller than `ceil(.8|X|)` or `ceil(.8|Y|)`, contradicting the Jaccard threshold. So this is not approximate MinHash; the tests compare against a complete all-pairs computation. Headlines with empty token sets do not compute 0/0 and are not joined to each other; only those whose normalized forms are identical are merged.

`Decisions` is first parsed with `ast.parse(mode='eval')`, the raw Dict keys are checked and raw/normalized duplicate entity keys are rejected, and then `ast.literal_eval` is applied; `eval` is forbidden. Non-dictionaries, anomalous syntax, empty keys, unknown labels, duplicate keys and so on quarantine the whole row, with no guessed repair. Different labels across rows for the same normalized headline and the same normalized entity are all quarantined; different labels for different entities in the same headline are legitimate multi-target supervision. Identical headline + entity + label keeps only one sample, keeping all source IDs, to avoid duplicate weighting. Different labels on near-duplicate but non-identical headlines are kept, but must be in the same cluster. All records with a duplicate source ID are quarantined.

The family ID is the SHA256 of the sorted complete normalized member headlines; the split uses a hash of the family ID with fixed seed=130, with integer boundaries 70% train / 15% development / 15% test. The proportions are the design proportions of a deterministic hash assignment; actual sample proportions are not forced to match, and there is no re-splitting by label or performance. If any partition is empty, the real CLI refuses to output and does not change the seed. After partitioning, it checks that ids are unique, that no family crosses splits, that 0 normalized headlines cross splits and that 0 near-duplicate edges cross splits, and reports the largest connected component.

Entities that do not appear literally are not deleted; presence is counted separately as an exact raw substring and as a normalized substring; this is not a claim that entity identity or the security mapping has been verified. This split **is not a time split and has not completed semantic event deduplication**. Lexical clusters give only the isolation of the current algorithm and do not prove future or event independence; downstream training vectorizers may be fitted only on train.

## Private schema and products

All row-level products are written only to `research/private/<run-directory>/`, by default `research/private/real_baseline/`. Existing products are not overwritten. The original old repository is read-only.

Each line of `rows.jsonl` and of `train.jsonl`, `development.jsonl`, `test.jsonl` contains:

- `id`: a stable sample hash of the normalized headline and entity; `headline`, `target`: the retained source text and entity.
- `label`, `label_id`: the original task label and the fixed 0/1/2; `family_id`, `split`: the lexical cluster and the frozen partition.
- `source_ids`: all original source numbers of the merged duplicate samples.
- `input_text`: `[ENTITY] target`, a newline, then `[TITLE] headline`, keeping the target field.
- `entity_literal_substring`, `entity_normalized_substring`: target-presence diagnostics, not used as deletion conditions.

`quarantine.jsonl` holds the private anomaly details, with a fixed reason, the line number and the source fields that need review; it does not appear in public reports. `aggregate_manifest.json` can be shared; it has only totals, per-class/per-partition counts, conflict-type counts, the largest cluster, the number of deduplication comparisons, quarantine checks, and input and product hashes; it contains no per-row text, labels, group members or predictions.

```powershell
& '..\130U-FinLLM\.venv\Scripts\python.exe' -X utf8 -m unittest research.real_baseline.test_prepare -v
& '..\130U-FinLLM\.venv\Scripts\python.exe' -X utf8 -m research.real_baseline.prepare --source '../130U-FinLLM/data/raw/candidates/sentfin/SEntFiN.csv'
```

The unit tests use only hand-made synthetic examples, with no real news text. The public preparation code does not print text after reading SEntFiN rows; the CLI prints only aggregate counts. This document does not replace the parent task's training pre-registration, and does not interpret the existing licence records as full verification of third-party publishers' rights.

## Executed: 2026-11-16

Run after the parent task confirmed that the pre-registration and the private-directory exclusion check were complete. The 12 synthetic tests passed, the latest run taking about 0.020 seconds; among them, prefix filtering and the all-pairs oracle agree edge for edge on all subsets of 7 tokens and on fixed random sets / length boundaries. This is an implementation check; the global reason why candidates miss no edge is still the prefix argument above.

The real preparation run used Python 3.12.14 and took 0.766725 seconds; peak memory not measured; GPU/network requests/training tokens all 0. The SHA256 of the original CSV matches the pre-registered value, and 10,753 rows were read strictly; the original file was not modified. The public numbers come from [aggregate_manifest.json](aggregate_manifest.json), and all per-row results stay in the private directory.

| Item | Observed in this round |
|---|---:|
| Whole rows quarantined for syntax anomalies | 13 |
| Conflict keys (same normalized headline + entity, different labels) quarantined | 7 |
| Extra occurrences merged for identical headline + entity + label | 73 |
| Retained entity samples / lexical clusters | 14,284 / 10,591 |
| Retained samples whose entity is not a raw literal substring | 19 |
| Normalized headlines / lexical connected components in the full input | 10,686 / 10,611 |
| Exact Jaccard comparisons / edges meeting the threshold | 40,488 / 77 |
| Normalized headlines / retained samples in the largest connected component | 3 / 7 |
| family / normalized headlines / near-duplicate edges crossing splits | 0 / 0 / 0 |

13 is the number of whole-row parse anomalies and 7 is the number of conflicting entity–headline keys; they cannot be added and called "20 source file rows". Label anomalies were not repaired by guessing; different retained entities can legitimately have different labels.

| split | Samples | Lexical clusters | negative | neutral | positive |
|---|---:|---:|---:|---:|---:|
| train | 10,041 | 7,438 | 2,658 | 3,831 | 3,552 |
| development | 2,136 | 1,583 | 572 | 838 | 726 |
| test | 2,107 | 1,570 | 558 | 787 | 762 |

All three partitions have support for all three classes, and no giant connected cluster appeared; the seed was not re-chosen and the grouping was not changed because of these results. The SHA256 of the private `rows.jsonl` is `8ab314ebd74680466f3a24055433f3a44d442107773607204cd3983122d87567`. The SHA256 of the preparation source is `c7f56b29875b6e76b7d2201cb4de6bea329c97b3582523218424096af53af06c`; the fingerprints of the full partition and quarantine files are in the aggregate manifest. The downstream trainer should first verify these fingerprints and then use an independently frozen entity-marking transformation; the raw `input_text` is not feature text that has already had the `TARGET_ENTITY` replacement applied.

These are data preparation results for the original real-source task; there is no model-performance conclusion, and they do not prove complete event independence, absence of historical look-ahead, or that this project's investment-stance gold standard has been established.
