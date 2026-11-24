"""Reproduce the mentor rule, then audit all analyzable T1 programs."""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
import csv
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import platform
from law_core import (read_rows,exact,centers_half,gradient_radius,range_certificate,
                      classify_range,growth_descriptor,jsonable)

ROOT=Path(__file__).resolve().parent
TAUS=(F(1,1000),F(1,200),F(1,100),F(1,50),F(1,20))


def confusion(pairs):
    c=Counter((pred,truth) for pred,truth in pairs if truth in ("inside","outside"))
    n=sum(c.values()); correct=c[False,"inside"]+c[True,"outside"]
    return {"n":n,"true_positive":c[True,"outside"],"false_positive":c[True,"inside"],
            "true_negative":c[False,"inside"],"false_negative":c[False,"outside"],
            "accuracy":correct/n if n else None,"unresolved":sum(t=="unresolved" for _,t in pairs)}


def write_csv(path,rows,fieldnames=None):
    if not rows and fieldnames is None: return
    with path.open("w",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=fieldnames or list(rows[0]),lineterminator="\n")
        writer.writeheader();writer.writerows(rows)


def simple_reason(row,descriptor,raw_delta,truth,cert):
    if descriptor is None: return "Program is not a growth rate of two numbers; the original category's structural label is too broad"
    if descriptor["unit_ratio"]!=1: return "Raw inputs have different units; direct subtraction skips the program's unit conversion"
    center=exact(row["center"]); gold=F(str(row["exe_ans"]))
    center_truth=classify_range(cert,center,F(1,100))
    if center_truth!=truth: return "The offset between gold and the center value changes the boundary margin"
    if not descriptor["equal_units"]: return "The two inputs have different displayed units; the simple difference rule misses the weighted sensitivity"
    if not descriptor["same_sign"]: return "The two numbers have opposite signs; the small-growth same-sign approximation does not apply"
    return "Omits the finite growth factor (1+g/2) and the nonlinear denominator correction; not the small-growth limit"


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",type=Path,default=ROOT.parent/"t1_rounding/results/per_question.jsonl")
    parser.add_argument("--output-dir",type=Path,default=ROOT/"results")
    args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=True)
    all_rows=read_rows(args.input);rows=[r for r in all_rows if r["status"]=="analyzed"]
    results=[];mentor=[];mistakes=[];fo_mistakes=[];tau_mistakes=[];canonical_mistakes=[]
    methods=Counter();contradictions=[]
    for row in rows:
        center,radius,gradient=gradient_radius(row)
        assert center==exact(row["center"]),(row["id"],center,row["center"])
        gold=F(str(row["exe_ans"]));offset=abs(center-gold)
        cert=range_certificate(row);methods[cert["method"]]+=1
        desc=growth_descriptor(row)
        pred=offset+radius>abs(gold)/100
        t1_status={"certified_inside":"inside","witnessed_outside":"outside","unresolved":"unresolved"}[row["relative_1pct"]["status"]]
        statuses={str(float(tau)):classify_range(cert,gold,tau) for tau in TAUS}
        truth=statuses["0.01"]
        if t1_status!="unresolved" and truth!="unresolved" and truth!=t1_status:
            contradictions.append(row["id"])
        details={"id":row["id"],"split":row["split"],"category":row["category"],
                 "program":row["program"],"t1_status":t1_status,"exact_status":truth,
                 "center":center,"gold":gold,"gold_offset":offset,"first_order_radius":radius,
                 "first_order_prediction":"outside" if pred else "inside",
                 "centered_first_order_prediction":"outside" if radius>abs(center)/100 else "inside",
                 "gradient":gradient,"range_method":cert["method"],"range_exact":cert["exact"],
                 "lo":cert["lo"],"hi":cert["hi"],"status_by_tau":statuses,
                 "first_order_by_tau":{str(float(tau)):"outside" if offset+radius>abs(gold)*tau else "inside" for tau in TAUS},
                 "growth":desc}
        for tau in TAUS:
            key=str(float(tau))
            if statuses[key]!="unresolved" and details["first_order_by_tau"][key]!=statuses[key]:
                tau_mistakes.append({"id":row["id"],"split":row["split"],"category":row["category"],
                                    "tau":float(tau),"program":row["program"],
                                    "prediction":details["first_order_by_tau"][key],"truth":statuses[key],
                                    "reason":"First-order linearization does not include the nonlinear remainder or the asymmetry of the true range",
                                    "center":str(center),"gold":str(gold),"radius":str(radius),
                                    "lo":str(cert["lo"]),"hi":str(cert["hi"]),"margin":str(abs(gold)*tau-offset)})
        if desc is not None and truth!="unresolved" and (desc["delta"]<100)!=(truth=="outside"):
            canonical_mistakes.append({"id":row["id"],"split":row["split"],"program":row["program"],
                "delta":float(desc["delta"]),"delta_exact":str(desc["delta"]),"g":float(desc["g"]),
                "prediction":"outside" if desc["delta"]<100 else "inside","truth":truth,
                "reason":simple_reason(row,desc,desc["delta"],truth,cert),"center":str(center),
                "gold":str(gold),"radius":str(radius),"lo":str(cert["lo"]),"hi":str(cert["hi"])})
        if truth!="unresolved" and pred!=(truth=="outside"):
            reason=("The first-order remainder pushes the true deviation past the threshold" if not pred else
                    "The first-order symmetric radius is added to the gold offset in the same direction; the asymmetry of the true range is not used")
            fo_mistakes.append({"id":row["id"],"split":row["split"],"category":row["category"],
                                "program":row["program"],"prediction":details["first_order_prediction"],
                                "truth":truth,"reason":reason,"center":str(center),"gold":str(gold),
                                "radius":str(radius),"lo":str(cert["lo"]),"hi":str(cert["hi"]),
                                "margin":str(abs(gold)/100-offset)})
        if row["category"]=="growth" and len(row["input_intervals"])==2:
            centers,half=centers_half(row);values=list(centers.values())
            raw_delta=abs(values[0]-values[1])/sum(half.values())
            details["raw_delta"]=raw_delta
            if t1_status!="unresolved":
                mpred=raw_delta<100;correct=mpred==(t1_status=="outside")
                m={"id":row["id"],"split":row["split"],"program":row["program"],
                   "raw_delta":float(raw_delta),"raw_delta_exact":str(raw_delta),
                   "prediction":"outside" if mpred else "inside","t1_status":t1_status,
                   "correct":correct,"canonical_growth":desc is not None,
                   "canonical_delta":None if desc is None else float(desc["delta"]),
                   "g":None if desc is None else float(desc["g"]),
                   "first_order_relative_radius":None if not center else float(radius/abs(center)),
                   "exact_relative_radius":None if not center else float(max(abs(cert["lo"]-center),abs(cert["hi"]-center))/abs(center)),
                   "gold_margin":str(abs(gold)/100-offset),
                   "reason":"" if correct else simple_reason(row,desc,raw_delta,t1_status,cert)}
                mentor.append(m)
                if not correct: mistakes.append(m)
        results.append(details)
    assert not contradictions,contradictions
    by_category={}
    for category in sorted(set(r["category"] for r in results)):
        group=[r for r in results if r["category"]==category]
        by_category[category]={"n":len(group),
            "against_t1":confusion([(r["first_order_prediction"]=="outside",r["t1_status"]) for r in group]),
            "against_recomputed":confusion([(r["first_order_prediction"]=="outside",r["exact_status"]) for r in group]),
            "range_methods":dict(Counter(r["range_method"] for r in group))}
    curve=[]
    for split in ("all","train","dev","test"):
        group=[r for r in results if split=="all" or r["split"]==split]
        total=sum(split=="all" or r["split"]==split for r in all_rows)
        for tau in TAUS:
            key=str(float(tau));counts=Counter(r["status_by_tau"][key] for r in group)
            curve.append({"split":split,"tau":float(tau),"analyzed_n":len(group),"all_questions_n":total,
                          "outside":counts["outside"],"inside":counts["inside"],"unresolved":counts["unresolved"],
                          "outside_fraction_analyzed":counts["outside"]/len(group),
                          "outside_fraction_all_questions":counts["outside"]/total,
                          "upper_fraction_analyzed":(counts["outside"]+counts["unresolved"])/len(group)})
    bins=[]
    for lower,upper in ((0,60),(60,100),(100,150),(150,300),(300,float("inf"))):
        group=[r for r in mentor if lower<=r["raw_delta"]<upper]
        n=len(group);outside=sum(r["t1_status"]=="outside" for r in group)
        bins.append({"lower":lower,"upper":None if upper==float("inf") else upper,
                     "n":n,"outside":outside,"fraction":outside/n if n else None})
    canonical=[r for r in results if r["growth"] is not None]
    strict=[]
    for row in rows:
        s=row["steps"]
        if len(s) not in (2,3) or s[0][0]!="subtract": continue
        _,b,a=s[0]
        if a not in row["input_intervals"] or b not in row["input_intervals"] or a==b: continue
        if s[1]!=["divide","#0",a]: continue
        if len(s)==3 and s[2] not in (["multiply","#1","const_100"],["multiply","const_100","#1"]):continue
        strict.append(row["id"])
    summary={"date":"2026-11-16","timezone":"America/New_York",
             "python":platform.python_version(),"input_sha256":hashlib.sha256(args.input.read_bytes()).hexdigest(),
             "n_all":len(all_rows),"n_analyzed":len(results),"n_unanalyzed":len(all_rows)-len(results),
             "interpretation":"Conditional on T1 source binding and independent half-unit rounding boxes. Not an official FinQA scoring rule.",
             "rule":"abs(center-gold) + sum(abs(gradient_i)*h_i) > tau*abs(gold)",
             "mentor_replication":{"n":len(mentor),"correct":sum(r["correct"] for r in mentor),
                 "accuracy":sum(r["correct"] for r in mentor)/len(mentor),"errors":len(mistakes),
                 "definition":"T1 analyzed; category growth; exactly 2 bound inputs; T1 non-unresolved; raw unconverted center difference / sum halfwidths",
                 "bins":bins,"error_reasons":dict(Counter(r["reason"] for r in mistakes))},
             "canonical_growth_n":len(canonical),"strict_original_growth_n":len(strict),
             "canonical_simple_rule":confusion([(r["growth"]["delta"]<100,r["exact_status"]) for r in canonical]),
             "first_order_by_tau":{str(float(tau)):confusion([(r["first_order_by_tau"][str(float(tau))]=="outside",r["status_by_tau"][str(float(tau))]) for r in results]) for tau in TAUS},
             "centered_first_order_errors":sum(r["centered_first_order_prediction"]!=r["exact_status"] for r in results),
             "by_category":by_category,"range_methods":dict(methods),"t1_certificate_contradictions":contradictions,
             "recomputed_status_counts":dict(Counter(r["exact_status"] for r in results)),
             "resolved_original_unresolved":[{"id":r["id"],"status":r["exact_status"],"method":r["range_method"]} for r in results if r["t1_status"]=="unresolved"],
             "first_order_error_count":len(fo_mistakes),"tolerance_curve":curve}
    (args.output_dir/"per_question.jsonl").write_text("".join(json.dumps(jsonable(r),ensure_ascii=False)+"\n" for r in results),encoding="utf-8")
    (args.output_dir/"summary.json").write_text(json.dumps(jsonable(summary),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    write_csv(args.output_dir/"mentor_replication.csv",mentor)
    write_csv(args.output_dir/"simple_rule_mismatches.csv",mistakes)
    write_csv(args.output_dir/"first_order_mismatches.csv",fo_mistakes,["id","split","category","program","prediction","truth","reason","center","gold","radius","lo","hi","margin"])
    write_csv(args.output_dir/"first_order_tau_mismatches.csv",tau_mistakes)
    write_csv(args.output_dir/"canonical_simple_mismatches.csv",canonical_mistakes)
    write_csv(args.output_dir/"tolerance_curve.csv",curve)
    print(json.dumps({"mentor":summary["mentor_replication"],"by_category":by_category,
                      "canonical_growth_n":len(canonical),"strict_original_growth_n":len(strict),
                      "range_methods":dict(methods),"status_counts":summary["recomputed_status_counts"]},ensure_ascii=True,indent=2))


if __name__=="__main__": main()
