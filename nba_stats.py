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
    Fetch a player's aggregated season totals for a given year.
    The player_name is normalized to improve matching.
    """
    # Fetch all players' season totals for the given season.
    season_totals = client.players_season_totals(season_end_year=year)

    # Normalize the player name from the query.
    norm_query = normalize_str(player_name)
    
    # Filter using normalized names.
    player_data = [
        p for p in season_totals 
        if norm_query in normalize_str(p['name'])
    ]

    print("All season totals:")
    pprint.pprint(season_totals)

    print(f"Filtered data for {player_name}:")
    pprint.pprint(player_data)

    if not player_data:
        return None

    # Return the first matching entry.
    return player_data[0]

if __name__ == "__main__":
    # Example usage for testing; try with "Luka Doncic" even if the data has "Luka Dončić".
    example_stats = get_player_season_totals("Luka Doncic", 2023)
    print("Example stats for Luka Doncic in 2022-23:")
    pprint.pprint(example_stats)
