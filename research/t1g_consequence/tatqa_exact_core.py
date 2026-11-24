"""Independent rational arithmetic for the frozen T1 per-question records.

No T1 source module is imported. Input identity is the T1 variable name, so
repeated occurrences share a single perturbation.
"""
from __future__ import annotations

from fractions import Fraction as F
from itertools import product
from functools import lru_cache
import json
import sympy as sp


def read_rows(path):
    with open(path, encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def exact(value):
    return F(value["exact"]) if isinstance(value, dict) else F(str(value))


def centers_half(row):
    centers, half = {}, {}
    for key, interval in row["input_intervals"].items():
        lo, hi = exact(interval["lo"]), exact(interval["hi"])
        centers[key], half[key] = (lo + hi) / 2, (hi - lo) / 2
    return centers, half


def constant(token):
    if token == "const_m1": return F(-1)
    return F(token[6:] if token.startswith("const_") else token)


def evaluate(row, values):
    outputs = []
    def operand(token):
        if token in values:
            return values[token]
        if token.startswith("#"):
            return outputs[int(token[1:])]
        # A float or ndarray evaluator must not receive Fraction objects.
        value = constant(token)
        return value if all(isinstance(v, F) for v in values.values()) else float(value)
    for op, left, right in row["steps"]:
        a, b = operand(left), operand(right)
        outputs.append({"add": lambda: a + b, "subtract": lambda: a - b,
                        "multiply": lambda: a * b, "divide": lambda: a / b}[op]())
    return outputs[-1]


def gradient_radius(row):
    centers, half = centers_half(row)
    names = list(centers)
    outputs = []
    def operand(token):
        if token in centers:
            return centers[token], {name: F(name == token) for name in names}
        if token.startswith("#"):
            return outputs[int(token[1:])]
        return constant(token), {name: F(0) for name in names}
    for op, left, right in row["steps"]:
        a, da = operand(left)
        b, db = operand(right)
        if op == "add":
            y, dy = a+b, {k: da[k]+db[k] for k in names}
        elif op == "subtract":
            y, dy = a-b, {k: da[k]-db[k] for k in names}
        elif op == "multiply":
            y, dy = a*b, {k: b*da[k]+a*db[k] for k in names}
        else:
            y, dy = a/b, {k: (b*da[k]-a*db[k])/(b*b) for k in names}
        outputs.append((y, dy))
    center, grad = outputs[-1]
    return center, sum(abs(grad[k])*half[k] for k in names), grad


def iadd(a,b): return a[0]+b[0], a[1]+b[1]
def ineg(a): return -a[1], -a[0]
def isub(a,b): return iadd(a, ineg(b))
def imul(a,b):
    values = [x*y for x in a for y in b]
    return min(values), max(values)
def idiv(a,b):
    if b[0] <= 0 <= b[1]:
        raise ZeroDivisionError("Interval denominator contains zero")
    return imul(a, (min(1/b[0],1/b[1]), max(1/b[0],1/b[1])))


def interval_ad(row):
    centers, half = centers_half(row)
    names = list(centers)
    outputs=[]
    def operand(token):
        if token in centers:
            return (centers[token]-half[token],centers[token]+half[token]), {
                k:(F(k==token),F(k==token)) for k in names}
        if token.startswith("#"):
            return outputs[int(token[1:])]
        c=constant(token)
        return (c,c), {k:(F(0),F(0)) for k in names}
    for op,l,r in row["steps"]:
        a,da=operand(l); b,db=operand(r)
        if op in ("add","subtract"):
            fn=iadd if op=="add" else isub
            y,dy=fn(a,b),{k:fn(da[k],db[k]) for k in names}
        elif op=="multiply":
            y,dy=imul(a,b),{k:iadd(imul(b,da[k]),imul(a,db[k])) for k in names}
        else:
            y=idiv(a,b)
            b2=(min(b[0]*b[0],b[1]*b[1]),max(b[0]*b[0],b[1]*b[1]))
            dy={k:idiv(isub(imul(b,da[k]),imul(a,db[k])),b2) for k in names}
        outputs.append((y,dy))
    return outputs[-1]


@lru_cache(maxsize=None)
def symbolic(steps_tuple, names_tuple):
    symbols={name:sp.Symbol(name) for name in names_tuple}
    outputs=[]; denominators=[]
    def operand(token):
        if token in symbols: return symbols[token]
        if token.startswith("#"): return outputs[int(token[1:])]
        c=constant(token); return sp.Rational(c.numerator,c.denominator)
    for op,l,r in steps_tuple:
        a,b=operand(l),operand(r)
        if op=="divide": denominators.append(sp.cancel(b))
        outputs.append(sp.cancel({"add":lambda:a+b,"subtract":lambda:a-b,
                                  "multiply":lambda:a*b,"divide":lambda:a/b}[op]()))
    return outputs[-1],denominators,symbols


def _poly_multiaffine(expr, symbols):
    poly=sp.Poly(expr,*symbols.values())
    return all(max(monomial,default=0)<=1 for monomial in poly.monoms())


def range_certificate(row):
    """Exact extrema when certified, otherwise sound enclosure and witnesses."""
    centers,half=centers_half(row); names=list(centers)
    corners=[]; interior=[]
    for signs in product((-1,1),repeat=len(names)):
        values={k:centers[k]+s*half[k] for k,s in zip(names,signs)}
        try: corners.append(evaluate(row,values))
        except ZeroDivisionError: pass
        values={k:centers[k]+s*half[k]*F(999,1000) for k,s in zip(names,signs)}
        try: interior.append(evaluate(row,values))
        except ZeroDivisionError: pass
    natural=None; gradients=None
    try: natural,gradients=interval_ad(row)
    except ZeroDivisionError: pass
    if natural is not None and all(lo>=0 or hi<=0 for lo,hi in gradients.values()):
        return {"exact":True,"method":"monotone_interval_derivatives", "lo":min(corners),"hi":max(corners),"witness_lo":min(interior),"witness_hi":max(interior)}
    expr,denominators,symbols=symbolic(tuple(map(tuple,row["steps"])),tuple(names))
    num,den=sp.fraction(expr)
    # Natural interval denominators safe => the original DAG is defined everywhere.
    if natural is not None and _poly_multiaffine(num,symbols) and _poly_multiaffine(den,symbols):
        return {"exact":True,"method":"coordinatewise_linear_fractional", "lo":min(corners),"hi":max(corners),"witness_lo":min(interior),"witness_hi":max(interior)}
    return {"exact":False,"method":"interval_and_interior_witnesses", "lo":None if natural is None else natural[0],"hi":None if natural is None else natural[1],"witness_lo":min(interior) if interior else None,"witness_hi":max(interior) if interior else None}


def classify_range(cert,gold,tau):
    lo,hi=gold-abs(gold)*tau,gold+abs(gold)*tau
    if cert["exact"]:
        return "outside" if cert["lo"]<lo or cert["hi"]>hi else "inside"
    if cert["lo"] is not None and lo<=cert["lo"]<=cert["hi"]<=hi:
        return "inside"
    if cert["witness_lo"] is not None and (cert["witness_lo"]<lo or cert["witness_hi"]>hi):
        return "outside"
    return "unresolved"


def growth_descriptor(row):
    """Canonical f = scale * (b/a - 1); source centers may be rescaled.

    scale can be negative for (a-b)/a. Requires two distinct sources, a single
    denominator source, and no extra additive offset. Algebraic identity is
    checked, not inferred from category alone.
    """
    if row["category"]!="growth" or len(row["input_intervals"])!=2:
        return None
    centers,half=centers_half(row); names=list(centers)
    expr,_,symbols=symbolic(tuple(map(tuple,row["steps"])),tuple(names))
    for a_name in names:
        b_name=next(n for n in names if n!=a_name)
        a_sym,b_sym=symbols[a_name],symbols[b_name]
        # If f = A*b/a + B, identify B=-scale and b rescaling A/scale.
        slope=sp.cancel(sp.diff(expr,b_sym)*a_sym)
        offset=sp.cancel(expr-slope*b_sym/a_sym)
        if slope.free_symbols or offset.free_symbols or not slope or not offset:
            continue
        scale=-F(str(offset)); unit_ratio=F(str(slope))/scale
        # A stored extra offset of 100 is not an output percentage scaling.
        if abs(scale) not in (F(1),F(100)): continue
        if unit_ratio<=0: continue
        a,b=centers[a_name],unit_ratio*centers[b_name]
        ha,hb=half[a_name],unit_ratio*half[b_name]
        if abs(a)<=ha: continue
        delta=abs(b-a)/(ha+hb)
        return {"a_name":a_name,"b_name":b_name,"a":a,"b":b,"ha":ha,"hb":hb,
                "scale":scale,"unit_ratio":unit_ratio,"delta":delta,"g":b/a-1,
                "same_sign":a*b>0,"equal_units":ha==hb,
                "k_a":row["input_provenance"][a_name]["sig"],
                "k_b":row["input_provenance"][b_name]["sig"]}
    return None


def jsonable(value):
    if isinstance(value,F): return {"exact":str(value),"decimal":float(value)}
    if isinstance(value,dict): return {str(k):jsonable(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [jsonable(v) for v in value]
    return value
