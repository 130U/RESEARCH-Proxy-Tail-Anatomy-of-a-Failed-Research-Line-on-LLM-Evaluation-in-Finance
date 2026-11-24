# Local real-source audit: FOMC date evidence and the usable scope of SEntFiN

Date: 2026-11-16 (America/New_York). Method: fully offline, read-only access to the old repository; no internet access, downloads, training or sending of materials outside. Output is only in the new workspace `research/data/`.

## Conclusion

**The FOMC "list publication date" now has more direct local source support, but the historical byte versions are still unproven.** Of the 10 records selected by date from the 120 raw records, in every case the Released date that the saved official calendar / historical index states explicitly next to the minutes link agrees with the JSONL and the source manifest; the hashes of the relevant minutes and index snapshots all match. The Last Update of the 10 minutes pages also happens to agree, but it is used only as a comparison of the update field and cannot independently replace publication evidence. Among the machine-readable date entry points it supports, the tool found no fields such as datePublished/dateModified; this is not an exhaustive negative claim about arbitrary page scripts.

These results support treating the documents as **real-text candidates whose sources are traceable and whose date claims have been reviewed**. They do not allow the bytes saved in 2026 to be declared the versions published as-is in 2011–2025, and they cannot produce a historical core with zero failure probability. Selecting the sample at fixed dates is not a random audit, and 10/10 agreement does not mean the population mislabelling rate is zero.

**SEntFiN can serve as a new local private Phase 0 baseline candidate for its "source-native task: entity-level sentiment"; this does not upgrade it to investment-stance data on verified securities.** This is a research-use judgment based on the current scope of user authorization and the saved source / approval records, not a new proof of third-party publisher rights. The authors' MIT licence, the private research boundary, the semantics of the source labels, the project's human confirmation and event / time isolation must each be kept separate. The current task only reviews these boundaries; it did not read the raw CSV, construct new splits or train a baseline.

## Input scope, rules and execution record

All old-file relative paths below are rooted at `<workspace>/130U-FinLLM`. Before execution, the old repository and all its ancestors, and the data/docs/runs subdirectories involved, were checked, and the research guidelines of the initial plan were read separately; their training and internet steps were not part of this round.

The FOMC inputs are `data/raw/expansion_v1/corpora/finance_candidate.jsonl`, `manifest.json` in the same directory, the 10 selected minutes HTML files, and the 8 corresponding discovery HTML snapshots. The JSONL actually has 120 records and 6,977,681 bytes, consistent with the manifest; its SHA256 is `5a9b357c4b979b5e85dc7622e28c5793068baeb67a48abbd218e81e7d8219a0a`. Publication dates range from 2011-02-16 to 2025-12-30; the source record states a crawl time of `2026-10-11T10:39:20.795698+00:00`. These values come from this round's file checks, not from an external live query.

The sample is selected by first sorting by `(published_at,text_sha256)` and taking the zero-based ranks `i*(N−1)//9, i=0,…,9`, covering both ends, without reading labels and without replacing samples based on results. It is a cross-date structural check, not a probability sampling design. The source file SHAs and the program SHA are all saved in [source_audit.json](source_audit.json), so the objects of a rerun can be confirmed.

The program is [fomc_source_audit.py](fomc_source_audit.py), using only the Python standard library. It computes the SHA256 of each minutes document from its bytes; the full-text hash is checked against the UTF-8 text in the JSONL; the minutes metadata are compared field by field with the admitted manifest. The publication date is taken from **the local paragraph or minutes container that holds the unique target minutes link**; falling back to an arbitrary date anywhere on the page is forbidden. All links in the container must also belong to the same minutes identity: only known minutes HTML/PDF paths on the official domain are accepted, and the 8-digit meeting date must agree; the same date appearing in any other path does not count as an identity match. Duplicate target links, other minutes, unknown link identities, unknown containers, missing dates or multiple dates all keep a missing-evidence / ambiguous status, with no guessing. Parsing uses HTMLParser and does not execute page scripts; one old page needs a cp1252 fallback, and the hash of the raw bytes is unaffected by the choice of decoding.

After the final fix, the runtime was Python 3.12.14, the audit took 0.341598 seconds, and peak memory was not measured; 0 network requests, 0 training tokens. The 10 tests took about 0.005 seconds and cover: binding of links and dates, rejecting mixed minutes in the same container, the same minutes in both HTML/PDF orders, rejecting unknown paths / external sites / query parameters, forbidding whole-page fallback, rejecting duplicate links and multiple dates, keeping the publication / update channels separate, and old character encodings. The tests check the implementation on constructed examples; they do not prove historical authenticity. The pre-execution estimate and the reason for the additional reading of discovery snapshots are in [compute_budget.md](compute_budget.md).

### Record of the fix after independent code review

The first implementation only checked "the target link is unique + the local container has only one Released date". The reviewer gave a fatal interface counterexample: one paragraph contains two different minutes A and B, the single date actually belongs to B, and the old function would still assign it to A. This is not automatically ruled out by the manifest or by a single link count, and it cannot be handled by just adding a sentence about limitations to the report.

The program now includes a check that the minutes identity is consistent within a container, and the counterexample above plus a positive example with HTML/PDF of the same identity have been added. The independent reviewer and the author each checked the current fixed sample: each of the 10 local containers has two links, an HTML and a PDF for the same meeting date; in the first 7 the HTML comes first, in the last 3 the PDF comes first. The new check allows both orders, rejects links to different minutes or links whose identity cannot be confirmed, and does not rely on link text or order to guess which minutes a date belongs to. The new JSON explicitly records `container_link_count` and `container_document_identity`; all real samples still have consistent dates. The original sampling rule, the raw files and the conclusion that historical versions lack evidence are all unchanged.

After the fix, the program SHA256 is `96577f6b877e02259cd6a138e7359f574fe0da722abec30b6ceb2777c55e2987`, matching the same field in the JSON. This rerun replaced the audit results in the new workspace and did not modify the old repository snapshot. The fix closes the reported multi-link mismatch problem; the restricted HTML parsing contract is still not a proof of complete page semantics.

```powershell
# Run from the root of the new research workspace; the tool writes JSON only to its own research/data/.
& '..\130U-FinLLM\.venv\Scripts\python.exe' -X utf8 research/data/fomc_source_audit.py --self-test
& '..\130U-FinLLM\.venv\Scripts\python.exe' -X utf8 research/data/fomc_source_audit.py --source-root '..\130U-FinLLM'
```

## Fixed-sample results

All numbers are observations from this round's local audit. Every row passes: JSONL/manifest dates and links agree, full-text hash agrees, minutes HTML hash agrees, corresponding index snapshot hash agrees, Released date next to the link agrees, and the Last Update comparison agrees.

| Anonymous ID | Sort rank | Meeting date | Publication date stated by index / manifest date | Days from meeting to publication | Minutes page update date |
|---|---:|---|---|---:|---|
| FOMC-A01 | 0 | 2011-01-26 | 2011-02-16 | 21 | 2011-02-16 |
| FOMC-A02 | 13 | 2012-09-13 | 2012-10-04 | 21 | 2012-10-04 |
| FOMC-A03 | 26 | 2014-04-30 | 2014-05-21 | 21 | 2014-05-21 |
| FOMC-A04 | 39 | 2015-12-16 | 2016-01-06 | 21 | 2016-01-06 |
| FOMC-A05 | 52 | 2017-07-26 | 2017-08-16 | 21 | 2017-08-16 |
| FOMC-A06 | 66 | 2019-05-01 | 2019-05-22 | 21 | 2019-05-22 |
| FOMC-A07 | 79 | 2020-12-16 | 2021-01-06 | 21 | 2021-01-06 |
| FOMC-A08 | 92 | 2022-07-27 | 2022-08-17 | 21 | 2022-08-17 |
| FOMC-A09 | 105 | 2024-03-20 | 2024-04-10 | 21 | 2024-04-10 |
| FOMC-A10 | 119 | 2025-12-10 | 2025-12-30 | 20 | 2025-12-30 |

The JSON contains no titles, full text, URLs or per-item labels; the IDs are anonymous audit IDs. Because dates and hashes are kept, this is audit metadata with direct text identifiers removed, **not a privacy anonymization that promises the public documents cannot be re-identified**.

## Which link of the P1 certificate chain this actually adds

1. **Strengthened: the source of the date fields.** The dates next to the minutes links in the locally saved official indexes can be reread and reviewed independently of the JSONL fields. The full-text hash and the HTML hash connect the current extracted records to the saved snapshots, reducing reliance on the manifest's own claims. But both still come from the same 2026 source crawl; they are not independent historical witnesses.
2. **Still unknown: historical content versions.** A current page marked with an early Last Update does not rule out later unmarked revisions, archive migrations or changes in page generation; the hash only proves that the two current saved objects agree. A time-stamped immutable archive / version chain is needed to strengthen "these bytes were visible at that point in time", and this round did not obtain one.
3. **Still unknown: intraday availability.** The precision of this round's evidence is the date. The minutes text mentions that a policy statement was released at 2 p.m.; this may describe the post-meeting statement, and that time must not be wrongly assigned to minutes released weeks later. No arbitrary time string from the full text was used to fill in the release time or time zone of the minutes. This is still not enough for intraday statistics; adopting a conservative rule such as "available only on the next day" is also just an additional contract that must be defined separately, and cannot be written back as a known true time.
4. **Still unknown: the historical selection process.** Selecting old texts in 2026 according to the current index and fixed years does not automatically guarantee that the selection was measurable in the past. Whether documents survived, were revised or entered the index, which years were selected, and which preprocessing was used can all bring in future information. The current audit sample was selected by sorting on publication dates visible later; it is used only for diagnosis and does not directly serve as a historical training core.
5. **Explicitly ruled out: using the meeting date in place of the publication date.** Every sample has a gap of 20–21 days, including meeting / publication dates that span a year boundary; training or backtesting on the meeting date could introduce look-ahead. This round did not check whether any model actually followed the filtering rule.

So the next step of real-text preparation can use these source records, but P1's `historical_byte_version_proven` is always false; G0/G1 do not pass automatically because 10 dates agree.

## SEntFiN: rights, approval, semantics and events judged separately

Based only on local files; external links in them were not opened. The files read and their SHA256 are in `rights_document_fingerprints` in the JSON:

| Old-repository evidence | What it does support | What it does not support |
|---|---|---|
| `data/raw/candidates/sentfin/LICENSE`; `docs/research/stance_sources_20261009.md` | The fixed version of the authors' repository has MIT text and attribution; the original task is entity-level positive/negative/neutral; the local research candidate and the boundary of not publishing the original text are already recorded | That upstream publisher rights have been independently verified; that the original sentiment equals this project's investment direction; that reliable per-item publication dates or security identifiers are complete |
| `docs/POST_DOMAIN_NEXT.md`; `docs/TASK_REVIEW_NEXT.md` | Headline-stance materials that I later confirmed already exist, so the early description "zero human confirmation" cannot be applied to the whole project | That this confirmation covers the full raw data, security identity, source rights, event independence or DPO preferences |
| `docs/REVIEW_WORKSPACE.md` | Human stance confirmation is separate from asset verification; AI drafts cannot pose as human ground truth; formal training has its own gate | That a single `human_reviewed` flag can pass all source and semantic reviews at once |
| `docs/ENTITY_SFT_PILOT.md`; `runs/task_pilot/entity_v1/task_manifest.json` | The project already allows private exploration targeting literal entities; the existing pilot uses a non-temporal, lexical / source-grouped split; `private_research_only` is explicit | Real security / price prediction ability, a complete semantic event review, a final independent test, or a historical no-leakage certificate |

**New private Phase 0 judgment: under the current local research authorization, a baseline preparation plan can be built on the original authors' entity-sentiment task, keeping the original label names and source provenance; they do not first need to be changed to bullish/bearish.** "Original-author labels" are the supervision definition of that existing dataset; they are not a new human approval by this project, nor an AI proposal. If the task is to be changed to asset stance, the actual approved scope and the unfinished gates must still be followed; the name "Phase 0" cannot be used to bypass semantic acceptance. The `formal_training_ready=false` in the old documents still holds for the corresponding derived candidates; the permitted exploration of the source-native task cannot be read as approval of all formal training.

This judgment has the following specific boundaries:

- **Rights boundary:** use the existing raw materials, keep the LICENSE/attribution, and keep the data and per-row outputs private; do not publicly copy news text or label packages. The local evidence of the authors' licence is enough to avoid saying "no source at all", but it does not close the gap in publisher rights, and it makes no commitment about future public / commercial use.
- **Semantic boundary:** the first-version target must be called source-native entity sentiment. A regulator's neutral, past price moves, the author's attitude and investment direction may differ, and cannot be hidden by renaming. Security identity can be a separate missing field; the literal-entity baseline does not claim that tradable securities have been verified.
- **Label-handling boundary:** anomalous literals in the source file cannot be fixed by opaque guessing; we recommend freezing the parsing rules, isolating failed rows and reporting their number. The source label rows were not reread here, and neither the number of classes was recomputed nor the approval status of specific rows decided.
- **Event and evaluation boundary:** multiple entities in one headline, exact duplicates, lexical near-duplicates and the same event must be grouped jointly before splitting. The existing lexical grouping is not a complete event gold standard; without reliable per-item dates, it cannot be called temporal extrapolation. The new baseline needs a new versioned split that states explicitly that the old development data have already been used; old scores cannot directly become new independent evidence of effectiveness.
- **Start-from-scratch boundary:** a new local text/linear baseline can be built without old checkpoints; training a model from scratch also does not automatically remove event duplication, preprocessing choices or source-time risk. I decided to build from scratch; this round's task scope is the source audit, no new baseline training has been run, and only the source judgment and the contracts needed for the next step are delivered.

## Actual scope of contact and things not done

The raw `SEntFiN.csv`, the private training / evaluation JSONL and the per-item human review tables were not read, and no full news passages or FOMC full text were output. **One exception to the scope occurred during the initial reading of a manifest: `candidate_manifest.json` embeds examples of entity labels whose parsing partly failed, and the tool output displayed this content; it was not copied into any deliverable file.** After that only whitelisted summaries and scope files were read; this report does not repeat those examples, and does not claim that no per-item label information was ever seen. The checker itself has no interface for reading SEntFiN rows.

The current status of the external licence was not verified, the raw labels were not adjudicated item by item, the new baseline for the source-native task was not completed, natural document / event independence was not proven, and no real XBRL gold standard was obtained. The existing public source records and this round's data checks are enough to make the follow-up work concrete, while keeping these weakest links visible and not automatically recording missing evidence as either failed or passed.
