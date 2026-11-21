"""Limit-law diagnostics: exact sample-total laws, moments, KS distances.

Under uniform block sampling the distribution of the HT sample total is *not*
simulated here -- it is computed exactly, because selecting block j contributes
blocksum(w)_j with probability p_j. Simulation is only used for the SRSWOR
side, where the normal approximation is the object under test.
"""

from __future__ import annotations

import math
import random
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from .algebra import block_sums, hajek_ratio, max_abs, mean, population_variance
from .designs import Design
from .exact import as_fraction


# ---------------------------------------------------------------- construction


def exponential_quantiles(N: int) -> List[float]:
    """The centered exponential-quantile vector w used by Chen (2026), Sec. 4.1."""
    raw = [-math.log(1.0 - (i + 0.5) / N) for i in range(N)]
    mu = sum(raw) / len(raw)
    return [value - mu for value in raw]


def centered_rational_quantiles(N: int, denominator: int = 1000) -> List[Fraction]:
    """Exact rational version of ``exponential_quantiles``, centered exactly.

    Rounding to a 1/denominator grid keeps all downstream identities checkable
    in rational arithmetic while leaving the shape (skewness near 2) intact.
    """
    values = [Fraction(round(value * denominator), denominator) for value in exponential_quantiles(N)]
    mu = sum(values, Fraction(0)) / len(values)
    return [value - mu for value in values]


def permute(values: Sequence[Fraction], permutation: Optional[Sequence[int]]) -> List[Fraction]:
    """Apply a permutation of block labels to the prescribed block totals."""
    if permutation is None:
        return list(values)
    if len(permutation) != len(values):
        raise ValueError("permutation length mismatch")
    return [values[permutation[j]] for j in range(len(values))]


# -------------------------------------------------------------------- moments


def moments(values: Sequence[Fraction], probs: Sequence[Fraction]) -> Dict[str, object]:
    """Exact mean / variance / skewness / kurtosis of a finite distribution."""
    if len(values) != len(probs):
        raise ValueError("values/probs length mismatch")
    total = sum(probs, Fraction(0))
    if total != 1:
        raise ValueError("probabilities sum to %s, not 1" % total)
    mu = sum((v * p for v, p in zip(values, probs)), Fraction(0))
    var = sum(((v - mu) ** 2) * p for v, p in zip(values, probs))
    if var == 0:
        raise ValueError("degenerate distribution")
    sd = math.sqrt(float(var))
    m3 = sum(((v - mu) ** 3) * p for v, p in zip(values, probs))
    m4 = sum(((v - mu) ** 4) * p for v, p in zip(values, probs))
    return {
        "mean": "%.10f" % float(mu),
        "sd": "%.10f" % sd,
        "variance": "%.10f" % float(var),
        "skewness": "%.6f" % (float(m3) / sd ** 3),
        "kurtosis": "%.6f" % (float(m4) / sd ** 4),
        "support_size": len(values),
    }


def sample_total_law(
    design: Design,
    y: Sequence[Fraction],
    weights: Optional[Sequence[Fraction]] = None,
) -> Dict[str, object]:
    """Exact law of the sample total under (possibly weighted) block sampling."""
    totals = block_sums(design, y)
    if weights is None:
        weights = [Fraction(1, design.b) for _ in range(design.b)]
    if len(weights) != design.b:
        raise ValueError("weights length mismatch")
    groups: Dict[Fraction, Fraction] = {}
    for value, p in zip(totals, weights):
        if p:
            groups[value] = groups.get(value, Fraction(0)) + p
    values = sorted(groups)
    probs = [groups[value] for value in values]
    return {
        "values": values,
        "probs": probs,
        "moments": moments(values, probs),
        "uniform_block_weights": all(abs(p - Fraction(1, design.b)) == 0 for p in weights),
    }


# ------------------------------------------------------------------ distances


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def ks_distance_to_standard_normal(values: Sequence[Fraction], probs: Sequence[Fraction]) -> float:
    """Kolmogorov-Smirnov distance of a finite law (standardized) to N(0,1)."""
    mu = float(sum((v * p for v, p in zip(values, probs)), Fraction(0)))
    var = float(sum(((v - mu) ** 2) * p for v, p in zip(values, probs)))
    sd = math.sqrt(var)
    cumulative = 0.0
    distance = 0.0
    for value, p in sorted(zip(values, probs)):
        cumulative += float(p)
        z = (float(value) - mu) / sd
        distance = max(distance, abs(cumulative - normal_cdf(z)))
    return distance


def ks_distance_empirical_to_normal(samples: Sequence[float]) -> Dict[str, float]:
    """KS distance of iid samples to a normal fitted by sample moments."""
    n = len(samples)
    if n < 2:
        raise ValueError("need at least two samples")
    mu = sum(samples) / n
    var = sum((x - mu) ** 2 for x in samples) / (n - 1)
    sd = math.sqrt(var)
    ordered = sorted(samples)
    distance = 0.0
    for index, value in enumerate(ordered):
        z = (value - mu) / sd
        cdf = normal_cdf(z)
        distance = max(distance, abs(cdf - index / n), abs((index + 1) / n - cdf))
    return {"ks": distance, "mean": mu, "sd": sd, "n": float(n)}


def sample_moments(samples: Sequence[float]) -> Dict[str, float]:
    n = len(samples)
    mu = sum(samples) / n
    var = sum((x - mu) ** 2 for x in samples) / n
    sd = math.sqrt(var)
    m3 = sum((x - mu) ** 3 for x in samples) / n
    m4 = sum((x - mu) ** 4 for x in samples) / n
    return {"mean": mu, "sd": sd, "skewness": m3 / sd ** 3, "kurtosis": m4 / sd ** 4}


# ------------------------------------------------------------------- SRSWOR


def srswor_sample_totals(
    y: Sequence[Fraction],
    n: int,
    reps: int,
    seed: int = 20261023,
) -> List[float]:
    """Monte-Carlo SRSWOR sample totals (floats; the SRSWOR side is the object under test)."""
    values = [float(item) for item in y]
    N = len(values)
    if not (0 < n <= N):
        raise ValueError("sample size out of range")
    rng = random.Random(seed)
    out: List[float] = []
    for _ in range(reps):
        idx = rng.sample(range(N), n)
        out.append(sum(values[i] for i in idx))
    return out


def exact_variances(design: Design, y: Sequence[Fraction]) -> Dict[str, object]:
    """Exact HT variance under block sampling vs. under SRSWOR.

    The two designs share pi_i = n/N and pi_ij = n(n-1)/(N(N-1)), so the closed
    form for the SRSWOR variance must equal the variance of the exact block law.
    Equality here is the paper's punchline: identical first two moments,
    different limit law.
    """
    N = design.v
    n = design.block_size
    pi = Fraction(n, N)
    pi2 = Fraction(n * (n - 1), N * (N - 1))
    yc = [item - mean(y) for item in y]
    sum_sq = sum((item * item for item in yc), Fraction(0))
    closed_form = (Fraction(N, n) - pi2 / (pi * pi)) * sum_sq

    law = sample_total_law(design, y)
    mu = sum((v * p for v, p in zip(law["values"], law["probs"])), Fraction(0))
    block_total_var = sum(
        (((v - mu) ** 2) * p for v, p in zip(law["values"], law["probs"])),
        Fraction(0),
    )
    # The HT estimator is T_block / pi, so its variance carries a 1/pi^2 factor.
    ht_var_block = block_total_var / (pi * pi)
    return {
        "srswor_closed_form": closed_form,
        "block_law": ht_var_block,
        "block_total_law_raw": block_total_var,
        "pi_squared": str(pi * pi),
        "equal": closed_form == ht_var_block,
        "mean_closed_form": pi * sum(y, Fraction(0)),
        "mean_block_law": mu,
        "means_equal": pi * sum(y, Fraction(0)) == mu,
    }


def block_law_ks_to_normal(law: Dict[str, object]) -> float:
    """KS distance from the exact block-sample-total law to fitted N(mean, sd)."""
    values = law["values"]  # type: ignore[index]
    probs = law["probs"]  # type: ignore[index]
    mu = float(sum((v * p for v, p in zip(values, probs)), Fraction(0)))
    var = float(sum(((v - mu) ** 2) * p for v, p in zip(values, probs)))
    sd = math.sqrt(var)
    cumulative = 0.0
    distance = 0.0
    for value, p in sorted(zip(values, probs)):
        cumulative += float(p)
        distance = max(distance, abs(cumulative - normal_cdf((float(value) - mu) / sd)))
    return distance


def hajek_decay_study(qs: Sequence[int]) -> Dict[str, object]:
    """Measure whether the finite-N Hajek ratio decays like the theoretical O(1/q).

    Uses the closed-form inverse on PG(2, q) designs. A fitted log-log slope near
    -1 is numerical evidence that the sufficient condition tends to zero along
    the construction; it is not a proof of the asymptotic statement.
    """
    from .algebra import back_solve_closed_form, hajek_ratio
    from .designs import projective_plane

    rows = []
    for q in qs:
        design = projective_plane(q)
        w = centered_rational_quantiles(design.b)
        y = back_solve_closed_form(design, w)["y"]
        rows.append(
            {
                "q": q,
                "N": design.v,
                "n": design.block_size,
                "max_abs_y": float(max_abs(y)),
                "hajek_ratio": float(hajek_ratio(y, design.block_size)),
            }
        )
    slope = _loglog_slope([row["q"] for row in rows], [row["hajek_ratio"] for row in rows])
    endpoints_decrease = rows[-1]["hajek_ratio"] < rows[0]["hajek_ratio"] and rows[-1]["max_abs_y"] < rows[0]["max_abs_y"]
    return {
        "rows": rows,
        "loglog_slope": slope,
        "endpoints_decrease": endpoints_decrease,
        "consistent_with_o_one_over_q": bool(
            slope is not None and slope <= -0.25 and endpoints_decrease
        ),
    }


def _loglog_slope(xs: Sequence[float], ys: Sequence[float]):
    points = [(math.log(x), math.log(y)) for x, y in zip(xs, ys) if x > 0 and y > 0]
    if len(points) < 2:
        return None
    n = len(points)
    mx = sum(p[0] for p in points) / n
    my = sum(p[1] for p in points) / n
    num = sum((p[0] - mx) * (p[1] - my) for p in points)
    den = sum((p[0] - mx) ** 2 for p in points)
    if den == 0:
        return None
    return num / den


def check_srswor_clt(
    y: Sequence[Fraction],
    n: int,
    reps: int = 20000,
    seed: int = 20261023,
    threshold: float = 0.05,
) -> Dict[str, object]:
    """Finite-N diagnostics for the SRSWOR CLT on this population.

    Reports the exact Hajek ratio (the sufficient condition used in the paper)
    plus an empirical normality check on simulated SRSWOR totals. ``passes``
    means the ratio is below ``threshold`` *at this N* -- it is a finite-size
    diagnostic, not a proof of an asymptotic statement.
    """
    ratio = hajek_ratio(y, n)
    totals = srswor_sample_totals(y, n, reps, seed)
    shape = sample_moments(totals)
    ks = ks_distance_empirical_to_normal(totals)
    return {
        "n": n,
        "N": len(y),
        "max_abs_y": "%.6f" % float(max_abs(y)),
        "hajek_ratio": "%.6f" % float(ratio),
        "threshold": threshold,
        "passes_finite_n": float(ratio) < threshold,
        "srswor_totals": {
            "reps": reps,
            "seed": seed,
            "skewness": round(shape["skewness"], 6),
            "kurtosis": round(shape["kurtosis"], 6),
            "ks_vs_normal": round(ks["ks"], 6),
        },
        "population": {
            "mean": "%.10f" % float(mean(y)),
            "variance": "%.10f" % float(population_variance(y)),
        },
    }
