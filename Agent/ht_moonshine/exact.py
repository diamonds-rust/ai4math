"""Exact combinatorial arithmetic used across the HT toolkit.

Everything here is stdlib-only and exact (int / Fraction). The point of the
package is that no inclusion probability, block total or population value is
ever produced by a float when an exact answer is computable.
"""

from __future__ import annotations

from fractions import Fraction
from math import comb


def falling(a: int, s: int) -> int:
    """Return a(a-1)...(a-s+1), i.e. the falling factorial a_(s)."""
    if s < 0:
        raise ValueError("s must be non-negative")
    out = 1
    for k in range(s):
        out *= a - k
    return out


def srswor_inclusion_prob(N: int, n: int, s: int) -> Fraction:
    """Exact s-th order inclusion probability under SRSWOR of size n from N.

    This is the benchmark every counterexample must match: C(n, s) / C(N, s).
    """
    if not (0 <= s <= n <= N):
        raise ValueError("need 0 <= s <= n <= N, got %r/%r/%r" % (s, n, N))
    return Fraction(comb(n, s), comb(N, s))


def as_fraction(value) -> Fraction:
    """Coerce an int/float/str/Fraction into an exact Fraction.

    Floats are converted through their decimal string so that 0.1 means 1/10
    rather than the binary expansion. Callers that need a rational population
    vector should pass ints or strings.
    """
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        return Fraction(str(value))
    return Fraction(str(value))


def rationalize(values, denominator: int = 10 ** 6):
    """Round floats to a fixed grid and return exact Fractions.

    Used to turn the exponential-quantile construction vector w into exact
    rational data, so that the identity A y = w can be checked exactly.
    """
    out = []
    for item in values:
        out.append(Fraction(round(float(item) * denominator), denominator))
    return out


def fraction_to_str(value: Fraction) -> str:
    """Render a Fraction compactly for JSON-ish output."""
    if value.denominator == 1:
        return str(value.numerator)
    return "%d/%d" % (value.numerator, value.denominator)
