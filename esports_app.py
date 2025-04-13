import streamlit as st
import requests
import google.generativeai as genai
import urllib3
import re
import json
import csv
import os
from bs4 import BeautifulSoup

# ----------------------------------------------------------------------------
# STREAMLIT CONFIG: Must be the first Streamlit command
# ----------------------------------------------------------------------------
st.set_page_config(page_title="EsportsBot AI", layout="centered")

# ----------------------------------------------------------------------------
# CONFIG & KEYS
# ----------------------------------------------------------------------------
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Replace these with your own keys
GEMINI_API_KEY = "AIzaSyAmTrwak5aM6WCTAqoPrL_XCM1VkzvS64E"
ESPORTS_API_KEY = "04ccf967a4efb358193fa74801d5151ae92526ed003f10ebc6b28e94d07a128"

genai.configure(api_key=GEMINI_API_KEY)

BASE_URL = "https://api.esportsearnings.com/v0/"

# ----------------------------------------------------------------------------
# OPTIONAL: CSV-BASED GAME ID MAPPING
# ----------------------------------------------------------------------------
CSV_FILENAME = "esports_games.csv"

def load_game_ids(csv_file=CSV_FILENAME):
    """
    Reads game IDs from a CSV file of format:
    game_id,game_name
    (or gameid,gamename)
    Returns a dictionary mapping lowercased name -> game_id (string).
    """
    game_map = {}
    if not os.path.exists(csv_file):
        return game_map

    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            # Attempt to figure out header
            reader = csv.DictReader(f)
            headers = [h.lower() for h in reader.fieldnames]
            # Expect something like ["game_id", "game_name"] or ["gameid","gamename"]
            col_id = None
            col_name = None
            for h in headers:
                if "id" in h:
                    col_id = h
                if "name" in h:
                    col_name = h

            for row in reader:
                raw_id = row[col_id].strip()
                raw_name = row[col_name].strip().lower()
                game_map[raw_name] = raw_id

        return game_map
    except Exception as e:
        st.error(f"Failed to parse {csv_file}: {e}")
        return {}

# Load the map once at startup
GAME_ID_MAP = load_game_ids()

# ----------------------------------------------------------------------------
# GEMINI LLM CALL
# ----------------------------------------------------------------------------
def gemini_flash(prompt: str) -> str:
    """
    Uses Google Gemini 2.0 Flash to generate a content response.
    """
    # Return the generated text (often found at `response.generations[0].text`)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text

# ----------------------------------------------------------------------------
# ESPORTS API CALL
# ----------------------------------------------------------------------------
def call_esports_api(endpoint: str, params: dict) -> dict:
    """
    Calls Esports Earnings API with specified endpoint and parameters.
    Expects JSON output (default).
    """
    params["apikey"] = ESPORTS_API_KEY
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", params=params, verify=False)
        if not response.text.strip():
            return {"error": "Empty response from the API. Possibly invalid parameters."}
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# ----------------------------------------------------------------------------
# IMAGE URL EXTRACTOR
# ----------------------------------------------------------------------------
def extract_image_urls(text: str):
    """
    Finds any image URLs (jpg, png, gif) in 'text' and returns them as a list.
    """
    return re.findall(r'(https?://\S+\.(?:jpg|jpeg|png|gif))', text)

# ----------------------------------------------------------------------------
# STREAMLIT UI
# ----------------------------------------------------------------------------
st.title("🎮 EsportsBot AI powered by Gemini 2.0 Flash")

user_query = st.text_input("Enter your query about esports earnings:")

if st.button("Get Information") and user_query:
    # 2) Use Gemini to decide the endpoint + params
    with st.spinner("🔍 Interpreting your request..."):
        prompt_api_format = f"""
You are a smart API assistant for an Esports data app.

Given the user query: \"{user_query}\"

You must choose the most relevant API method from this list:
- LookupPlayerById (use only if a specific player ID or name is known)
- LookupPlayerTournaments
- LookupHighestEarningPlayers
- LookupHighestEarningPlayersByGame
- LookupHighestEarningTeams
- LookupHighestEarningTeamsByGame
- LookupGameById
- LookupRecentTournaments
- LookupTournamentById
- LookupTournamentResultsByTournamentId
- LookupTournamentTeamResultsByTournamentId
- LookupTournamentTeamPlayersByTournamentId

LookupPlayerById

LookupPlayerById returns earnings for a single player.

Parameters:
apikey - The unique API Key associated with your account.
format - Format of the output. (default: JSON)
playerid - The unique ID associated with the player on the website.
Output:
NameFirst - Player's first name.
NameLast - Player's last name.
CurrentHandle - Player's currently used in-game handle or ID.
CountryCode - Two-letter country code based on the ISO 3166-1 alpha-2 standard.
WorldRanking - Worldwide prize money ranking.
CountryRanking - Country-specific prize money ranking determined by the player's country code.
TotalUSDPrize - Total prize money won by the player in US Dollars.
TotalTournaments - Number of tournaments the player has recorded results in.

LookupPlayerTournaments

LookupPlayerTournaments returns a list of 100 tournament results for a single player, sorted by date.

Parameters:
apikey - The unique API Key associated with your account.
format - Format of the output. (default: JSON)
playerid - The unique ID associated with the player on the website.
offset - The number of tournaments to skip before returning results. (default: 0)
Output:
RankText - Text associated with the player's placement in the tournament.
Prize - Raw value of the prize money issued in its original currency.
ExchangeRate - Exchange Rate to US Dollars on the date the tournament ended. Used to calculate value of prize money in USD.
CurrencyCode - Three-letter currency code based on the ISO 4217 standard.
TournamentName - Short-hand name of the tournament. (or full name if it's short enough)
EndDate - Date the tournament ended.
GameId - Unique identification number associated with a game on the site.
Note - Additional notes describing the curcumstances of the tournament result.
TeamPlayers - Number of players on the team, if applicable. Used to divide the prize money in earning calculations.

LookupHighestEarningPlayers

LookupHighestEarningPlayers returns a list of 100 players with the highest overall prize money won.

Parameters:
apikey - The unique API Key associated with your account.
format - Format of the output. (default: JSON)
offset - The number of players to skip before returning results. (default: 0)
Output:
PlayerId - Unique identification number associated with a player on the site.
NameFirst - Player's first name.
NameLast - Player's last name.
CurrentHandle - Player's currently used in-game handle or ID.
CountryCode - Two-letter country code based on the ISO 3166-1 alpha-2 standard.
TotalUSDPrize - Total prize money won by the player in US Dollars.

LookupGameById

LookupGameById returns the prize money for a single game.

Parameters:
apikey - The unique API Key associated with your account.
format - Format of the output. (default: JSON)
gameid - The unique ID associated with the game on the website.
Output:
GameName - Name of the game.
TotalUSDPrize - Total prize money awarded for the game in US Dollars.
TotalTournaments - Number of recorded tournaments for the game.
TotalPlayers - Number of players with records in the game.

LookupHighestEarningPlayersByGame

LookupHighestEarningPlayersByGame returns a list of 100 players with the highest overall prize money won.

Parameters:
apikey - The unique API Key associated with your account.
format - Format of the output. (default: JSON)
gameid - The unique ID associated with the game on the website.
offset - The number of players to skip before returning results. (default: 0)
Output:
PlayerId - Unique identification number associated with a player on the site.
NameFirst - Player's first name.
NameLast - Player's last name.
CurrentHandle - Player's currently used in-game handle or ID.
CountryCode - Two-letter country code based on the ISO 3166-1 alpha-2 standard.
TotalUSDPrize - Total prize money won by the player in US Dollars.

LookupRecentTournaments

LookupRecentTournaments returns a list of the latest 100 tournaments that ended chronologically.

Parameters:
apikey - The unique API Key associated with your account.
format - Format of the output. (default: JSON)
offset - The number of players to skip before returning results. (default: 0)
Output:
TournamentId - Unique identification number associated with a tournament on the site.
GameId - Unique identification number associated with a game on the site.
TournamentName - TournamentName - Short-hand name of the tournament. (or full name if it's short enough)
StartDate - Date the tournament started.
EndDate - Date the tournament ended.
Location - Town or city that the event took place (or "online" if it was held online).
Teamplay - Boolean determining whether the tournament was held between individuals (1v1, FFA) or teams (2v2, 3v3, 4v4, 5v5, etc.).
TotalUSDPrize - Total prize money awarded in the tournament in US Dollars.
Notes:
If "Teamplay" is false, use "LookupTournamentResultsByTournamentId" to retrieve results.
If "Teamplay" is true, use "LookupTournamentTeamResultsByTournamentId" to retrieve results, and "LookupTournamentTeamPlayersByTournamentId" to retrieve players.

LookupTournamentById

LookupTournamentById returns the prize money and other information for a single tournament.

Parameters:
apikey - The unique API Key associated with your account.
format - Format of the output. (default: JSON)
tournamentid - The unique ID associated with the tournament on the website.
Output:
GameId - Unique identification number associated with a game on the site.
TournamentName - TournamentName - Short-hand name of the tournament. (or full name if it's short enough)
StartDate - Date the tournament started.
EndDate - Date the tournament ended.
Location - Town or city that the event took place (or "online" if it was held online).
Teamplay - Boolean determining whether the tournament was held between individuals (1v1, FFA) or teams (2v2, 5v5, etc.).
TotalUSDPrize - Total prize money awarded in the tournament in US Dollars.
Notes:
If "Teamplay" is false, use "LookupTournamentResultsByTournamentId" to retrieve results.
If "Teamplay" is true, use "LookupTournamentTeamResultsByTournamentId" to retrieve results, and "LookupTournamentTeamPlayersByTournamentId" to retrieve players for those results.
Individual-based tournaments and team-based tournaments have two completely different methods of accounting for unknown players. See the notes of those methods for more information.

LookupTournamentResultsByTournamentId

LookupTournamentResultsByTournamentId returns a list of tournament placements for tournaments held between individuals (1v1, FFA). Use this method if "Teamplay" is set to false.

Parameters:
apikey - The unique API Key associated with your account.
format - Format of the output. (default: JSON)
tournamentid - The unique ID associated with the tournament on the website.
Output:
Ranking - Number that determines ordering on the list. Ranks 1, 2 and 3 are also used to show a gold, silver and bronze background respectively.
RankText - Formatted text associated with the player's placement in the tournament.
TeamId - Unique identification number associated with a team on the site.
TeamName - Name of the player's associated team.
PlayerId - Unique identification number associated with a player on the site.
CountryCode - Two-letter country code based on the ISO 3166-1 alpha-2 standard.
NameFirst - Player's first name.
NameLast - Player's last name.
CurrentHandle - Player's currently used in-game handle or ID.
ShowLastNameFirst - Boolean determining whether or not the last name should be displayed before the first name.
PrizeUSD - Prize money awarded to the player in US Dollars.
Notes:
For v0 of the API, "TeamId" and "TeamName" may not work as intended. The site currently has an unreliable method of determining team associations from individual and team earnings. This will be rectified in v1.
If a placement is associated with an unknown player, the "CurrentHandle" will be "##UNKNOWN##". "PlayerId" in this instance is only used to return a unique row for each unknown player and can be discarded.

LookupTournamentTeamResultsByTournamentId

LookupTournamentTeamResultsByTournamentId returns a list of tournament placements for tournaments held between teams (2v2, 5v5, etc.). Use this method if "Teamplay" is set to true.

Parameters:
apikey - The unique API Key associated with your account.
format - Format of the output. (default: JSON)
tournamentid - The unique ID associated with the tournament on the website.
Output:
Ranking - Number that determines ordering on the list. Ranks 1, 2 and 3 are also used to show a gold, silver and bronze background respectively.
RankText - Formatted text associated with the player's placement in the tournament.
TeamId - Unique identification number associated with a team on the site.
TeamName - Name of the player's associated team.
TournamentTeamId - Unique identification number associated with a team earning on the site. Not to be confused with "TeamId".
TournamentTeamName - Name of the team associated with the team placement.
PrizeUSD - Prize money awarded to the team in US Dollars. Divide this value by the number of players + UnknownPlayerCount to get the prize per player.
UnknownPlayerCount - Number of unknown players on the team. Used if the full roster of the team is not known to correct division with PrizeUSD.
Notes:
For v0 of the API, "TeamId" and "TeamName" may not work as intended. The site currently has an unreliable method of determining team associations for individual and team earnings. This will be rectified in v1.
"TournamentTeamId" refers to a team earning for a single tournament, while "TeamId" refers to a team record on the site.
"TournamentTeamName" is the name of the team specifically for the associated tournament. It may include the title sponsor where appropriate (Fnatic.MSI for Fnatic), or may not be associated with a team at all, such as an all-stars match or two players pairing up for a 2v2 tournament.
The "LookupTournamentTeamResultsByTournamentId" method should be called along with "LookupTournamentTeamPlayersByTournamentId". Use "TournamentTeamId" to associate players with their respective team earning.
Formula for calculating prize money for each player: PrizeUSD / (Number of known players + UnknownPlayerCount)
Number of known players retrieved from the "LookupTournamentTeamPlayersByTournamentId" method may be zero for some tournaments, and "UnknownPlayerCount" is usually zero. Ensure that you are not dividing by zero!

LookupTournamentTeamPlayersByTournamentId

LookupTournamentTeamPlayersByTournamentId returns a list of players associated with the "tournament teams" of a tournament. Use this method if "Teamplay" is set to true.

Parameters:
apikey - The unique API Key associated with your account.
format - Format of the output. (default: JSON)
tournamentid - The unique ID associated with the tournament on the website.
Output:
TournamentTeamId - Unique identification number associated with a team earning on the site. Used to group players with their associated team earning.
PlayerId - Unique identification number associated with a player on the site.
CountryCode - Two-letter country code based on the ISO 3166-1 alpha-2 standard.
NameFirst - Player's first name.
NameLast - Player's last name.
CurrentHandle - Player's currently used in-game handle or ID.
ShowLastNameFirst - Boolean determining whether or not the last name should be displayed before the first name.
Notes:
The "LookupTournamentTeamPlayersByTournamentId" method should be called along with "LookupTournamentTeamResultsByTournamentId". Use "TournamentTeamId" to associate players with their respective team earning.
Some team-based tournaments will return team earnings, but not players for those team earnings. This is because information on player rosters for those tournaments have not been added yet.

LookupHighestEarningTeams

LookupHighestEarningTeams returns a list of 100 teams with the highest overall prize money won.

Parameters:
apikey - The unique API Key associated with your account.
format - Format of the output. (default: JSON)
offset - The number of teams to skip before returning results. (default: 0)
Output:
TeamId - Unique identification number associated with a team on the site.
TeamName - Name of the team.
TotalUSDPrize - Total prize won by the team in US Dollars.
TotalTournaments - Total number of tournaments that a team received prize money in.

LookupHighestEarningTeamsByGame

LookupHighestEarningTeamsByGame returns a list of 100 teams with the highest prize money won for a specific game.

Parameters:
apikey - The unique API Key associated with your account.
format - Format of the output. (default: JSON)
gameid - The unique ID associated with the game on the website.
offset - The number of teams to skip before returning results. (default: 0)
Output:
TeamId - Unique identification number associated with a team on the site.
TeamName - Name of the team.
TotalUSDPrize - Total prize won by the team for the game in US Dollars.
TotalTournaments - Total number of tournaments for the game that a team received prize money in.

If the query mentions a player name (e.g., 'TenZ'), prioritize LookupPlayerById or LookupPlayerTournaments and set 'playerid' to the player name.
If the query references a game name, set 'gameid' to that name (e.g., 'valorant').
For match history, prefer LookupPlayerTournaments to get the latest tournament.

If the user references a game name, set \"gameid\" to that name (e.g. \"valorant\"), and we will resolve it from the csv.
If the user references a player name use LookupPlayerById.
Return ONLY a valid JSON object in this format:
{{
  \"endpoint\": \"<API_METHOD>\",
  \"params\": {{
    \"gameid\": \"valorant\",
    \"offset\": 0,
    \"tournamentid\": \"1234\"
  }}
}}
"""


        raw_output = gemini_flash(prompt_api_format)
        match = re.search(r'\{[\s\S]+\}', raw_output)

        if not match:
            st.error("Gemini did not produce a valid JSON format. Try rephrasing your query.")
            st.stop()

        try:
            api_request = json.loads(match.group())
            endpoint = api_request["endpoint"]
            params = api_request["params"]

            # If user typed a textual game name, map it using the CSV-based dictionary
            if "gameid" in params:
                potential_game_name = str(params["gameid"]).strip().lower()
                # If it's not numeric, try to map from CSV
                if not potential_game_name.isdigit() and potential_game_name:
                    if potential_game_name in GAME_ID_MAP:
                        params["gameid"] = GAME_ID_MAP[potential_game_name]
                    else:
                        st.warning(f"Could not find game '{potential_game_name}' in CSV. We only have {len(GAME_ID_MAP)} games.")
                        st.stop()

        except json.JSONDecodeError:
            st.error("Failed to parse JSON from Gemini. Try again.")
            st.stop()

    # 3) Call the Esports Earnings API
    with st.spinner(f"📡 Fetching data from Esports API ({endpoint})..."):
        api_data = call_esports_api(endpoint, params)
        if "error" in api_data:
            st.error(f"API Error: {api_data['error']}")
            st.stop()

    # 4) Summarize with Gemini
    with st.spinner("🧠 Summarizing..."):
        summarization_prompt = f"""
User asked: \"{user_query}\"

Here is the data from the API:
{json.dumps(api_data, indent=2)}

Summarize this info for a general user. If there's no direct match for age or certain fields,
please clarify the limitation. If any image URLs appear, mention them.
"""
        summary = gemini_flash(summarization_prompt)

    st.success("✅ Here's your answer:")
    st.write(summary)

    # 5) Check for any image URLs
    images = extract_image_urls(summary)
    if images:
        st.subheader("🖼️ Related Images:")
        for url in images:
            st.image(url, use_column_width=True)
