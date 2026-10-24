# Scarcity Equilibrium, in plain English

## The one idea
Shortages spread. When one thing runs short, it makes the things that depend on it run
short too, after a delay. The model is a map of *what depends on what*, plus rules for
how fast and how hard a shortage passes along each link.

## The pieces, using Sudan as the example (`cascades.py`)

**1. Domains (nodes).** Things you can measure: security, aid access, food, purchasing
power, nutrition, survival. Each gets a score from 0 to 1:
`0` = severe shortage, `0.5` = normal, `1` = big surplus.

**2. Links (edges).** "Fighting closes roads" is a link *security -> access*. Each link
has a **strength** (how much of the shock passes along) and a **lag** (how long it takes).
Here wasting turns into deaths with a ~2-week lag.

**3. A dead-band.** Small wobbles don't spread. A domain has to move clearly away from its
normal before it starts dragging its neighbours. That's why most bad news fizzles.

**4. Loops.** Follow the links and you sometimes come back to where you started:
- *Reinforcing* loop - makes itself worse: less food -> wasting -> deaths -> fewer people
  working the fields -> less food. If it is strong enough, things spiral.
- *Balancing* loop - corrects itself: deaths -> aid agencies surge in -> more access ->
  more food. This is what stops most crises becoming catastrophes.
The model's job is to say which loop wins, and when.

**5. Adaptive "normal" (the framework's own idea).** What counts as normal shifts. After
3.5 years of war, Darfur's camps don't drift back to peacetime levels by themselves; they
hover at a crisis level. So the model measures shortage relative to *that* level.
Catch: because of this, a place that has adapted to misery transmits nothing unless it
gets *worse*. A lasting shock (a refugee surge) therefore has to be modelled as a
separate "driver" that keeps pushing - we learned this the hard way while building it.

**6. Reality vs the report.** Conditions on the ground are one thing; an official
"Famine" label is another. The question resolves on the label, so the model splits it:
P(conditions get that bad) x P(it gets measured and published in time).

## What it gives you
Run it many times with the uncertain numbers jiggled (Monte Carlo) and count how often
the bad outcome happens. For Sudan: famine conditions in the worst camps ~0% by 1 Dec,
~15% by mid-January, ~58% by March. That's a **timing** forecast - the shortage is real,
but the chain from hunger to death takes months, so it mostly lands *after* the
question closes.

## When to use it - and when not
Use it only when the question is about a shock spreading through linked systems with
delays: famine, bank runs, supply chains, recessions, grid failures. It is useless for
"who wins the election" or "will X announce Y" - those use base rates and news
(Route A). In this batch, 1 of 5 questions qualified.

## Its weakness
The link strengths are guesses. Change them and the answer moves. So its output enters
the forecast as one piece of evidence with a modest weight, never as the answer.
