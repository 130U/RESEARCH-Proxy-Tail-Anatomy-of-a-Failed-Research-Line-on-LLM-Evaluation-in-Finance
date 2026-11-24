# WP0.4: offline restricted inline-XBRL parsing prototype

Date: 2026-11-15. Status: **offline prototype complete; feasibility on a real corpus not evaluated**. All examples here are hand-written synthetic XML; they are not SEC filings, not data scraped from outside, and not fully compliant iXBRL examples. The program has only a local file interface and no networking code.

```powershell
python -m research.xbrl.parse_local research/xbrl/synthetic_fixture.xml research/xbrl/example_result.json
python -m unittest research.xbrl.test_parse_local -v
```

Supported domain: `nonFraction` in the 2013 iXBRL namespace; non-negative decimal literals without a transformation; negative sign expressed only by `sign="-"`; integer `scale`, and `decimals` as an integer or `INF`; a unit referencing one simple measure; a context with an explicit entity identifier and an instant or startDate/endDate. `scale` and finite `decimals` are limited to [-18,18], and numeric literals to at most 100 characters. Declared values are converted exactly with Decimal. QNames are expanded to URIs, **without verifying that the taxonomy actually exists or its economic semantics**.

The following cases return rejection/abstain instead of guessing: unknown format/transformation, parenthesized negatives/numbers with commas, continuation, nested fact text, nil, missing unit/context, complex units, dimensions/scenario, unknown/inverted/non-ISO periods, and the precision attribute. Duplicate XML ids, namespace rebinding or invalid XML reject the whole file. `fraction/nonNumeric` are only counted as unsupported and not parsed; unknown structures in other namespaces should not be interpreted as verified.

`declared_rounding_enclosure` is only a conservative closed interval around the declared value, under the condition that "the document's decimals accuracy declaration is trustworthy and the corresponding rounding interpretation is adopted". It does not prove the company's true value, does not guarantee financial identities, and does not prove that the document is tagged correctly. `INF` is handled exactly at the declared value; this is not an official XBRL validator.

The time certificate is always output as `null`. `accepted`, the filing period, the web publication date and the download time are fields with different semantics; linking the acceptance time to the currently downloaded content version also needs provenance and revision-correspondence evidence. **The presence of an accepted field does not prove that the content was publicly available at the moment of acceptance**, and it must not be used directly as core evidence with zero failure probability. Quarterly aggregate files also cannot automatically be treated as snapshots visible at some past moment: later corrections, restatements, duplicate facts and version selection must be handled. This prototype did not read or confirm SEC field formats, precision, publication delays, calculation relationships or statistics of real quarterly data.

What later real verification can plug in: local files that may be used, with their content hashes; acceptance/public-availability/download/revision time metadata; manually checked fact-text alignment and parse results. The pass/reject proportions on these 4 hand-made facts cannot be extrapolated to real coverage or error rates. If new data fall outside the supported domain, first extend the explicit specification and counterexamples, then measure accuracy; do not silently fall back to guessing numbers.
