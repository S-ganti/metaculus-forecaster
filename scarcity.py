"""
scarcity.py — the Scarcity Equilibrium framework as a runnable simulator.

Implements the corrected mathematics from scarcity_equilibrium_framework.md:
  * state equation with self-restoration + delayed network influence + noise   (sec 4.2)
  * dead-band influence function h(d), continuous & bounded                     (sec 4.3)
  * adaptive set points with anchor + cross-domain drift (j != i enforced)      (sec 4.4)
  * closed-loop enumeration with sign / gain / lag                              (sec 4.6)

The point of wiring it up (rather than reasoning by hand) is the Monte Carlo layer:
run the cascade a few hundred times with noise and parameter jitter, and the fraction
of runs in which the target domain breaches its threshold by the horizon IS your
inside-view probability P_inside for a cascade-type Metaculus question -- with a
confidence interval that honestly reflects parameter uncertainty.

Integration: fixed-step Euler-Maruyama with a delay history buffer. Adequate for the
5-10 node networks this framework targets; for stiff or long-delay systems, shrink dt.

Requires numpy only.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np


# --------------------------------------------------------------------------- #
#  Model objects
# --------------------------------------------------------------------------- #
@dataclass
class Node:
    """A domain. x in [0,1]: 0 = severe scarcity, 0.5 = baseline, 1 = severe excess."""
    name: str
    s0: float = 0.5          # long-run anchor set point  (s_i^0)
    k: float = 0.4           # self-restoration rate      (k_i > 0)
    delta: float = 0.05      # scarcity dead-band         (δ_i)
    eps: float = 0.05        # excess dead-band           (ε_i)
    eta: float = 0.02        # set-point adaptation rate  (η_i, usually << k)
    sigma: float = 0.0       # noise intensity            (σ_i >= 0)
    x0: Optional[float] = None   # initial state (defaults to s0)
    s_init: Optional[float] = None  # initial set point (defaults to s0)


@dataclass
class Edge:
    """Directed influence  src -> dst  (j -> i)."""
    src: str
    dst: str
    c: float                 # signed coupling  c_ji  (+ spillover, - competition)
    tau: float = 0.0         # lag τ_ji (same time units as the sim horizon)
    alpha: float = 0.0       # set-point cross-adaptation α_ji (+ aspiration, - substitution)
    mech: str = ""           # one-line mechanism note (documentation only)


@dataclass
class Network:
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    sharp: float = 3.0       # global threshold sharpness (α "sharpness" in the paper)

    def index(self) -> dict[str, int]:
        return {n.name: i for i, n in enumerate(self.nodes)}

    def add_node(self, *a, **kw) -> "Network":
        self.nodes.append(Node(*a, **kw)); return self

    def add_edge(self, *a, **kw) -> "Network":
        self.edges.append(Edge(*a, **kw)); return self


# --------------------------------------------------------------------------- #
#  Influence function (sec 4.3) and its derivative (for loop gains, sec 4.6)
# --------------------------------------------------------------------------- #
def h(d: np.ndarray, sharp: float, delta: np.ndarray, eps: np.ndarray) -> np.ndarray:
    """Dead-band, saturating influence. Continuous at ±threshold, bounded in (-1,1)."""
    out = np.zeros_like(d)
    hi = d > eps
    lo = d < -delta
    out[hi] = np.tanh(sharp * (d[hi] - eps[hi]))
    out[lo] = np.tanh(sharp * (d[lo] + delta[lo]))
    return out


def h_prime(d: float, sharp: float, delta: float, eps: float) -> float:
    """d/dd of h in the active region (0 inside the dead-band)."""
    if d > eps:
        return sharp * (1.0 - math.tanh(sharp * (d - eps)) ** 2)
    if d < -delta:
        return sharp * (1.0 - math.tanh(sharp * (d + delta)) ** 2)
    return 0.0


# --------------------------------------------------------------------------- #
#  Simulation
# --------------------------------------------------------------------------- #
@dataclass
class SimResult:
    t: np.ndarray            # (steps+1,)
    X: np.ndarray            # (steps+1, n) states
    S: np.ndarray            # (steps+1, n) set points
    names: list[str]

    def series(self, name: str) -> np.ndarray:
        return self.X[:, self.names.index(name)]

    def time_to_threshold(self, name: str, level: float, below: bool = True) -> Optional[float]:
        """First time the domain crosses `level` (below=True for scarcity breaches)."""
        x = self.series(name)
        hits = np.where(x <= level)[0] if below else np.where(x >= level)[0]
        return float(self.t[hits[0]]) if len(hits) else None

    def breach_order(self, level: float = 0.3, below: bool = True) -> list[tuple[str, float]]:
        """Which domains breach `level`, in the order they do so (predicts output #1)."""
        times = []
        for nm in self.names:
            tt = self.time_to_threshold(nm, level, below)
            if tt is not None:
                times.append((nm, tt))
        return sorted(times, key=lambda z: z[1])


def simulate(
    net: Network,
    t_end: float,
    dt: float = 0.1,
    shock: Optional[dict[str, float]] = None,
    seed: Optional[int] = None,
) -> SimResult:
    """Integrate the network to t_end.

    shock : {node_name: delta_x} added to the initial state (e.g. {"tasks": +0.3}).
    seed  : RNG seed for the noise term (only matters if any node has sigma > 0).
    """
    rng = np.random.default_rng(seed)
    idx = net.index()
    n = len(net.nodes)

    s0 = np.array([nd.s0 for nd in net.nodes])
    kk = np.array([nd.k for nd in net.nodes])
    delta = np.array([nd.delta for nd in net.nodes])
    eps = np.array([nd.eps for nd in net.nodes])
    eta = np.array([nd.eta for nd in net.nodes])
    sig = np.array([nd.sigma for nd in net.nodes])

    x = np.array([nd.x0 if nd.x0 is not None else nd.s0 for nd in net.nodes], dtype=float)
    s = np.array([nd.s_init if nd.s_init is not None else nd.s0 for nd in net.nodes], dtype=float)
    # Pre-shock deviation = the DDE history for t < 0. Before a lag elapses, downstream
    # nodes must see the baseline, not the shock, or the delay is a no-op (the shock
    # would "arrive" instantly). This is the constant-history assumption for t<0.
    d_prehist = x - s
    if shock:
        for nm, dv in shock.items():
            x[idx[nm]] = float(np.clip(x[idx[nm]] + dv, 0.0, 1.0))

    # Edge arrays
    src = np.array([idx[e.src] for e in net.edges], dtype=int)
    dst = np.array([idx[e.dst] for e in net.edges], dtype=int)
    cc = np.array([e.c for e in net.edges])
    aa = np.array([e.alpha for e in net.edges])
    lag_steps = np.array([int(round(e.tau / dt)) for e in net.edges], dtype=int)

    steps = int(round(t_end / dt))
    X = np.empty((steps + 1, n)); S = np.empty((steps + 1, n))
    Dhist = np.empty((steps + 1, n))
    X[0], S[0] = x, s
    Dhist[0] = x - s

    sqrt_dt = math.sqrt(dt)
    for step in range(steps):
        d_now = Dhist[step]

        # --- network influence with per-edge delays (uses SOURCE node thresholds) ---
        net_infl = np.zeros(n)
        if len(net.edges):
            back = step - lag_steps
            valid = back >= 0                                    # lag has elapsed?
            rows = np.clip(back, 0, None)
            d_src_delayed = np.where(valid, Dhist[rows, src], d_prehist[src])
            hv = h(d_src_delayed, net.sharp, delta[src], eps[src])
            np.add.at(net_infl, dst, cc * hv)

        drift = -kk * (x - s) + net_infl
        noise = sig * sqrt_dt * rng.standard_normal(n) if np.any(sig > 0) else 0.0
        x = np.clip(x + drift * dt + noise, 0.0, 1.0)

        # --- adaptive set points (cross term uses CURRENT deviation, j != i) ---
        cross = np.zeros(n)
        if len(net.edges):
            np.add.at(cross, dst, aa * d_now[src])
        s = s + eta * ((s0 - s) + cross) * dt
        s = np.clip(s, 0.0, 1.0)

        X[step + 1], S[step + 1] = x, s
        Dhist[step + 1] = x - s

    t = np.arange(steps + 1) * dt
    return SimResult(t=t, X=X, S=S, names=[nd.name for nd in net.nodes])


# --------------------------------------------------------------------------- #
#  Loop analysis (sec 4.6)
# --------------------------------------------------------------------------- #
@dataclass
class Loop:
    nodes: list[str]
    sign: int                # +1 reinforcing, -1 balancing
    gain: float              # linearized loop gain (>1 + reinforcing => runaway risk)
    lag: float               # total lag around the loop
    edges: list[Edge]

    @property
    def kind(self) -> str:
        return "reinforcing" if self.sign > 0 else "balancing"

    def describe(self) -> str:
        # `gain` is the ACTIVATION gain: h' evaluated right at each node's threshold,
        # where sensitivity peaks. It is an upper bound on sustained loop gain (tanh
        # saturates as nodes move deeper, pulling h' back toward 0). Read it as
        # "how hard this loop can bite the moment it switches on", not a steady figure.
        chain = " -> ".join(self.nodes + [self.nodes[0]])
        risk = ""
        if self.sign > 0 and self.gain >= 1.0:
            risk = "  <== TIPPING RISK (reinforcing, activation gain>=1)"
        elif self.sign > 0:
            risk = "  (reinforcing but sub-unity even at activation: slow drift)"
        return f"{chain} | {self.kind}, act.gain={self.gain:.2f}, lag={self.lag:g}{risk}"


def find_loops(net: Network, d_star: Optional[dict[str, float]] = None,
               max_len: int = 8) -> list[Loop]:
    """Enumerate simple directed cycles and score each (sign, gain, lag).

    d_star : deviation at which to linearize each node for the gain (h'(d*)). Defaults
             to just past each node's threshold, i.e. the gain right as the loop activates
             -- the relevant number for tipping-point risk.
    """
    idx = net.index()
    names = [n.name for n in net.nodes]
    # adjacency: src_name -> list of edges
    adj: dict[str, list[Edge]] = {nm: [] for nm in names}
    for e in net.edges:
        adj[e.src].append(e)

    node_by_name = {n.name: n for n in net.nodes}

    def dstar(nm: str) -> float:
        if d_star and nm in d_star:
            return d_star[nm]
        return node_by_name[nm].eps + 1e-3  # just inside the active region

    loops: list[Loop] = []
    seen: set[tuple] = set()

    def dfs(start: str, current: str, path_nodes: list[str], path_edges: list[Edge]):
        if len(path_nodes) > max_len:
            return
        for e in adj[current]:
            if e.dst == start and len(path_nodes) >= 1:
                cyc = path_nodes[:]
                key = _canonical(cyc)
                if key not in seen:
                    seen.add(key)
                    loops.append(_score_loop(cyc, path_edges + [e], net, dstar))
            elif e.dst not in path_nodes:
                dfs(start, e.dst, path_nodes + [e.dst], path_edges + [e])

    for nm in names:
        dfs(nm, nm, [nm], [])
    return loops


def _canonical(cycle: list[str]) -> tuple:
    """Rotation-invariant key so each simple cycle is counted once."""
    m = min(range(len(cycle)), key=lambda i: cycle[i])
    rot = tuple(cycle[m:] + cycle[:m])
    return rot


def _score_loop(cycle: list[str], edges: list[Edge], net: Network,
                dstar: Callable[[str], float]) -> Loop:
    node_by_name = {n.name: n for n in net.nodes}
    sign = 1
    gain = 1.0
    lag = 0.0
    for e in edges:
        sign *= (1 if e.c >= 0 else -1)
        nd = node_by_name[e.src]
        gain *= abs(e.c) * abs(h_prime(dstar(e.src), net.sharp, nd.delta, nd.eps))
        lag += e.tau
    return Loop(nodes=cycle, sign=sign, gain=gain, lag=lag, edges=edges)


# --------------------------------------------------------------------------- #
#  Monte Carlo -> probability (the bridge to aggregate.py)
# --------------------------------------------------------------------------- #
@dataclass
class MCResult:
    p: float                 # P(condition true) across runs
    lo: float                # 90% CI (Wilson) low
    hi: float                # 90% CI high
    n: int
    mean_time: Optional[float]  # mean time-to-condition among runs that hit it
    detail: dict

    def as_report(self) -> str:
        mt = f"{self.mean_time:.2f}" if self.mean_time is not None else "n/a"
        return (f"P(condition) = {self.p:.1%}  90% CI [{self.lo:.1%}, {self.hi:.1%}]  "
                f"(n={self.n}, mean time-to-event={mt})")


def monte_carlo(
    build: Callable[[np.random.Generator], tuple[Network, dict]],
    condition: Callable[[SimResult], bool],
    n: int = 400,
    t_end: float = 30.0,
    dt: float = 0.1,
    time_of: Optional[Callable[[SimResult], Optional[float]]] = None,
    seed: int = 0,
) -> MCResult:
    """Estimate P(condition) over an ensemble with parameter + noise variation.

    build(rng)   -> (Network, shock_dict). Sample uncertain c/tau/alpha/sigma HERE so
                    each run reflects a plausible parameterization (see METHODOLOGY.md,
                    'sensitivity as probability').
    condition(r) -> bool, the event you're forecasting (e.g. target node breaches 0.3).
    time_of(r)   -> optional float, time the event occurred (for mean-time diagnostics).
    """
    rng = np.random.default_rng(seed)
    hits = 0
    times: list[float] = []
    for i in range(n):
        net, shock = build(rng)
        r = simulate(net, t_end=t_end, dt=dt, shock=shock, seed=int(rng.integers(1 << 31)))
        if condition(r):
            hits += 1
            if time_of is not None:
                tt = time_of(r)
                if tt is not None:
                    times.append(tt)
    p = hits / n
    lo, hi = _wilson(hits, n, z=1.645)
    return MCResult(
        p=p, lo=lo, hi=hi, n=n,
        mean_time=(float(np.mean(times)) if times else None),
        detail={"hits": hits},
    )


def _wilson(k: int, n: int, z: float = 1.645) -> tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    phat = k / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = (z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n))) / denom
    return max(0.0, center - half), min(1.0, center + half)


# --------------------------------------------------------------------------- #
#  Self-test: the burnout example (sec 10) -- validates signs & ordering
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    net = Network(sharp=3.0)
    for nm in ["sleep", "focus", "tasks", "errors", "mood"]:
        net.add_node(nm, s0=0.5, k=0.4, delta=0.04, eps=0.04, eta=0.02)
    net.add_edge("tasks", "sleep",  c=-0.5, tau=1, mech="more tasks -> less sleep")
    net.add_edge("sleep", "focus",  c=+0.6, tau=1, mech="less sleep -> less focus")
    net.add_edge("focus", "errors", c=-0.5, tau=1, mech="less focus -> more errors")
    net.add_edge("errors", "tasks", c=+0.4, tau=3, mech="errors -> rework -> tasks")
    net.add_edge("errors", "mood",  c=-0.4, tau=2, mech="errors -> worse mood")
    net.add_edge("mood",  "focus",  c=+0.3, tau=1, mech="worse mood -> less focus")

    print("LOOPS")
    for lp in sorted(find_loops(net), key=lambda L: -L.gain):
        print("  " + lp.describe())

    res = simulate(net, t_end=30, dt=0.1, shock={"tasks": +0.35})
    print("\nBREACH ORDER (level<=0.42 scarcity):")
    for nm, tt in res.breach_order(level=0.42, below=True):
        print(f"  {nm:<8} breaches at t={tt:.1f} d")

    print("\nMONTE CARLO: P(sleep falls below 0.35 within 21 days | task shock)")

    def build(rng):
        nz = Network(sharp=3.0)
        for nm in ["sleep", "focus", "tasks", "errors", "mood"]:
            nz.add_node(nm, s0=0.5, k=0.4, delta=0.04, eps=0.04, eta=0.02, sigma=0.02)
        # jitter couplings +/-30%
        j = lambda v: v * (1 + 0.30 * (rng.random() * 2 - 1))
        nz.add_edge("tasks", "sleep",  c=j(-0.5), tau=1)
        nz.add_edge("sleep", "focus",  c=j(+0.6), tau=1)
        nz.add_edge("focus", "errors", c=j(-0.5), tau=1)
        nz.add_edge("errors", "tasks", c=j(+0.4), tau=3)
        nz.add_edge("errors", "mood",  c=j(-0.4), tau=2)
        nz.add_edge("mood",  "focus",  c=j(+0.3), tau=1)
        return nz, {"tasks": +0.35}

    mc = monte_carlo(
        build,
        condition=lambda r: r.time_to_threshold("sleep", 0.35, below=True) is not None
                            and r.time_to_threshold("sleep", 0.35) <= 21,
        time_of=lambda r: r.time_to_threshold("sleep", 0.35, below=True),
        n=300, t_end=30, dt=0.1,
    )
    print("  " + mc.as_report())
