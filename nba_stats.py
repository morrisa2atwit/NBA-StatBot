from basketball_reference_web_scraper import client
from basketball_reference_web_scraper.data import OutputType
import pprint
import unicodedata

def normalize_str(s: str) -> str:
    """
    Normalize a string by removing diacritics and converting to lowercase.
    """
    normalized = unicodedata.normalize('NFD', s)
    return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn').lower()

def get_player_season_totals(player_name: str, year: int):
    """
    Fetch a player's aggregated season totals (per game stats) for the given season.
    Returns the first matching record or None if not found.
    """
    season_totals = client.players_season_totals(season_end_year=year)
    player_data = [
        p for p in season_totals if normalize_str(player_name) in normalize_str(p['name'])
    ]
    if not player_data:
        return None
    return player_data[0]

def get_league_leader(stat_key: str, year: int):
    """
    Fetch league totals for the given season and return the player with the highest
    per game average for the given stat.
    
    For stat_key "points", "assists", "turnovers", "attempted_field_goals", or "attempted_free_throws",
    per game average is computed as value / games_played.
    
    For "rebounds", we sum offensive and defensive rebounds.
    
    Returns a tuple (player, avg_value) or (None, None) if not found.
    """
    season_totals = client.players_season_totals(season_end_year=year)
    valid_players = [p for p in season_totals if p['games_played'] > 0]
    leader = None
    leader_avg = -1
    for p in valid_players:
        games = p['games_played']
        if stat_key == "rebounds":
            avg = (p['offensive_rebounds'] + p['defensive_rebounds']) / games
        else:
            avg = p.get(stat_key, 0) / games
        if avg > leader_avg:
            leader_avg = avg
            leader = p
    return leader, leader_avg

if __name__ == "__main__":
    # Test per game stats for LeBron James in 2023 season (2022-23)
    stats = get_player_season_totals("LeBron James", 2023)
    print("Per Game Stats:")
    pprint.pprint(stats)
    
    # Test league leader in scoring (points) in 2023 season
    leader, avg = get_league_leader("points", 2023)
    print("\nLeague Leader in Scoring (PPG):")
    print(leader['name'] if leader else "None", avg)
