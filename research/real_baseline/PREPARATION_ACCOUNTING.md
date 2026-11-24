# Preparation count reconciliation: source rows, entity occurrences and conflict keys must not be added together

Date: 2026-11-16. Nature: a supplementary read-only accounting in response to the independent review's comments. No data were regenerated, re-split or trained on, and the frozen `prepare.py`, manifest and rows/split files were not modified; there was no network access. The public output contains only aggregate counts, with no headlines, entity names or per-row labels.

**The two correct main ledgers are `10,753 = 13 + 10,740` (source rows) and `14,371 = 14 + 73 + 14,284` (entity-label occurrences after successful parsing).** The 13 anomalous source rows, 7 conflict keys and 73 duplicate entity occurrences in the original report use three different counting units and cannot be subtracted directly from the same total.

## Evidence and counting method

First, [prepare.py](prepare.py) and the frozen [aggregate_manifest.json](aggregate_manifest.json) were read, read-only. The original manifest is enough to explain the variable definitions and gives some of the equations, but it does not directly record "the total number of successfully parsed entity occurrences" or "the total number of entity occurrences covered by conflict keys"; from the 7 conflict keys alone one cannot infer whether 7 or 14 entity occurrences were removed.

To fill the missing items, this round again read, read-only, the same byte version of the local original CSV, and used the frozen strict parsing/normalization functions to compute entity–headline keys and their occurrence counts. Only counting was done: the preparer's `run` was not called, no row-level files were written, and no private predictions or model scores were read. This supplementary accounting reuses the established parsing definitions and **is not a new independent annotation of the source label semantics**. It took about 0.220020 seconds, and all reconciliation assertions passed; the original manifest was byte-identical before and after reading.

Fixed fingerprints:

- Source CSV SHA256: `570af7ba58f724f3fcc414dd5ba80da5b1a3b342134d76c6ebdf53a32c54a92f`.
- Frozen prepare.py SHA256: `c7f56b29875b6e76b7d2201cb4de6bea329c97b3582523218424096af53af06c`.
- Frozen aggregate manifest SHA256: `6a8e8175bbbe391e866528e8b9d1e35fb3292c9d693da61948a4a91a44eac212`.
- Private rows SHA256 recorded by the frozen manifest: `8ab314ebd74680466f3a24055433f3a44d442107773607204cd3983122d87567`; this round did not reread or rewrite that row-level product.

## Layer one: raw CSV source rows

| Quantity | Unit | Count | Basis |
|---|---|---:|---|
| Raw input | CSV source rows | 10,753 | Frozen manifest; the supplementary read-only count agrees |
| Strict literal-syntax parse failures | CSV source rows | 13 | Frozen manifest; the supplementary count confirms the only cause is syntax errors |
| Successfully parsed and entering entity expansion | CSV source rows | 10,740 | Frozen manifest; the supplementary count agrees |
| Sources with at least one finally retained entity key | Distinct CSV source rows | 10,726 | Supplementary count; equals the sum of source_rows_represented over partitions |
| Parsed but without any finally retained entity key | Distinct CSV source rows | 14 | Supplementary count in this round |

The reconciliation is:

```text
10,753 = 13 + 10,740
10,740 = 14 + 10,726
10,753 = 13 + 14 + 10,726
```

Each of these 14 rows involves a conflict key and has no other non-conflicting entity to keep; the number of source rows that involve a conflict and still keep another entity is 0. So in this data version, 27 source rows contribute no retained entity at all. **This is not the general formula `anomalous rows + 2×conflict keys`**: in other data one conflict key can repeat more times, the same row can contain several conflict keys, and a row can also contain other valid entities at the same time.

## Layer two: entity-label occurrences and final samples

An "entity-label occurrence" is one entity→label record in the dictionary of a successfully parsed source row; the same entity–headline appearing again in a different source row is counted again. A "key" is `(normalized headline, normalized entity)`; a "final sample" is the one sample kept per key after the conflict check. Different labels for different entities are legitimate and are not conflicts.

| Quantity | Unit | Count | Basis |
|---|---|---:|---|
| All entity-label records in successfully parsed source rows | Entity occurrences | 14,371 | Supplementary count in this round |
| All distinct normalized headline + entity keys | Distinct keys | 14,291 | Supplementary count in this round |
| Keys with at least two different source labels | Conflict keys | 7 | Frozen manifest and supplementary count agree |
| All records contained in these conflict keys | Entity occurrences | 14 | Supplementary count in this round; here exactly 2 per key |
| All records contained in non-conflict keys | Entity occurrences | 14,357 | Supplementary count in this round |
| Extra occurrences merged within non-conflict keys | Entity occurrences | 73 | Frozen manifest and supplementary count agree |
| Non-conflict keys / final samples | Distinct keys / samples | 14,284 | Frozen manifest and supplementary count agree |

The full reconciliation is:

```text
14,371 = 14 (all conflict records quarantined) + 14,357 (non-conflict records)
14,357 = 73 (extra occurrences duplicating the same label) + 14,284 (final samples)
14,371 = 14 + 73 + 14,284

14,291 (all distinct keys) = 7 (conflict keys) + 14,284 (non-conflict keys)
14,371 − 14,291 = 80 (occurrences beyond the first, over all keys)
80 = 73 (extra occurrences of non-conflict keys) + 7 (occurrences beyond the first in conflict keys)
```

73 does not mean that 73 headlines or 73 source rows were deleted; it is the number of extra entity occurrences merged into retained keys. Conflict keys are quarantined as a whole first and never enter the `merged_duplicate_entity_title_occurrences` count. Nor is 7 the complete record count of 7 deleted samples, because all 14 occurrences they involve are excluded.

The 13 and the 7 in `quarantine_reasons` correspond to different `stage`s: in the former each quarantine record represents one source row, in the latter each quarantine record represents one conflict key with all its members. They can be added to give 20 quarantine record objects of different types, but cannot be called 20 source rows or 20 entity labels.

## Layer three: cross-checks of headlines, partitions and clusters

The full input has 10,686 normalized headlines; the final samples cover 10,666. The supplementary count found 13 headlines unique to syntax anomalies and 7 headlines unique to conflicts, with an intersection of 0, and none of these headlines has a retained entity, so:

```text
10,686 = 13 + 7 + 10,666 (normalized headlines)
10,666 = 7,494 train + 1,595 development + 1,577 test
10,726 = 7,537 train + 1,606 development + 1,583 test (source-row coverage)
14,284 = 10,041 train + 2,136 development + 2,107 test (final entity samples)
14,284 = 3,788 negative + 5,456 neutral + 5,040 positive
10,591 = 7,438 train + 1,583 development + 1,570 test (retained lexical clusters)
```

These partition and class counts all come from the original manifest and agree with the totals the supplementary count needed to check. Source IDs, headlines and families do not cross partitions, so the corresponding partition counts can be summed. Lexical clusters are another unit: all valid headlines first give 10,611 lexical connected components, of which the finally retained samples involve 10,591; the number of lexical clusters must not be taken as the number of entity samples or of reviewed semantic events.

## Quantities that cannot be recovered or claimed yet

1. **The number of entity labels that the 13 syntactically anomalous source rows were "meant to express" is unknown.** This round did not recover them by regex repair, manual guessing or AI interpretation. So 14,371 is the number of entity occurrences in successfully and strictly parsed rows; it cannot be called the complete total of intended labels in the whole original CSV, nor can an unverified count of anomalous labels be added to match an external report.
2. The original manifest by itself did not record the total number of occurrences of conflict members; this round's 14 comes from a supplementary read-only accounting on the fixed input. If the data version changes in future, the observation "exactly two per conflict key" cannot be reused.
3. The reconciliation proves that the counts are self-consistent under the current preparation rules; it does not prove that the source label semantics are correct, that the security mapping is correct, that events are independent, or that the historical information set has no leakage. It did not change the estimand of the original experiment, nor rename seen data as a new confirmation set.

The notes above complete the explanation of the counts without modifying the frozen data or the original experimental results.
