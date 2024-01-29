import os
import orjson as json
import yaml
from collections import defaultdict
from dataclasses import dataclass
import itertools
from datetime import datetime
from typing import List, Dict
import math

from mgz.model import parse_match, serialize
from mgz.summary import Summary, FullSummary
from trueskill import Rating, rate, quality, BETA
import trueskill

from IPython import embed

resolved_matches = []
unclear_matches = []
relevant_players = yaml.load(open('config.yaml'), Loader=yaml.FullLoader).get('humans', [])
humans = relevant_players

processed_games = set()

testfile = "MP Replay v101.102.33868.0 @2024.01.18 222811 (4).aoe2record"

rank_dict = defaultdict(lambda: Rating())

@dataclass
class GameRow:
    date: datetime
    filename: str
    winners: List[str]
    losers: List[str]
    included: bool
    playerratings: Dict[str, float]

output_rows = []

def game_identifier(game):
    return f"{game['date']} {game['map_seed']}"

def parse_game_date(filename):
    date = filename.split(' ')[-3]
    assert date.startswith('@')
    date = date[1:]
    parsed_date = datetime.strptime(date, '%Y.%m.%d')
    return parsed_date


# with open(testfile, 'rb') as testfile:
#     sum = parse_match(testfile)
#     embed()
#     exit()

def generate_output_row(filename, winners, losers, included=True):
    def get_rank(player):
        if player in rank_dict:
            return rank_dict[player].mu
        else:
            return None
        
    row = GameRow(
        date=parse_game_date(filename),
        filename=filename,
        winners=winners,
        losers=losers,
        included=included,
        playerratings={player:get_rank(player) for player in relevant_players},
    )
    return row

def get_game_files():
    files_dict = defaultdict(list)
    relevant_dates = set()
    outfiles = set(os.listdir('data/processed-data'))
    return [
        filename
        for filename 
        in os.listdir('data/save-data') 
        if filename.endswith('.aoe2record') 
            and filename.replace('.aoe2record', '.json') not in outfiles
            # and filename == testfile
    ]

def ordered_game_outputs():
    files_dict = defaultdict(list)
    relevant_dates = set()

    for filename in os.listdir('data/processed-data'):
        filedate = parse_game_date(filename)
        files_dict[filedate].append(filename)
        relevant_dates.add(filedate)

    out_arr = []
    for date in sorted(relevant_dates):
        for filename in files_dict[date]:
            out_arr.append(filename)

    return out_arr

def playername(player):
    if player['name'] not in humans:
        return "HardComputer"
    return player['name']

def process_games():
    for filename in get_game_files():

        print(filename)
        with open('data/save-data/' + filename, 'rb') as f:
            try:
                sum = FullSummary(f)
            except:
                with open("data/processed-data/" + filename.replace('.aoe2record', '.json'), 'w') as outfile:
                    outfile.write('{"error": "error parsing"}')
                print(f"Error parsing {filename}")
                continue
           
            players = sum.get_players()
            teams = sum.get_teams()

            outcome = {'winners': [], 'losers': []}
            for player in players:
                if player['winner']:
                    outcome['winners'].append(playername(player))
                else:
                    outcome['losers'].append(playername(player))
            processed_result = {
                "filename": filename,
                "date": parse_game_date(filename),
                "winners": outcome['winners'],
                "losers": outcome['losers'],
                "players": [playername(player) for player in players],
                "raw_players": players,
                "duration": sum.get_duration(),
                "settings": sum.get_settings(),
                "completed": sum.get_completed(),
                "map_seed": sum.get_header().get('replay', {}).get('random_seed'),
                "save_version": sum.get_header()['version'].value,


            }
            with open('data/processed-data/' + filename.replace('.aoe2record', '.json'), 'w') as outfile:
                output_bytes = json.dumps(processed_result, option=json.OPT_INDENT_2)
                outfile.write(output_bytes.decode('utf-8'))

def win_probability(team1, team2):
    team1 = [rank_dict[player] for player in team1]
    team2 = [rank_dict[player] for player in team2]
    delta_mu = sum(r.mu for r in team1) - sum(r.mu for r in team2)
    sum_sigma = sum(r.sigma ** 2 for r in itertools.chain(team1, team2))
    size = len(team1) + len(team2)
    denom = math.sqrt(size * (BETA * BETA) + sum_sigma)
    ts = trueskill.global_env()
    return ts.cdf(delta_mu / denom)
                
def process_scores():

    for filename in ordered_game_outputs():
        print(filename)
        with open('data/processed-data/' + filename, 'r') as f:
            try:
                filedata = f.read()
                game = json.loads(filedata)
            except:
                print(f"Error parsing {filename}")
                continue
            if game.get('error'):
                continue

            if game_identifier(game) in processed_games:
                print(f"Skipping {filename} because it's already processed")
                continue
            processed_games.add(game_identifier(game))
            if len(game['winners']) != len(game['losers']):
                unclear_matches.append(filename)
                output_rows.append(generate_output_row(filename, game['winners'], game['losers'], included=False))
                continue

            update_rankings(game['winners'], game['losers'])

            output_rows.append(generate_output_row(filename, game['winners'], game['losers'], included=True))

def update_rankings(winning_team, losing_team):
    winning_rankings = [rank_dict[player] for player in winning_team]
    losing_rankings = [rank_dict[player] for player in losing_team]
    new_winning, new_losing = rate([winning_rankings, losing_rankings], ranks=[0, 1])
    for i, player in enumerate(winning_team):
        rank_dict[player] = new_winning[i]
    for i, player in enumerate(losing_team):
        rank_dict[player] = new_losing[i]

def match_quality(team1, team2):
    team1_rankings = [rank_dict[player] for player in team1]
    team2_rankings = [rank_dict[player] for player in team2]
    winrate = quality([team1_rankings, team2_rankings])
    return winrate

if __name__ == "__main__":
    process_games()
    process_scores()
    for player in rank_dict:
        
        print(f"{player:20} {rank_dict[player].mu:.1f} - {rank_dict[player].sigma:.1f}")

    with open('progress.csv', 'w') as out_csv:
        # Use csvwriter
        csv_headers = ['date', 'filename', 'included', 'winners', 'losers'] + relevant_players
        out_csv.write(','.join(csv_headers) + '\n')
        for row in output_rows:
            output_row = [
                row.date, 
                row.filename, 
                row.included, 
                ':'.join(row.winners), 
                ':'.join(row.losers)
            ] + [row.playerratings[player] for player in relevant_players]
            out_csv.write(','.join([str(x) for x in output_row]) + '\n')
        
    with open("matchups.csv", "w") as matchups_csv:
        matchups_csv.write("team1,team2,match_quality,team1_win_probability\n")
        for team1 in itertools.combinations(humans, 2):
            for team2 in itertools.combinations([h for h in humans if h not in team1], 2):
                match_q = match_quality(team1, team2)
                win_odds = win_probability(team1, team2)
                matchups_csv.write(f"{':'.join(team1)},{':'.join(team2)},{match_q},{win_odds}\n")

