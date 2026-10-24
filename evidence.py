"""
evidence.py - turn news into a Bayesian update (the "inside view" ledger).

Each piece of evidence is written down as a likelihood ratio (LR):

    LR = P(seeing this evidence | YES) / P(seeing this evidence | NO)

    LR = 3    "this is 3x more likely to show up in a world where the answer is YES"
    LR = 1    uninformative
    LR = 0.3  points toward NO

Odds multiply by the LR. In log-odds the updates simply add, so the ledger is:

    logit(P_inside) = logit(P_base) + sum( reliability_i * ln(LR_i) )

reliability (0..1) shrinks a source's pull: an official primary source = 1.0, a wire
report = 0.8, an opinion piece = 0.4. The total update is capped at +/-MAX_SHIFT
so a pile of correlated headlines can't run away (ten articles about one event are
one piece of evidence, not ten - put it in once).

This module only produces an Estimate. How estimates are fused is aggregate.py's job,
unchanged.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from aggregate import Estimate, expit, logit

MAX_SHIFT = 3.0   # max total log-odds move from evidence (~x20 in odds)


@dataclass
class Evidence:
    what: str            # one line: the fact
    source: str          # outlet / document
    date: str            # YYYY-MM-DD of the fact
    lr: float            # likelihood ratio, >1 favours YES
    reliability: float = 0.8

    @property
    def shift(self) -> float:
        return self.reliability * math.log(self.lr)


@dataclass
class Ledger:
    prior: float                              # usually the base rate
    items: list[Evidence] = field(default_factory=list)

    def add(self, *a, **kw) -> "Ledger":
        self.items.append(Evidence(*a, **kw)); return self

    @property
    def total_shift(self) -> float:
        s = sum(e.shift for e in self.items)
        return max(-MAX_SHIFT, min(MAX_SHIFT, s))

    @property
    def posterior(self) -> float:
        return expit(logit(self.prior) + self.total_shift)

    def estimate(self, weight: float, label: str = "inside (evidence)") -> Estimate:
        return Estimate(self.posterior, weight=weight, label=label)

    def report(self) -> str:
        lines = [f"    prior (base rate)                                      {self.prior:6.1%}"]
        for e in self.items:
            arrow = "YES" if e.lr > 1 else "NO " if e.lr < 1 else " - "
            lines.append(f"    {e.date}  LR {e.lr:4.2f} x rel {e.reliability:.1f} -> {arrow}  "
                         f"{e.what[:62]}  [{e.source}]")
        raw = sum(e.shift for e in self.items)
        cap = "  (capped)" if abs(raw) > MAX_SHIFT else ""
        lines.append(f"    total log-odds shift {self.total_shift:+.2f}{cap}  ->  P_inside {self.posterior:6.1%}")
        return "\n".join(lines)
