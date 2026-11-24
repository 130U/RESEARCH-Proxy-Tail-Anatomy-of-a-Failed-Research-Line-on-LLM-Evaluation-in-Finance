# T1.1 historical non-interference: construction and counterexample check protocol

2026-11-16, recorded before execution. Source level: the numbers this round will produce are all "our finite construction checks", not financial empirics or a provenance audit. Work is local only: no downloads, no network, no reading of private text, no main-line model training. G0 stays not passed; this round advances the theorem and its constructive component checks, which were already allowed to proceed early.

## Goal and scope

Work package WP1.2 requires every component to take the cutoff date explicitly, so that future appends do not change past outputs. Here the requirement is written as a checkable mathematical interface: the complete version log is first projected to a snapshot at the knowledge cutoff, and the later filtering, deduplication, sampling, validation-split, vocabulary fitting and hyperparameter selection may only read that snapshot. The new research manuscript should distinguish historically equivalent non-interference, factorization and invariance under future appends, and the valid input domain these conclusions need.

Projecting by recorded time alone can prove **non-interference relative to the given records**; it does not certify that the recorded times are true, that old versions were public at the time, that labels were available at the time, or that rules were really set at the time. Real historicity still needs provenance evidence. Source code/configuration/random seeds are also inputs; they must be fixed and determined by historically measurable information or by an independent exogenous mechanism. A configuration chosen today because it works better cannot be disguised as a historical configuration.

## Construction contract

1. Documents are handled per version/event, keeping a stable document ID, content hash, knowledge time, source and core marker; revisions and deletions must not be written back into old events. A document's event time does not replace its knowledge time. Labels, roles and other metadata that affect training all fall within the scope of version validity.
2. Project by knowledge time first, then choose the visible version, filter and deduplicate. Future revisions of the same ID, future tombstones and future near-duplicate bridges must not change past components. Valid-domain checks such as the outer time type of the input are to be distinguished from access to future payloads; there is no promise to return a model result for an arbitrarily corrupted database.
3. Each component produces deterministic canonical bytes. Fixed seeds, canonical ordering, exact tie rules; samples, vocabularies or candidates are not determined by the full log's length, hash, number of future exclusions or the system clock.
4. Operational information such as a full-log fingerprint, processing time or the number of future records, if it needs to be recorded, goes only into a separate audit envelope; it is not part of the historical product claimed to be invariant. A historical stable hash may only bind the visible projection and the fixed exogenous inputs.
5. Vocabulary candidates are fitted only on the historical train split and chosen deterministically by the unknown-word rate on the historical dev split and a pre-fixed capacity cost. This only tests the full dependency chain of hyperparameter selection; no financial classifier or language model is trained, and this vocabulary-selection objective is not treated as a research performance contribution. Empty historical/empty development partitions use default behaviour written down in advance and cannot be filled in with future data.
6. A test of a single future append can be iterated to all finite appends only under conditions such as a valid projection/extension closure; passing finite runs does not prove the global conditions. Code, pen-and-paper proofs and finite counterexample checks are reported separately.

## Pre-run budget and decision rules

- CPU, standard library; 0 GPU/API/model-training tokens; target ≤60 seconds for construction tests and pre-specified examples combined.
- The main example uses a small slice of the existing WP0.5 world, at most 1,000 version events; hand-made minimal counterexamples and finite enumerations are also used. Real private corpora do not enter this round.
- Expected memory ≤100MB, but without a measurement no claim is made that it was actually met; record the actual wall time, Python/platform, and code and configuration hashes.
- All six specified components must be covered, including changes in future versions, deletions, content, metadata and permutations; do not compare only the final hash and miss the intermediate stages.
- Rejection/fix conditions: any valid future extension changes any stable component; a hidden future input affects candidates or partitions; the actual version is not before the cutoff; a promise is stronger than the implementation/input domain. When a failure is found, record and fix it first; do not drop failing scenarios.
- The counterexample implementation should actually demonstrate the failure of "process the whole corpus first, then filter"; the correct implementation passing and the wrong one failing is not to be taken as evidence of novelty.

## To deliver

Conditional propositions and proofs, a canonical snapshot / reference implementation of the six components, boundary and counterexample tests, a run summary with hashes, an independent review and a fix record. The products are placed in research/pit for now; migration to the final top-level repository layout is still accepted separately. This component cannot replace a real trusted core, a timestamp audit, shard training or a non-empty historical backtest certificate.
