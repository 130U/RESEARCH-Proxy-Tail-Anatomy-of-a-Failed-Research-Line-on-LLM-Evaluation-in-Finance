"""Parameter-free population plug-in prediction, without observed mantissas.

Primary model: empirical growth marginal independent of the empirical joint
display-precision pair; log-uniform baseline mantissa independent of both.
Joint (growth, precision) plug-in and first-digit-only bounds are sensitivities.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path

from law_core import read_rows, growth_descriptor, range_certificate, classify_range, exact

ROOT = Path(__file__).resolve().parent
TAUS = (.001, .005, .01, .02, .05)


def mantissa_prediction(g, ka, kb, tau):
    """Integrate exact relative worst-case radius over M in [1,10).

    Returns full Benford-mantissa, uniform-within-first-digit sensitivity,
    and identification lower/upper bounds with first-digit probabilities only.
    Assumes r=1+g>0; positive baseline, g != 0, decimal significant digits.
    """
    r = 1+g
    if r <= 0 or g == 0: raise ValueError("outside prior model domain")
    ha = .5*10.**(1-ka)
    points = [float(d) for d in range(1, 11)]
    for e in range(math.floor(math.log10(r))-1, math.floor(math.log10(10*r))+2):
        point = 10.**e/r
        if 1 < point < 10: points.append(point)
    points = sorted(set(points))
    log_mass = 0.
    lengths = {d:0. for d in range(1,10)}
    every_segment = {d:True for d in range(1,10)}
    any_segment = {d:False for d in range(1,10)}
    for left, right in zip(points, points[1:]):
        mid = (left+right)/2
        hb = .5*10.**(math.floor(math.log10(r*mid))-kb+1)
        boundary = ha + (hb+r*ha)/(tau*abs(g))
        upper = min(right, max(left, boundary))
        log_mass += math.log10(upper/left)
        digit = min(9, int(mid))
        lengths[digit] += upper-left
        every_segment[digit] &= boundary >= right
        any_segment[digit] |= boundary > left
    weights = {d: math.log10(1+1/d) for d in range(1,10)}
    within_digit_uniform = sum(weights[d]*lengths[d] for d in range(1,10))
    lower = sum(weights[d] for d in range(1,10) if every_segment[d])
    upper = sum(weights[d] for d in range(1,10) if any_segment[d])
    return log_mass, within_digit_uniform, lower, upper


def avg(values):
    return [sum(x[i]*w for x,w in values)/sum(w for _,w in values) for i in range(4)]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",type=Path,default=ROOT.parent/"t1_rounding/results/per_question.jsonl")
    parser.add_argument("--output-dir",type=Path,default=ROOT/"results")
    args=parser.parse_args()
    eligible=[]; excluded=Counter()
    for row in read_rows(args.input):
        if row["status"]!="analyzed" or row["category"]!="growth": continue
        desc=growth_descriptor(row)
        if desc is None:
            excluded["not_canonical_two_source_growth"]+=1; continue
        if not desc["same_sign"]:
            excluded["opposite_sign_or_zero_current_value"]+=1; continue
        if desc["g"]==0:
            excluded["zero_growth"]+=1; continue
        cert=range_certificate(row)
        if not cert["exact"]:
            raise AssertionError("Canonical growth range must be exact")
        # Full mantissas used below ONLY for the observed outcome, never predictor.
        gold=exact(row["exe_ans"]); center=exact(row["center"])
        item={"id":row["id"],"split":row["split"],"g":float(desc["g"]),"k_a":desc["k_a"],"k_b":desc["k_b"]}
        for tau in TAUS:
            t=exact(tau)
            item["observed_gold_"+str(tau)]=classify_range(cert,gold,t)=="outside"
            item["observed_center_"+str(tau)]=classify_range(cert,center,t)=="outside"
        eligible.append(item)
    summary={"scope":"Same-sign canonical two-input nonzero growth; all analyzed splits, no test/train fitting.",
             "primary":"Empirical marginal growth distribution independent of empirical joint (k_a,k_b) distribution; baseline mantissa log-uniform on [1,10), independent of both. Gold assumed equal to displayed-center calculation.",
             "sensitivity":"Joint empirical (g,k_a,k_b); uniform within each Benford first-digit bin; first-digit-only bounds. All are same-data plug-in checks, not out-of-sample forecasts.",
             "excluded_growth_rows":dict(excluded),"n":len(eligible),"by_tolerance":{},"by_k_a":[],"by_split":{}}
    precisions=Counter((r["k_a"],r["k_b"]) for r in eligible)
    growths=Counter(r["g"] for r in eligible)
    cache={}
    def pred(g,ka,kb,tau):
        key=(g,ka,kb,tau)
        if key not in cache: cache[key]=mantissa_prediction(g,ka,kb,tau)
        return cache[key]
    def summarize(subset, tau, global_growths=None):
        ps=Counter((r["k_a"],r["k_b"]) for r in subset)
        gs=global_growths or Counter(r["g"] for r in subset)
        marginal=avg([(pred(g,ka,kb,tau),ng*nk) for g,ng in gs.items() for (ka,kb),nk in ps.items()])
        joint=avg([(pred(r["g"],r["k_a"],r["k_b"],tau),1) for r in subset])
        gold=sum(r["observed_gold_"+str(tau)] for r in subset)/len(subset)
        center=sum(r["observed_center_"+str(tau)] for r in subset)/len(subset)
        return {"n":len(subset),"observed_gold_rate":gold,"observed_center_rate":center,
                "marginal_prediction":marginal[0],"marginal_error_pp":100*(marginal[0]-gold),
                "joint_prediction":joint[0],"joint_error_pp":100*(joint[0]-gold),
                "marginal_uniform_within_digit":marginal[1],
                "marginal_first_digit_only_lower":marginal[2],"marginal_first_digit_only_upper":marginal[3]}
    for tau in TAUS: summary["by_tolerance"][str(tau)]=summarize(eligible,tau)
    for ka in sorted(set(r["k_a"] for r in eligible)):
        sub=[r for r in eligible if r["k_a"]==ka]
        summary["by_k_a"].append({"k_a":ka,**summarize(sub,.01,growths)})
    for split in ("train","dev","test"):
        summary["by_split"][split]=summarize([r for r in eligible if r["split"]==split],.01)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/"benford_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    with (args.output_dir/"benford_inputs_and_outcomes.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(eligible[0]));writer.writeheader();writer.writerows(eligible)
    print(json.dumps({"n":summary["n"],"excluded":dict(excluded),"1pct":summary["by_tolerance"]["0.01"]},indent=2))


if __name__=="__main__":main()
