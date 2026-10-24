"""
run_questions.py - forecast every question in questions.py end to end.

    python run_questions.py            # uses cached data in data/cache (reproducible)
    python run_questions.py --refresh  # re-fetch news and Reddit first

Per question:
  1. base rate                        -> prior
  2. news evidence ledger (LRs)       -> updates the prior        (evidence.py)
  3. Reddit + news stance             -> one capped LR            (sentiment.py)
  4. Route B only: cascade model      -> timing evidence          (cascades.py)
  => P_inside
  5. fuse P_inside with the Metaculus community in log-odds, calibrate (aggregate.py,
     maths unchanged)
Writes reports/forecasts-<date>.md.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import sources as S
from aggregate import BaseRate, Estimate, forecast_binary
from evidence import Evidence, Ledger
from questions import QUESTIONS, TODAY
from sentiment import analyze, stance_evidence

INSIDE_WEIGHT = 1.5
CAL_SLOPE = 0.9


def load(name: str) -> list[dict]:
    f = S.CACHE / f"{name}.json"
    if not f.exists():
        return []
    import json
    return json.loads(f.read_text(encoding="utf-8"))["items"]


def run_one(q: dict, today: date) -> tuple[str, dict]:
    out = []
    b = q["base"]
    prior = b["p"] if "p" in b else BaseRate(b["k"], b["n"]).mean
    led = Ledger(prior=prior, items=list(q["evidence"]))

    # sentiment over news headlines + Reddit posts
    news, red = load(q["news"]), load(q["reddit"])
    posts = [{"title": n["title"], "date": n["date"]} for n in news] + red
    sres = analyze(posts, q["yes_cues"], q["no_cues"], today)
    rres = analyze(red, q["yes_cues"], q["no_cues"], today)
    led.items.append(stance_evidence(sres, "news+Reddit", TODAY))

    cascade_txt = ""
    if q["route"] == "B" and q["key"] == "sudan":
        from cascades import run_sudan
        r = run_sudan(n=800)
        h = r["horizons"]
        led.items.append(Evidence(
            f"Cascade: camp famine conditions {h[1.5]:.0%} by 1 Dec, {h[3.0]:.0%} mid-Jan, {h[4.5]:.0%} by Mar",
            "cascades.py", TODAY, lr=0.6, reliability=0.6))
        cascade_txt = ("\n  Route B cascade (worst-hit camps; misses besieged towns, so used as evidence, not a probability):\n"
                       + "\n".join("    " + L.describe() for L in r["loops"][:3])
                       + f"\n    P(all 3 IPC Famine thresholds crossed) by horizon: "
                       + ", ".join(f"{k:g} mo {v:.0%}" for k, v in h.items())
                       + "\n    -> mortality lags malnutrition ~2 months: famine conditions are a Jan-Mar risk, "
                         "mostly after this question closes.")

    cp, nf = q["community"]
    comm = Estimate(cp, weight=q["community_weight"], label=f"community ({nf})")
    inside = led.estimate(INSIDE_WEIGHT)
    fused = forecast_binary(community=comm, inside=inside, calibration_slope=CAL_SLOPE)

    out.append("=" * 88)
    out.append(f"{q['title']}\n{q['url']}")
    out.append(f"RESOLVES: {q['resolution']}")
    out.append(f"ROUTE {q['route']}   |   community {cp:.1%} ({nf} forecasters)")
    out.append(f"\n  Base rate: {prior:.1%}  - {b['label']}")
    out.append("\n  Evidence ledger:")
    out.append(led.report())
    out.append(f"\n  Sentiment: {sres['n']} items (Reddit {rres['n']}), polarity {sres['polarity']:+.2f}, "
               f"attention x{sres['attention']:.1f} vs prior 3 weeks; stance {sres['stance']['yes']} YES / "
               f"{sres['stance']['no']} NO")
    if cascade_txt:
        out.append(cascade_txt)
    out.append("\n  Fusion (log-odds, precision-weighted) then calibration slope 0.9:")
    out.append(fused.as_report())
    out.append(f"\n  >>> FORECAST {fused.p:.1%}   90% CI {fused.lo:.0%}-{fused.hi:.0%}   "
               f"(community {cp:.1%}, gap {100*(fused.p-cp):+.1f} pts)")
    out.append(f"  Would change my mind: {q['change_mind']}")
    return "\n".join(out), {"key": q["key"], "title": q["title"], "url": q["url"],
                            "p": fused.p, "lo": fused.lo, "hi": fused.hi, "cp": cp,
                            "inside": inside.p, "prior": prior}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if "--refresh" in sys.argv:
        print("refresh: re-run the fetch block in README to update data/cache")
    today = date.fromisoformat(TODAY)
    blocks, rows = [], []
    for q in QUESTIONS:
        txt, row = run_one(q, today)
        print(txt)
        blocks.append(txt)
        rows.append(row)

    print("\n" + "=" * 88 + "\nSUMMARY (pre-registered " + TODAY + ")")
    for r in rows:
        print(f"  {r['p']:6.1%}  (community {r['cp']:5.1%}, inside {r['inside']:5.1%})  {r['title'][:70]}")

    rep = Path(__file__).parent / "reports"
    rep.mkdir(exist_ok=True)
    md = [f"# Forecasts pre-registered {TODAY}\n",
          "| Question | Community | Inside view | **Forecast** | 90% CI |", "|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| [{r['title']}]({r['url']}) | {r['cp']:.1%} | {r['inside']:.1%} | **{r['p']:.1%}** | "
                  f"{r['lo']:.0%}-{r['hi']:.0%} |")
    md.append("\n## Working\n\n```\n" + "\n\n".join(blocks) + "\n```\n")
    md.append("Score at resolution with `aggregate.score_history`.\n")
    f = rep / f"forecasts-{TODAY}.md"
    f.write_text("\n".join(md), encoding="utf-8")
    print(f"\nwrote {f}")


if __name__ == "__main__":
    main()
