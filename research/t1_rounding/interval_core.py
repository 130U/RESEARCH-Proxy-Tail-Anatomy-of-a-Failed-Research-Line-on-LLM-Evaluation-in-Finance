"""Exact rational interval bounds and consistent-input counterexamples.

An interval extending outside an acceptance set is NOT a counterexample.
``classify`` therefore separates certified containment, witnessed failure,
and unresolved cases. Witnesses use one value per variable throughout the DAG.
No claim is made that a rounding box captures every constraint in a document.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from typing import Mapping, Sequence


class IntervalDomainError(ValueError):
    """An interval operation cannot certify a finite defined output."""


class UnsupportedOperation(ValueError):
    """The operation is outside the exact rational arithmetic subset."""


Number = Fraction | int | str
Step = tuple[str, str | Fraction | int, str | Fraction | int]


def as_fraction(value: Number) -> Fraction:
    """Require an exact source; silently accepting binary floats is unsafe."""
    if isinstance(value, Fraction):
        return value
    if isinstance(value, (int, str)) and not isinstance(value, bool):
        return Fraction(value)
    raise TypeError(f"Expected Fraction, integer, or numeric string, got {type(value).__name__}")


@dataclass(frozen=True)
class Interval:
    lo: Fraction
    hi: Fraction

    def __post_init__(self) -> None:
        object.__setattr__(self, "lo", as_fraction(self.lo))
        object.__setattr__(self, "hi", as_fraction(self.hi))
        if self.lo > self.hi:
            raise ValueError("Interval lower bound exceeds upper bound")

    @classmethod
    def point(cls, value: Number) -> "Interval":
        number = as_fraction(value)
        return cls(number, number)

    @property
    def midpoint(self) -> Fraction:
        return (self.lo + self.hi) / 2

    @property
    def halfwidth(self) -> Fraction:
        return (self.hi - self.lo) / 2

    def __add__(self, other: "Interval | Number") -> "Interval":
        right = as_interval(other)
        return Interval(self.lo + right.lo, self.hi + right.hi)

    __radd__ = __add__

    def __neg__(self) -> "Interval":
        return Interval(-self.hi, -self.lo)

    def __sub__(self, other: "Interval | Number") -> "Interval":
        return self + (-as_interval(other))

    def __rsub__(self, other: "Interval | Number") -> "Interval":
        return as_interval(other) - self

    def __mul__(self, other: "Interval | Number") -> "Interval":
        right = as_interval(other)
        endpoints = [self.lo * right.lo, self.lo * right.hi,
                     self.hi * right.lo, self.hi * right.hi]
        return Interval(min(endpoints), max(endpoints))

    __rmul__ = __mul__

    def reciprocal(self) -> "Interval":
        if self.lo <= 0 <= self.hi:
            raise IntervalDomainError("Divisor interval contains zero")
        return Interval(1 / self.hi, 1 / self.lo)

    def __truediv__(self, other: "Interval | Number") -> "Interval":
        return self * as_interval(other).reciprocal()

    def __rtruediv__(self, other: "Interval | Number") -> "Interval":
        return as_interval(other) / self

    def integer_power(self, exponent: int) -> "Interval":
        if exponent == 0:
            return Interval.point(1)
        if exponent < 0:
            return self.integer_power(-exponent).reciprocal()
        left, right = self.lo ** exponent, self.hi ** exponent
        low = 0 if exponent % 2 == 0 and self.lo <= 0 <= self.hi else min(left, right)
        return Interval(low, max(left, right))


def as_interval(value: Interval | Number) -> Interval:
    return value if isinstance(value, Interval) else Interval.point(value)


def _constant(token: str | Fraction | int) -> Fraction:
    if isinstance(token, str) and token.startswith("const_"):
        suffix = token[6:]
        return Fraction(-1) if suffix == "m1" else as_fraction(suffix)
    return as_fraction(token)


def _run(steps: Sequence[Step], inputs: Mapping, interval: bool):
    if not steps:
        raise ValueError("At least one operation is required")
    results = []

    def resolve(argument):
        if isinstance(argument, str) and argument.startswith("#"):
            index = int(argument[1:])
            if index < 0 or index >= len(results):
                raise ValueError(f"Invalid or forward reference: {argument}")
            return results[index]
        if isinstance(argument, str) and argument in inputs:
            value = inputs[argument]
            return as_interval(value) if interval else as_fraction(value)
        number = _constant(argument)
        return Interval.point(number) if interval else number

    for operation, arg1, arg2 in steps:
        left, right = resolve(arg1), resolve(arg2)
        if operation in ("add", "+"):
            value = left + right
        elif operation in ("subtract", "-"):
            value = left - right
        elif operation in ("multiply", "*"):
            value = left * right
        elif operation in ("divide", "/"):
            value = left / right
        elif operation in ("exp", "**"):
            if interval:
                if right.lo != right.hi:
                    raise UnsupportedOperation("Uncertain exponent is unsupported")
                exponent = right.lo
            else:
                exponent = right
            if exponent.denominator != 1:
                raise UnsupportedOperation("Only integer powers are exact in this engine")
            value = left.integer_power(int(exponent)) if interval else left ** int(exponent)
        else:
            raise UnsupportedOperation(f"Unsupported operation: {operation}")
        results.append(value)
    return results[-1]


def eval_scalar(steps: Sequence[Step], inputs: Mapping[str, Number]) -> Fraction:
    """Evaluate a numeric arithmetic DAG without rounding intermediate results."""
    return _run(steps, inputs, interval=False)


def eval_interval(steps: Sequence[Step], inputs: Mapping[str, Interval | Number]) -> Interval:
    """Return an exact rational OUTER enclosure, preserving no correlations."""
    return _run(steps, inputs, interval=True)


def evaluate(steps: Sequence[Step], inputs: Mapping):
    """Dispatch to interval arithmetic when any supplied input is an Interval."""
    return _run(steps, inputs, interval=any(isinstance(x, Interval) for x in inputs.values()))


def classify(
    steps: Sequence[Step],
    input_intervals: Mapping[str, Interval | Number],
    acceptance: Interval,
    *,
    max_corner_vars: int = 12,
    interior_factor: Fraction = Fraction(999, 1000),
    lower_closed: bool = True,
    upper_closed: bool = True,
) -> dict:
    """Certify containment or return an exact, consistent outside witness.

    ``acceptance`` is a single real interval. Open endpoints are supported.
    A box midpoint outside acceptance is reported as ``witnessed_outside``;
    callers must separate baseline/gold mismatch from perturbation sensitivity.

    For at most ``max_corner_vars`` uncertain used variables, search all
    shrunken-box corners. With more variables search the two diagonal corners
    and each one-variable perturbation. Failure to find a witness never proves
    containment. ``corner_search_complete`` means the finite search was complete,
    NOT that the function range has been characterized.

    Fractions and Interval instances are retained in the returned dictionary so
    callers can serialize without first losing exactness to binary floats.
    """
    interior_factor = as_fraction(interior_factor)
    if not 0 < interior_factor < 1:
        raise ValueError("interior_factor must lie strictly between zero and one")
    if max_corner_vars < 0:
        raise ValueError("max_corner_vars must be nonnegative")
    box = {name: as_interval(value) for name, value in input_intervals.items()}
    used = {arg for _, first, second in steps for arg in (first, second)
            if isinstance(arg, str) and arg in box}
    variable_names = sorted(name for name in used if box[name].lo != box[name].hi)
    centers = {name: value.midpoint for name, value in box.items()}

    def accepted(value: Fraction) -> bool:
        return ((value >= acceptance.lo if lower_closed else value > acceptance.lo)
                and (value <= acceptance.hi if upper_closed else value < acceptance.hi))

    def contains_enclosure(value: Interval) -> bool:
        return ((value.lo >= acceptance.lo if lower_closed else value.lo > acceptance.lo)
                and (value.hi <= acceptance.hi if upper_closed else value.hi < acceptance.hi))

    result = {
        "status": "unresolved", "enclosure": None, "interval_error": None,
        "center_value": None, "center_inside": None, "center_error": None,
        "witness": None, "witness_value": None, "witness_kind": None,
        "evaluated_witnesses": 0, "invalid_witnesses": 0,
        "corner_search_complete": False, "variable_count": len(variable_names),
    }
    caught = (ValueError, TypeError, ZeroDivisionError, OverflowError)
    try:
        value = eval_scalar(steps, centers)
        result["center_value"] = value
        result["center_inside"] = accepted(value)
    except caught as error:
        result["center_error"] = f"{type(error).__name__}: {error}"
    try:
        result["enclosure"] = eval_interval(steps, box)
    except caught as error:
        result["interval_error"] = f"{type(error).__name__}: {error}"

    if result["enclosure"] is not None and contains_enclosure(result["enclosure"]):
        result["status"] = "certified_inside"
        return result
    if result["center_inside"] is False:
        result.update(status="witnessed_outside", witness=centers,
                      witness_value=result["center_value"], witness_kind="center")
        return result

    def check(signs, kind):
        candidate = dict(centers)
        for name, sign in zip(variable_names, signs):
            candidate[name] += sign * interior_factor * box[name].halfwidth
        try:
            value = eval_scalar(steps, candidate)
        except caught:
            result["invalid_witnesses"] += 1
            return False
        result["evaluated_witnesses"] += 1
        if not accepted(value):
            result.update(status="witnessed_outside", witness=candidate,
                          witness_value=value, witness_kind=kind)
            return True
        return False

    count = len(variable_names)
    if count <= max_corner_vars:
        for signs in product((-1, 1), repeat=count):
            if check(signs, "interior_corner"):
                return result
        result["corner_search_complete"] = True
    else:
        for signs in [(-1,) * count, (1,) * count]:
            if check(signs, "interior_diagonal"):
                return result
        for index in range(count):
            for sign in (-1, 1):
                signs = [0] * count
                signs[index] = sign
                if check(signs, "single_variable"):
                    return result
    return result
