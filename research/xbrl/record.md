# Experiment WP0.4-offline: restricted numeric and unit parsing

## Question to test

Only verify the unit, scale, sign, decimals and context conversion, and the rejection behaviour on failure, for a local hand-made synthetic fixture; this does not answer whether the real SEC corpus is sufficient to support a trusted core.

## Budget

The pre-run record is in [budget.md](budget.md): CPU, expected within 10 seconds, 0 GPU memory, 0 training tokens, no network.

## Configuration

- Base commit: 8e4dd0b33c95ac2ac1a6015eba6f2dfafe5c1254; the new code is in research/xbrl/ and was not committed at run time.
- Python 3.12.14, Windows AMD64 CPU, standard library; no random seed needed.
- Data: `synthetic_fixture.xml`, SHA256 in [example_result.json](example_result.json). The fact structure was specified by hand in this round.
- Actual tests: all 8 unittests passed; the test framework timed 0.006 seconds, and the parse + test tool calls took about 1.35 seconds (including process start-up). Source level: **our experiment WP0.4-offline**.

## Results

| Condition | Output | Interpretation |
|---|---|---|
| 123.40 × 10^6 USD | 123400000 | Exact scale conversion |
| 5.2 × 10^3 USD, sign=- | -5200 | sign and scale applied separately |
| ratio=0.125, decimals=3 | Declared rounding interval [0.1245,0.1255] | Conditional on the accuracy declaration; not verification of the true value |
| unknown accounting transformation | Rejected, reason kept | (1,234) is not guessed to be a supported input |
| missing unit/context, continuation, reversed period, out-of-domain scale, missing decimals | The corresponding facts are rejected | No value is returned that looks valid but lacks its premises |
| duplicate ID / DTD | Whole document rejected | No ambiguous binding is chosen |

The full JSON is in `example_result.json`, with 3 parsed facts, 1 format rejection, `status=partial` and `timestamp_certificate=null`. These counts are deterministic checks of specific hand-made cases, not a random sample, so there is no 95% interval for the true error rate.

## Conclusion and limits

The interface from local files to restricted structured values runs. Real SEC statistics, calc coverage, accepted precision, amended filings, inline text alignment and yearly supervision scale were not measured. The prototype cannot prove real absence of look-ahead or correct unit parsing on open text, and it does not constitute full WP0.4 acceptance. No new external access was added.
