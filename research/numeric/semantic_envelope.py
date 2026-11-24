"""Finite semantic probability envelopes with certified rational arithmetic.

No parser, model training, empirical calibration, or branch probabilities are
implemented. Validity is conditional on the supplied branch set/model/domain.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
from functools import lru_cache


class BudgetExceeded(ValueError):
    """No certified result is returned when the numerical budget is exhausted."""


def rational(value, name: str = "value") -> Fraction:
    if type(value) not in {int, Fraction}:
        raise TypeError(name + " must be an exact int or Fraction; floats/bools are rejected")
    return Fraction(value)


@dataclass(frozen=True)
class Interval:
    lower: Fraction
    upper: Fraction

    def __post_init__(self):
        object.__setattr__(self, "lower", rational(self.lower, "lower"))
        object.__setattr__(self, "upper", rational(self.upper, "upper"))
        if self.lower > self.upper:
            raise ValueError("Interval lower must not exceed upper")

    @property
    def width(self) -> Fraction:
        return self.upper - self.lower

    def to_json(self) -> dict:
        return {"lower": str(self.lower), "upper": str(self.upper)}


def _interval(value) -> None:
    if type(value) is not Interval:
        raise TypeError("Expected an exact Interval")


@dataclass(frozen=True)
class Budget:
    tolerance: Fraction = Fraction(1, 10**12)
    max_terms: int = 1000
    max_abs_argument: Fraction = Fraction(50)

    def __post_init__(self):
        object.__setattr__(self, "tolerance", rational(self.tolerance, "tolerance"))
        object.__setattr__(self, "max_abs_argument", rational(self.max_abs_argument, "max_abs_argument"))
        if self.tolerance <= 0 or self.max_abs_argument < 0:
            raise ValueError("Tolerance must be positive and argument limit nonnegative")
        if type(self.max_terms) is not int or self.max_terms < 1:
            raise ValueError("max_terms must be a positive integer, not bool")


def _budget(value) -> None:
    if type(value) is not Budget:
        raise TypeError("Expected a Budget")


def rescale_interval(interval: Interval, positive_scale: Fraction) -> Interval:
    _interval(interval)
    scale = rational(positive_scale, "positive_scale")
    if scale <= 0:
        raise ValueError("Unit scale must be strictly positive")
    return Interval(interval.lower * scale, interval.upper * scale)


def ratio_interval(x: Interval, baseline: Interval) -> Interval:
    """Exact x/b range on the independent rectangle with strictly positive b.

    If inputs are actually dependent, the rectangle remains an enclosure but
    its extrema need not be attainable under those unrepresented constraints.
    """
    _interval(x)
    _interval(baseline)
    if baseline.lower <= 0:
        raise ValueError("Baseline interval must be strictly positive")
    corners = [a / b for a in (x.lower, x.upper) for b in (baseline.lower, baseline.upper)]
    return Interval(min(corners), max(corners))


def relative_change_interval(x: Interval, baseline: Interval) -> Interval:
    ratio = ratio_interval(x, baseline)
    return Interval(ratio.lower - 1, ratio.upper - 1)


def difference_interval(x: Interval, baseline: Interval) -> Interval:
    _interval(x)
    _interval(baseline)
    return Interval(x.lower - baseline.upper, x.upper - baseline.lower)


@lru_cache(maxsize=4096)
def _positive_exp_bounds(x: Fraction, budget: Budget) -> Interval:
    # S_n <= exp(x) <= S_n + next/(1-x/(n+2)) for x>=0, x<n+2.
    # Every later term ratio is <=x/(n+2), so the geometric tail is valid.
    term = total = Fraction(1)
    for degree in range(budget.max_terms):
        next_term = term * x / (degree + 1)
        if x < degree + 2:
            tail = next_term / (1 - x / (degree + 2))
            if tail <= budget.tolerance:
                return Interval(total, total + tail)
        if degree + 1 < budget.max_terms:
            term = next_term
            total += term
    raise BudgetExceeded("Taylor term budget exhausted; no enclosure returned")


def exp_bounds(x: Fraction, budget: Budget = Budget()) -> Interval:
    x = rational(x, "exponential argument")
    _budget(budget)
    if abs(x) > budget.max_abs_argument:
        raise BudgetExceeded("Exponential argument exceeds the declared budget")
    positive = _positive_exp_bounds(abs(x), budget)
    if x >= 0:
        return positive
    # positive.lower>=1, so reciprocal also has width<=the requested tolerance.
    return Interval(1 / positive.upper, 1 / positive.lower)


def sigmoid_bounds(x: Fraction, budget: Budget = Budget()) -> Interval:
    x = rational(x, "sigmoid argument")
    _budget(budget)
    positive = exp_bounds(abs(x), budget)
    # Use exp(abs(x))>=1. Both maps have derivative magnitude <=1/4;
    # thus width is certainly <=budget.tolerance (in fact <=one quarter).
    if x >= 0:
        return Interval(positive.lower / (1 + positive.lower), positive.upper / (1 + positive.upper))
    return Interval(1 / (1 + positive.upper), 1 / (1 + positive.lower))


@dataclass(frozen=True)
class SemanticBranch:
    semantic_id: str
    g_interval: Interval
    slope: Fraction
    offset: Fraction
    thresholds: tuple[Fraction, ...]
    target_id: str = "declared-example-target"
    class_labels: tuple[str, ...] | None = None

    def __post_init__(self):
        if type(self.semantic_id) is not str or not self.semantic_id.strip():
            raise ValueError("semantic_id must be a nonempty string")
        _interval(self.g_interval)
        object.__setattr__(self, "slope", rational(self.slope, "slope"))
        object.__setattr__(self, "offset", rational(self.offset, "offset"))
        if type(self.thresholds) is not tuple or not self.thresholds:
            raise ValueError("At least one fixed threshold is required (K>=2)")
        thresholds = tuple(rational(value, "threshold") for value in self.thresholds)
        if any(a >= b for a, b in zip(thresholds, thresholds[1:])):
            raise ValueError("Thresholds must be strictly increasing")
        object.__setattr__(self, "thresholds", thresholds)
        if type(self.target_id) is not str or not self.target_id.strip():
            raise ValueError("target_id must be a nonempty declared target")
        labels = tuple(f"class_{i}" for i in range(len(thresholds)+1)) if self.class_labels is None else self.class_labels
        if type(labels) is not tuple or len(labels) != len(thresholds)+1 or any(type(label) is not str or not label.strip() for label in labels) or len(set(labels)) != len(labels):
            raise ValueError("class_labels must be distinct ordered strings matching K")
        object.__setattr__(self, "class_labels", labels)

    @property
    def eta_interval(self) -> Interval:
        endpoints = (self.slope * self.g_interval.lower + self.offset, self.slope * self.g_interval.upper + self.offset)
        return Interval(min(endpoints), max(endpoints))


@dataclass(frozen=True)
class RangeCertificate:
    """Numerical enclosures of the true minimum and maximum, separately."""
    minimum: Interval
    maximum: Interval

    @property
    def interval(self) -> Interval:
        return Interval(self.minimum.lower, self.maximum.upper)

    def to_json(self) -> dict:
        return {"minimum_enclosure": self.minimum.to_json(), "maximum_enclosure": self.maximum.to_json(), "range_enclosure": self.interval.to_json()}


def _subtract_probabilities(left: Interval, right: Interval) -> Interval:
    # Ordered thresholds guarantee this true difference is a probability.
    lower = max(Fraction(0), left.lower - right.upper)
    upper = min(Fraction(1), left.upper - right.lower)
    if lower > upper:
        raise ArithmeticError("Inconsistent certified probability bounds")
    return Interval(lower, upper)


def probabilities_at_eta(eta: Fraction, thresholds: tuple[Fraction, ...], budget: Budget = Budget()) -> tuple[Interval, ...]:
    """Certified point probabilities; these intervals are numerical uncertainty."""
    eta = rational(eta, "eta")
    # Reuse branch validation without assuming any semantic meaning.
    branch = SemanticBranch("point", Interval(0, 0), 0, eta, thresholds)
    _budget(budget)
    local = replace(budget, tolerance=budget.tolerance / 4)
    cumulative = [sigmoid_bounds(threshold - eta, local) for threshold in branch.thresholds]
    result = [cumulative[0]]
    result.extend(_subtract_probabilities(cumulative[i], cumulative[i-1]) for i in range(1, len(cumulative)))
    result.append(sigmoid_bounds(eta - branch.thresholds[-1], local))
    if any(interval.width > budget.tolerance for interval in result):
        raise ArithmeticError("Numerical tolerance contract violated")
    return tuple(result)


def _minimum_enclosure(candidates: list[Interval]) -> Interval:
    return Interval(min(x.lower for x in candidates), min(x.upper for x in candidates))


def _maximum_enclosure(candidates: list[Interval]) -> Interval:
    return Interval(max(x.lower for x in candidates), max(x.upper for x in candidates))


def branch_probability_extrema(branch: SemanticBranch, budget: Budget = Budget()) -> tuple[RangeCertificate, ...]:
    if type(branch) is not SemanticBranch:
        raise TypeError("Expected a SemanticBranch")
    _budget(budget)
    eta = branch.eta_interval
    left = probabilities_at_eta(eta.lower, branch.thresholds, budget)
    right = probabilities_at_eta(eta.upper, branch.thresholds, budget)
    result = []
    for index in range(len(branch.thresholds) + 1):
        endpoint_values = [left[index], right[index]]
        maximum_values = list(endpoint_values)
        if 0 < index < len(branch.thresholds):
            peak = (branch.thresholds[index-1] + branch.thresholds[index]) / 2
            if eta.lower <= peak <= eta.upper:
                maximum_values.append(probabilities_at_eta(peak, branch.thresholds, budget)[index])
        minimum = _minimum_enclosure(endpoint_values)
        maximum = _maximum_enclosure(maximum_values)
        if minimum.width > budget.tolerance or maximum.width > budget.tolerance:
            raise ArithmeticError("Extremum tolerance contract violated")
        result.append(RangeCertificate(minimum, maximum))
    return tuple(result)


def branch_probability_ranges(branch: SemanticBranch, budget: Budget = Budget()) -> tuple[Interval, ...]:
    return tuple(certificate.interval for certificate in branch_probability_extrema(branch, budget))


@dataclass(frozen=True)
class Envelope:
    semantic_ids: tuple[str, ...]
    class_intervals: tuple[Interval, ...]
    extrema: tuple[RangeCertificate, ...]
    branch_intervals: tuple[tuple[Interval, ...], ...]
    tolerance: Fraction
    target_id: str
    class_labels: tuple[str, ...]

    def to_json(self) -> dict:
        return {"semantic_ids": list(self.semantic_ids), "target_id": self.target_id, "class_labels": list(self.class_labels), "declared_schema_consistency_only": True, "class_intervals": [x.to_json() for x in self.class_intervals],
                "extrema": [x.to_json() for x in self.extrema],
                "branch_intervals": [{"semantic_id": identity, "class_intervals": [x.to_json() for x in bounds]} for identity, bounds in zip(self.semantic_ids, self.branch_intervals)],
                "tolerance_per_extremum": str(self.tolerance), "branch_probabilities_assumed": False,
                "all_box_points_attainable": False, "numerical_result": "certified rational outer enclosure, not exact transcendental endpoints"}


def semantic_envelope(branches, budget: Budget = Budget()) -> Envelope:
    _budget(budget)
    if type(branches) not in {list, tuple} or not branches or any(type(branch) is not SemanticBranch for branch in branches):
        raise ValueError("A nonempty finite sequence of SemanticBranch objects is required")
    identities = [branch.semantic_id for branch in branches]
    if len(set(identities)) != len(identities):
        raise ValueError("semantic_id values must be unique")
    if len({len(branch.thresholds) for branch in branches}) != 1:
        raise ValueError("All branches must use the same number and meaning of ordered classes")
    if len({(branch.target_id, branch.class_labels) for branch in branches}) != 1:
        raise ValueError("Cannot union branches with different declared targets or class semantics")
    # Finish every branch before returning anything. A failed branch invalidates
    # the requested whole envelope; there is no partial acceptance fallback.
    per_branch = [branch_probability_extrema(branch, budget) for branch in branches]
    extrema = tuple(RangeCertificate(_minimum_enclosure([bounds[i].minimum for bounds in per_branch]), _maximum_enclosure([bounds[i].maximum for bounds in per_branch])) for i in range(len(per_branch[0])))
    if any(c.minimum.width > budget.tolerance or c.maximum.width > budget.tolerance for c in extrema):
        raise ArithmeticError("Union extremum tolerance contract violated")
    return Envelope(tuple(identities), tuple(c.interval for c in extrema), extrema, tuple(tuple(c.interval for c in bounds) for bounds in per_branch), budget.tolerance, branches[0].target_id, branches[0].class_labels)


@dataclass(frozen=True)
class WidthDecision:
    status: str
    width_bounds: Interval
    threshold: Fraction

    def to_json(self) -> dict:
        return {"status": self.status, "true_maximum_coordinate_width_bounds": self.width_bounds.to_json(), "threshold": str(self.threshold)}


def width_gate(envelope: Envelope, threshold: Fraction) -> WidthDecision:
    """Three-way test of the true maximum coordinate-range width <=threshold.

    A certified outer width exceeding the target alone cannot prove failure;
    the lower width bound must also exceed it. This is a numerical gate only.
    """
    if type(envelope) is not Envelope:
        raise TypeError("Expected a computed Envelope")
    threshold = rational(threshold, "width threshold")
    if threshold < 0:
        raise ValueError("Width threshold must be nonnegative")
    widths = [Interval(max(Fraction(0), certificate.maximum.lower-certificate.minimum.upper), certificate.maximum.upper-certificate.minimum.lower) for certificate in envelope.extrema]
    bounds = Interval(max(width.lower for width in widths), max(width.upper for width in widths))
    status = "pass" if bounds.upper <= threshold else "fail" if bounds.lower > threshold else "undetermined"
    return WidthDecision(status, bounds, threshold)


def label_set(values: Interval, zero_tolerance: Fraction = Fraction(0)) -> tuple[str, ...]:
    """Numeric comparison labels only; equal means within the specified band."""
    _interval(values)
    tolerance = rational(zero_tolerance, "zero_tolerance")
    if tolerance < 0:
        raise ValueError("zero_tolerance must be nonnegative")
    possible = []
    if values.lower < -tolerance:
        possible.append("below")
    if values.lower <= tolerance and values.upper >= -tolerance:
        possible.append("equal")
    if values.upper > tolerance:
        possible.append("above")
    return tuple(possible)


def robust_label(branch_intervals, zero_tolerance: Fraction = Fraction(0)) -> str | None:
    if type(branch_intervals) not in {list, tuple} or not branch_intervals:
        raise ValueError("At least one numeric interpretation is required")
    possible = {label for interval in branch_intervals for label in label_set(interval, zero_tolerance)}
    return next(iter(possible)) if len(possible) == 1 else None
