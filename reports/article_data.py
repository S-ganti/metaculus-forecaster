"""
article_data.py - compute every figure's data for the Sudan article from the model itself.

    python reports/article_data.py      -> reports/article_data.json

Nothing in the article's charts is hand-drawn except where the article says "schematic".
"""
from __future__ import annotations

import json
import math
import sys
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import cascades as C                                   # noqa: E402
from aggregate import Estimate, forecast_binary, BaseRate   # noqa: E402
from evidence import Evidence, Ledger                 # noqa: E402
from questions import QUESTIONS, TODAY                # noqa: E402
from scarcity import Network, simulate, find_loops, h  # noqa: E402
from sentiment import analyze, stance_evidence        # noqa: E402
import run_questions as R                             # noqa: E402

DT = 0.02
NODES = ["security", "access", "food", "purchasing", "nutrition", "survival"]
out: dict = {"generated": TODAY}


def r3(a):
    return [round(float(v), 4) for v in a]


def series(res, names, step=0.1):
    k = int(round(step / DT))
    return {"t": r3(res.t[::k]), **{n: r3(res.series(n)[::k]) for n in names}}


def first_famine(res):
    f, n, s = res.series("food"), res.series("nutrition"), res.series("survival")
    idx = np.where((f <= C.FAMINE_LINE) & (n <= C.FAMINE_LINE) & (s <= C.FAMINE_LINE))[0]
    return float(res.t[idx[0]]) if len(idx) else None


def first_cross(res, node, line=C.FAMINE_LINE):
    idx = np.where(res.series(node) <= line)[0]
    return float(res.t[idx[0]]) if len(idx) else None


# ---------------------------------------------------------------- A. influence function
d = np.round(np.arange(-0.40, 0.4001, 0.01), 3)
out["h_curve"] = {"d": r3(d),
                  "sharp2": r3(h(d, 2.0, np.full_like(d, 0.05), np.full_like(d, 0.05))),
                  "sharp4": r3(h(d, 4.0, np.full_like(d, 0.05), np.full_like(d, 0.05))),
                  "deadband": 0.05}

# ---------------------------------------------------------------- B. kick vs driver, and ordering
rng = np.random.default_rng(0)
net_drv, _ = C.build_sudan(rng, jitter=False, hit={"displacement"})
for nd in net_drv.nodes:
    nd.sigma = 0.0
res_drv = simulate(net_drv, t_end=6.0, dt=DT)

net_kick, _ = C.build_sudan(np.random.default_rng(0), jitter=False, hit=set())
for nd in net_kick.nodes:
    nd.sigma = 0.0
res_kick = simulate(net_kick, t_end=6.0, dt=DT, shock={"food": -0.12})
out["kick_vs_driver"] = {"driver": series(res_drv, ["food", "nutrition", "survival"]),
                         "kick": series(res_kick, ["food", "nutrition", "survival"])}

net_all, _ = C.build_sudan(np.random.default_rng(0), jitter=False,
                           hit={"displacement", "conflict", "aid"})
for nd in net_all.nodes:
    nd.sigma = 0.0
res_all = simulate(net_all, t_end=6.0, dt=DT)
out["all_shocks"] = series(res_all, NODES)
out["order_all"] = {n: first_cross(res_all, n) for n in NODES}
out["order_driver"] = {n: first_cross(res_drv, n) for n in NODES}
out["famine_time_all"] = first_famine(res_all)
out["famine_time_driver"] = first_famine(res_drv)

# ---------------------------------------------------------------- C. adaptive set point demo
net_sp = Network(sharp=2.0)
net_sp.add_node("neighbours", s0=0.5, k=1e-4, eta=0.0, x0=0.30)       # region stays poor
net_sp.add_node("camp", s0=0.5, k=0.5, eta=0.12, x0=0.5)
net_sp.add_edge("neighbours", "camp", c=0.0, alpha=0.6)               # only the NORMAL moves
res_sp = simulate(net_sp, t_end=24.0, dt=0.05)
k = int(round(0.5 / 0.05))
out["setpoint"] = {"t": r3(res_sp.t[::k]),
                   "x": r3(res_sp.series("camp")[::k]),
                   "s": r3(res_sp.S[::k, 1])}

# ---------------------------------------------------------------- D/E. Monte Carlo
rng = np.random.default_rng(42)
N = 1500
times, branches, fan = [], [], []
order = list(C.SHOCKS.values())
for i in range(N):
    hit = {drv for p, drv in order if rng.random() < p}
    net, _ = C.build_sudan(rng, hit=hit)
    res = simulate(net, t_end=6.0, dt=DT, seed=int(rng.integers(1 << 31)))
    t = first_famine(res)
    times.append(t)
    branches.append(sorted(hit))
    if i < 90:
        kk = int(round(0.1 / DT))
        fan.append({"hit": sorted(hit), "famine": t,
                    "survival": r3(res.series("survival")[::kk])})
out["fan"] = {"t": r3(np.arange(0, 6.0001, 0.1)), "runs": fan}

grid = np.round(np.arange(0, 6.0001, 0.25), 2)


def cdf(mask):
    ts = [t for t, m in zip(times, mask) if m]
    n = sum(mask)
    return {"n": n, "p": [round(sum(1 for t in ts if t is not None and t <= g) / n, 4) if n else 0
                          for g in grid]}


everyone = [True] * N
out["horizon"] = {
    "grid": r3(grid),
    "all": cdf(everyone),
    "none": cdf([b == [] for b in branches]),
    "displacement_only": cdf([b == ["displacement"] for b in branches]),
    "conflict_only": cdf([b == ["conflict"] for b in branches]),
    "two_plus": cdf([len(b) >= 2 for b in branches]),
    "close_month": round((date(2026, 12, 1) - date.fromisoformat(TODAY)).days / 30.44, 2),
    "q_close_month": round((date(2027, 1, 1) - date.fromisoformat(TODAY)).days / 30.44, 2),
}
out["branch_share"] = {
    "none": sum(b == [] for b in branches) / N,
    "one": sum(len(b) == 1 for b in branches) / N,
    "two_plus": sum(len(b) >= 2 for b in branches) / N,
}

# ---------------------------------------------------------------- F. lag sensitivity
lag = []
for ls in (0.5, 0.75, 1.0, 1.5):
    rng = np.random.default_rng(7)
    hits15 = hits3 = 0
    M = 600
    for i in range(M):
        hit = {drv for p, drv in order if rng.random() < p}
        net, _ = C.build_sudan(rng, hit=hit, lag_scale=ls)
        res = simulate(net, t_end=3.0, dt=DT, seed=int(rng.integers(1 << 31)))
        t = first_famine(res)
        hits15 += t is not None and t <= 1.5
        hits3 += t is not None and t <= 3.0
    lag.append({"scale": ls, "p15": hits15 / M, "p30": hits3 / M})
out["lag_sensitivity"] = lag

# ---------------------------------------------------------------- G. loops
mean_net, _ = C.build_sudan(np.random.default_rng(0), jitter=False)
out["loops"] = [{"nodes": L.nodes, "kind": L.kind, "gain": round(L.gain, 3), "lag": L.lag}
                for L in sorted(find_loops(mean_net), key=lambda L: -L.gain)]
out["edges"] = [{"src": e.src, "dst": e.dst, "c": e.c, "tau": e.tau, "mech": e.mech}
                for e in mean_net.edges]

# ---------------------------------------------------------------- H/I. ledger + fusion
q = next(x for x in QUESTIONS if x["key"] == "sudan")
prior = BaseRate(q["base"]["k"], q["base"]["n"]).mean
led = Ledger(prior=prior, items=list(q["evidence"]))
news, red = R.load(q["news"]), R.load(q["reddit"])
posts = [{"title": n["title"], "date": n["date"]} for n in news] + red
sres = analyze(posts, q["yes_cues"], q["no_cues"], date.fromisoformat(TODAY))
led.items.append(stance_evidence(sres, "news+Reddit", TODAY))
hz = {h_: out["horizon"]["all"]["p"][list(grid).index(h_)] for h_ in (1.5, 3.0, 4.5)}
led.items.append(Evidence(
    f"Cascade: camp famine conditions {hz[1.5]:.0%} by 1 Dec, {hz[3.0]:.0%} mid-Jan, {hz[4.5]:.0%} by Mar",
    "cascades.py", TODAY, lr=0.6, reliability=0.6))
out["ledger"] = {"prior": prior, "items": [{"what": e.what, "source": e.source, "date": e.date,
                                            "lr": e.lr, "rel": e.reliability,
                                            "shift": round(e.shift, 4)} for e in led.items],
                 "posterior": led.posterior}
out["sentiment"] = {"n": sres["n"], "polarity": sres["polarity"], "stance": sres["stance"],
                    "attention": sres["attention"]}
comm = Estimate(q["community"][0], weight=q["community_weight"], label="community")
ins = Estimate(led.posterior, weight=R.INSIDE_WEIGHT, label="inside")
f09 = forecast_binary(community=comm, inside=ins, calibration_slope=0.9)
f10 = forecast_binary(community=comm, inside=ins, calibration_slope=1.0)
out["fusion"] = {"community": q["community"][0], "n_forecasters": q["community"][1],
                 "w_comm": comm.weight, "inside": led.posterior, "w_inside": ins.weight,
                 "slope09": {"p": f09.p, "lo": f09.lo, "hi": f09.hi},
                 "slope10": {"p": f10.p, "lo": f10.lo, "hi": f10.hi}}

(ROOT / "reports" / "article_data.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print("horizon all:", dict(zip(out["horizon"]["grid"][::2], out["horizon"]["all"]["p"][::2])))
print("branch share:", out["branch_share"])
print("order (all shocks):", out["order_all"], "famine at", out["famine_time_all"])
print("order (displacement):", out["order_driver"], "famine at", out["famine_time_driver"])
print("lag:", lag)
print("ledger posterior", round(led.posterior, 4), "fusion", out["fusion"])
