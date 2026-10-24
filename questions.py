"""
questions.py - the five Metaculus questions forecast on 2026-10-16, as data.

Everything here is either read from a source on 2026-10-16 (community numbers, resolution
criteria, news facts - source and date given) or a judgement (likelihood ratios, base
rates marked "judgement"). The judgements are the LLM layer; keeping them as data makes
them auditable and easy to argue with.

Likelihood ratio (LR) = how much more likely this fact is in a YES world than a NO world.
"""
from evidence import Evidence as E

TODAY = "2026-10-16"

QUESTIONS = [
# ------------------------------------------------------------------------------------
{
 "key": "house",
 "title": "Which party will hold the most seats in the US House after the 2026 elections? (P = Democrats)",
 "url": "https://www.metaculus.com/questions/36369/us-house-plurality-after-2026-midterms/",
 "resolution": "Party holding more seats than any other in the 120th Congress (elected 3 Nov 2026); "
               "independents counted with the party they caucus with.",
 "route": "A",
 "community": (0.919, 626), "community_weight": 5.0,
 "base": {"k": 17, "n": 20, "label": "president's party lost >=5 House seats in 17 of 20 midterms 1946-2022 "
                                      "(enough to flip a ~3-seat majority)"},
 "evidence": [
   E("Generic ballot: D+3 (AARP) to D+7 (NewsNation/DDHQ)", "The Hill / Yahoo", "2026-10-15", 2.0, 0.8),
   E("Fox News Power Rankings now project Democrats flip the House", "Fox News", "2026-10-13", 1.5, 0.6),
   E("Silver Bulletin: Democratic House chances at a new high", "Newsweek", "2026-10-09", 1.4, 0.5),
   E("GOP mid-decade redistricting adds R-leaning seats (partly offset by CA Prop 50)", "Silver Bulletin / Metaculus key factor", "2026-10-13", 0.8, 0.8),
 ],
 "news": "news_house_polls", "reddit": "reddit_house",
 "yes_cues": [r"democrats? (will |to |could |are going to )?(win|flip|take|retake)( back)? the house",
              r"blue wave", r"dems? (lead|ahead)", r"house (flips|falls)"],
 "no_cues": [r"republicans? (will |to |could )?(hold|keep|retain) the house", r"red wave",
             r"gop (holds|keeps)", r"democrats? (won't|will not|can't) (win|flip)"],
 "change_mind": "A generic-ballot average back under D+2, or a run of polls showing GOP leads in "
                "NY/CA swing seats.",
},
# ------------------------------------------------------------------------------------
{
 "key": "sudan",
 "title": "Will FEWS NET classify any area of Sudan as experiencing Famine before 2027?",
 "url": "https://www.metaculus.com/questions/45464/will-fews-net-classify-any-area-of-sudan-as-experiencing-famine-before-2027/",
 "resolution": "Any FEWS NET classification map reported after Aug 2026 and before Jan 2027 shows an area "
               "in IPC Phase 5 Famine for the current period. Phase 4 with '!' does not count.",
 "route": "B",
 "community": (0.25, 152), "community_weight": 4.0,
 "base": {"k": 3, "n": 12, "label": "FEWS NET Sudan maps showed Phase 5 Famine in ~3 of the ~12 quarters "
                                     "since the war began (Dec 2024, late 2025) - judgement from question background"},
 "evidence": [
   E("FEWS NET's own Oct 8 projection (to Jan 2027) keeps areas at Phase 4; 'risk of Famine' only", "FEWS NET via ReliefWeb", "2026-10-08", 0.4, 1.0),
   E("GAM above Famine threshold in 2 of 4 IDP camps; risk expands to East Jebel Marra", "FEWS NET via ReliefWeb", "2026-10-08", 1.6, 1.0),
   E("Oct-Dec is harvest season (below average, but seasonal relief)", "FEWS NET via ReliefWeb", "2026-10-08", 0.8, 0.6),
   E("WFP / UN warn aid system could collapse on funding cuts", "UN News / allAfrica", "2026-09-14", 1.2, 0.6),
 ],
 "news": "news_sudan2", "reddit": "reddit_sudan",
 "yes_cues": [r"famine (declared|confirmed|classification|has been declared|is underway)",
              r"declare[sd]? (a )?famine", r"phase 5"],
 "no_cues": [r"risk of famine", r"no famine", r"not (yet )?(a )?famine", r"thresholds? (are )?(not|no longer) met"],
 "change_mind": "FEWS NET's October Key Message Update or the new Outlook (due ~Nov) mapping any Phase 5 area; "
                "or reports of mortality surging in East Jebel Marra or besieged Kadugli/Dilling.",
},
# ------------------------------------------------------------------------------------
{
 "key": "venezuela",
 "title": "Will Venezuela announce a presidential election before 2027?",
 "url": "https://www.metaculus.com/questions/45419/will-venezuela-announce-a-presidential-election-before-2027/",
 "resolution": "Before 1 Jan 2027, a legally empowered person/body officially announces a presidential "
               "election with a specific date, voting scheduled before 1 Jan 2028.",
 "route": "A",
 "community": (0.068, 129), "community_weight": 4.0,
 "base": {"p": 0.12, "label": "judgement: no date in the 9 months since Jan 2026; sequence still TSJ -> new CNE "
                                "-> date; ~15-month expected wait -> ~12% for the next 2.5 months"},
 "evidence": [
   E("Rodriguez promised elections at the UN, gave no date", "Al Jazeera / Reuters", "2026-09-24", 0.7, 0.9),
   E("Returned from US with 'no firm election date'; elections 'when ready', Trump agreed", "Reuters", "2026-09-26", 0.6, 0.9),
   E("TSJ reform only through first reading (Aug 27); new CNE not yet named", "Metaculus background", "2026-08-27", 0.6, 0.8),
   E("New US-backed negotiation round began Oct 14; Rubio wants votes soon", "Al Jazeera", "2026-10-14", 1.4, 0.7),
   E("US delisted Jorge Rodriguez (National Assembly) - reward for cooperation", "Al Jazeera / MercoPress", "2026-10-14", 1.1, 0.5),
   E("US policy prioritises oil reopening over the ballot", "Dallas News / Eurasia Review", "2026-09-28", 0.8, 0.5),
 ],
 "news": "news_venezuela", "reddit": "reddit_venezuela",
 "yes_cues": [r"election date (set|announced|fixed)", r"elections? (will be held|scheduled|set) (on|in|for)",
              r"announce[sd]? (the |a )?(presidential )?election", r"cne (sets|announces|calls)"],
 "no_cues": [r"no (firm |clear )?(election )?date", r"without (setting |a )?(a )?date",
             r"when (they are |we are |it is )?ready", r"postpone|delay"],
 "change_mind": "The National Assembly passing the TSJ law and naming a new CNE board - that is the step "
                "right before a date can be set.",
},
# ------------------------------------------------------------------------------------
{
 "key": "johnson",
 "title": "Will Mike Johnson remain Speaker of the House until January 3, 2027?",
 "url": "https://www.metaculus.com/questions/40976/will-johnson-remain-speaker-until-end-of-119th-congress/",
 "resolution": "YES if Johnson is Speaker continuously until the end of the 119th Congress (3 Jan 2027). "
               "An announced resignation effective after 3 Jan still resolves YES.",
 "route": "A",
 "community": (0.785, 22), "community_weight": 1.5,     # only 22 forecasters: thin, likely stale
 "base": {"k": 60, "n": 62, "label": "Speakers in office 2.5 months before a Congress ended who served to the end, "
                                      "since 1900; the two exceptions were deaths (Rainey 1934, Bankhead 1940). "
                                      "No Speaker has ever been removed in a lame duck; Gingrich (1998) quit after "
                                      "losses but stayed Speaker to the end - judgement from history"},
 "evidence": [
   E("Johnson campaigning nationwide as Speaker (NC, ME, TX)", "AP / WaPo", "2026-10-15", 1.1, 0.8),
   E("GOP brace for a leader fight IF they lose - about the next Congress, not removing him now", "CNN / Axios", "2026-10-15", 0.9, 0.7),
   E("Fine print: resignation effective after Jan 3 still counts YES", "Metaculus resolution", "2026-10-16", 1.2, 1.0),
 ],
 "news": "news_johnson", "reddit": "reddit_johnson",
 "yes_cues": [r"(remain|stay|keep|retain)s? (as )?speaker", r"backs? johnson", r"keeps? the gavel"],
 "no_cues": [r"motion to vacate", r"\boust", r"johnson (to )?(resign|step down)", r"replace johnson"],
 "change_mind": "A motion to vacate filed in the lame duck, or Johnson taking another post before Jan 3.",
},
# ------------------------------------------------------------------------------------
{
 "key": "kennedy",
 "title": "Will Trump demolish the Kennedy Center before January 1, 2027?",
 "url": "https://www.metaculus.com/questions/45810/will-trump-demolish-the-kennedy-center-before-january-1-2027/",
 "resolution": "YES if the Kennedy Center is substantially demolished (more than a de minimis portion "
               "intentionally destroyed) before 1 Jan 2027.",
 "route": "A",
 "community": (0.04, 115), "community_weight": 4.0,
 "base": {"p": 0.05, "label": "judgement: demolishing a protected federal landmark under active litigation within "
                                "2.5 months is rare; raised from ~1% because the White House East Wing was "
                                "torn down within days in Oct 2025"},
 "evidence": [
   E("Court is supervising: work blocked, discovery extended to Oct 23", "USA Today / Metaculus comments", "2026-09-29", 0.4, 0.9),
   E("Unsealed JLL plan is renovation (repairs, HVAC, theatres), reopening summer 2028", "Newsweek / court filings", "2026-10-08", 0.5, 0.9),
   E("Trump refuses to rule out demolition; held a demolition rendering", "Washington Post / The Hill", "2026-10-01", 2.0, 0.7),
   E("Sen. Mike Lee blocked bipartisan bill barring demolition", "CNN / WaPo", "2026-09-29", 1.2, 0.6),
   E("DOJ filing framed demolition as a threat if the court blocks renovation", "ABC News", "2026-08-26", 1.3, 0.6),
 ],
 "news": "news_kennedy", "reddit": "reddit_kennedy",
 "yes_cues": [r"(will|plans? to|going to|set to) (demolish|tear down|raze)", r"demolition (begins|began|started|underway)",
              r"bulldoz"],
 "no_cues": [r"(block|blocks|blocked|halt|halts|stop|prevent|bar|bars)\w* .{0,40}demoli", r"(court|judge) (block|bars|halts)",
             r"renovat"],
 "change_mind": "The court lifting its block, or demolition contracts / permits appearing.",
},
]
