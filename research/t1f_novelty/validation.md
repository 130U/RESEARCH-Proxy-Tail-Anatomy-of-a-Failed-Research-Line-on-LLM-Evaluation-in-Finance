# Deliverable validation record

Date: 2026-11-17.

| Check | Result and limits |
|---|---|
| Task scope | The one-page summary opens with the specified 7-column table; all five items use the specified one-of-three conclusions and give a colour, near neighbours, increment and confidence |
| Closest sources | Each item lists three primary sources with short quotations and sections/page numbers; candidate 5 explicitly includes a PR and an issue and does not pass them off as three independent papers |
| Search log | Each item has more than 10 sets of actual searches, in Chinese and English; `site:` restrictions, native database failures, GitHub search and REST enumeration are recorded separately |
| Full-text reading | The group lists give the scope and source level item by item; full texts not retrieved are listed separately; abstracts or second-hand content are not treated as full text |
| Key cross-checks | The root agent re-checked XBRL §5.5, Chemistry §3.2, the point ground truth of Gauging Overprecision, FinQAPT §4.5.1 and FinanceReasoning Table1; another agent independently checked candidate 2's broad boundary |
| Versions | The formal ACL PDF of FinanceReasoning still contains the 1420/1330 contradiction; FINESSE uses the authors' arXiv v2; XBRL uses the 2024 errata version; EnvCommons PR4 is pinned to the merge SHA |
| FINESSE question correspondence | See [data_identity_check.json](data_identity_check.json): the authors' 1147 questions all match the original FinQA test in the same order; all references match exe_ans. This check only confirms data identity; the shared error rate of the 53 models was not recomputed |
| Convention of local material | The 98.4% metric has been corrected per §6 of the draft to the factor-of-two width criterion; this project's experiments were not re-run; the README and the draft paper are outside the scope of changes |
| Citation identity | Main sources were checked against ACL, publisher, arXiv and official specification metadata; short quotations are kept within 25 English words per source, and shared sources are excerpted only once where possible |
| DOI script | verify_citations.py was run as the skill specifies. The first run failed on Chinese punctuation extraction / Windows encoding; it was re-run with an explicit DOI list and UTF-8. All 4 DOI registration requests returned no result because the sandbox refused the local proxy connection; the [JSON record](citation_verification.json) stays inconclusive, and the manual check of the original web-page metadata is recorded separately; a failed request is not interpreted as the DOI not existing |
| Attachment links | All relative Markdown links in this directory were checked before delivery; the results are stored in [validation_manifest.json](validation_manifest.json) |
| Published content | Only self-written reports and validation summaries under research/t1f_novelty were added; no full PDFs by others, cached web full texts, dataset copies or workspace environment logs are uploaded |

Public web pages and GitHub code are mutable resources, so formal paper identifiers, specification versions, arXiv versions and merge commits are given in preference. The cited-by literature in Google Scholar/Semantic Scholar was not exhausted, and the journal full text of FinQA-fix was not obtained; these are substantive coverage limits of the novelty check and should not be hidden by the "colour".
