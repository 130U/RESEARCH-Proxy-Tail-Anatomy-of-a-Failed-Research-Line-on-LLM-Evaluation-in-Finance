# WP0.1 pre-run budget

Date: 2026-11-15; base commit: 8e4dd0b33c95ac2ac1a6015eba6f2dfafe5c1254.

- Hardware: local CPU, NumPy; no GPU.
- Expected time: confusion-matrix enumeration, 4 × 100,000 multinomial bootstrap draws and the tests take no more than 3 minutes in total.
- Expected GPU memory: 0; expected RAM below 256 MiB.
- Input: the published summary of the 101-row development set; no private text is read or published; no training tokens.
- Output: all matrices consistent with the integer margins, a 95% percentile bootstrap interval for each matrix, and a reproducible results JSON.
- Source level of numbers: the input is the repository's public summary (a second-hand record of my earlier training logs); the computed output is "our experiment wp0_1".
- Pre-registered limits: this is a sensitivity reconstruction with an IID row bootstrap, not a family bootstrap; it does not correct the development-set model-selection bias; it does not test the paired difference against TF-IDF. Without paired predictions and cluster IDs, no significant/non-significant verdict may be made.
