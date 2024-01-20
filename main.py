import os
import json

from mgz.model import parse_match, serialize
from mgz.summary import Summary

matches = []

for filename in os.listdir('save-data'):
    if filename.endswith('.aoe2record'):
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

