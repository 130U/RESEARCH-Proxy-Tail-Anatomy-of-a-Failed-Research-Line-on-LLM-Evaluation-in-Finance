# Scope, decision rules and review method

Date of execution and search cutoff: **2026-11-17, America/New_York**. Task source: `tasks/T1f_novelty.md`; the repository README and `paper/finqa_short_v0.md` were read first. The baseline commit is `5fcbe690f3fcd12bc20a9ffaa851cf64df472a19`. This round is a traceable, targeted novelty check, not a systematic review with a full-database export, two-person screening and PRISMA counts.

## Set the boundary first, then judge overlap

We judge by the five "what counts as already done" criteria set in the task, and in particular we keep their "or" conditions; a precedent is not required to match all of our design details at once. Academic papers, specifications, traceable public code and issues/PRs can all meet the task's standard for public precedent; specification examples and peer-reviewed data studies are clearly distinguished in the evidence tables. Existing theory or methods do not automatically equal an empirical study in the same domain, but new samples and numbers do not automatically make a new research question either.

"Not found after reading full texts" means only this: among the relevant full texts actually obtained and checked in this round, no study meeting that criterion was found. It does not prove that nobody has ever done it. Green is only a **conditional recommendation from the novelty-check side**. It does not mean the evidence chain has passed or that the paper will be accepted; the colour is a separate decision.

## Searching and reading

- Each of the five items used at least 10 actual sets of search queries, in Chinese and English; the log keeps the original wording, channel, results and access failures. ACL and arXiv full texts and GitHub primary material could be read and checked directly.
- `site:`-restricted general web searches were only a supplementary discovery tool and are not passed off as searches of the internal Google Scholar / Semantic Scholar databases. The direct interfaces and citation APIs of both have records of being inaccessible or rate-limited; a full export of citing papers was not obtained.
- Starting from FinQA/TAT-QA/ConvFinQA, we followed evaluation and cleaning papers from 2023 on, then traced citation chains along FinanceReasoning→BizBench/DocMath/FinanceMath and numeric precision→XBRL/statistical disclosure control/numeric LMs. The specific edges are in [citation chains](citation_chains.md).
- Three parallel research groups handled 1–2, 3 and 4; the root agent handled 5, the primary GitHub verification and the integration, and reviewed the decisive behavioural and field evidence. This is cross-checking between agents, **not independent double review by humans**.
- Each attachment lists the three closest sources with short excerpts. Full texts that were not retrieved are not listed as "read"; search snippets and second-hand descriptions cannot be upgraded to full-text evidence. Duplicate arXiv/formal versions and repository/release pages are not counted as separate studies.
- This round did not reproduce the project's 10.7%, 1/196, 98.4%, 55/68 or 508/7,952, and did not run any new model. All "our results" come from the task and the draft; the novelty check only judges their relation to prior work.

## Organisation of material and validation

The [one-page summary](README.md) collects the verdicts; `candidate_*.md` give the evidence and item-by-item verification, `queries_*.md` give the actual searches, and `reading_*.md` give the reading scope. Citations use the original publishers, ACL, arXiv, specification publishers and author repositories. Reading a web page's full text does not mean the attached PDF or supplementary material was also read successfully; failures are listed separately.

Key titles, years, sections/page numbers, and GitHub timestamps and merged versions have been checked; the results of the DOI script are in `citation_verification.json` and the [validation record](validation.md). Registration status only confirms the identifier and cannot replace checking that the original text supports the claim. FinQA-fix, whose full text was not retrieved, the raw supplementary responses of the Chemistry paper and the other listed leads remain gaps; they may further reduce novelty.

This round only adds novelty-check material under `research/t1f_novelty/`. Raw full-text caches stay in the local workspace of this run; the GitHub deliverable consists of the author's verification notes, short excerpts, links and search records.

## Workflow attribution

The local skill "Academic research - systematic literature review" was used to help with search records and evidence grading; as it requires, we credit the source of the method tool: Timothy Kassis, Vinayak Agarwal, Yuhuan He, Darshil Patel, Aubrey M. Brueckner (2026), [Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents](https://doi.org/10.48550/arXiv.2609.00065). Authors and year were checked against the arXiv record; this is workflow attribution, not novelty evidence for the five items above.
