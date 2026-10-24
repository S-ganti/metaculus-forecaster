# Forecasts pre-registered 2026-10-16

| Question | Community | Inside view | **Forecast** | 90% CI |
|---|---|---|---|---|
| [Which party will hold the most seats in the US House after the 2026 elections? (P = Democrats)](https://www.metaculus.com/questions/36369/us-house-plurality-after-2026-midterms/) | 91.9% | 92.5% | **90.0%** | 83%-95% |
| [Will FEWS NET classify any area of Sudan as experiencing Famine before 2027?](https://www.metaculus.com/questions/45464/will-fews-net-classify-any-area-of-sudan-as-experiencing-famine-before-2027/) | 25.0% | 13.2% | **23.5%** | 13%-38% |
| [Will Venezuela announce a presidential election before 2027?](https://www.metaculus.com/questions/45419/will-venezuela-announce-a-presidential-election-before-2027/) | 6.8% | 4.2% | **7.7%** | 4%-14% |
| [Will Mike Johnson remain Speaker of the House until January 3, 2027?](https://www.metaculus.com/questions/40976/will-johnson-remain-speaker-until-end-of-119th-congress/) | 78.5% | 96.4% | **88.7%** | 75%-95% |
| [Will Trump demolish the Kennedy Center before January 1, 2027?](https://www.metaculus.com/questions/45810/will-trump-demolish-the-kennedy-center-before-january-1-2027/) | 4.0% | 2.3% | **4.7%** | 2%-9% |

## Working

```
========================================================================================
Which party will hold the most seats in the US House after the 2026 elections? (P = Democrats)
https://www.metaculus.com/questions/36369/us-house-plurality-after-2026-midterms/
RESOLVES: Party holding more seats than any other in the 120th Congress (elected 3 Nov 2026); independents counted with the party they caucus with.
ROUTE A   |   community 91.9% (626 forecasters)

  Base rate: 83.3%  - president's party lost >=5 House seats in 17 of 20 midterms 1946-2022 (enough to flip a ~3-seat majority)

  Evidence ledger:
    prior (base rate)                                       83.3%
    2026-10-15  LR 2.00 x rel 0.8 -> YES  Generic ballot: D+3 (AARP) to D+7 (NewsNation/DDHQ)  [The Hill / Yahoo]
    2026-10-13  LR 1.50 x rel 0.6 -> YES  Fox News Power Rankings now project Democrats flip the House  [Fox News]
    2026-10-09  LR 1.40 x rel 0.5 -> YES  Silver Bulletin: Democratic House chances at a new high  [Newsweek]
    2026-10-13  LR 0.80 x rel 0.8 -> NO   GOP mid-decade redistricting adds R-leaning seats (partly offs  [Silver Bulletin / Metaculus key factor]
    2026-10-16  LR 1.25 x rel 0.5 -> YES  news+Reddit stance: 6 lean YES / 0 lean NO of 143 posts  [sentiment.py]
    total log-odds shift +0.90  ->  P_inside  92.5%

  Sentiment: 143 items (Reddit 100), polarity +0.10, attention x1.8 vs prior 3 weeks; stance 6 YES / 0 NO

  Fusion (log-odds, precision-weighted) then calibration slope 0.9:
  component            p        weight   logit
  community (626)     0.919     5.00    +2.43
  inside (evidence)   0.925     1.50    +2.51
  --------------------------------------------
  FUSED                 0.900            [0.826, 0.945] 90% CI

  >>> FORECAST 90.0%   90% CI 83%-95%   (community 91.9%, gap -1.9 pts)
  Would change my mind: A generic-ballot average back under D+2, or a run of polls showing GOP leads in NY/CA swing seats.

========================================================================================
Will FEWS NET classify any area of Sudan as experiencing Famine before 2027?
https://www.metaculus.com/questions/45464/will-fews-net-classify-any-area-of-sudan-as-experiencing-famine-before-2027/
RESOLVES: Any FEWS NET classification map reported after Aug 2026 and before Jan 2027 shows an area in IPC Phase 5 Famine for the current period. Phase 4 with '!' does not count.
ROUTE B   |   community 25.0% (152 forecasters)

  Base rate: 26.9%  - FEWS NET Sudan maps showed Phase 5 Famine in ~3 of the ~12 quarters since the war began (Dec 2024, late 2025) - judgement from question background

  Evidence ledger:
    prior (base rate)                                       26.9%
    2026-10-08  LR 0.40 x rel 1.0 -> NO   FEWS NET's own Oct 8 projection (to Jan 2027) keeps areas at P  [FEWS NET via ReliefWeb]
    2026-10-08  LR 1.60 x rel 1.0 -> YES  GAM above Famine threshold in 2 of 4 IDP camps; risk expands t  [FEWS NET via ReliefWeb]
    2026-10-08  LR 0.80 x rel 0.6 -> NO   Oct-Dec is harvest season (below average, but seasonal relief)  [FEWS NET via ReliefWeb]
    2026-09-14  LR 1.20 x rel 0.6 -> YES  WFP / UN warn aid system could collapse on funding cuts  [UN News / allAfrica]
    2026-10-16  LR 0.80 x rel 0.5 -> NO   news+Reddit stance: 0 lean YES / 3 lean NO of 39 posts  [sentiment.py]
    2026-10-16  LR 0.60 x rel 0.6 -> NO   Cascade: camp famine conditions 0% by 1 Dec, 15% mid-Jan, 58%   [cascades.py]
    total log-odds shift -0.89  ->  P_inside  13.2%

  Sentiment: 39 items (Reddit 29), polarity -0.47, attention x1.4 vs prior 3 weeks; stance 0 YES / 3 NO

  Route B cascade (worst-hit camps; misses besieged towns, so used as evidence, not a probability):
    access -> food -> nutrition -> survival -> access | balancing, act.gain=0.58, lag=1.75
    food -> nutrition -> survival -> food | reinforcing, act.gain=0.48, lag=1.5  (reinforcing but sub-unity even at activation: slow drift)
    access -> purchasing -> nutrition -> survival -> access | balancing, act.gain=0.26, lag=1.75
    P(all 3 IPC Famine thresholds crossed) by horizon: 1.5 mo 0%, 3 mo 15%, 4.5 mo 58%
    -> mortality lags malnutrition ~2 months: famine conditions are a Jan-Mar risk, mostly after this question closes.

  Fusion (log-odds, precision-weighted) then calibration slope 0.9:
  component            p        weight   logit
  community (152)     0.250     4.00    -1.10
  inside (evidence)   0.132     1.50    -1.89
  --------------------------------------------
  FUSED                 0.235            [0.132, 0.382] 90% CI

  >>> FORECAST 23.5%   90% CI 13%-38%   (community 25.0%, gap -1.5 pts)
  Would change my mind: FEWS NET's October Key Message Update or the new Outlook (due ~Nov) mapping any Phase 5 area; or reports of mortality surging in East Jebel Marra or besieged Kadugli/Dilling.

========================================================================================
Will Venezuela announce a presidential election before 2027?
https://www.metaculus.com/questions/45419/will-venezuela-announce-a-presidential-election-before-2027/
RESOLVES: Before 1 Jan 2027, a legally empowered person/body officially announces a presidential election with a specific date, voting scheduled before 1 Jan 2028.
ROUTE A   |   community 6.8% (129 forecasters)

  Base rate: 12.0%  - judgement: no date in the 9 months since Jan 2026; sequence still TSJ -> new CNE -> date; ~15-month expected wait -> ~12% for the next 2.5 months

  Evidence ledger:
    prior (base rate)                                       12.0%
    2026-09-24  LR 0.70 x rel 0.9 -> NO   Rodriguez promised elections at the UN, gave no date  [Al Jazeera / Reuters]
    2026-09-26  LR 0.60 x rel 0.9 -> NO   Returned from US with 'no firm election date'; elections 'when  [Reuters]
    2026-08-27  LR 0.60 x rel 0.8 -> NO   TSJ reform only through first reading (Aug 27); new CNE not ye  [Metaculus background]
    2026-10-14  LR 1.40 x rel 0.7 -> YES  New US-backed negotiation round began Oct 14; Rubio wants vote  [Al Jazeera]
    2026-10-14  LR 1.10 x rel 0.5 -> YES  US delisted Jorge Rodriguez (National Assembly) - reward for c  [Al Jazeera / MercoPress]
    2026-09-28  LR 0.80 x rel 0.5 -> NO   US policy prioritises oil reopening over the ballot  [Dallas News / Eurasia Review]
    2026-10-16  LR 0.80 x rel 0.5 -> NO   news+Reddit stance: 0 lean YES / 11 lean NO of 135 posts  [sentiment.py]
    total log-odds shift -1.13  ->  P_inside   4.2%

  Sentiment: 135 items (Reddit 91), polarity -0.01, attention x0.5 vs prior 3 weeks; stance 0 YES / 11 NO

  Fusion (log-odds, precision-weighted) then calibration slope 0.9:
  component            p        weight   logit
  community (129)     0.068     4.00    -2.62
  inside (evidence)   0.042     1.50    -3.12
  --------------------------------------------
  FUSED                 0.077            [0.040, 0.145] 90% CI

  >>> FORECAST 7.7%   90% CI 4%-14%   (community 6.8%, gap +0.9 pts)
  Would change my mind: The National Assembly passing the TSJ law and naming a new CNE board - that is the step right before a date can be set.

========================================================================================
Will Mike Johnson remain Speaker of the House until January 3, 2027?
https://www.metaculus.com/questions/40976/will-johnson-remain-speaker-until-end-of-119th-congress/
RESOLVES: YES if Johnson is Speaker continuously until the end of the 119th Congress (3 Jan 2027). An announced resignation effective after 3 Jan still resolves YES.
ROUTE A   |   community 78.5% (22 forecasters)

  Base rate: 96.0%  - Speakers in office 2.5 months before a Congress ended who served to the end, since 1900; the two exceptions were deaths (Rainey 1934, Bankhead 1940). No Speaker has ever been removed in a lame duck; Gingrich (1998) quit after losses but stayed Speaker to the end - judgement from history

  Evidence ledger:
    prior (base rate)                                       96.0%
    2026-10-15  LR 1.10 x rel 0.8 -> YES  Johnson campaigning nationwide as Speaker (NC, ME, TX)  [AP / WaPo]
    2026-10-15  LR 0.90 x rel 0.7 -> NO   GOP brace for a leader fight IF they lose - about the next Con  [CNN / Axios]
    2026-10-16  LR 1.20 x rel 1.0 -> YES  Fine print: resignation effective after Jan 3 still counts YES  [Metaculus resolution]
    2026-10-16  LR 0.85 x rel 0.5 -> NO   news+Reddit stance: 0 lean YES / 1 lean NO of 200 posts  [sentiment.py]
    total log-odds shift +0.10  ->  P_inside  96.4%

  Sentiment: 200 items (Reddit 100), polarity -0.02, attention x3.0 vs prior 3 weeks; stance 0 YES / 1 NO

  Fusion (log-odds, precision-weighted) then calibration slope 0.9:
  component            p        weight   logit
  community (22)      0.785     1.50    +1.30
  inside (evidence)   0.964     1.50    +3.29
  --------------------------------------------
  FUSED                 0.887            [0.753, 0.953] 90% CI

  >>> FORECAST 88.7%   90% CI 75%-95%   (community 78.5%, gap +10.2 pts)
  Would change my mind: A motion to vacate filed in the lame duck, or Johnson taking another post before Jan 3.

========================================================================================
Will Trump demolish the Kennedy Center before January 1, 2027?
https://www.metaculus.com/questions/45810/will-trump-demolish-the-kennedy-center-before-january-1-2027/
RESOLVES: YES if the Kennedy Center is substantially demolished (more than a de minimis portion intentionally destroyed) before 1 Jan 2027.
ROUTE A   |   community 4.0% (115 forecasters)

  Base rate: 5.0%  - judgement: demolishing a protected federal landmark under active litigation within 2.5 months is rare; raised from ~1% because the White House East Wing was torn down within days in Oct 2025

  Evidence ledger:
    prior (base rate)                                        5.0%
    2026-09-29  LR 0.40 x rel 0.9 -> NO   Court is supervising: work blocked, discovery extended to Oct   [USA Today / Metaculus comments]
    2026-10-08  LR 0.50 x rel 0.9 -> NO   Unsealed JLL plan is renovation (repairs, HVAC, theatres), reo  [Newsweek / court filings]
    2026-10-01  LR 2.00 x rel 0.7 -> YES  Trump refuses to rule out demolition; held a demolition render  [Washington Post / The Hill]
    2026-09-29  LR 1.20 x rel 0.6 -> YES  Sen. Mike Lee blocked bipartisan bill barring demolition  [CNN / WaPo]
    2026-08-26  LR 1.30 x rel 0.6 -> YES  DOJ filing framed demolition as a threat if the court blocks r  [ABC News]
    2026-10-16  LR 0.80 x rel 0.5 -> NO   news+Reddit stance: 2 lean YES / 20 lean NO of 200 posts  [sentiment.py]
    total log-odds shift -0.81  ->  P_inside   2.3%

  Sentiment: 200 items (Reddit 100), polarity -0.14, attention x1.7 vs prior 3 weeks; stance 2 YES / 20 NO

  Fusion (log-odds, precision-weighted) then calibration slope 0.9:
  component            p        weight   logit
  community (115)     0.040     4.00    -3.18
  inside (evidence)   0.023     1.50    -3.75
  --------------------------------------------
  FUSED                 0.047            [0.024, 0.091] 90% CI

  >>> FORECAST 4.7%   90% CI 2%-9%   (community 4.0%, gap +0.7 pts)
  Would change my mind: The court lifting its block, or demolition contracts / permits appearing.
```

Score at resolution with `aggregate.score_history`.
