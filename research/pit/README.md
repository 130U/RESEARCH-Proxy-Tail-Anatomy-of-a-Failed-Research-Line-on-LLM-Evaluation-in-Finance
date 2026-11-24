# T1.1 reference implementation of a historical snapshot pipeline

This is a set of pure-standard-library constructive components with no model training, implemented according to the [pre-execution protocol](PROTOCOL.md). It tests the code dependency chain of "depending only on information before the given knowledge cutoff"; it does not certify that source times are true, is not a new financial model, and is not evidence of the paper's novelty. The interfaces below do not read real private corpora and do not access the network.

## Event log and valid input domain

Each upsert is a complete state, not a patch that reads fields from "the current latest object". An event contains `event_id,document_id,knowledge_time,record_time,operation,payload`. An upsert's payload contains `text,content_sha256,source,core,label,metadata`; a tombstone's payload is null. Labels, even when not used to fit the vocabulary, are versioned together with the source, core marker and metadata, and must not be written back into old states in the future.

`knowledge_time` is **the time at which this complete state is claimed to have become knowable**, and determines the projection and version selection; `record_time` is the retained time claimed by the original record and cannot replace the knowledge time. A revision can have a new knowledge_time while keeping the old record_time. A visible record requires integers and `record_time≤knowledge_time`; this is only an internal-consistency check of the declarations. That the knowledge time is no earlier than the true time at which every field (content, label, source/core, rule metadata and so on) became known is an **external premise**; the current implementation has no per-field evidence of when each field became known, and cannot claim to have verified it.

The valid outer domain is a finite list/tuple whose elements are dictionaries, with non-empty string event/document IDs in the header and a non-bool integer knowledge_time. Reading the outer header is necessary to determine the projection; arbitrarily corrupted headers are outside the domain of the "invariant under future appends" promise. For events with a valid header and knowledge_time>cutoff, the program does not read, validate, serialize or hash the payload; even if a future payload has the wrong type, a bad hash or missing body fields, past results do not change.

Project first, then check, for **all visible events**, the full schema, declared hash, label/metadata types, the record_time constraint and uniqueness of visible event_ids, and then take the latest state of each document_id in ascending `(knowledge_time,event_id)` order. This deterministic tie rule does not use input line numbers; the event_id itself must be historically frozen. A future event_id that duplicates an old event_id does not make the old snapshot fail; it is rejected as a visible-log conflict only once it becomes visible. A future tombstone does not delete the old snapshot; when it takes effect it deletes the latest active object. Retroactively modifying an old event, or appending an event whose knowledge time is also retroactive, is not a valid "pure future append".

An append-only log, integrity, true time semantics and tamper resistance are all parts of the data-provenance contract; this module is a projection and processing function, and does not implement tamper-proof storage or an authenticated time service.

## Stable products and historical equivalence

`HistoricalSnapshot` keeps the canonicalized **full history of visible events** and the active documents restored from it; historical equivalence means that this projection is the same under the same cutoff, not merely that the final active documents are the same. Even if two logs end with the same active documents, the history hash can differ if their past revision histories differ. The full-log hash, the whole-corpus length, the number of future exclusions and the run time do not enter any stable product.

The main entry point is:

```python
from research.pit.pipeline import FrozenConfig, build_at_cutoff, world_adapter
from research.local.world import generate

events = world_adapter(generate(companies=4, quarters=6, contamination=0))
artifacts = build_at_cutoff(events, cutoff=0, config=FrozenConfig(), seed=130)
# artifacts: dict[str, bytes], for the caller to save or compare item by item.
```

The lower-level entry point `canonical_history(events,cutoff=...)` returns a snapshot, and `run_pipeline(snapshot,cutoff=...,config=...,seed=...)` re-checks that its canonicalized history agrees with the documents and binds the cutoff. A snapshot that directly forges different documents or mixes in future history is rejected; this is not a cryptographic proof of historical integrity. An arbitrary hand-made State is not an independently certified object; the guarantees of the six stages apply to states produced by the main entry point from a verified snapshot, and to their composition. Each stage still rejects input with an inconsistent cutoff or a recorded knowledge time later than the cutoff.

The stable files are: `configuration.json`, `history.json`, `snapshot.json`, `filter.json`, `deduplicate.json`, `sample.json`, `split.json`, `tokenizer_candidates.json`, `selected_tokenizer.json`, `artifact_hashes.json`. They are canonically ordered UTF-8 JSON bytes with no run clock. For the same historical projection, code version, exogenous configuration and seed, in the same Python/Unicode-normalization runtime, all stages should be byte-identical; determinism across Unicode versions is not claimed. The runtime version/hash, timing and full-log operational information are placed by the external runner in a separate record and must not be mixed into the "invariant" objects.

## Six components with an explicit cutoff

1. `filter_documents`: may only read the snapshot and filters by the exogenous allowed_sources and require_core; it tokenizes with fixed Unicode NFKC/casefold/whitespace rules and `\w+`, then removes the exogenous stopwords. The truth of source/core is not proven by a boolean check.
2. `deduplicate`: only on the historical filter result, joins an edge when the normalized full text is an exact duplicate or the non-empty token-set Jaccard reaches a fixed rational threshold, and performs a deterministic transitive merge. The representative is the one with the earliest knowledge time, then by document/event ID. Empty token sets are not joined to each other through 0/0. This reference implementation uses an all-pairs check, with a budgeted scale of at most 1,000 events; it does not build clusters through future near-duplicate bridges.
3. `sample_documents`: takes sample_limit using an independent exogenous seed and a fixed hash ordering of **historical document IDs**. It does not use the whole-corpus length, the full-log hash, the number of future candidates, or let future objects consume the random stream first. The ID hash under a fixed configuration is an ordering tool, not a provenance proof.
4. `split_documents`: uses another fixed hash namespace and seed to divide the historical sample into train/development. It does not look at the future to fill up the development set. It only promises the split of this synthetic reference pipeline and does not claim that the split has real event independence.
5. `fit_tokenizer`: counts only historical train tokens; the candidates are the pre-given `(capacity,min_frequency)`. It generates the vocabulary in descending train frequency with lexicographic tie-breaking, and reserves the unknown-word/padding IDs. Vocabulary fitting is preprocessing, not neural training.
6. `select_tokenizer`: only reads non-overlapping train/development from the same historical source; it selects by the development-set unknown-token rate plus `fixed capacity penalty×capacity`, all in exact Fraction values. Ties go by the exogenous candidate order. With no development tokens it always picks the first candidate; an empty history gives an empty vocabulary. With an empty train split it keeps the empty vocabulary and computes the result on the visible dev split, without borrowing future corpus to fill in training.

Configuration candidates, stopwords, source/core rules, all thresholds, seeds and algorithm versions must be historically available or come from an independent exogenous mechanism. To claim that the random seed carries no extra future information, it should be independent of the whole world, or be conditionally independent of the future given the history; being independent of the future marginally is not enough. Composition of measurable functions does not itself need this independence; see the [mathematical manuscript](../theory/pit_noninterference.md). A "fixed configuration" picked today based on future performance does not become historically measurable just because it is written into FrozenConfig.

## Synthetic adapter, counterexamples and tests

`world_adapter` only reads the `id,recorded_time,text` of WP0.5 rows; the tests use an object that restricts field access to check that it does not read fields such as `available_time,contaminated,stance,price`. Assigning recorded_time to knowledge_time is a declared convention for the hand-made example; it **does not detect contaminated record times and does not prove the true available_time**. The source is fixed as synthetic-world, core=false, label=null; simulated samples must not be described as a real trusted core.

The three `naive_*` functions are deliberately kept wrong counterexamples and are not called by the main pipeline: fitting the vocabulary on the whole corpus first takes in future words; choosing the latest duplicate representative on the whole corpus first lets an old document be pushed out by a future copy; and even when only old documents are chosen, choosing them by the whole-corpus length can leak future information. The correct implementation being stable stage by stage and the wrong ones showing counterexamples is a mechanism check and cannot on its own support an innovation claim.

```powershell
& '..\130U-FinLLM\.venv\Scripts\python.exe' -X utf8 -m unittest research.pit.test_pipeline -v
```

The tests cover future same-ID revisions/tombstones/source/core/label/metadata, unknown future payloads, future duplicate event IDs, declared time different from knowledge time, ties at the same time, permutation invariance, future duplicate bridges, empty history / empty development set, train-only vocabulary, cutoff binding at each stage, rejection of forged snapshots, finite future extensions at several cutoffs, and three kinds of actual counterexamples. Finite tests do not exhaust all program bugs, hidden inputs or real provenance risks. The actual records of the external runner and the independent theoretical proof are delivered separately; no passing result is pre-filled here.

## Independent review fix record

The reviewer constructed a bool/int consistency bypass in the first-round code: Python dataclass equality treats `False` and `0`, and `True` and `1`, as equal, so `label=0→False`, `core=True→1` or `cutoff=1→True` could pass the old checks while changing the canonical JSON bytes. This is now fixed with strict field type checks, plus a comparison of canonical document bytes after rebuilding the history; the State's cutoff and document types are checked in the same way. The regression tests include these three kinds of input and bool variants of the document knowledge time. This fix closes an actual entry-point problem rather than pushing it onto the external assumption of true timestamps; the first-version results are not used as evidence of passing.
