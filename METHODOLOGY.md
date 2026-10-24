# The Combined Model — Scarcity-Equilibrium × Superforecasting for Metaculus

*Two engines, one number.* A **statistical outside view** (reference-class base rates +,
for cascade questions, the Scarcity Equilibrium network simulator) and an **LLM inside
view** (mechanism reasoning + live web evidence), fused in log-odds and calibrated
against overconfidence. No single method carries a forecast; the pipeline does.

This file is the protocol. The math lives in `aggregate.py` (fusion/calibration) and
`scarcity.py` (the network simulator). `forecast.py` runs a question end-to-end.

---

## 0. Why this shape

Metaculus is scored by a **log score** (proper scoring rule): you are rewarded for being
*calibrated*, not for being bold. The two things that move a track record most are
(1) starting from the right base rate and (2) not being overconfident. The Scarcity
Equilibrium framework is a specialist tool — it is excellent for the *subset* of
questions about shortages/excesses propagating through coupled domains, and irrelevant
for most others. So it is wired in as **one inside-view route**, not the whole model.

The design principle: **the LLM proposes, the statistics dispose.** I (Claude) do the
things models are good at — picking reference classes, reading current evidence, writing
down mechanisms and network structure. The code does the things humans are bad at —
combining several probabilities coherently, propagating uncertainty, and resisting the
pull to 0 or 1.

---

## 1. The pipeline

```
  (1) Parse & classify          →  binary? date-conditioned? cascade-shaped?
  (2) Outside view              →  reference class → base rate → time-adjust      [P_base]
  (3) Community prior           →  read the Metaculus community prediction        [P_comm]
  (4) Inside view               →  Route A: decomposition / evidence              [P_inside]
                                   Route B: Scarcity network + Monte Carlo
  (5) Evidence sweep            →  web search; update each estimate
  (6) Fuse → calibrate          →  log-odds precision-weighted pool + anti-overconf
  (7) Record & pre-register     →  final p + CI, "what would change my mind", score later
```

Each numbered step maps to a function or section below.

---

## 2. Step 1 — Classify the question (and decide if the network earns its keep)

Write down the **exact resolution criterion** first. Most bad forecasts are answers to a
slightly different question than the one that will be scored. Note the resolution date,
the source of truth, and any edge cases ("resolves YES if X *announces*" ≠ "if X *ships*").

Then route the inside view. Use the **Scarcity Equilibrium network (Route B)** only when
the question has *all four* of these; otherwise use Route A.

| Test | Route B (network) if… |
|---|---|
| **Coupled domains** | the outcome depends on ≥3 measurable domains that influence each other |
| **Propagation** | the mechanism of interest is a shock *spreading* (shortage→shortage, panic→failure) |
| **Feedback** | there is at least one plausible reinforcing or balancing loop |
| **Lag** | timing matters and effects arrive with delays you can estimate |

Canonical Route-B questions: banking/liquidity contagion, drug/supply-chain shortage
cascades, grid stress under a heat dome, fertility/housing/time cascades, refugee/food/
price spirals. Canonical Route-A questions: "will X win the election", "will model Y beat
benchmark Z by date", "will this treaty be signed" — single-shot events with no cascade.

> If in doubt, run Route A. A network you can't parameterize is worse than an honest base
> rate. The framework itself warns: an unidentifiable model is a guess with extra steps.

---

## 3. Step 2 — Outside view (P_base)

1. **Pick a reference class.** The set of past situations "like this one." Prefer the
   narrowest class you still have ≥5–10 data points for. Write down *k events / n cases*.
2. **Base rate = k/n**, but carry the uncertainty: `aggregate.BaseRate(k, n)` gives the
   Beta-posterior mean and a 90% band. Small n ⇒ wide band ⇒ the fuser trusts it less
   (its `.precision()` is the weight).
3. **Time-adjust** for "will X happen *by* date D" questions. A base rate is usually a
   *per-period hazard*; convert to a cumulative probability over the horizon with
   `aggregate.survival_prob(rate, n_periods)`. Getting the horizon right is often a bigger
   correction than getting the rate right.
4. **Status-quo anchor.** Most things that can be phrased as "will something change" don't,
   within a typical Metaculus horizon. When unsure, the base rate for *change* is low.

The base rate is where you *start*, never where you stop. But a forecast that never
touches one is unmoored.

---

## 4. Step 3 — The community prior (P_comm)

The Metaculus community prediction is a **strong, hard-to-beat prior** — an aggregate of
many forecasters with a good track record. Treat it as a Bayesian prior, not as the
answer and not as noise.

- **Weight it heavily** in the fusion (precision 3–6) when the question has been open a
  while and has many predictors; less for brand-new or thinly-traded questions.
- **You are allowed to deviate** only when you can name a *specific* reason the crowd is
  wrong here: fresh evidence it hasn't priced, a reference class it's ignoring, or a
  mechanism (often a Route-B cascade) it's under-weighting. Write that reason down. If you
  can't, your number should sit close to the community.
- After fusing, an optional `toward_community(p, p_comm, pull=0.15–0.35)` shrink protects
  the score when your edge is real but modest. Default pull 0.25 unless you have a strong,
  specific edge.

> Beating the community is *supposed* to be hard. A model that always agrees adds nothing;
> a model that always disagrees is overconfident. Deviate on evidence, not on vibes.

---

## 5. Step 4B — The Scarcity Equilibrium network in practice

When Route B fires, build the model in `scarcity.py` and let Monte Carlo produce P_inside.

1. **Nodes (5–10).** One measurable proxy per domain. `x∈[0,1]`: 0 = severe scarcity,
   0.5 = baseline, 1 = severe excess. Define what the bounds mean in natural units.
2. **Edges.** For each ordered pair, the sign of `c` (does *j*'s excess raise or lower
   *i*?), a magnitude (L/M/H → ≈0.2/0.4/0.7), and a lag `τ` from domain knowledge.
   `c>0` = spillover/propagation; `c<0` = competition/zero-sum.
3. **Map the outcome to a node condition.** The Metaculus question becomes a statement
   like "domain *T* breaches x≤0.3 before the horizon." That is the event you count.
4. **Run Monte Carlo, not a single path.** This is the crucial move. The framework's #1
   failure mode is parameter unidentifiability — you *don't* know `c`, `τ`, `α` exactly.
   So sample them from plausible ranges (and add node noise `σ`) on every run; the
   fraction of runs meeting the condition **is P_inside**, and its Wilson interval is an
   honest uncertainty band. *Sensitivity analysis and probability become the same
   computation.* (`scarcity.monte_carlo`.)
5. **Read the loops first** (`find_loops`). A reinforcing loop with activation gain ≥ 1
   and short lag is the tell for a fast cascade; long lag ⇒ "looks fine, then doesn't";
   balancing loops ⇒ the system likely absorbs the shock (a valuable *non-cascade*
   prediction — see §9).

Route B outputs more than a probability: an **order** of breakage, a **time-to-effect**,
and a **magnitude** per domain. On Metaculus these feed sub-questions and conditional
pairs, and they are what you score yourself against later (framework §6).

---

## 6. Step 4A — Inside view without the network

For the majority of questions:
- **Decompose.** Break the event into a chain of necessary conditions and estimate each
  (`P = p1·p2·…`), or a Fermi estimate for quantities. Independent-ish factors multiply.
- **Find the dominant driver** and reason explicitly about it with current evidence.
- **Take the outside view of the inside view:** how often do plans/timelines/announcements
  of this kind actually land on schedule? (Almost always: later and less than claimed.)

Produce a single `P_inside` with an honest confidence (→ its fusion weight).

---

## 7. Step 5 — Evidence sweep (web search protocol)

Search *after* you've written down the base rate, so the base rate anchors you and the
evidence updates you — not the reverse (avoids anchoring on the loudest recent headline).

- Query for: the resolution source directly; the latest data point on each driver / node
  proxy; recent expert base-rate-style statements; and explicitly for **disconfirming**
  evidence ("why X won't happen by D").
- **Weight sources** by track record and distance from the event (primary/official >
  domain expert > generalist media > social). Prefer numbers over narratives.
- **Recency-weight**, but beware recency *bias*: one fresh datapoint rarely overturns a
  well-populated reference class. Move each estimate a *bounded* amount per new fact.
- Note the date of every load-bearing fact; on Metaculus, staleness is a silent killer.

Then update `P_base`, `P_comm` (has it moved?), and `P_inside` accordingly.

---

## 8. Step 6 — Fuse and calibrate (the combined number)

1. **Fuse in log-odds**, precision-weighted (`aggregate.forecast_binary`). Log-odds is the
   right space: it treats "0.01→0.02" and "0.50→0.66" as the same one-bit update, and it
   never lets a single confident source pin the pool at 0 or 1.
2. **Weights = precision** (1/variance in log-odds). Guide:

   | Source | Weight |
   |---|---|
   | Community prediction (mature, many predictors) | 3 – 6 |
   | Solid base rate (large reference class) | 2 – 4 |
   | Inside view / Monte Carlo with real evidence | 1 – 2 |
   | Speculative mechanism or thin data | 0.3 – 0.8 |

3. **Correlation caveat.** The fuser assumes inputs are independent observations of the
   truth. If your base rate and your inside view lean on the *same* study, they aren't —
   **down-weight one**, don't let the agreement fool the pool into false confidence.
   (This is why we do *not* extremize our own three inputs; `extremize()` is only for
   genuinely independent forecasters.)
4. **Calibrate against overconfidence.** Apply `calibrate(p, slope=0.9)` by default — a
   mild pull toward 0.5 that fixes the near-universal human/LLM failure of being too sure.
   Replace 0.9 with your *fitted* slope once you have ≥30 resolved questions
   (`score_history` builds the calibration table you fit from).
5. **Widen for long horizons and thin models.** The further out and the flimsier the
   parameters, the closer to 50% (or to the community) you belong. `community_pull`
   encodes this.

The output is a **point probability plus a 90% CI**. Submit the point; the CI tells you
how much a new fact should be allowed to move you.

---

## 9. Failure modes (framework §8), mapped to forecasting discipline

| Framework failure mode | How it bites a forecast | Guardrail |
|---|---|---|
| Parameter unidentifiability | fake precision from guessed `c`, `τ` | Monte Carlo the ranges; report the CI, not a point |
| Descriptive in deep scarcity | linearized gain misleads when many nodes saturate | simulate; don't trust the rules-of-thumb table alone |
| Omitted-node risk | the real driver is outside your 5 nodes | always ask "what's outside the boundary?"; keep P off 0/1 |
| Set-point vs objective confusion | "expectations rose" read as "conditions worsened" | separate perceived vs objective; survey data if available |
| Loops as artifacts of a common driver | A,B co-move via hidden Z, won't respond to intervention | prefer lagged/causal evidence over raw correlation |
| **Post-hoc fitting ≠ validation** | a model tuned to explain the past predicts nothing | **pre-register** the number + date *before* resolution |

The single most important line: **a non-cascade prediction that comes true (you said the
system absorbs the shock, and it did) is as valuable as a cascade you called.** Look for
chances to predict *nothing happens* — the crowd systematically over-forecasts drama.

---

## 10. Step 7 — Record, score, and improve

- Log every forecast as `(question, p, resolution_date)` **before** it resolves.
- When it resolves, append the outcome and run `aggregate.score_history` over your log:
  mean Brier, mean log score, and a **calibration table** (predicted vs realized by
  decile). If your 70% bucket resolves YES 55% of the time, you're overconfident — lower
  your `calibrate` slope.
- For Route-B questions, also score the framework's five outputs (order, timing,
  magnitude, cross-section, policy elasticity). Getting 3/5 *pre-registered* right is
  strong evidence; reproducing history after the fact is not.

Calibration is a skill with a gradient. This loop is how the model gets better than me.

---

## 11. The LLM's job, made explicit (the prompts I run each time)

For each question, I (Claude) fill these in — this is where "LLM + web + info access"
enters the statistical machine:

- **Reference class:** "What are the last N situations most like this, and how did they
  resolve?" → feeds `BaseRate(k, n)`.
- **Network structure (Route B only):** "What are the 5–8 domains, the signed edges with
  lags, and the outcome-as-node-condition?" → feeds `scarcity.Network`.
- **Evidence:** targeted web searches per §7 → updates each estimate + source dates.
- **Weights & correlation:** "How independent are these three inputs; who do I trust?" →
  sets fusion weights.
- **Sanity + red team:** "What's the strongest case I'm wrong? What node did I omit?" →
  bounds the final away from 0/1 and sets `community_pull`.

The numbers are the code's. The judgments above are mine. The forecast is the handshake.

---

## 12. One-screen checklist

```
[ ] Exact resolution criterion + date written down
[ ] Route A or B decided (4-part test)
[ ] Reference class → BaseRate(k,n) → time-adjusted to the horizon
[ ] Community prediction read + its weight set
[ ] Inside view: decomposition (A) or network+MonteCarlo (B) → P_inside + CI
[ ] Web sweep incl. explicit disconfirming search; source dates noted
[ ] Fuse (log-odds, precision weights, correlation-adjusted)
[ ] Calibrate (slope 0.9 default) + community_pull if edge is modest
[ ] Final p + 90% CI + "what would change my mind"
[ ] Logged for scoring BEFORE resolution
```
