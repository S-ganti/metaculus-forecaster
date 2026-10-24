"""
sentiment.py - news / Reddit / X text -> three signals, standard library only.

1. polarity  (-1..+1)  general tone: is coverage upbeat or alarmed? Lexicon scorer with
                       negation handling ("not good" counts as negative). Descriptive.
2. stance    (-1..+1)  does the chatter EXPECT the question to resolve YES or NO?
                       Counted with per-question cue phrases. This is the one that
                       feeds the forecast.
3. attention (ratio)   posts in the last 7 days vs the 7-day average before that.
                       A spike means something is happening; it says nothing about
                       direction. Descriptive.

How stance enters the forecast, and why it is capped hard:
social chatter is a biased sample (loud, partisan, drawn to drama - "they'll demolish
it!" gets posted more than "the injunction holds"). There is no track record here
showing it beats the Metaculus crowd. So stance becomes ONE likelihood ratio in the
evidence ledger, bounded to [1/1.25, 1.25] (it can move odds by at most 25%) at
reliability 0.5. It can nudge a forecast; it can never drive one.
Once you have resolved questions, check whether stance helped (score_history) before
loosening the cap.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from datetime import date, timedelta

from evidence import Evidence

POS = set("""good great win wins winning won gain gains gained lead leads leading ahead
strong stronger surge surges rally rallies hope hopeful progress breakthrough agree agreed
agreement deal success successful support supports boost boosted improve improves improved
recovery relief safe secure peace peaceful stable confident optimistic positive approve
approved approval protect protected victory record best momentum restore restored""".split())

NEG = set("""bad worse worst lose loses losing lost loss losses fall falls falling fell crisis
collapse collapsing threat threatens threatened fear fears warn warns warning risk risks
danger dangerous deadly death deaths killed kill attack attacks war conflict famine
hunger starving starvation fail fails failed failure decline declining drop drops
plunge chaos fraud corrupt corruption scandal blocked block blocks lawsuit sue sued
demolish demolition destroy destroyed angry outrage protest protests panic weak
weaker uncertain uncertainty concern concerns concerned delay delayed sanction""".split())

NEGATORS = {"not", "no", "never", "without", "nor", "n't", "cannot", "wont", "won't",
            "isn't", "aren't", "wasn't", "didn't", "doesn't", "don't"}

_tok = re.compile(r"[a-z']+")


def polarity(text: str) -> float:
    """Lexicon polarity in [-1, 1]; a word right after a negator flips sign."""
    words = _tok.findall(text.lower())
    score = hits = 0
    for i, w in enumerate(words):
        s = 1 if w in POS else -1 if w in NEG else 0
        if not s:
            continue
        if any(x in NEGATORS for x in words[max(0, i - 3):i]):
            s = -s
        score += s
        hits += 1
    return 0.0 if hits == 0 else score / (hits + 2)   # +2 shrinks short texts to 0


def _text(post: dict) -> str:
    return " ".join(str(post.get(k, "")) for k in ("title", "body", "text"))


def stance(posts: list[dict], yes_cues: list[str], no_cues: list[str]) -> dict:
    """Count posts that lean YES / NO by cue phrase (regex, case-insensitive)."""
    ry = [re.compile(c, re.I) for c in yes_cues]
    rn = [re.compile(c, re.I) for c in no_cues]
    yes = no = 0
    for p in posts:
        t = _text(p)
        y = any(r.search(t) for r in ry)
        n = any(r.search(t) for r in rn)
        if y and not n:
            yes += 1
        elif n and not y:
            no += 1
    # shrink toward 0 with 5 pseudo-posts so 2 posts can't produce a strong signal
    net = (yes - no) / (yes + no + 5)
    return {"yes": yes, "no": no, "net": net}


def attention(posts: list[dict], today: date) -> float:
    d = Counter(p.get("date", "") for p in posts)
    last7 = sum(d[(today - timedelta(i)).isoformat()] for i in range(7))
    prev = sum(d[(today - timedelta(i)).isoformat()] for i in range(7, 28)) / 3
    return last7 / prev if prev else float("inf") if last7 else 1.0


def analyze(posts: list[dict], yes_cues: list[str], no_cues: list[str],
            today: date) -> dict:
    pol = [polarity(_text(p)) for p in posts]
    st = stance(posts, yes_cues, no_cues)
    return {"n": len(posts),
            "polarity": sum(pol) / len(pol) if pol else 0.0,
            "stance": st,
            "attention": attention(posts, today)}


def stance_evidence(result: dict, label: str, today: str,
                    k: float = 1.0, max_lr: float = 1.25) -> Evidence:
    """Convert stance into one bounded likelihood ratio for the evidence ledger."""
    cap = math.log(max_lr)
    shift = max(-cap, min(cap, k * result["stance"]["net"]))
    s = result["stance"]
    return Evidence(f"{label} stance: {s['yes']} lean YES / {s['no']} lean NO "
                    f"of {result['n']} posts", "sentiment.py", today,
                    lr=math.exp(shift), reliability=0.5)
