| | Condition A: not asked | Condition B: asked | Condition C: asked and taught |
|---|---:|---:|---:|
| Scorable responses | 378/392; 96.4% [94.3%, 98.3%] | 374/392; 95.4% [93.1%, 97.5%] | 375/392; 95.7% [93.4%, 97.7%] |
| Median claimed digits | 5.00 [4.00, 11.00] | 2.00 [1.00, 2.00] | 2.00 [1.00, 2.00] |
| Median true reliable digits | 2.07 [1.95, 2.32] | 2.07 [1.95, 2.34] | 2.05 [1.94, 2.32] |
| Share over-reporting by more than one digit | 61.6% [56.1%, 67.0%] | 0.3% [0.0%, 0.8%] | 0.3% [0.0%, 0.8%] |
| Share of intervals "accurate" | — | 98.4% [96.6%, 99.7%] | 98.1% [96.3%, 99.7%] |
| Share of intervals "too narrow" | — | 1.1% [0.0%, 2.5%] | 1.1% [0.0%, 2.5%] |
| 1% judgment accuracy | — | 99.7% [99.2%, 100.0%] | 99.5% [98.6%, 100.0%] |

Brackets in the table are 95% intervals from 10,000 bootstrap draws over the fixed 237 page clusters; the first row also gives the scorable fraction. For A, "claimed digits" means only the literally printed digits. The previous round's 16/12 digits are the group medians for the 144 growth questions with the same source and the same formula.

Under the threshold fixed before execution (interval-accurate share ≥80% and 1% judgment accuracy ≥90%), this round is classified as **the model already knows**.
Same-question pairing C−B: interval-accurate share -0.3 percentage points [-0.8, +0.0]; 1% judgment accuracy -0.3 percentage points [-0.8, +0.0]. For 1/374 questions the true 1% status changed with the formula or source; the difference cannot be read as a pure causal effect of precision awareness.

Main semantic-review figure: **139 → 123** (valid in both rounds); valid by majority: 132. Two-round agreement on the 196 witness questions 88.3% [84.1%, 92.2%], κ=0.76 [0.67, 0.84]. Second-round invalid/uncertain: stable questions 18/60 (30.0% [18.2%, 42.4%]), witness questions 70/196 (35.7% [29.1%, 42.6%]).
The 68 T1C rejection cases: two-round attribution agreement 92.6% [86.2%, 98.5%], κ=0.88 [0.77, 0.97]; among the 63 cases where both rounds agree on the attribution, "reference error" 32/63 (50.8% [37.9%, 63.9%]), "defensible alternative convention" 23/63 (36.5% [23.8%, 49.2%]); as strict counts over all reviewed cases, the two categories are 32/68 and 23/68.

Independent rerun of B (gpt-6.1-sol / high): 375/392 scorable, interval accurate 98.1% [96.3%, 99.7%], over-reporting by more than one digit 0.5% [0.0%, 1.4%], 1% judgment accuracy 99.5% [98.6%, 100.0%]; not mixed into the main conclusion.

Interpretation limits: A's printed digits are not the same as an active statement of reliable precision; B was already reminded that the numbers are rounded, so it measures whether the model can compute after the reminder. Every truth value follows the response's own formula. FinQA is public, so training exposure may exist; the absence of interval labels does not mean contamination has been ruled out. The exact service version for A was not exposed, and B/C ran at different times, so cross-condition comparisons keep the service-condition limitation.
