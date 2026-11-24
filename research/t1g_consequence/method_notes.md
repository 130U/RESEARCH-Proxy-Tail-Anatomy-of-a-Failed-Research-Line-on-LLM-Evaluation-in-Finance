# T1g conventions and evidence

2026-11-17. Source levels are marked separately: task text, earlier experiments, our experiment. The work is limited to the task's four questions and the verification of two citations; the README and the paper are not changed.

## Goal and sources

Goal: judge visible consequences under T1g's original thresholds, and run the out-of-sample rule test on TAT-QA. The scope is financial question-answering benchmarks; the object is the propagation of displayed precision; the units are table relations and questions with explicitly bound sources. This is an experimental study of existing data, supported by a preliminary exploratory novelty check.

The primary sources, in order, are the official pinned versions of the FinQA/TAT-QA data and scoring code, the full texts of the original papers, and the frozen results of the earlier T1/T1a/T1b/T1c/T1d. Secondary web material is used only to locate original texts. Each fact and its source are recorded in the reports of the individual parts and in literature.md.

## Execution boundaries

Parts One and Two wait for the novelty-check gate; all exact TAT-QA range computations wait until the Part Three prediction has been committed on its own. Part Three must not change the prediction based on the measurements. Computed conclusions use exact rationals or certified envelopes; sampled probabilities are called only numerical estimates under the model. AI reading is not passed off as human review.

When the same document appears across several questions, table-row statistics are deduplicated; QA statistics are counted per question. Missed detections, parse exclusions, unclear units, and semantic mismatches are all reported, and are not treated as stable or consistent.

## Prior derivation for amount differences

Let the two levels share the same last-digit unit d, and let the errors U,V of the two true levels relative to the displayed centers be independent and uniform on [-d/2,d/2]. The true difference is obtained by subtracting the same true levels and is then rounded to the nearest multiple of d. The difference of the displayed centers lies exactly on the grid of d, so the printed difference differs from the center difference if and only if |U−V|>d/2. In the unit square the two corner triangles each have area 1/8, for a total probability of 1/4. The probability of equality at the boundary is zero.

Here "each rounded separately" does not mean the three rounding errors are statistically independent: the third error is determined by U−V and the rounding grid. Forcing the three errors to be mutually independent while also requiring the true-difference identity makes the model inconsistent. The 1/4 requires the two levels to have the same last digit and the difference to use the same last digit as well; rows with mixed precision must be integrated row by row.

Percentage changes work the same way: first perturb the two true levels, then form the ratio and round it; the third printed value cannot be treated as a separate independent random draw. Nor should the position histogram be expected to be uniform: even if the input errors are uniform, the difference has a triangular distribution, and the ratio is usually even less uniform. It must be compared with the predicted histogram from the same generative model.
