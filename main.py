import os
import json
from collections import defaultdict

from mgz.model import parse_match, serialize
from mgz.summary import Summary, FullSummary
from trueskill import Rating, rate

from IPython import embed

resolved_matches = []
unclear_matches = []

testfile = "save-data/MP Replay v101.102.33868.0 @2024.01.18 222811 (4).aoe2record"

rank_dict = defaultdict(lambda: Rating())



# with open(testfile, 'rb') as testfile:
#     sum = parse_match(testfile)
#     embed()
#     exit()

def parse_games():
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
                if len(outcome['winners']) != len(outcome['losers']):
                    unclear_matches.append(filename)
                    continue
                update_rankings(outcome['winners'], outcome['losers'])
                resolved_matches.append(outcome)

def update_rankings(winning_team, losing_team):
    winning_rankings = [rank_dict[player] for player in winning_team]
    losing_rankings = [rank_dict[player] for player in losing_team]
    new_winning, new_losing = rate([winning_rankings, losing_rankings], ranks=[0, 1])
    for i, player in enumerate(winning_team):
        rank_dict[player] = new_winning[i]
    for i, player in enumerate(losing_team):
        rank_dict[player] = new_losing[i]

if __name__ == "__main__":
    parse_games()
    for player in rank_dict:
        
        print(f"{player:20} {rank_dict[player].mu:.1f} - {rank_dict[player].sigma:.1f}")

    print(f"{len(resolved_matches)} matches resolved, {len(unclear_matches)} unclear")
