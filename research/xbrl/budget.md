# WP0.4 offline check budget

Date: 2026-11-15. Status: filled in before the run.

- CPU, Python standard library, expected under 10 seconds; 0 GPU memory, 0 training tokens, memory expected below 64MiB.
- Data: a hand-written miniature XML fixture, explicitly synthetic; no real SEC files are used and no network endpoint is requested.
- Checked: parsing of unit, scale, sign, decimals and context in the restricted non-fraction fact domain; explicit rejection of formats outside the supported scope.
- This is not used to estimate real parsing accuracy, timestamp reliability, text coverage or yearly data volume.
