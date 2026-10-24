# Forecast Worksheet — <question short name>

> Copy this file per question. Fill top-to-bottom. Don't skip the base rate.
> Pre-register the final number + date BEFORE it resolves (§10 of METHODOLOGY.md).

## 1. The question, exactly
- **Text:**
- **Resolution source / criterion:**
- **Resolution date:**
- **Edge cases** (announces vs ships, etc.):
- **Type:** binary / date-conditioned / numeric range
- **Route:** A (base-rate/decomposition) or B (Scarcity network) — 4-part test:
  coupled domains? propagation? feedback loop? estimable lags? →

## 2. Outside view  → P_base
- **Reference class** (narrowest with ≥5–10 cases):
- **k events / n cases:**  k = __ , n = __   → `BaseRate(k, n)` mean = __
- **Horizon** in base-rate periods: __   → `survival_prob(rate, n)` = __
- **P_base = __**  (weight __, from Beta band width)

## 3. Community prior  → P_comm
- **Community prediction:** __  (as of date __, # predictors __)
- **Do I have a specific reason to deviate?** (name it or stay close):
- **P_comm = __**  (weight __, 3–6 if mature)

## 4. Inside view  → P_inside
### Route A (decomposition)
- Necessary conditions & their probabilities:  p1·p2·… = __
- Dominant driver + current evidence:
- Outside-view-of-the-inside-view (do such plans land on time?):

### Route B (network) — see `forecast.py` for the code pattern
- Nodes (proxy, bounds):
- Edges (src→dst, sign, mag, lag, mechanism):
- Loops (sign / activation gain / lag):
- Outcome as node condition:
- Monte Carlo P_inside = __  90% CI [__, __]  (n runs __)

- **P_inside = __**  (weight __)

## 5. Evidence sweep (web)
| Fact | Source | Date | Moves which estimate, which way |
|---|---|---|---|
| | | | |
- Explicit disconfirming search done? Y/N — strongest counter-fact:

## 6. Fuse → calibrate  → FINAL
- Fused (log-odds, weights above): __
- Calibration slope applied: __ (default 0.9)
- community_pull: __ (0 if strong edge; 0.25 if modest)
- **FINAL p = __   90% CI [__, __]**

## 7. Pre-registration
- **What would change my mind** (the fact that would move me >10pts):
- **Non-cascade check** (could the right answer be "nothing happens"?):
- Logged on (date): __  → outcome (fill at resolution): __  → Brier/log: __
