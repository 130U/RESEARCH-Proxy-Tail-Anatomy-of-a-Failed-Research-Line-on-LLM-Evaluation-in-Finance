"""FinQA rounding-box audit. No model calls; exact decimal/rational arithmetic."""
from __future__ import annotations

import argparse
import csv
import html
import itertools
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal
from fractions import Fraction as F
from pathlib import Path

from interval_core import Interval, eval_scalar, classify

ROOT = Path(__file__).resolve().parent
NUM = re.compile(r"(?<![\w.])[-+]?\s*(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)(?:\s*%)?(?![\w.])")
PROGRAM = re.compile(r"(\w+)\(([^,]+),\s*([^)]*)\)")


def clean(s):
    s = re.sub(r"<sup>.*?</sup>", "", str(s), flags=re.I)
    return html.unescape(re.sub(r"<[^>]*>", "", s)).replace("−", "-").replace("\u00a0", " ")


def number(s):
    s = str(s).strip().replace(",", "").replace(" ", "")
    pct = s.endswith("%")
    if pct:
        s = s[:-1]
    value = F(Decimal(s))
    places = max(0, -Decimal(s).as_tuple().exponent)
    half = F(1, 2 * 10**places)
    digits = len(s.lstrip("+-").replace(".", "").lstrip("0")) or 1
    return value, half, digits, pct


def tokens(s, loc, context, table=False):
    text = clean(s)
    hits = list(NUM.finditer(text))
    if table and len(hits) != 1:
        return []
    out = []
    previous_end = None
    for h in hits:
        raw = h.group().strip()
        try:
            val, half, sig, pct = number(raw)
        except Exception:
            continue
        before = text[:h.start()].rstrip()
        after = text[h.end():].lstrip()
        if before.endswith("(") and after.startswith(")"):
            if (out and previous_end is not None and abs(out[-1]["value"]) == abs(val)
                    and re.fullmatch(r"[\s()%]*", text[previous_end:h.start()])):
                # FinQA text normalization often appends '(60 %)' after '60%'.
                # This is not a second negative fact.
                previous_end = h.end()
                continue
            val = -abs(val)
        # Years are metadata; retaining these as uncertain operands invents noise.
        if not pct and 1900 <= val <= 2100 and half == F(1, 2):
            if not table or re.search(r"year|date|period", context, re.I):
                continue
        out.append(dict(value=val, half=half, sig=sig, percent=pct,
                        raw=raw, loc=loc + ("" if table else f":{h.start()}"),
                        context=context, text=text))
        previous_end = h.end()
    return out


def source_numbers(record):
    qa = record["qa"]
    gold = qa.get("gold_inds", {})
    table = record.get("table_ori", record["table"])
    normlabel = lambda s: re.sub(r"[^a-z0-9]", "", clean(s).lower())
    selected_labels = {normlabel(record["table"][int(k.split("_")[1])][0])
                       for k in gold if k.startswith("table_")
                       and int(k.split("_")[1]) < len(record["table"])}
    selected = []
    full = []
    for i, row in enumerate(table):
        if i == 0:
            continue
        for j, cell in enumerate(row):
            if j == 0:
                continue
            label = clean(row[0]) + " | " + clean(table[0][j] if j < len(table[0]) else "")
            ts = tokens(cell, f"table_{i}:{j}", label, table=True)
            full.extend(ts)
            if normlabel(row[0]) in selected_labels:
                selected.extend(ts)
    for key, text in gold.items():
        if key.startswith("text_"):
            selected.extend(tokens(text, key, text))
    for i, text in enumerate(record.get("pre_text", []) + record.get("post_text", [])):
        full.extend(tokens(text, f"text_{i}", text))
    return selected, full


def match(token, candidates):
    val = F(Decimal(token.replace(",", "")))
    exact = [(c, F(1)) for c in candidates if c["value"] == val]
    if exact:
        return exact
    return [(c, F(1, 100)) for c in candidates if c["percent"] and c["value"] / 100 == val]


def bind(record):
    qa = record["qa"]
    steps = [(op, a.strip(), b.strip()) for op, a, b in PROGRAM.findall(qa["program"])]
    if not steps:
        raise ValueError("invalid_program")
    if any(op not in {"add", "subtract", "multiply", "divide", "exp"} for op, _, _ in steps):
        raise ValueError("unsupported_operation")
    if any(a == b and not a.startswith(("#", "const_")) for _, a, b in steps):
        # A single phrase '2.6 billion in both years' names two different facts.
        # One lexical span does not justify collapsing their economic roles.
        raise ValueError("same_literal_distinct_roles_possible")
    selected, full = source_numbers(record)
    inputs, provenance, mapping = {}, {}, {}
    warnings = []
    for op, a, b in steps:
        for arg in (a, b):
            if arg.startswith("#") or arg in mapping:
                continue
            if arg.startswith("const_"):
                # FinQA constants can also encode source facts. Ambiguous roles
                # are excluded rather than silently assigned a rounding width.
                val = arg[6:].replace("m", "-").replace("_", ".")
                try:
                    possible = match(val, selected)
                except Exception:
                    raise ValueError("invalid_constant")
                if possible:
                    raise ValueError("constant_source_role_ambiguous")
                mapping[arg] = arg
                continue
            try:
                candidates = match(arg, selected)
                fallback = False
                if not candidates:
                    candidates = match(arg, full)
                    fallback = True
            except Exception:
                raise ValueError("invalid_operand")
            if not candidates:
                raise ValueError("source_not_found")
            # Collapse identical repeated lexical evidence but never different
            # precisions. The measured model ties equal program literals.
            precision = {(c["value"] * scale, c["half"] * scale) for c, scale in candidates}
            if len(precision) != 1:
                raise ValueError("source_precision_ambiguous")
            if len(candidates) != 1:
                raise ValueError("source_identity_ambiguous")
            c, scale = candidates[0]
            value, half = c["value"] * scale, c["half"] * scale
            # Exact integer counts are a semantic issue. Flag and exclude
            # obvious unscaled counts; million/thousand-scaled counts can round.
            ctx = c["context"].lower()
            count_context = ctx + " " + qa["question"].lower()
            if (half == F(1, 2) and re.search(r"employees|\bnumber\b|shares|members|stores|facilities|months|days|years|call cent(?:er|re)s", count_context)
                    and not re.search(r"million|billion|thousand|000", count_context)):
                raise ValueError("possibly_exact_count")
            if re.search(r"dividend.*per.*share|per.*share.*dividend|exercise price|contractual|useful life", ctx):
                raise ValueError("possibly_exact_or_semantic_quantity")
            doc = " ".join(record.get("pre_text", []) + record.get("post_text", []))
            if value == 100 and re.search(r"assum.{0,150}100|100.{0,100}invest|base.{0,40}100", doc, re.I):
                raise ValueError("defined_index_base")
            name = f"x{len(inputs)}"
            inputs[name] = Interval(value - half, value + half)
            mapping[arg] = name
            provenance[name] = dict(program_token=arg, value=str(value), half=str(half),
                                    sig=c["sig"], raw=c["raw"], location=c["loc"],
                                    context=c["context"], fallback=fallback,
                                    candidate_count=len(candidates),
                                    candidates=[dict(location=z["loc"],raw=z["raw"],context=z["context"]) for z, _ in candidates])
            if len(candidates) > 1:
                warnings.append("equal_literal_multiple_occurrences")
    mapped = [(op, mapping.get(a, a), mapping.get(b, b)) for op, a, b in steps]
    if not inputs:
        raise ValueError("no_uncertain_inputs")
    return mapped, inputs, provenance, sorted(set(warnings))


def category(steps):
    for i, (op, a, b) in enumerate(steps):
        if op == "divide" and a.startswith("#"):
            j = int(a[1:])
            if j < i and steps[j][0] == "subtract" and b in steps[j][1:]:
                return "growth"
        if op == "subtract" and a.startswith("#") and b in {"const_1", "1"}:
            j = int(a[1:])
            if j < i and steps[j][0] == "divide":
                return "growth"
    ops = [s[0] for s in steps]
    if "divide" in ops:
        return "ratio"
    if "subtract" in ops:
        return "difference"
    if all(o == "add" for o in ops):
        return "sum"
    return "other"


def display_acceptance(answer, center):
    text = clean(answer).strip()
    hits = tokens(text, "answer", "answer", table=True)
    if len(hits) != 1:
        return None
    h = hits[0]
    # Match only canonical percent scaling, retaining the literal answer ULP.
    factors = [F(1), F(1, 100)] if h["percent"] else [F(1)]
    plausible = []
    for factor in factors:
        v, half = h["value"] * factor, h["half"] * factor
        if abs(center - v) <= half:
            plausible.append((v, half, factor))
    if len(plausible) != 1:
        return None
    v, half, factor = plausible[0]
    return Interval(v - half, v + half), factor


def rounding_cell_classify(steps, inputs, acceptance):
    result = classify(steps, inputs, acceptance)
    # An enclosing closed cell supplies only STRICT-outside witnesses. If
    # containment touches a tie boundary, defer rather than assume a tie rule.
    enclosure = result["enclosure"]
    if result["status"] == "certified_inside" and enclosure is not None:
        if enclosure.lo == acceptance.lo or enclosure.hi == acceptance.hi:
            result["status"] = "unresolved"
            result["boundary_tie"] = True
    return result


def serialize(value):
    if isinstance(value, F):
        return {"exact":str(value), "decimal":float(value)}
    if isinstance(value, Interval):
        return {"lo":serialize(value.lo), "hi":serialize(value.hi)}
    if isinstance(value, dict):
        return {str(k):serialize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize(v) for v in value]
    return value


def analyze_one(r, split):
    qa = r["qa"]
    row = dict(id=r["id"], split=split, program=qa["program"], answer=qa.get("answer"),
               exe_ans=qa.get("exe_ans"), question=qa["question"], status="excluded")
    if isinstance(qa.get("exe_ans"), str):
        row["reason"] = "non_numeric_answer"
        return row
    try:
        steps, inputs, provenance, warnings = bind(r)
        row.update(category=category(steps), input_provenance=provenance, warnings=warnings,
                   min_sig=min(x["sig"] for x in provenance.values()), steps=steps)
        center = eval_scalar(steps, {k:(v.lo + v.hi)/2 for k,v in inputs.items()})
        target = F(str(qa["exe_ans"]))
        row["center"] = center
        # Official gold executable labels are stored to five decimal places.
        if abs(center-target) > F(1, 200000):
            row["reason"] = "program_center_mismatch"
            return row
        band = Interval(target-abs(target)/100, target+abs(target)/100)
        if not band.lo <= center <= band.hi:
            row["reason"] = "center_outside_relative_acceptance"
            return row
        row.update(status="analyzed", reason=None, input_intervals=inputs)
        row["relative_1pct"] = classify(steps, inputs, band)
        display = display_acceptance(qa.get("answer", ""), center)
        row["display"] = rounding_cell_classify(steps, inputs, display[0]) if display else None
        row["display_unavailable_reason"] = None if display else "unparsed_or_center_gold_incompatible"
        row["display_factor"] = display[1] if display else None
        row["official_decimal_cell"] = rounding_cell_classify(steps, inputs, Interval(target-F(1,200000),target+F(1,200000)))
        row["precision_counterfactual"] = {}
        for factor in [10, 100, 1000]:
            narrower = {k:Interval((v.lo+v.hi)/2-(v.hi-v.lo)/(2*factor),
                                  (v.lo+v.hi)/2+(v.hi-v.lo)/(2*factor)) for k,v in inputs.items()}
            row["precision_counterfactual"][str(factor)] = classify(steps,narrower,band)
    except (ValueError, ZeroDivisionError, ArithmeticError, KeyError, TypeError) as e:
        row["reason"] = str(e)
    return row


def summarize(rows):
    out = {}
    groupings = {"all":rows}
    for split in sorted({r["split"] for r in rows}):
        groupings[split] = [r for r in rows if r["split"] == split]
    for name, group in groupings.items():
        analyzed = [r for r in group if r["status"] == "analyzed"]
        s = dict(n_all=len(group), n_numeric=sum(not isinstance(r["exe_ans"],str) for r in group),
                 n_analyzed=len(analyzed), exclusions=dict(Counter(r["reason"] for r in group if r["status"] != "analyzed")))
        def counts(xs, key):
            c = Counter(r[key]["status"] if r.get(key) else "unavailable" for r in xs)
            return dict(n=len(xs), **dict(c))
        for key in ["relative_1pct","display","official_decimal_cell"]:
            s[key]=counts(analyzed,key)
        s["by_operation"]={c:counts([r for r in analyzed if r["category"]==c],"relative_1pct") for c in sorted({r["category"] for r in analyzed})}
        s["by_min_sig"]={str(c):counts([r for r in analyzed if min(5,r["min_sig"])==c],"relative_1pct") for c in range(1,6)}
        s["precision_counterfactual"]={str(f):dict(Counter(r["precision_counterfactual"][str(f)]["status"] for r in analyzed)) for f in [10,100,1000]}
        s["multiple_occurrence_analyzed"]=sum(bool(r["warnings"]) for r in analyzed)
        out[name]=s
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--splits", nargs="+", default=["test","dev","train"])
    p.add_argument("--limit", type=int)
    args=p.parse_args()
    rows=[]
    for split in args.splits:
        data=json.loads((ROOT/"data"/"finqa"/f"{split}.json").read_text(encoding="utf-8"))
        for i,r in enumerate(data[:args.limit]):
            rows.append(analyze_one(r,split))
            if (i+1)%500==0:
                print(split,i+1,flush=True)
    (ROOT/"results").mkdir(exist_ok=True)
    suffix="_pilot" if args.limit else ""
    with (ROOT/"results"/f"per_question{suffix}.jsonl").open("w",encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(serialize(row),ensure_ascii=False)+"\n")
    summary=summarize(rows)
    (ROOT/"results"/f"summary{suffix}.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
