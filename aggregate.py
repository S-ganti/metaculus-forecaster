"""
aggregate.py — the statistical synthesis engine for Metaculus forecasting.

This is the "combined statistical answer" layer. It takes several *independent-ish*
probability estimates for the SAME binary question and fuses them into one calibrated
number with an uncertainty band. The three canonical inputs are:

    P_base       outside view  -- a reference-class base rate (optionally time-adjusted)
    P_community  the Metaculus community/consensus prediction (a strong prior)
    P_inside     inside view   -- mechanism reasoning, current evidence, or the output
                                  of the Scarcity Equilibrium Monte Carlo (scarcity.py)

Fusion happens in LOG-ODDS space with precision weights, which is the mathematically
natural place to combine probabilities (a 0.01->0.02 move and a 0.50->0.66 move are the
same evidence strength -- one "bit" -- and only log-odds treats them equally).

Nothing here is Metaculus-specific; it is generic probabilistic-forecast machinery.
Requires: numpy, scipy (both confirmed present in this environment).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Optional

import numpy as np

try:
    from scipy.stats import beta as _beta
    _HAVE_SCIPY = True
except Exception:  # pragma: no cover
    _HAVE_SCIPY = False

# Clip probabilities into an open interval so log-odds stay finite.
_PCLIP = 1e-6


# --------------------------------------------------------------------------- #
#  Core log-odds primitives
# --------------------------------------------------------------------------- #
def logit(p: float) -> float:
    """Log-odds of p. p is clipped to (1e-6, 1-1e-6) to stay finite."""
    p = min(max(p, _PCLIP), 1.0 - _PCLIP)
    return math.log(p / (1.0 - p))


def expit(x: float) -> float:
    """Inverse of logit (the logistic function)."""
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


# --------------------------------------------------------------------------- #
#  Time / hazard adjustment for "will X happen by <date>" questions
# --------------------------------------------------------------------------- #
def survival_prob(rate_per_period: float, n_periods: float, poisson: bool = False) -> float:
    """
    Convert a per-period event rate into P(at least one event within n_periods).

    Use this to turn "≈8% of governments like this collapse in a given year" into
    "P(collapse before the resolution date 2.5 years out)".

    rate_per_period : hazard per base period (e.g. per year). 0..1 for the Bernoulli
                      form; any positive number for the Poisson form.
    n_periods       : horizon measured in the same base period (may be fractional).
    poisson         : if True use 1 - exp(-rate*n) (events can recur / rate>1 allowed);
                      else the discrete-survival form 1 - (1-rate)**n.
    """
    n = max(n_periods, 0.0)
    if poisson:
        return 1.0 - math.exp(-max(rate_per_period, 0.0) * n)
    r = min(max(rate_per_period, 0.0), 1.0)
    return 1.0 - (1.0 - r) ** n


def annualize(p_total: float, n_periods: float) -> float:
    """Inverse of the Bernoulli survival form: recover the per-period hazard from a
    cumulative probability over n_periods. Handy for sanity checks."""
    p_total = min(max(p_total, _PCLIP), 1.0 - _PCLIP)
    n = max(n_periods, 1e-9)
    return 1.0 - (1.0 - p_total) ** (1.0 / n)


# --------------------------------------------------------------------------- #
#  Reference-class base rate with an honest uncertainty band (Beta model)
# --------------------------------------------------------------------------- #
@dataclass
class BaseRate:
    """A base rate estimated from a reference class of k events in n trials.

    The point estimate is the Beta-posterior mean; the band is a credible interval.
    A wide band (small n) tells the aggregator to trust this input less."""

    k: float                 # events observed in the reference class
    n: float                 # size of the reference class
    prior_a: float = 0.5     # Jeffreys prior by default
    prior_b: float = 0.5
    label: str = "base rate"

    @property
    def a(self) -> float:
        return self.prior_a + self.k

    @property
    def b(self) -> float:
        return self.prior_b + (self.n - self.k)

    @property
    def mean(self) -> float:
        return self.a / (self.a + self.b)

    def interval(self, mass: float = 0.90) -> tuple[float, float]:
        lo = (1.0 - mass) / 2.0
        hi = 1.0 - lo
        if _HAVE_SCIPY:
            return float(_beta.ppf(lo, self.a, self.b)), float(_beta.ppf(hi, self.a, self.b))
        # Normal approximation fallback
        m = self.mean
        v = (self.a * self.b) / ((self.a + self.b) ** 2 * (self.a + self.b + 1))
        z = 1.6448536269514722  # 90%
        s = math.sqrt(v)
        return max(0.0, m - z * s), min(1.0, m + z * s)

    def precision(self) -> float:
        """A weight for the aggregator: precision of the Beta mean in log-odds units.
        More reference-class data -> higher precision -> more influence.

        Derived from the delta-method variance of logit(mean): Var ≈ 1/a + 1/b, so
        precision ≈ 1/(1/a + 1/b). Capped so a single base rate can't dominate."""
        var_logit = 1.0 / self.a + 1.0 / self.b
        return min(1.0 / var_logit, 6.0)


# --------------------------------------------------------------------------- #
#  The fusion step
# --------------------------------------------------------------------------- #
@dataclass
class Estimate:
    """One probability estimate feeding the fusion.

    weight is a *precision* (1/variance in log-odds space): how many "units of
    confidence" this source is worth. Rough guide:
        community prediction (many forecasters, liquid) ... 3 - 6
        solid base rate (large reference class) .......... 2 - 4
        mechanism / inside view with real evidence ....... 1 - 2
        speculative hunch ................................ 0.3 - 0.8
    """

    p: float
    weight: float = 1.0
    label: str = ""


@dataclass
class Fusion:
    p: float
    lo: float
    hi: float
    logodds: float
    var: float
    components: list[Estimate] = field(default_factory=list)

    def as_report(self) -> str:
        lines = ["  component            p        weight   logit"]
        for e in self.components:
            lines.append(f"  {e.label:<18} {e.p:6.3f}   {e.weight:6.2f}   {logit(e.p):+6.2f}")
        lines.append("  " + "-" * 44)
        lines.append(
            f"  FUSED                {self.p:6.3f}            "
            f"[{self.lo:.3f}, {self.hi:.3f}] 90% CI"
        )
        return "\n".join(lines)


def fuse(estimates: Iterable[Estimate], mass: float = 0.90) -> Fusion:
    """Precision-weighted Gaussian fusion in log-odds space.

    Treat each estimate as a noisy observation of the true log-odds with precision
    = weight. The posterior is Gaussian with
        mean = Σ w_k L_k / Σ w_k
        var  = 1 / Σ w_k
    This is the Bayes-optimal pool of independent Gaussian observations, and it gives
    a coherent credible interval for free. Correlated inputs (e.g. your base rate and
    your inside view lean on the same study) should be *down-weighted* by the caller,
    not extremized -- see notes in METHODOLOGY.md.
    """
    ests = list(estimates)
    if not ests:
        raise ValueError("fuse() needs at least one estimate")
    W = sum(max(e.weight, 1e-9) for e in ests)
    L = sum(max(e.weight, 1e-9) * logit(e.p) for e in ests) / W
    var = 1.0 / W
    z = 1.6448536269514722 if abs(mass - 0.90) < 1e-6 else _z_for_mass(mass)
    sd = math.sqrt(var)
    return Fusion(
        p=expit(L),
        lo=expit(L - z * sd),
        hi=expit(L + z * sd),
        logodds=L,
        var=var,
        components=ests,
    )


def _z_for_mass(mass: float) -> float:
    if _HAVE_SCIPY:
        from scipy.stats import norm
        return float(norm.ppf(1.0 - (1.0 - mass) / 2.0))
    return 1.6448536269514722


# --------------------------------------------------------------------------- #
#  Calibration transforms (apply AFTER fusion)
# --------------------------------------------------------------------------- #
def calibrate(p: float, slope: float = 1.0, shift: float = 0.0) -> float:
    """Platt-style recalibration in log-odds: logit' = slope*logit + shift.

    slope < 1 pulls toward 0.5 (fixes overconfidence -- the usual human failure mode).
    slope > 1 pushes toward the extremes.
    Fit slope/shift from your own track record once you have ~30+ resolved questions;
    until then leave slope=1. A mild slope=0.9 is a safe default against overconfidence.
    """
    return expit(slope * logit(p) + shift)


def extremize(p: float, d: float = 1.0) -> float:
    """Aggregate-extremizing for N *independent* forecasters (Satopää et al.).

    Only valid when pooling genuinely independent opinions (e.g. several people, or
    several uncorrelated models). Do NOT apply to your own base/community/inside inputs,
    which are correlated. d=1 is a no-op; d≈2.0-2.5 is typical for crowds.
    """
    return expit(d * logit(p))


def toward_community(p: float, p_comm: Optional[float], pull: float = 0.25) -> float:
    """Shrink your forecast a fraction `pull` toward the community prediction in
    log-odds. The Metaculus community is hard to beat; unless you have a specific edge,
    a 0.15-0.35 pull toward it improves expected score. No-op if p_comm is None."""
    if p_comm is None:
        return p
    L = (1.0 - pull) * logit(p) + pull * logit(p_comm)
    return expit(L)


# --------------------------------------------------------------------------- #
#  Scoring (track your calibration -- section 6/8 of the framework)
# --------------------------------------------------------------------------- #
def brier(p: float, outcome: int) -> float:
    """Brier score (lower is better). outcome in {0,1}."""
    return (p - outcome) ** 2


def log_score(p: float, outcome: int) -> float:
    """Log score (higher is better) -- the family Metaculus uses. outcome in {0,1}."""
    p = min(max(p, _PCLIP), 1.0 - _PCLIP)
    return math.log(p) if outcome == 1 else math.log(1.0 - p)


def score_history(preds: list[tuple[float, int]]) -> dict:
    """Summarize a track record of (probability, outcome) pairs.

    Returns mean Brier, mean log score, and a calibration table (predicted vs realized
    frequency in deciles) -- the raw material for fitting `calibrate`."""
    if not preds:
        return {"n": 0}
    ps = np.array([p for p, _ in preds], dtype=float)
    ys = np.array([y for _, y in preds], dtype=float)
    briers = (ps - ys) ** 2
    logs = np.where(ys == 1, np.log(np.clip(ps, _PCLIP, 1)), np.log(np.clip(1 - ps, _PCLIP, 1)))
    bins = np.clip((ps * 10).astype(int), 0, 9)
    table = []
    for b in range(10):
        m = bins == b
        if m.any():
            table.append({
                "bin": f"{b*10}-{b*10+10}%",
                "n": int(m.sum()),
                "mean_pred": float(ps[m].mean()),
                "realized": float(ys[m].mean()),
            })
    return {
        "n": len(preds),
        "brier": float(briers.mean()),
        "log_score": float(logs.mean()),
        "calibration": table,
    }


# --------------------------------------------------------------------------- #
#  Convenience: the full pipeline for a binary question
# --------------------------------------------------------------------------- #
def forecast_binary(
    base: Optional[Estimate] = None,
    community: Optional[Estimate] = None,
    inside: Optional[Estimate] = None,
    extra: Optional[list[Estimate]] = None,
    calibration_slope: float = 1.0,
    community_pull: float = 0.0,
) -> Fusion:
    """Run outside/community/inside estimates through fusion + optional calibration.

    Returns a Fusion whose `.p` is the final number to submit. `community_pull` applies
    an extra shrink toward the community after fusion (use when you're unsure of your edge).
    """
    comps = [e for e in (base, community, inside) if e is not None]
    if extra:
        comps.extend(extra)
    if not comps:
        raise ValueError("Provide at least one estimate")
    f = fuse(comps)
    p = f.p
    if calibration_slope != 1.0:
        p = calibrate(p, slope=calibration_slope)
    if community_pull > 0 and community is not None:
        p = toward_community(p, community.p, pull=community_pull)
    # Recompute the band around the (possibly) shifted point, preserving width.
    half = (logit(f.hi) - logit(f.lo)) / 2.0
    return Fusion(
        p=p,
        lo=expit(logit(p) - half),
        hi=expit(logit(p) + half),
        logodds=logit(p),
        var=f.var,
        components=comps,
    )


if __name__ == "__main__":
    # Tiny self-test / illustration.
    base = Estimate(survival_prob(0.08, 2.5), weight=2.5, label="base rate")
    comm = Estimate(0.30, weight=4.0, label="community")
    ins = Estimate(0.42, weight=1.2, label="inside/scarcity")
    f = forecast_binary(base=base, community=comm, inside=ins, calibration_slope=0.9)
    print("Demo fusion:")
    print(f.as_report())
    print(f"\nFinal (calibrated): {f.p:.1%}  90% CI [{f.lo:.1%}, {f.hi:.1%}]")

    hist = [(0.7, 1), (0.7, 1), (0.7, 0), (0.2, 0), (0.9, 1), (0.4, 0), (0.55, 1)]
    print("\nTrack-record demo:", score_history(hist))
