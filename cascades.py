"""
cascades.py - Route B (Scarcity Equilibrium) models for specific questions.

SUDAN FAMINE (Metaculus q45464): "Will FEWS NET classify any area of Sudan as Famine
(IPC Phase 5) in a map reported after Aug 2026 and before Jan 2027?"

Why this question suits the framework: famine is a cascade across coupled domains
(security -> access -> food -> purchasing power -> nutrition -> survival) with lags and
feedback. And it uses all three of the framework's distinctive ideas:

  * ADAPTIVE SET POINTS - after 3.5 years of war, these areas don't drift back toward
    "normal" on their own; they hover at a crisis equilibrium. So each node's anchor s0
    is today's crisis level, not 0.5. Restoration pulls toward misery, not recovery.
  * META-SCARCITY - a drought-hit harvest in one place pushes displaced people into
    another (East Jebel Marra), turning one area's shortage into another's.
  * OBJECTIVE vs PERCEIVED (reported) - the question resolves on a FEWS NET *map*, not on
    conditions. Conditions must cross all three IPC Famine thresholds at once, AND be
    measured, AND be published before 2027. The model splits these:
        P_inside = P(conditions cross)  x  P(classified & published | conditions)

Scale: x in [0,1] is domain health. Famine thresholds sit at x <= 0.15 for food
consumption, nutrition (GAM >= 30%) and survival (CDR >= 2/10,000/day).
Time unit: months from 2026-10-16. Conditions must exist by ~late Nov to reach a map
reported before Jan 1, so the horizon is 1.5 months.

Sources (read 2026-10-16): FEWS NET Sudan Key Message Update, 8 Oct 2026 (ReliefWeb):
Phase 4 widespread through Jan; Phase 5 households in N Darfur / S Kordofan hotspots;
GAM above the Famine threshold in 2 of 4 assessed IDP camps but mortality and food
consumption at Emergency, "these findings do not establish a Famine classification";
risk of Famine expands to East Jebel Marra if drought drives more displacement.
"""
from __future__ import annotations

import numpy as np

from scarcity import Network, find_loops, monte_carlo

FAMINE_LINE = 0.15
HORIZON = 1.5            # months
# The question resolves on ANY area, so we model the WORST one (the assessed IDP camps),
# not an average of Darfur. Per FEWS NET 8 Oct: GAM already above the Famine line in
# 2 of 4 camps (nutrition below 0.15), food consumption and mortality at Emergency
# (just above the line). Crisis equilibrium (adapted set points) and today's state:
S0 = dict(security=0.22, access=0.22, food=0.22, purchasing=0.22, nutrition=0.15, survival=0.20)
X0 = dict(security=0.22, access=0.22, food=0.21, purchasing=0.22, nutrition=0.14, survival=0.20)
# Shock branches = FEWS NET's own named downside scenarios: (probability in window,
# driver node it hits). Each is SUSTAINED - more mouths on the same food, a siege that
# stays - so it is modelled as an exogenous DRIVER node that does not recover on its own
# (k ~ 0) and keeps pushing through its edges. (Lowering the anchor s0 instead would be
# wrong: the framework's influence runs on deviation from the set point, so a node whose
# anchor fell with it would transmit nothing - starving people would look "normal".)
SHOCKS = {
    "displacement surge into East Jebel Marra": (0.30, "displacement"),
    "siege / conflict escalation (Kadugli, Dilling, El-Obeid)": (0.30, "conflict"),
    "aid funding cut (WFP warning)": (0.25, "aid"),
}
SHOCK_SIZE = 0.30
P_DETECT = 0.5           # P(FEWS NET measures it and publishes Phase 5 in time | conditions)


def build_sudan(rng: np.random.Generator, jitter: bool = True, shock_scale: float = 1.0,
                hit: set | None = None, lag_scale: float = 1.0):
    """hit: force exactly these driver shocks (for figures); lag_scale: multiply every lag."""
    def j(v, spread=0.35):
        return v * (1 + spread * (rng.random() * 2 - 1)) if jitter else v

    if hit is None:
        hit = {drv for p, drv in SHOCKS.values() if rng.random() < p * shock_scale}

    net = Network(sharp=2.0)
    for nm in S0:
        net.add_node(nm, s0=S0[nm], k=0.5, delta=0.03, eps=0.03, eta=0.02,
                     sigma=0.02, x0=X0[nm])
    for drv in ("displacement", "conflict", "aid"):   # drivers: 0.5 = no shock
        net.add_node(drv, s0=0.5, k=1e-4, delta=0.03, eps=0.03, eta=0.0, sigma=0.0,
                     x0=0.5 - (SHOCK_SIZE if drv in hit else 0.0))
    e = net.add_edge
    e("displacement", "food",   c=j(0.25), tau=0.10, mech="more people on the same food")
    e("displacement", "access", c=j(0.05), tau=0.25, mech="crowded camps strain aid")
    e("conflict", "security",   c=j(0.50), tau=0.10, mech="siege / escalation")
    e("aid", "access",          c=j(0.30), tau=0.25, mech="funding cut shrinks rations")
    e("security", "access",     c=j(0.50), tau=0.25, mech="fighting closes roads and aid corridors")
    e("security", "food",       c=j(0.30), tau=0.50, mech="displacement, abandoned fields")
    e("access", "food",         c=j(0.40), tau=0.25, mech="convoys and markets supply food")
    e("access", "purchasing",   c=j(0.30), tau=0.25, mech="cut-off markets -> price spikes")
    e("food", "purchasing",     c=j(0.30), tau=0.25, mech="scarcity raises prices")
    e("food", "nutrition",      c=j(0.50), tau=0.50, mech="less food -> wasting")
    e("purchasing", "nutrition", c=j(0.30), tau=0.50, mech="can't afford food -> wasting")
    e("nutrition", "survival",  c=j(0.60), tau=0.50, mech="wasting -> deaths")
    e("survival", "food",       c=j(0.20), tau=0.50, mech="illness/deaths cut labour and foraging (reinforcing)")
    e("survival", "access",     c=-abs(j(0.30)), tau=0.50, mech="deaths trigger aid surge (balancing)")
    for ed in net.edges:
        ed.tau *= lag_scale
    return net, {}


def famine_conditions(r) -> bool:
    """All three IPC Famine thresholds crossed at the same time, inside the horizon."""
    f, n, s = r.series("food"), r.series("nutrition"), r.series("survival")
    return bool(np.any((f <= FAMINE_LINE) & (n <= FAMINE_LINE) & (s <= FAMINE_LINE)))


def run_sudan(n: int = 1500) -> dict:
    mc = monte_carlo(lambda rng: build_sudan(rng), famine_conditions,
                     n=n, t_end=HORIZON, dt=0.02, seed=3)
    sweep = {}
    for sc in (0.5, 1.0, 1.5):
        m = monte_carlo(lambda rng, sc=sc: build_sudan(rng, shock_scale=sc), famine_conditions,
                        n=500, t_end=HORIZON, dt=0.02, seed=5)
        sweep[sc] = m.p
    # Timing (framework output #2): mortality lags malnutrition, so the answer depends
    # heavily on the window. Same model, longer horizons:
    horizons = {}
    for h in (1.5, 3.0, 4.5):
        m = monte_carlo(lambda rng: build_sudan(rng), famine_conditions,
                        n=500, t_end=h, dt=0.02, seed=9)
        horizons[h] = m.p
    loops = sorted(find_loops(build_sudan(np.random.default_rng(0), jitter=False)[0]),
                   key=lambda L: -L.gain)
    return {"p_conditions": mc.p, "ci": (mc.lo, mc.hi), "p_detect": P_DETECT,
            "p_inside": mc.p * P_DETECT, "shock_sweep": sweep, "horizons": horizons,
            "loops": loops}


if __name__ == "__main__":
    r = run_sudan()
    for L in r["loops"]:
        print(" ", L.describe())
    print(f"P(famine conditions by ~1 Dec) = {r['p_conditions']:.1%} "
          f"[{r['ci'][0]:.1%}, {r['ci'][1]:.1%}]")
    print("shock-rate sweep:", {k: f"{v:.1%}" for k, v in r["shock_sweep"].items()})
    print("by horizon (months):", {k: f"{v:.1%}" for k, v in r["horizons"].items()})
    print(f"x P(classified & published) {r['p_detect']:.0%} -> P_inside {r['p_inside']:.1%}")
