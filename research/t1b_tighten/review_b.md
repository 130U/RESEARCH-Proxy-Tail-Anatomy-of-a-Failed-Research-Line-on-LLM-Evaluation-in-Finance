# T1B per-question source review B

Scope: the last 98 candidate questions after sorting by question ID. All of `table_ori`, `pre_text` and `post_text` provided by FinQA were read, and T1's physical sources, units, periods and standard programs were checked item by item; other pages of the original annual reports were not accessed. This file is a record of semantic review performed by an agent, not an independent human sign-off.

98 questions: valid=67; clearly invalid=22; uncertain=9. The 23 questions of the fixed-seed sample that fall in this part: valid=15, invalid=5, uncertain=3. These 23 alone cannot be used to infer the overall error rate; they should be combined with the 17 in part A.

## Sources and constraints

- Each input has its own `input_review`, which includes the search scope, the number of duplicate disclosures of the same fact found, and the number of narrower disclosures.
- Records of additional same-fact disclosures were confirmed for 14 inputs: the two operands of MSI 2008 have more precise table disclosures; the other 12 have the same precision, so intersecting them alone does not narrow anything. MSI's original text gives positive absolute loss amounts, while the table gives negative profit/loss figures, and `scale=-1/1000` is used explicitly.
- 272 semantically confirmed equations are kept, including totals, net amounts, opening-to-closing roll-forwards, and text-table links for the same fact. The exactness of table counts and the display rounding of amounts are handled separately.
- Of the 301 automatically generated numeric sum candidates, 86 are supported by a confirmed complete relation or are redundant expressions of one, and 215 are not supported; no identity was accepted just because the numbers happen to add up. The full disposition is in the JSON's `sum_candidate_review`.
- After the sign-handling fix, the automatic screen has 73 candidates in total: 2 are the confirmed precise MSI disclosures, and 71 were rejected for a wrong metric, year, unit or standard number; all have per-item reasons. MSI was first found by semantic reading and was then added to the automatic scanner's regression coverage.
- Missing entries are not uniformly treated as zero. Only displayed zeros within a sum structure are modeled with a conservative half-a-last-digit-unit zero interval; GIS's other long-term obligations that cannot be dated are not filled into the future installment columns. RSG's asset allocation total of 100% is a defined value.
- PM's "primarily due to" pension expense bridge was deleted after being challenged by another agent; PPG's product warranty narrative does not state that the changes are complete, so no complete roll-forward equation is imposed. The deletions did not depend on whether they help retain the conclusion.

## Samples that need particular attention

|Question|Judgment|Evidence|
|---|---|---|
|LMT/2014/page_77.pdf-3|invalid|1.3 billion is divided directly by 804 million, missing the factor-of-1000 unit conversion.|
|NCLH/2018/page_64.pdf-2|invalid|The question asks about 2017→2018, but the inputs are actually projected 2019/2020 capital expenditures.|
|STT/2009/page_25.pdf-2|invalid|2009 is 24 and 2008 is 31; the program uses (31−24)/24, inverting the years and the base period.|
|ZBH/2007/page_67.pdf-1|invalid|2007 is 1.0 and 2006 is 8.8; the program inverts the years and the denominator.|
|RSG/2018/page_135.pdf-1|invalid|82/18 is a policy target asset allocation and cannot by default be a measured value with hidden last digits.|
|MRO/2007/page_136.pdf-2|uncertain|37 million / a weighted average of 1.4 years gives only an average annualized value; how much is recognized in the first year cannot be determined.|
|MSI/2008/page_69.pdf-2|uncertain|The more precise disclosure can narrow the interval, but the question says decline while the original text has growing losses; the numerical repair is not allowed to mask the semantic problem.|
|HIG/2004/page_140.pdf-1|uncertain|The table is the effect of the initial adoption of SOP 03-1, while the question's prospective method corresponds to SFAS 123R later in the text; the scope is doubtful.|

## Interpretation conventions

"change / decline" allows a decrease to be expressed as a signed change; a question is not excluded merely because of wording about a negative sign. When a question omits dollar and the source is a table of asset values explicitly in millions, it is read as an amount and not misread as a count of vehicles or buildings. The T1 context year error in MAR 2004's multi-level header is pointed out separately, but the physical value binding is correct, so the question is kept. The 20011 in STT 2014 is explicitly recorded as an obvious input error for 2011; the data was not silently corrected.

The final numbers should come from the main pipeline re-reading this JSON, solving and verifying the certificates; this file does not replace the numerical results.
