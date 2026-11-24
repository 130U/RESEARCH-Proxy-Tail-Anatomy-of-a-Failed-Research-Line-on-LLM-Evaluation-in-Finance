"""Aggregate fixed, manually reviewed same-fact labels and source substitutions."""
import csv
import json
from collections import Counter
from fractions import Fraction as F
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def read(name):
    with (ROOT/name).open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))


def main():
    candidates=read("duplicate_precision_test_candidates.csv")
    one=read("duplicate_precision_test_review_part1.csv")
    two=read("duplicate_precision_test_review_part2.csv")
    subs=read("duplicate_precision_test_substitutions_part1.csv")
    flags=Counter("yes" if r["confirmed_same_fact"] in {"true","yes"} else
                  "no" if r["confirmed_same_fact"] in {"false","no"} else "uncertain" for r in one+two)
    qids=set()
    relative=set()
    display=set()
    display_unavailable=set()
    for r in subs:
        qids.add(r["question_id"])
        if r["original_1pct_inside"]=="True" and r["alternative_1pct_inside"]=="False":
            relative.add(r["question_id"])
        if r["display_original"]=="inside" and r["display_alternative"]=="outside":
            display.add(r["question_id"])
        if r["display_original"]!="inside":
            display_unavailable.add(r["question_id"])
    for r in two:
        for z in json.loads(r["coarse_substitution_checks"] or "[]"):
            qids.add(z["question_id"])
            if z["outside_1pct_exe_ans"]:
                relative.add(z["question_id"])
            if z["display_cell"]=="outside":
                display.add(z["question_id"])
            if z["display_cell"] in {"baseline_incompatible","unavailable"}:
                display_unavailable.add(z["question_id"])
    # Separate semantic-role case: one text span describes two yearly facts.
    pnc=F(2616,1000)-F(2572,1000)
    assert pnc==F(11,250)
    out=dict(n_test_questions=1147,n_test_pages=380,candidate_pairs=len(candidates),
             candidate_pages=len({r["filename"] for r in candidates}),reviewed_pairs=len(one)+len(two),
             reviewed_status=dict(flags),single_source_substitution_questions=len(qids),
             substitution_question_ids=sorted(qids),cross_1pct_question_ids=sorted(relative),
             cross_display_question_ids=sorted(display),display_unavailable_ids=sorted(display_unavailable),
             separate_two_role_case=dict(id="PNC/2014/page_111.pdf-1",original_program="subtract(2.6, 2.6)",
                 source_resolved_program="subtract(2.616, 2.572)",original_value="0",alternative_exact=str(pnc),
                 alternative_decimal=float(pnc),cross_zero_width_relative_band=True,cross_display_integer_cell=False),
             limitations="Candidate generator only covers chosen table/text unit-scaled precision patterns. Review is a model-assisted source reading. Counts are lower bounds for this search domain, not complete semantic duplicate prevalence. Single-source replacements hold all other operands fixed. PNC requires two distinct role bindings and is separate.")
    (ROOT/"results/duplicate_summary.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps({k:v for k,v in out.items() if not k.endswith("ids")},ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
