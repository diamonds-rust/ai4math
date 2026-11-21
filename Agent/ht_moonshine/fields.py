"""Finite field arithmetic needed to build projective-plane designs.

Only what the Singer construction requires: GF(p) for prime p, GF(p^3) as a
quotient F_p[x]/(f), a primitive element, and the trace down to F_p.

Stdlib only; elements are 3-tuples of ints for GF(p^3) and ints for GF(p).
"""

from __future__ import annotations


def _factorize(n: int):
    """Return the distinct prime factors of n by trial division."""
    factors = []
    d = 2
    m = n
    while d * d <= m:
        if m % d == 0:
            factors.append(d)
            while m % d == 0:
                m //= d
        d += 1 if d == 2 else 2
    if m > 1:
        factors.append(m)
    return factors


class GFp3(object):
    """GF(p^3) = F_p[x] / (x^3 + c1 x^2 + c2 x + c3)."""

    def __init__(self, p: int):
        if p < 2:
            raise ValueError("p must be prime")
        if not self._is_prime(p):
            raise ValueError("p must be prime, got %r" % (p,))
        self.p = p
        self.c = self._find_irreducible_cubic()
        self.zero = (0, 0, 0)
        self.one = (1, 0, 0)

    # ---- field construction -------------------------------------------------

    @staticmethod
    def _is_prime(n: int) -> bool:
        if n < 2:
            return False
        if n % 2 == 0:
            return n == 2
        d = 3
        while d * d <= n:
            if n % d == 0:
                return False
            d += 2
        return True

    def _find_irreducible_cubic(self):
        """Find c1,c2,c3 such that x^3 + c1 x^2 + c2 x + c3 has no root in F_p."""
        p = self.p
        for c1 in range(p):
            for c2 in range(p):
                for c3 in range(p):
                    if all((x * x * x + c1 * x * x + c2 * x + c3) % p != 0 for x in range(p)):
                        return (c1, c2, c3)
        raise RuntimeError("no irreducible cubic over F_%d" % p)

    # ---- ring operations ----------------------------------------------------

    def add(self, a, b):
        p = self.p
        return ((a[0] + b[0]) % p, (a[1] + b[1]) % p, (a[2] + b[2]) % p)

    def sub(self, a, b):
        p = self.p
        return ((a[0] - b[0]) % p, (a[1] - b[1]) % p, (a[2] - b[2]) % p)

    def neg(self, a):
        p = self.p
        return ((-a[0]) % p, (-a[1]) % p, (-a[2]) % p)

    def mul(self, a, b):
        p = self.p
        c1, c2, c3 = self.c
        # convolution of degree-2 polys -> degree 4
        poly = [0] * 5
        for i in range(3):
            for j in range(3):
                poly[i + j] = (poly[i + j] + a[i] * b[j]) % p
        # reduce x^3 = -(c1 x^2 + c2 x + c3)
        for degree in (4, 3):
            lead = poly[degree] % p
            if lead:
                shift = degree - 3
                # x^degree = x^shift * x^3 = -x^shift * (c1 x^2 + c2 x + c3)
                poly[shift + 2] = (poly[shift + 2] - lead * c1) % p
                poly[shift + 1] = (poly[shift + 1] - lead * c2) % p
                poly[shift + 0] = (poly[shift + 0] - lead * c3) % p
                poly[degree] = 0
        return (poly[0] % p, poly[1] % p, poly[2] % p)

    def pow(self, a, e: int):
        if e < 0:
            raise ValueError("negative exponent")
        result = self.one
        base = a
        while e:
            if e & 1:
                result = self.mul(result, base)
            base = self.mul(base, base)
            e >>= 1
        return result

    def trace(self, a):
        """Trace GF(p^3) -> GF(p): a + a^p + a^(p^2)."""
        total = self.add(self.add(a, self.pow(a, self.p)), self.pow(a, self.p * self.p))
        if total[1] != 0 or total[2] != 0:
            raise ArithmeticError("trace did not land in the base field")
        return total[0]

    def primitive_element(self):
        """Return an element of multiplicative order p^3 - 1."""
        order = self.p ** 3 - 1
        primes = _factorize(order)
        p = self.p
        for a0 in range(p):
            for a1 in range(p):
                for a2 in range(p):
                    cand = (a0, a1, a2)
                    if cand == self.zero:
                        continue
                    if all(self.pow(cand, order // r) != self.one for r in primes):
                        return cand
        raise RuntimeError("no primitive element found in GF(%d^3)" % p)


class GFp(object):
    """Prime field F_p, just the operations the design builder needs."""

    def __init__(self, p: int):
        self.p = p

    def inv(self, a: int) -> int:
        return pow(a % self.p, self.p - 2, self.p)

    def mul(self, a: int, b: int) -> int:
        return (a * b) % self.p
