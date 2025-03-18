import os
import openai
import re  # for regular expressions
from nba_stats import get_player_season_totals, get_league_leader

openai.api_key = "ditto"

def determine_query_type(user_query: str) -> str:
    """
    Determines whether the query is for per game stats, a player comparison, 
    or a general league query.
    """
    q = user_query.lower().strip()
    if "compare" in q or "vs" in q or "versus" in q:
        return "comparison"
    elif q.startswith("who") or q.startswith("which"):
        return "general"
    else:
        return "per_game"

def parse_season(season_str: str):
    """
    Converts a season string (e.g., "2022-23" or "2023") into a tuple (season_year, season_range)
    where season_year is the ending year.
    """
    season_match = re.search(r'(\d{4})\s*[-–]\s*(\d{2,4})', season_str)
    if season_match:
        start_year = int(season_match.group(1))
        end_year_part = season_match.group(2)
        if len(end_year_part) == 2:
            season_year = int(str(start_year)[:2] + end_year_part)
        else:
            season_year = int(end_year_part)
        season_range = f"{season_match.group(1)}-{end_year_part}"
        return season_year, season_range
    else:
        season_year = int(season_str)
        return season_year, season_str

def parse_user_query(user_query: str):
    """
    Extracts a single player's name, season year, and season range from the query.
    Supports queries like "lebron 2023 per game stats".
    """
    # --- Season extraction ---
    season_year = None
    season_range = None
    season_match = re.search(r'(\d{4}\s*[-–]\s*\d{2,4})', user_query)
    if season_match:
        season_str = season_match.group(1).replace(" ", "")
        season_year, season_range = parse_season(season_str)
    else:
        single_year_match = re.search(r'\b(\d{4})\b', user_query)
        if single_year_match:
            season_year = int(single_year_match.group(1))
            season_range = single_year_match.group(1)
        else:
            season_year = 2023
            season_range = "2023"

    # --- Player name extraction ---
    player_name = None
    # Try common patterns
    name_match = re.search(r"what are\s+(.+?)'s", user_query, re.IGNORECASE)
    if not name_match:
        name_match = re.search(r"stats for\s+([A-Za-z\s\.\-']+)", user_query, re.IGNORECASE)
    if name_match:
        player_name = name_match.group(1).strip()
    else:
        tokens = user_query.split()
        name_tokens = []
        skip_words = {'per', 'game', 'stats', 'general'}
        for token in tokens:
            if re.match(r'\d{4}[-–]\d{2,4}', token) or (token.isdigit() and len(token)==4):
                break
            if token.lower() in skip_words:
                continue
            name_tokens.append(token)
        if name_tokens:
            player_name = " ".join(name_tokens)
        else:
            player_name = "LeBron James"
    return player_name, season_year, season_range

def parse_comparison_query(user_query: str):
    """
    Extracts two players' names and season info for a comparison query.
    Expected format: "compare LeBron 2022-23 vs Stephen Curry 2021-22"
    Returns a tuple: (player1, season_year1, season_range1, player2, season_year2, season_range2)
    """
    pattern = re.compile(
        r"compare\s+(.+?)\s+(\d{4}(?:[-–]\d{2,4})?)\s+(?:vs|versus|and)\s+(.+?)\s+(\d{4}(?:[-–]\d{2,4})?)",
        re.IGNORECASE
    )
    match = pattern.search(user_query)
    if match:
        player1 = match.group(1).strip()
        season1_str = match.group(2).strip()
        player2 = match.group(3).strip()
        season2_str = match.group(4).strip()
        season_year1, season_range1 = parse_season(season1_str)
        season_year2, season_range2 = parse_season(season2_str)
        return player1, season_year1, season_range1, player2, season_year2, season_range2
    else:
        return "LeBron James", 2023, "2023", "Stephen Curry", 2023, "2023"

def parse_general_query(user_query: str):
    """
    For general league queries (e.g., "Who led the NBA in scoring in 2023?"),
    this function extracts the requested stat keyword and season.
    Returns (stat_key, season_year, season_range).
    
    The mapping below translates common query words to data keys:
      - "scor" or "points" or "ppg"  -> "points"
      - "assist"                   -> "assists"
      - "rebound"                  -> "rebounds"  (special: combined oreb+dreb)
      - "technical"                -> "technical_fouls" (if available)
    """
    # Default values:
    stat_key = "points"  # default to scoring
    season_year = 2023
    season_range = "2023"
    
    # Extract season info from query:
    season_match = re.search(r'(\d{4}\s*[-–]\s*\d{2,4})', user_query)
    if season_match:
        season_str = season_match.group(1).replace(" ", "")
        season_year, season_range = parse_season(season_str)
    else:
        single_year_match = re.search(r'\b(\d{4})\b', user_query)
        if single_year_match:
            season_year = int(single_year_match.group(1))
            season_range = single_year_match.group(1)
    
    # Determine which stat is requested.
    query_lower = user_query.lower()
    if "scor" in query_lower or "ppg" in query_lower or "points" in query_lower:
        stat_key = "points"
    elif "assist" in query_lower:
        stat_key = "assists"
    elif "rebound" in query_lower:
        stat_key = "rebounds"  # We'll handle this specially in get_league_leader.
    elif "technical" in query_lower:
        stat_key = "technical_fouls"
    
    return stat_key, season_year, season_range

def generate_response(user_query: str) -> str:
    """
    Main function to handle user queries.
    Branches based on query type:
      - "per_game": Returns a single player's per game stats.
      - "comparison": Compares per game stats of two players.
      - "general": Answers league questions like "Who led the NBA in scoring in 2023?"
    """
    query_type = determine_query_type(user_query)
    
    if query_type == "per_game":
        player_name, season_year, season_range = parse_user_query(user_query)
        stats = get_player_season_totals(player_name, season_year)
        if not stats:
            data_snippet = f"No stats found for {player_name} for the {season_range} season."
        else:
            games = stats['games_played'] if stats['games_played'] != 0 else 1
            ppg  = stats['points'] / games
            apg  = stats['assists'] / games
            orpg = stats['offensive_rebounds'] / games
            drpg = stats['defensive_rebounds'] / games
            rpg  = (stats['offensive_rebounds'] + stats['defensive_rebounds']) / games
            tpg  = stats['turnovers'] / games
            fga  = stats['attempted_field_goals'] / games
            fta  = stats['attempted_free_throws'] / games
            data_snippet = (
                f"In the {season_range} NBA season, {stats['name']} played in {stats['games_played']} games. "
                f"Here are his per game stats: PPG: {ppg:.1f}, APG: {apg:.1f}, RPG: {rpg:.1f}, "
                f"OREB: {orpg:.1f}, DREB: {drpg:.1f}, TO: {tpg:.1f}, FGA: {fga:.1f}, FTA: {fta:.1f}."
            )
    elif query_type == "comparison":
        player1, season_year1, season_range1, player2, season_year2, season_range2 = parse_comparison_query(user_query)
        stats1 = get_player_season_totals(player1, season_year1)
        stats2 = get_player_season_totals(player2, season_year2)
        if not stats1 or not stats2:
            data_snippet = "Stats not found for one or both players."
        else:
            games1 = stats1['games_played'] if stats1['games_played'] != 0 else 1
            games2 = stats2['games_played'] if stats2['games_played'] != 0 else 1
            ppg1 = stats1['points'] / games1
            apg1 = stats1['assists'] / games1
            rpg1 = (stats1['offensive_rebounds'] + stats1['defensive_rebounds']) / games1
            ppg2 = stats2['points'] / games2
            apg2 = stats2['assists'] / games2
            rpg2 = (stats2['offensive_rebounds'] + stats2['defensive_rebounds']) / games2
            data_snippet = (
                f"Comparison of per game stats:\n"
                f"{stats1['name']} ({season_range1}): PPG: {ppg1:.1f}, APG: {apg1:.1f}, RPG: {rpg1:.1f}\n"
                f"{stats2['name']} ({season_range2}): PPG: {ppg2:.1f}, APG: {apg2:.1f}, RPG: {rpg2:.1f}."
            )
    elif query_type == "general":
        stat_key, season_year, season_range = parse_general_query(user_query)
        leader, avg_value = get_league_leader(stat_key, season_year)
        if not leader:
            data_snippet = f"Could not determine a league leader for {stat_key} in the {season_range} season."
        else:
            # Special handling: if stat_key is "rebounds", avg_value is computed as combined oreb+dreb.
            label = stat_key.upper() if stat_key != "rebounds" else "RPG"
            data_snippet = (
                f"In the {season_range} NBA season, {leader['name']} led the league with a per game average of {avg_value:.1f} {label}."
            )
    else:
        data_snippet = "Query type not recognized."
    
    system_prompt = (
        "You are an NBA stats assistant. You have the following stats from a reliable source. "
        "Provide a brief answer using only the specified acronyms: "
        "(for per game: PPG, APG, RPG, OREB, DREB, TO, FGA, FTA; "
        "for general queries, simply answer with the stat abbreviation and value). "
        "Do NOT clarify acronyms.\n"
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
    return response.choices[0].message.content
