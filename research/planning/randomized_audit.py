"""Exact fixed-size randomized audits for a homogeneous r-of-d harmful family.

There are d strata, each with N distinct documents. Minimal harmful sets contain
one document in each of r different strata. The actual harmful set is fixed
before the random audit; it may not adapt to the random seed or sampled set.
The output contract MUST report the fixed target interval after every all-zero
audit, and the full statistic range after a finding. Permitting arbitrary
abstention would make a minimum-error claim meaningless (never report anything).

For an audit of exactly m distinct documents, a random permutation of strata,
q=m//N whole strata and t=m%N documents in the next stratum attain the minimax
zero-finding error. The function computes this error, not a posterior, an audit
success probability, historical provenance, or model utility. This module does
not implement adaptive or expected-budget extensions.

All arithmetic is exact Fraction/integer. The minimum-count functions use
monotone binary search. Binomial-integer bit costs remain relevant at large
parameters; the experiment scope and wall budget are frozen separately. The
sampler returns one deterministic replay draw for a supplied PRNG seed, not a
claim that a single fixed seed itself defines a repeated-sampling guarantee.
Its law is the stated uniform construction; exact byte replay also freezes the
Python implementation/version. No model training, I/O, or network is performed.
"""
from __future__ import annotations

from fractions import Fraction
from math import comb
import random
import re

_UNSET = object()


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _validate(population, layers, threshold, audits=_UNSET):
    if any(not _integer(value) or value < 1 for value in (population, layers, threshold)):
        raise ValueError('N, d, r must be positive integers, not bool/float')
    if threshold > layers:
        raise ValueError('r must not exceed d')
    total = population*layers
    if audits is not _UNSET and (not _integer(audits) or not 0 <= audits <= total):
        raise ValueError('m must be an integer in [0,d*N], not bool/float')
    return total


def _alpha(value):
    if isinstance(value, bool) or not isinstance(value, (int, str, Fraction)):
        raise ValueError('alpha must be an exact integer, rational/decimal string, or Fraction')
    if isinstance(value, str):
        if len(value) > 1024 or not re.fullmatch(r'[+-]?(?:\d+(?:/\d+)?|\d+\.\d*|\.\d+)', value.strip()):
            raise ValueError('alpha string must have bounded finite syntax without an exponent')
    try:
        result = Fraction(value)
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError('invalid exact alpha') from error
    if max(abs(result.numerator).bit_length(), result.denominator.bit_length()) > 4096:
        raise ValueError('alpha numerator/denominator exceeds the supported bit budget')
    if not 0 < result < 1:
        raise ValueError('alpha must be strictly between zero and one')
    return result


def _choose(n, k):
    return comb(n, k) if 0 <= k <= n else 0


def randomized_risk(population, layers, threshold, audits):
    """Minimax miss risk among all laws on exactly m distinct audit documents.

    Requires the homogeneous r-of-d family and the all-zero reporting contract
    described above. A single deterministic concentrated set generally does not
    have this worst-case risk: randomization across strata/documents is essential.
    """
    total = _validate(population, layers, threshold, audits)
    if audits == total:
        return Fraction(0)
    q, t = divmod(audits, population)
    remaining = layers-q-1
    numerator = population*_choose(remaining, threshold)
    numerator += (population-t)*_choose(remaining, threshold-1)
    return Fraction(numerator, population*comb(layers, threshold))


def pooled_srs_risk(population, layers, threshold, audits):
    """Miss risk for uniform SRS of m documents from the pooled population.

    C(d*N-r,m)/C(d*N,m) is computed by the equivalent complementary expression
    C(d*N-m,r)/C(d*N,r), avoiding unnecessary huge binomials when m is large.
    Each minimal harmful set has r distinct documents, irrespective of strata.
    """
    total = _validate(population, layers, threshold, audits)
    return Fraction(_choose(total-audits, threshold), comb(total, threshold))


def _minimum(population, layers, threshold, alpha, risk_function):
    total = _validate(population, layers, threshold)
    a = _alpha(alpha)
    lo, hi = 0, total
    while lo < hi:
        mid = (lo+hi)//2
        if risk_function(population, layers, threshold, mid) <= a:
            hi = mid
        else:
            lo = mid+1
    return lo


def minimum_randomized_audits(population, layers, threshold, alpha='1/20'):
    """Smallest fixed m whose randomized minimax miss risk is at most alpha."""
    return _minimum(population, layers, threshold, alpha, randomized_risk)


def minimum_pooled_audits(population, layers, threshold, alpha='1/20'):
    """Smallest fixed m for the uniform pooled-SRS comparator."""
    return _minimum(population, layers, threshold, alpha, pooled_srs_risk)


def sample_concentrated_audit(population, layers, audits, *, seed=0, max_output=100000):
    """Return a replayable sorted tuple of zero-based (stratum, document) IDs.

    Whole strata are selected uniformly without replacement, and any partial
    stratum is selected uniformly among the remaining strata. Its t documents
    are sampled uniformly without replacement. `seed` is a nonnegative integer;
    an application must separately justify its randomness/timing contract.
    `max_output` bounds the number of materialized IDs, not the risk computation.
    """
    total = _validate(population, layers, 1, audits)
    if not _integer(seed) or seed < 0:
        raise ValueError('seed must be a nonnegative integer, not bool/float')
    if not _integer(max_output) or max_output < 0:
        raise ValueError('max_output must be a nonnegative integer, not bool/float')
    if audits > max_output:
        raise ValueError('sampler output budget exceeded; no partial sample returned')
    if audits == total:
        return tuple((h, i) for h in range(layers) for i in range(population))
    q, t = divmod(audits, population)
    generator = random.Random(seed)
    order = generator.sample(range(layers), q+int(t > 0))
    chosen = [(h, i) for h in order[:q] for i in range(population)]
    if t:
        chosen.extend((order[-1], i) for i in generator.sample(range(population), t))
    return tuple(sorted(chosen))
