# Part One: intersection with existing answers

Source level: our experiment, reusing existing T1c/T1d answers; no new model calls.

Part One currently matches 5 FinQA question–printed-value pairs (5 distinct questions), of which 5 disagree under official scoring. The intersection with the original 392-question sample is **0 questions**; the intersection with officially affected questions is **0 questions**, with 0 matched answers in total.

T1d condition A reuses T1c and has been deduplicated; B, C, and B_secondary are each kept. The selected-value label first compares the exact value of the normalized expression, then the FinQA official five-decimal execution value. Equal numbers show only that the results agree; they do not prove which cell the model actually read.

If the intersection is zero, these existing answers cannot answer "does the model choose the printed value or the recomputed value on affected questions", nor can they be used to assert that the model does not show this behavior.

After `part1_questions.json` is updated, rerun `part1_existing_responses.py` to refresh the results.
