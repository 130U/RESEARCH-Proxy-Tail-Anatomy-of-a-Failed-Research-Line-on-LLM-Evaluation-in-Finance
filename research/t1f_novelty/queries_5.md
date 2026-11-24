# Search log for candidate 5 and supplementary searches

Date of execution: 2026-11-17 (America/New_York). "Web" is a general search tool; a `site:` restriction is not the same as searching the database directly. Results are those visible in this round; where no database-wide hit total was provided, no count is invented. All of the following were actually executed.

| ID | Channel | Full query or request | Result / use |
|---|---|---|---|
| 5-01 | Web | FinQA "answer" "exe_ans" inconsistent | Found the OpenReward consistency-filter documentation |
| 5-02 | Web | FinQA "answer" "exe_ans" cleaning | Same as above, plus the data schema |
| 5-03 | Web Chinese (query translated) | FinQA answer program execution inconsistent data cleaning | Much irrelevant cleaning material; not used to conclude that nothing exists |
| 5-04 | Web | FinQA "annotation errors" answer | Found the second-hand FinQA-fix lead, passed to group 4 to check the original |
| 5-05 | Web | "FinQA" "exe_ans" "inconsistent" | Nearby results such as the official implementation |
| 5-06 | Web | "FinQA" "written answer" "program" | Points to EnvCommons/OpenReward |
| 5-07 | Web | "FinQA-fix" | Second-hand lead; retrieval of the original is recorded by group 4 |
| 5-08 | Web/ACL domain | site:aclanthology.org FinQA "answer" "exe_ans" | Field descriptions such as ViNumQA; not a precedent for a conflict rate |
| 5-09 | Web/arXiv domain | site:arxiv.org FinQA "inconsistent" "annotation" | Obtained evaluation-related candidates; not exhaustive |
| 5-10 | Web/S2 domain | site:semanticscholar.org FinQA answer inconsistency cleaning | Mixed irrelevant results; not treated as zero hits in the database |
| 5-11 | Web/Scholar domain | site:scholar.google.com FinQA "annotation errors" | No usable database export obtained |
| 5-12 | Web Chinese (query translated) | FinQA human answer program result contradiction cleaning | Nearby material and noise |
| 5-13 | Web | FinQA "written answer" "consistency" | EnvCommons field consistency |
| 5-14 | Web | FinQA "exe_ans" "filter" | OpenReward filter rules |
| 5-15 | Web Chinese (query translated) | "FinQA" "FinQA-fix" "error" | Leads on cleaning and recent evaluations |
| 5-16 | GitHub search_issues | repo=czyssrs/FinQA; query=answer exe_ans; topn=100 | 1 item: issue #6 |
| 5-17 | GitHub search_issues | repo=czyssrs/FinQA; query=wrong OR incorrect OR inconsistency OR rounding; topn=100 | 1 item: issue #15 |
| 1-PR-01 | Web | site:github.com/EnvCommons/FinQA pull rounding | Follow-up check on the known tolerance discussion for 1, after which the PRs were enumerated |
| 1/5-PR-02 | GitHub search_prs | repo=EnvCommons/FinQA; query=""; topn=100 | Search returned 0; REST enumeration then found 6, so the search result cannot be used as evidence of absence |
| 5-18 | Google Scholar direct entry | https://scholar.google.com/scholar?q=FinQA+answer+exe_ans+inconsistency | The tool returned "not accessible" |
| 5-19 | Semantic Scholar direct entry | https://www.semanticscholar.org/search?q=FinQA%20answer%20inconsistency&sort=relevance | The tool returned "not accessible" |
| 5-20 | GitHub REST full enumeration | https://api.github.com/repos/czyssrs/FinQA/issues?state=all&per_page=100 | 15 visible issues/PRs, screened one by one; 6, 13 and 15 read closely |
| 5-21 | GitHub REST full enumeration | https://api.github.com/repos/EnvCommons/FinQA/pulls?state=all&per_page=100 | 6 PRs; 2, 3, 4, 5 and all patches of 4 read closely |
| 5-22 | GitHub REST cross-check | https://api.github.com/repos/EnvCommons/FinQA/issues?state=all&per_page=100 | The same 6 PRs, de-duplicated against the PR enumeration |

Extended reading: OpenReward Tasks/Reward; EnvCommons PR4 files, merge b0e5f907abda069f0915e93e006c4ba55658360e; the official evaluate.py; FinQAPT 2410.13959 (found via candidate 4's citation chain); Gauging Overprecision 2504.12098 and Chemistry 2024 (found by candidate 3, cross-checked by the root agent); metadata of the skill source 2609.00065. The Chemistry ISSN path 2673-7167 was first used by mistake and nothing was obtained; after correcting it to 2624-8549 it succeeded, and the failed path is not treated as a source.


## Supplementary citation-chain searches by the root agent

The following were actually executed on 2026-11-17 and do not count towards the minimum of 10 sets for candidate 5.

| Channel | Query / request | Result |
|---|---|---|
| Web | `"TAT-QA" "rounding" "uncertainty"` | Mostly scoring conventions and system evaluations; no direct precedent for an input-rounding audit found |
| Web | `"ConvFinQA" "annotation errors" "2024"` | Financial reasoning evaluations and dataset construction, combined with group 4's citation tracing |
| Web | `"FinQA" "condition number"` | No direct precedent located; not used as proof of absence |
| Web | `"FinQA" "rounding" "determinacy"` | No direct precedent located; not used as proof of absence |
| Semantic Scholar API | `/graph/v1/paper/ARXIV:2109.00122/citations?fields=title,year,url&limit=1000` | Tool could not access it; the full set of FinQA citations was not retrieved |
| Semantic Scholar API | `/graph/v1/paper/ARXIV:2105.07624/citations?fields=title,year,url&limit=1000` | Tool could not access it; the full set of TAT-QA citations was not retrieved |
| Semantic Scholar API | `/graph/v1/paper/ARXIV:2210.03849/citations?fields=title,year,url&limit=1000` | Tool could not access it; the full set of ConvFinQA citations was not retrieved |

In addition, to re-check originals already located, the root agent ran find on the Chemistry full text for `3.2.`, `2 out` and `10 out`; the latter two did not match literally, but the original text of §3.2 has "2 correct answers over 10 trials" followed by all 10 runs correct. find is not an independent literature search set.

Additional actual keywords: `"EEDP" "FinQA" "ConvFinQA"`; `"ConvFinQA" "TAT-QA" "error analysis" benchmark 2023 2024`. These found the formal EEDP paper and FINESSE-Bench (passed to group 4 to read the original). find keys in the EEDP full text: Precision errors, A Metadata, missing information, rounding; matches and non-matches for the latter two were both interpreted by reading the context.
