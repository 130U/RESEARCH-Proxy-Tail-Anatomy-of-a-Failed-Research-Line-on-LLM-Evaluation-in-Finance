# Candidate 3 search log

Date: 2026-11-17. All 39 sets of searches below were actually executed; each web-search batch had at most 4 sets. A web search is not the same as searching all records of a database; this round does not report fake total hit counts.

| ID | Query (verbatim; Chinese queries translated into English) | Channel | Return batch |
|---|---|---|---|
| C3-01 | "large language models" "significant figures" | general | q1 |
| C3-02 | "language models" "rounding" "uncertainty" "interval" | general | q1 |
| C3-03 | "ChatGPT" "significant digits" physics | general | q1 |
| C3-04 | "LLM" "numerical precision" "prompting" | general | q1 |
| C3-05 | site:aclanthology.org "significant figures" language | ACL site search | q2 |
| C3-06 | site:arxiv.org "significant figures" ChatGPT | arXiv site search | q2 |
| C3-07 | site:semanticscholar.org "language models" "precision" uncertainty | Semantic Scholar site search | q2 |
| C3-08 | site:scholar.google.com "large language models" "significant figures" | Google Scholar site search | q2 |
| C3-09 | "large language model" "significant figures" benchmark | general | q3 |
| C3-10 | "ChatGPT" "uncertainty propagation" assessment | general | q3 |
| C3-11 | "large language model" "significant figures" evaluation | general Chinese (query translated) | q3 |
| C3-12 | "language model" "rounding" "interval" precision | general Chinese (query translated) | q3 |
| C3-13 | site:github.com "issues" "significant figures" "LLM" | GitHub site search | q4 |
| C3-14 | "ChatGPT" "significant figures" physics education | general | q4 |
| C3-15 | "large language models" "measurement uncertainty" | general | q4 |
| C3-16 | "Training Autoregressive Language Models on Rounded" | general | q4 |
| C3-17 | "ChatGPT" "significant figures" chemistry assessment prompting | general | q5 |
| C3-18 | "language models" "error propagation" "rounded" | general | q5 |
| C3-19 | "language models" "uncertainty" "rounded inputs" | general | q5 |
| C3-20 | "ChatGPT" "significant figures" "prompt" study | general | q5 |
| C3-21 | "Optimizing Human–AI Collaboration in Chemistry" Wang | general identity check | q6 |
| C3-22 | "Gauging Overprecision" 2026 | general citation followup | q6 |
| C3-23 | "large language models" "significant digits" "uncertainty" | general | q6 |
| C3-24 | "large language models" "numerical uncertainty" precision | general | q6 |
| C3-25 | "significant figures" "LLM" | GitHub issue API; topn=20 | platform0 |
| C3-26 | "FinQA" "precision" | GitHub issue API; topn=20 | platform1 |
| C3-27 | "chemistry-06-00043" "s001" | supplement discovery | q7 |
| C3-28 | "Optimizing Human" "Table S8" | supplement discovery | q7 |
| C3-29 | "LLM" "interval arithmetic" benchmark | general | q7 |
| C3-30 | "language models" "rounding error" "FinQA" | general | q7 |
| C3-31 | Number Cookbook number understanding processing NUPA 2025 | general | q8 |
| C3-32 | Just Ask for Calibration Strategies for Eliciting Calibrated Confidence Scores from Language Models | general | q8 |
| C3-33 | "FinQA" "interval" "overprecision" | general citation chain | q8 |
| C3-34 | "TAT-QA" "significant" precision language | general citation chain | q8 |
| C3-35 | LLM benchmark unit conversion measurement units UnitBench | general | q9 |
| C3-36 | "large language models" "significant figures" "uncertainty propagation" | general | q9 |
| C3-37 | "language models" "precision" "rounded measurements" | general | q9 |
| C3-38 | "model" "significant figures" "uncertainty" ChatGPT | general Chinese (query translated) | q9 |
| C3-39 | Spithourakis Riedel 2018 numeracy language models rounding precision interval | backward citation chain | q10 |

Direct platform follow-up searches:

- Google Scholar: `https://scholar.google.com/scholar?q=%22large+language+models%22+%22significant+figures%22`; the tool returned "not accessible". `site:` searches were executed, but they cannot replace Scholar's internal search.
- Semantic Scholar: `https://www.semanticscholar.org/search?q=language%20models%20numerical%20precision&sort=relevance`; the tool returned "not accessible". `site:` searches serve only as a supplement.
- GitHub: C3-25 and C3-26 were run through the connector, each returning 20 items, whose titles and bodies were screened; most results were implementation issues / automatic paper summaries and were not treated as checked papers. In C3-25, LitXBench issue #19 is a public case of displayed precision affecting numeric scoring, but it does not run an experiment on active/passive precision behaviour of models.
- ACL, arXiv: after a search hit, the Anthology PDF / arXiv HTML full text and the relevant appendices were read directly.

Discovery paths: C3-01–04 → Bahaj et al. (2025) → FinQA citations in the text and the prompt appendix; C3-17–20 → Vidhani & Mariappan (2024) → §3.2/Fig.4 and the supplementary-material links; C3-05 → Guo et al. (2024) → AMPS Task 6; Chinese searches → NUPA → arXiv full text/appendix; C3-16 → Yan et al. (2026).

Originals/attachments that could not be accessed:

- Chemistry 2024 supplementary material `/article/10.3390/chemistry6040043/s1`: cache miss; the full-text PDF `/2624-8549/6/4/43/pdf` also failed. An attempt at the mdpi-res s001.pdf path also failed. The public full text §3.2 could be read completely, so 2/10→10/10 is marked as the authors' report in the full text, without falsely claiming that the raw responses in S6–S8 were re-checked.
- ACS 2026 `10.1021/acs.jchemed.5c01611`: the abstract is readable, the full text is not accessible, so it is not used as decisive evidence for a colour downgrade.
- The anonymous ICLR 2026 OpenReview PDF of Gauging Overprecision came up in the search, but a direct connection returned 404; it is not double-counted with the arXiv version that was read, and there is no claim that it was accepted at ICLR.
- The official CVPR 2026 PDF of MeasureBench returned 403; kept as a lead to read later.

`sources/precision_search_log.json` keeps the titles, URLs, tool citation identifiers and lengths of the returned results; to avoid redistributing large amounts of source text, the full scraped texts are not included in the deliverable.

