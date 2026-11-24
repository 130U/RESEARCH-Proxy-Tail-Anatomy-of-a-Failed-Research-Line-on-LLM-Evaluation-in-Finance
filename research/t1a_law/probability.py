"""Independent uniform rounding model; exact linear-fractional CDF or seeded MC.

Reads only the frozen T1 per-question JSONL. No fitting and no model API calls.
Run from any directory; outputs stay under this task's results directory.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
import sympy as sp

ROOT = Path(__file__).resolve().parent
TAUS = (.001, .005, .01, .02, .05)


def constant(t):
    token = t.removeprefix("const_").replace("_", ".")
    return "-1" if token == "m1" else token


def load(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines()]


def geometry(row):
    names = list(row["input_intervals"])
    ends = [(float(sp.Rational(row["input_intervals"][n]["lo"]["exact"])),
             float(sp.Rational(row["input_intervals"][n]["hi"]["exact"]))) for n in names]
    return names, np.array([(lo+hi)/2 for lo, hi in ends]), np.array([(hi-lo)/2 for lo, hi in ends])


def execute(row, values):
    intermediate = []
    def val(t):
        if t in values:
            return values[t]
        if t.startswith("#"):
            return intermediate[int(t[1:])]
        return float(constant(t))
    for op, l, r in row["steps"]:
        x, y = val(l), val(r)
        if op == "add": z = x+y
        elif op == "subtract": z = x-y
        elif op == "multiply": z = x*y
        elif op == "divide": z = x/y
        else: raise ValueError(op)
        intermediate.append(z)
    return intermediate[-1]


def affine_fraction(row):
    """Exact symbolic reduction, at most two independent rounding variables."""
    names = list(row["input_intervals"])
    if len(names) > 2:
        return None
    symbols = dict(zip(names, sp.symbols(" ".join(names), seq=True)))
    steps = []
    def v(t):
        if t in symbols: return symbols[t]
        if t.startswith("#"): return steps[int(t[1:])]
        return sp.Rational(constant(t))
    for op, a, b in row["steps"]:
        x, y = v(a), v(b)
        steps.append({"add": lambda: x+y, "subtract": lambda: x-y,
                      "multiply": lambda: x*y, "divide": lambda: x/y}[op]())
    num, den = sp.fraction(sp.cancel(steps[-1]))
    pn, pd = sp.Poly(num, *symbols.values()), sp.Poly(den, *symbols.values())
    if pn.total_degree() > 1 or pd.total_degree() > 1:
        return None
    zero = {s: 0 for s in symbols.values()}
    n0, d0 = float(num.subs(zero)), float(den.subs(zero))
    nc = np.array([float(sp.diff(num, s)) for s in symbols.values()])
    dc = np.array([float(sp.diff(den, s)) for s in symbols.values()])
    _, centers, half = geometry(row)
    denom = d0 + dc@centers
    if abs(denom) <= np.abs(dc)@half:
        return None
    return n0, nc, d0, dc, centers, half, np.sign(denom)


def uniform_cdf(z, p, q):
    """CDF of Unif[-p,p]+Unif[-q,q], stable piecewise quadratic."""
    p, q = max(abs(p), abs(q)), min(abs(p), abs(q))
    if p == 0:
        return float(z >= 0)
    if q == 0:
        return min(1., max(0., (z+p)/(2*p)))
    if z <= -p-q: return 0.
    if z < -p+q: return (z+p+q)**2/(8*p*q)
    if z <= p-q: return (z+p)/(2*p)
    if z < p+q: return 1-(p+q-z)**2/(8*p*q)
    return 1.


def exact_probability(model, lo, hi):
    n0, nc, d0, dc, c, h, sign = model
    def cdf(t, strict=False):
        coeff = sign*(nc-t*dc)
        center = sign*(n0-t*d0)+(coeff@c)
        widths = list(abs(coeff)*h) + [0., 0.]
        if max(widths) == 0:
            return float(center < 0 if strict else center <= 0)
        return uniform_cdf(-center, widths[0], widths[1])
    return min(1., max(0., cdf(lo, strict=True)+1-cdf(hi)))


def wilson(k, n):
    z = 1.959963984540054
    p = k/n
    mid = (p+z*z/(2*n))/(1+z*z/n)
    half = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return max(0., mid-half), min(1., mid+half)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT.parent/"t1_rounding/results/per_question.jsonl")
    parser.add_argument("--output-dir", type=Path, default=ROOT/"results")
    parser.add_argument("--samples", type=int, default=262144)
    args = parser.parse_args()
    rows = load(args.input)
    analyzed = [r for r in rows if r["status"] == "analyzed"]
    output = []
    for i, row in enumerate(analyzed):
        gold = float(row["exe_ans"])
        model = affine_fraction(row)
        record = {"id": row["id"], "split": row["split"], "category": row["category"]}
        probs = []
        if model is not None:
            method = "closed_form_affine_fraction"
            for tau in TAUS:
                p = exact_probability(model, gold-tau*abs(gold), gold+tau*abs(gold))
                probs.append((p, p, p, 0))
        else:
            # Independent pseudorandom streams across questions: no shared MC error.
            seed = int.from_bytes(hashlib.sha256(("t1a-uniform-v1:"+row["split"]+":"+row["id"]).encode()).digest()[:8], "big")
            rng = np.random.default_rng(seed)
            names, centers, half = geometry(row)
            draws = centers[:, None]+half[:, None]*rng.uniform(-1, 1, (len(names), args.samples))
            with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
                ans = np.asarray(execute(row, dict(zip(names, draws))))
            if ans.ndim == 0: ans = np.full(args.samples, ans)
            if not np.all(np.isfinite(ans)): raise ValueError("undefined draws: "+row["id"])
            method = "independent_uniform_monte_carlo"
            for tau in TAUS:
                k = int(np.sum(abs(ans-gold) > tau*abs(gold)))
                lower, upper = wilson(k, args.samples)
                probs.append((k/args.samples, lower, upper, k))
        record["method"] = method
        record["n_mc"] = args.samples if model is None else 0
        for tau, (p, lower, upper, k) in zip(TAUS, probs):
            suffix = str(tau)
            record["p_"+suffix] = p
            record["mc_lower_"+suffix] = lower
            record["mc_upper_"+suffix] = upper
            if model is None: record["mc_hits_"+suffix] = k
        assert all(probs[j][0] >= probs[j+1][0]-1e-12 for j in range(len(TAUS)-1))
        # T1 certified inclusion at 1% implies zero model probability.
        if row["relative_1pct"]["status"] == "certified_inside":
            assert probs[2][0] < 1e-9, (row["id"], probs[2][0])
        output.append(record)
        if (i+1) % 1000 == 0: print(f"probability {i+1}/{len(analyzed)}", flush=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir/"probabilities.jsonl").write_text("".join(json.dumps(r)+"\n" for r in output), encoding="utf-8")
    summary = {"assumption": "Independent continuous uniform input rounding errors, shared draws for repeated references; no claim this distribution describes actual hidden financial values.",
               "methods": dict(Counter(r["method"] for r in output)), "mc_samples_per_question": args.samples,
               "mc_interval_note": "Per-question Wilson 95% intervals measure numerical sampling error only. Aggregate MC SE assumes independent question streams. Excluded rows have unknown probabilities; all-row lower/upper rates assign those probabilities 0/1.",
               "groups": {}}
    groups = {"all": output, **{s:[r for r in output if r["split"] == s] for s in ("train", "dev", "test")},
              **{"category_"+c:[r for r in output if r["category"] == c] for c in sorted(set(r["category"] for r in output))}}
    for name, rr in groups.items():
        total = len(rows) if name == "all" else sum(r["split"] == name for r in rows) if name in ("train", "dev", "test") else len(rr)
        item = {"analyzed": len(rr), "all_rows": total, "by_tolerance": {}}
        for tau in TAUS:
            pp = np.array([r["p_"+str(tau)] for r in rr])
            var = sum(max(r["p_"+str(tau)]*(1-r["p_"+str(tau)]), .25/args.samples)/args.samples for r in rr if r["n_mc"])
            item["by_tolerance"][str(tau)] = {"expected_count": float(pp.sum()), "analyzed_rate": float(pp.mean()),
                "all_rows_rate_lower": float(pp.sum()/total), "all_rows_rate_upper": float((pp.sum()+total-len(rr))/total),
                "aggregate_mc_se_rate": math.sqrt(var)/len(rr)}
        summary["groups"][name] = item
    (args.output_dir/"probability_summary.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"methods":summary["methods"],"test_1pct":summary["groups"]["test"]["by_tolerance"]["0.01"]}, indent=2))


if __name__ == "__main__":
    main()
