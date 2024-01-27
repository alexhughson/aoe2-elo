# Calculating Player Skill in AOE2

This repo can process replay files for Age of Empires 2: Definitive Edition and compile scores for player skill

Microsoft TrueSkill is used to calulate the scores, using the `trueskill` python library

# Usage

## Setup
Add all replay files to ./data/save-data

Add a list of players to track to `config.yaml` in the root:

```
humans: ["player1", "player2"]
```

## Run

Run using `make run`

## Outputs

A progress.csv file will be output showing all games and relative player scores after each round

Processed game data will be in `./data/processed-data` 

Games are deduplicated based on game date and map seed, to ensure that different recordings of the same game don't get double counted.