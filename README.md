# Metaculus Forecaster — Scarcity-Equilibrium × Superforecasting

A small toolkit that turns the *Scarcity Equilibrium* framework into a practical Metaculus
forecasting engine: a **statistical core** (reference-class base rates + a cascade-network
Monte Carlo) fused with an **LLM inside view** (mechanism reasoning + live web evidence),
combined in log-odds and calibrated against overconfidence.

## Files
| File | What it is |
|---|---|
| `METHODOLOGY.md` | The reusable protocol — the "brain." Read this first. |
| `QUESTION_TEMPLATE.md` | One-page worksheet to fill per question. |
| `aggregate.py` | Fusion engine: base rates, survival/hazard time-adjust, Beta intervals, log-odds pooling, calibration, Brier/log scoring. |
| `scarcity.py` | The framework as a runnable delay-diff simulator: dead-band influence, adaptive set points, loop analysis, Monte Carlo → probability. |
| `forecast.py` | Orchestrator + a real worked demo (US-recession, 12-mo). |
| `EXPLAINER.md` | Scarcity Equilibrium in plain English, using the Sudan model. |
| `sources.py` | Free public data: Google News RSS, Reddit (via PullPush archive), FRED, GDELT. Cached in `data/cache/`. |
| `sentiment.py` | Polarity, YES/NO stance and attention from news + Reddit text. Stance enters as one likelihood ratio capped at x1.25. |
| `evidence.py` | Evidence ledger: each news fact is a likelihood ratio that updates the base rate -> inside view. |
| `cascades.py` | Route B model for the Sudan famine question (driver nodes, timing by horizon). |
| `questions.py` | The 5 questions forecast on 2026-10-16: rules, community, base rate, evidence with sources and dates. |
| `run_questions.py` | Runs all questions end to end and writes `reports/forecasts-<date>.md`. |

## Run
```
python run_questions.py       # the 5 live forecasts (uses cached data)
python forecast.py            # recession worked demo
python cascades.py            # Sudan famine cascade on its own
python aggregate.py           # fusion + scoring self-test
python scarcity.py            # simulator self-test (burnout cascade)
```

## Data sources (status 2026-10-16)
| Source | Status |
|---|---|
| Google News RSS, FRED | work from Python |
| Reddit | reddit.com blocks this network; PullPush public archive works (lags ~3 days) |
| GDELT | rate-limited (HTTP 429); optional |
| X / Twitter | needs a signed-in account. Sign into X in BrowserOS neo yourself, then posts can be collected in the browser and loaded with `sources.load_posts()` |
| Metaculus API | needs a Metaculus account token; community numbers were read from the public pages instead |
| Prediction markets | Polymarket timed out, Kalshi rendered empty; not used |
Requires Python 3 + numpy + scipy (both already installed here).

## The pipeline (see METHODOLOGY.md for the full version)
1. **Classify** — exact resolution criterion; Route A (base-rate) or B (cascade network)?
2. **Outside view** → `BaseRate(k, n)` → `survival_prob` to the horizon → `P_base`.
3. **Community prior** → read Metaculus crowd → `P_comm` (weight it heavily).
4. **Inside view** → decomposition (A) or `scarcity` network + `monte_carlo` (B) → `P_inside`.
5. **Evidence sweep** (web) → update each estimate; note source dates.
6. **Fuse → calibrate** → `forecast_binary(...)` → final `p` + 90% CI.
7. **Pre-register** the number + date; score with `score_history` at resolution.

## Forecasting a new question
- **Route A (most questions):** fill `QUESTION_TEMPLATE.md`, then in a Python shell:
  ```python
  from aggregate import Estimate, BaseRate, survival_prob, forecast_binary
  base = Estimate(survival_prob(0.10, 1.0), weight=BaseRate(5,50).precision(), label="base")
  comm = Estimate(0.30, weight=4, label="community")
  inside = Estimate(0.45, weight=1.2, label="inside")
  print(forecast_binary(base=base, community=comm, inside=inside, calibration_slope=0.9).as_report())
  ```
- **Route B (cascades):** copy `build_recession_net` in `forecast.py` as a pattern —
  define nodes/edges for your domains, map the outcome to a node-threshold condition,
  `monte_carlo(...)` for `P_inside`, then fuse as above.

## The one principle
The LLM proposes (reference classes, network structure, live evidence); the statistics
dispose (coherent log-odds fusion, propagated uncertainty, calibration). No single method
owns the forecast — and a mis-specified input can't blow it up, because it's fused at low
weight. Pre-register; score; refit the calibration slope. That loop is the whole game.
