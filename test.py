import json
import trueskill as ts

MAJOR_LEAGUES = ["98767991299243165", "98767991332355509", "98767991310872058", "98767991302996019", "98767991349978712", "101382741235120470", "98767991314006698", "104366947889790212", "107213827295848783"]
INTL_EVENTS = ["98767991325878492", "98767975604431411"]
leagueMapping = open('internationalMappings.json')
LM = json.load(leagueMapping)
f = open('esports-data/tournaments.json')
data = json.load(f)
t = open('esports-data/teams.json')
TEAMS = json.load(t)

# current - TS: https://trueskill.org/ 
# Glicko-2: http://www.glicko.net/glicko/glicko2.pdf
# ELO: https://medium.com/purple-theory/what-is-elo-rating-c4eb7a9061e0


# Can we reduce teams down to region - e.g. T1, Gen. G, DRX --> LCK, TSM, C9, GG --> NA and compare international competition to instill a baseline rating for each region? 
# e.g. LCK teams for last 3 years smoked NA teams, so LCK region teams rating "start" at 1650, NA will start at 1400 (not sure how to implement in TS)
# So when int'l competition comes around, LCK teams should (expectedly) have a higher overall rating than NA teams, unless the NA team really was cracked and demolished the region, then maybe they're close? 

# realistically, historical data means nothing as major meta changes happen every season, massive team turnover. we use it for determining what the 'ingredients' of a winning team are + rank the regions based on recent (last 3 yrs) results? 


def getRegion(teamId):
  if teamId in LM['data2']:
    return LM['data2'][teamId]
  return "OTHER"

def rankRegions(res):
  leagueRankings = {k:ts.Rating() for k in LM['data1'].keys()} 
  leagueRankings["OTHER"] = ts.Rating()
  for d in res:
    if d['leagueId'] in INTL_EVENTS:
      for i, stage in enumerate(d['stages']):
        #can use i to maybe 'increase' gains as we move into later rounds?
        for section in stage['sections']:
          for match in section['matches']:
            if match["teams"][0]["result"]["outcome"] == "loss":
              #rate_1vs1(winner, loser) to recalc
              winner, loser = ts.rate_1vs1(leagueRankings[getRegion(match["teams"][1]["id"])], leagueRankings[getRegion(match["teams"][0]["id"])])
              leagueRankings[getRegion(match["teams"][0]["id"])] = loser
              leagueRankings[getRegion(match["teams"][1]["id"])] = winner
  return leagueRankings

def rankLeague(league, base=None):
  #based on slugs
  if base:
    ts.TrueSkill(mu=base.mu)
  teamContainer = {}
  for l in data:
    if l["slug"] == league:
      #stages[0] = Regular Season, stages[1] = Playoffs for Leagues
      #Can we weigh playoffs more heavily?
      #Only checking reg season rn
      for game in l["stages"][0]["sections"][0]["matches"]:
        #Adding teams to container if not already there, with default rating
        if game["teams"][0]["id"] not in teamContainer:
          teamContainer[game["teams"][0]["id"]] = ts.Rating(mu=base.mu)
        if game["teams"][1]["id"] not in teamContainer:
          teamContainer[game["teams"][1]["id"]] = ts.Rating(mu=base.mu)

        #Calculating their gain/loss based on outcome
        if game["teams"][0]["result"]["outcome"] == "loss":
          #rate_1vs1(winner, loser) to recalc
          winner, loser = ts.rate_1vs1(teamContainer[game["teams"][1]["id"]], teamContainer[game["teams"][0]["id"]])
          teamContainer[game["teams"][0]["id"]] = loser
          teamContainer[game["teams"][1]["id"]] = winner
    #This just renames from id to team name for my sanity
    for t in TEAMS:
      if t["team_id"] in teamContainer:
        teamContainer[t["name"]] = teamContainer[t["team_id"]]
        teamContainer.pop(t["team_id"])
  return teamContainer


test = rankLeague("lck_summer_2023", rankRegions(data)["LCK"])
test.update(rankLeague("lcs_summer_2023", rankRegions(data)["LCS"]))
test.update(rankLeague("lec_summer_2023", rankRegions(data)["LEC"]))
test.update(rankLeague("lpl_summer_2023", rankRegions(data)["LPL"]))
#orders them based on sigma
print({k: v for k, v in reversed(sorted(test.items(), key=lambda item: item[1].mu))})

#MSI 2021/2022 - R1 Group A/B/C --> R2 Groups --> R3 KO (3 rounds)
#MSI 2023 - R1 Play-In Knockouts --> R2 Brackets (2 rounds)

#Worlds - R1 Play Ins --> R2 Play In KO --> Groups --> Playoffs (4 rounds)
