import os
import json

from mgz.model import parse_match, serialize
from mgz.summary import Summary, FullSummary
from IPython import embed

matches = []

testfile = "save-data/MP Replay v101.102.33868.0 @2024.01.18 222811 (4).aoe2record"

# with open(testfile, 'rb') as testfile:
#     sum = parse_match(testfile)
#     embed()
#     exit()

for filename in os.listdir('save-data'):
    if filename.endswith('.aoe2record') and '2024' in filename:
        print(filename)
        with open('save-data/' + filename, 'rb') as f:
            try:
                sum = Summary(f)
            except:
                print(f"Error parsing {filename}")
                continue
            players = sum.get_players()
            teams = sum.get_teams()

            outcome = {'winners': [], 'losers': []}
            for player in players:
                if player['winner']:
                    outcome['winners'].append(player['name'])
                else:
                    outcome['losers'].append(player['name'])
            
            matches.append(outcome)

with open('data.txt', 'w') as outfile:
    for match in matches:
        outfile.write(" and ".join(match['winners']) + " beat " + " and ".join(match['losers']) + "\n")

