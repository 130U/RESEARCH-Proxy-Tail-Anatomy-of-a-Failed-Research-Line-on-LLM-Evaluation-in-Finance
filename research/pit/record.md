# T1.1 construction checks: run record and limits of the results

2026-11-16, round five. Source level: **our finite construction checks**; the attached real-date counts are only a re-summary of the previous round's public provenance-audit JSON. This round had no network access, no reading of private rows, no main-line model training and no performance evaluation. The budget was written down first in [PROTOCOL](PROTOCOL.md), the mathematical statements are in [PNI1–PNI6](../theory/pit_noninterference.md), and the implementation is in [README](README.md).

## Proposition checked

The same complete visible version projection, with fixed configuration/seed/cutoff, should give the same historical snapshot and all the same downstream products. Visibility is determined by knowledge_time; the retained record_time has no priority. The finite checks test whether the reference program violates this construction; they cannot be used to assign a zero error probability to real time declarations.

## Budget and run identity

Pre-execution targets: CPU ≤60 seconds, scale ≤1,000 version events, memory ≤100MB; no GPU/API/main-line training tokens. The actual main world had 4 companies × 10 periods, 40 version events in total; the extensions include revisions, deletions, duplicates and opaque future payloads. The main check first took 1.468044 seconds; the latest rerun value is in [results.json](results.json); peak memory was not measured, so we cannot claim to have measured that 100MB was met.

The code is based on branch research/certifiable, base commit 8e4dd0b33c95ac2ac1a6015eba6f2dfafe5c1254; the new files are still uncommitted. The runner records Python, platform, and the SHA256 of pipeline/runner/seed-check/world/protocol. All stable products are compared directly byte by byte; hashes are only used for indexing, and hash equality is not used in place of byte equality. Operational information such as run time and source identity is in results and does not enter the historical products being compared.

## Pre-specified main check

Two frozen configurations, three pipeline seeds (11/130/2026) and five cutoffs (−5/−2/0/2/4) make 30 historical base cases. Each case compares seven inputs: the complete existing log, the reversed log, future revisions and metadata changes, future tombstones, future copies, valid headers with opaque future payloads and duplicate event_ids, and combined extensions. In total there were 210 whole-pipeline comparisons and 2,100 byte comparisons of stable products, all identical. At the last cutoff the "existing future" can be empty; so these are finite comparison counts, not 210 independent non-empty future scenarios, and still less a statistical sample size.

The 10 products are the configuration, the complete visible history, the active snapshot, filtering, deduplication, sampling, the train/dev split, all candidate vocabularies with their development scores, the selected vocabulary, and the product digest table. 29 of the 30 base cases have development documents, so at least the real development-selection branch is covered; the empty-development branch has a separate fixed first-candidate rule and unit tests. The development objective here is the unknown-word rate + an ex-ante capacity cost, not financial classification performance.

The independent implementation tests add another 18 items, covering cutoff boundaries, historical/future versions, tombstones, ties at the same time, deduplication bridges, bad future payloads, empty state, train-only vocabulary, and type consistency of hand-made snapshots. The finite extensions in the tests overlap with the main runner, so the counts cannot be added up as independent evidence.

## Three required negative controls

| Deliberately wrong program | Actual observation | Wrong inference refuted |
|---|---|---|
| Build the vocabulary on the whole corpus first, then sample by date | New future words change the vocabulary | Filtering the body text is enough |
| Choose the latest duplicate representative on the whole corpus first, then filter | A future copy pushes out the historical representative | Deduplicating first and truncating afterwards does not change the past |
| Choose one old document by the full-log length | Newly added future rows change the selected old ID | If the final input is all old documents, there is no selection leakage |

The three wrong functions serve only as negative controls and are not called by the main pipeline. The results are saved in full in results.json. A finite counterexample can overturn the corresponding universal claim; finite passes of the correct program cannot conversely prove safety for arbitrary inputs.

## The checker does not recognize the truth of times

In the synthetic world, where the latent truth is known, 3 mislabelled records were planted: their true availability time is after cutoff=0, but their recorded/claimed knowledge time was set to 0. The adapter only reads id, recorded_time and text, and does not read latent truth such as available_time/contaminated; only the runner's independent oracle reads the truth to check the planted count.

The result is that **all 3 mislabelled records were taken in by the pipeline, while invariance under future appends still passed**. This is not a program bug: it strictly follows the given times. It shows that this checker does not certify the truth of times, and a historical certificate still needs external provenance/audit evidence. That nothing added in the future changes the past cannot correct a past time field that was already wrong.

## Exact counterexample for the randomness assumption

The independent review pointed out that saying only that the seed is marginally independent of the future is not sufficient. If history H and future B are independent and uniform and seed=H xor B, then the seed is marginally independent of B, yet the output H xor seed equals B. What is needed is conditional independence given the history, or a seed independent of the whole data world. Composition of measurable functions and fixed-seed non-interference do not themselves need this independence; the three statements must be kept apart.

[seed_checks.py](seed_checks.py) checks exactly with Fraction all 16 deterministic boolean seed maps on independent uniform H, B: 6 are marginally independent and 4 are conditionally independent; the other 2 are exactly XOR/XNOR. This is a finite mathematical counterexample verification, not a statistical test of the project's actual seed-generation process. The old shorthand in the overall notes in Markdown and TeX has been corrected.

## Relation to real local material

A re-summary of the 10 FOMC provenance-audit records selected non-randomly in the previous round, with no new reading of raw data:

| Cutoff | Claimed publication date ≤ cutoff | Claimed local retrieval date ≤ cutoff | Corresponding historical byte version proven |
|---|---:|---:|---:|
| 2015-12-31 | 3 | 0 | 0 |
| 2020-12-31 | 6 | 0 | 0 |
| 2025-12-31 | 10 | 0 | 0 |

The retrieval declarations are from 2026; the dates checked earlier agree with the current byte hashes; this still does not prove that the same bytes existed in the historical year. **Lacking historical byte evidence does not mean those contents were unavailable at the time.** This table also cannot estimate the error rate for the population of 120 sources, and it is not a new provenance audit or a PIT run on real text. The hash of the original JSON is saved in this round's results.

## Review and open obligations

The independent review actually reproduced a snapshot-validation flaw in the first version: dataclass equality conflates False with 0 and True with 1, so a forged snapshot was accepted while the serialized bytes changed. The fix switched to strict type constraints and a comparison of rebuilt canonical bytes; all three original counterexamples are now rejected and have been added to the regression tests.

The mathematical review also separated information measurability from provenance admission: constant text that only becomes public in the future, or a checkpoint fixed after the fact, can both be measurable in the chosen probability space; this does not prove that they could really be constructed or were allowed to be used at the time. The ex-ante algorithm, the cross-world interpretation and the actual version-admission contract must be fixed. PNI6 gives a two-world example with the same observed log, with clean accuracy 0 and 1 respectively; any deterministic closed interval that is reliable in both can only cover [0,1].

The completed scope is the PIT reference components and the corresponding conditional proofs/finite checks. Tamper-proof storage, a trusted time service and global verification of third-party training programs are not implemented; the real historical certificate, G0/G1 and the final top-level repository migration are not done. These general mathematical facts are also not claimed as original contributions of this project.
