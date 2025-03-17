import os
import openai
import re  # for regular expressions
from nba_stats import get_player_season_totals

openai.api_key = "ditto"

def generate_response(user_query: str) -> str:
    """
    Main function to handle the user query about NBA stats.
    All stats are represented in a per-game format using only the acronyms:
    PPG, APG, RPG, OREB, DREB, TO, FGA, FTA.
    Do NOT clarify acronyms.
    """
    # Parse the query to extract player's name, season ending year, and season range.
    player_name, season_year, season_range = parse_user_query(user_query)

    # Fetch the stats using the season's ending year (e.g., 2023 for a 2022-23 season)
    player_stats = get_player_season_totals(player_name, season_year)

    if player_stats is None:
        data_snippet = f"No stats found for {player_name} for the {season_range} season."
    else:
        games = player_stats['games_played']
        if games == 0:
            games = 1  # prevent division by zero

        # Compute per-game averages for the specified stats.
        ppg  = player_stats['points'] / games
        apg  = player_stats['assists'] / games
        orpg = player_stats['offensive_rebounds'] / games
        drpg = player_stats['defensive_rebounds'] / games
        rpg  = (player_stats['offensive_rebounds'] + player_stats['defensive_rebounds']) / games
        tpg  = player_stats['turnovers'] / games
        fga  = player_stats['attempted_field_goals'] / games
        fta  = player_stats['attempted_free_throws'] / games

        data_snippet = (
            f"In the {season_range} NBA season, {player_stats['name']} played in {player_stats['games_played']} games. "
            "Here are his per game stats: "
            f"PPG: {ppg:.1f}, "
            f"APG: {apg:.1f}, "
            f"RPG: {rpg:.1f}, "
            f"OREB: {orpg:.1f}, "
            f"DREB: {drpg:.1f}, "
            f"TO: {tpg:.1f}, "
            f"FGA: {fga:.1f}, "
            f"FTA: {fta:.1f}."
        )

    system_prompt = (
        "You are an NBA stats assistant. You have the following stats (all in per game format) from a reliable source. "
        "Please only use these acronyms in your answer without clarification:\n"
        f"Player stats:\n{data_snippet}\n\n"
        "User query:"
    )

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ],
        max_tokens=200,
        temperature=0.3
    )

    answer = response.choices[0].message.content
    return answer

def parse_user_query(user_query: str):
    """
    Extracts the player's name, the ending year of the season, and the season range from the query.
    Supports season ranges like "2022-23". If a range is found, it returns the full string (e.g., "2022-23")
    and uses the ending year (e.g., 2023) for fetching stats.
    
    Now it works with short queries like "rj barrett 2022-23 stats" by tokenizing the query and collecting
    tokens before the season token (ignoring common filler words).
    """
    # --- Season extraction ---
    season_year = None
    season_range = None
    season_match = re.search(r'(\d{4})\s*[-–]\s*(\d{2,4})', user_query)
    if season_match:
        start_year = int(season_match.group(1))
        end_year_part = season_match.group(2)
        if len(end_year_part) == 2:
            season_year = int(str(start_year)[:2] + end_year_part)
        else:
            season_year = int(end_year_part)
        season_range = f"{season_match.group(1)}-{end_year_part}"
    else:
        single_year_match = re.search(r'\b(\d{4})\b', user_query)
        if single_year_match:
            season_year = int(single_year_match.group(1))
            season_range = f"{season_year}"
        else:
            season_year = 2023
            season_range = "2023"

    # --- Player name extraction ---
    player_name = None
    # Try pattern: "what are {player}'s"
    name_match = re.search(r"what are\s+(.+?)'s", user_query, re.IGNORECASE)
    if not name_match:
        # Try pattern: "stats for {player}"
        name_match = re.search(r"stats for\s+([A-Za-z\s\.\-']+)", user_query, re.IGNORECASE)
    if name_match:
        player_name = name_match.group(1).strip()
    else:
        # Fallback: collect tokens before the first token that looks like a season range.
        tokens = user_query.split()
        name_tokens = []
        skip_words = {'per', 'game', 'stats'}
        for token in tokens:
            # If the token matches a season range pattern, break the loop.
            if re.match(r'\d{4}[-–]\d{2,4}', token):
                break
            # Also break if the token is a 4-digit number (season year).
            if token.isdigit() and len(token) == 4:
                break
            if token.lower() in skip_words:
                continue
            name_tokens.append(token)
        if name_tokens:
            player_name = " ".join(name_tokens)
        else:
            player_name = "LeBron James"
    
    return player_name, season_year, season_range
