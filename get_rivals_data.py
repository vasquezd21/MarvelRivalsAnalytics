import requests
import pandas as pd
import json

# --- CONFIGURATION (ADJUST THESE) ---
# The base URL for your running MCP server (e.g., "http://localhost:3000")
# THIS MUST BE ADJUSTED BY THE USER BASED ON THEIR MCP SERVER'S OUTPUT
MCP_API_BASE_URL = "http://localhost:3000"
# User's exact in-game Marvel Rivals Name and Battletag
YOUR_MARVEL_RIVALS_ID = "YourPlayerName#YourTag" # Example: "IronManFan#1234"

# --- Function to fetch player match history ---
def get_player_match_history(player_id):
    """
    Fetches match history for a given player ID from the MCP Marvel Rivals server.
    Returns a pandas DataFrame of processed match data.
    """
    try:
        endpoint = f"{MCP_API_BASE_URL}/getPlayerMatchHistory"
        params = {"username": player_id}

        print(f"Attempting to fetch match history from: {endpoint} with username: {player_id}")
        response = requests.get(endpoint, params=params)
        response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)

        data = response.json()
        print("Successfully fetched raw match history data!")

        # --- DEBUGGING AID: UNCOMMENT TO SEE RAW JSON STRUCTURE ---
        # print("\n--- Raw JSON Response (first 1000 chars) ---")
        # print(json.dumps(data, indent=4)[:1000])
        # print("...\n")

        # The exact key for the list of matches will depend on the MCP server's response.
        # Common patterns are 'matches', 'data', 'matchHistory', etc.
        # USER MUST INSPECT THE RAW JSON OUTPUT TO DETERMINE THE CORRECT KEY.
        match_records = data.get('matches', []) # Placeholder: User to confirm actual key
        if not match_records:
            print(f"Warning: No 'matches' key found or it's empty in the response. Full JSON structure might be different.")
            print("Please inspect the raw JSON output and adjust 'match_records = data.get(...)' accordingly.")
            return pd.DataFrame()

        processed_matches = []
        for match in match_records:
            # Example of extracting common fields.
            # USER MUST ADJUST THESE KEYS AND ADD MORE BASED ON ACTUAL DATA IN `match` OBJECT
            processed_match = {
                'match_id': match.get('matchId'),
                'outcome': match.get('outcome'), # e.g., "Victory", "Defeat"
                'map_name': match.get('mapName'),
                'hero_played': match.get('heroPlayed'),
                'duration_seconds': match.get('durationSeconds'),
                # Add more relevant stats as found in the raw JSON for each match:
                # 'kills': match.get('kills'),
                # 'deaths': match.get('deaths'),
                # 'assists': match.get('assists'),
                # 'damage_dealt': match.get('damageDealt'),
                # 'healing_done': match.get('healingDone'),
                # 'ultimate_uses': match.get('ultimateUses'),
                # 'time_played_hero_seconds': match.get('timePlayedHeroSeconds')
            }
            processed_matches.append(processed_match)

        return pd.DataFrame(processed_matches)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from MCP server: {e}")
        print("Please ensure the 'MCP Marvel Rivals' server is running and accessible at the specified URL.")
        print(f"Tried to access: {endpoint} with params: {params}")
        return pd.DataFrame()
    except json.JSONDecodeError:
        print("Error decoding JSON response. Server might not be returning valid JSON.")
        return pd.DataFrame()
    except Exception as e:
        print(f"An unexpected error occurred during data processing: {e}")
        return pd.DataFrame()


# --- Main execution block ---
if __name__ == "__main__":
    print("Starting Marvel Rivals Data Analysis Project.")
    print("Ensure the 'MCP Marvel Rivals' server is running in a separate terminal.")
    print(f"Attempting to fetch data for player: {YOUR_MARVEL_RIVALS_ID}")

    my_match_df = get_player_match_history(YOUR_MARVEL_RIVALS_ID)

    if not my_match_df.empty:
        print("\n--- Successfully created DataFrame with match history ---")
        print(my_match_df.head())
        print(f"\nTotal matches fetched: {len(my_match_df)}")

        # Save to CSV for later analysis (or direct use in subsequent Python scripts)
        csv_filename = f"{YOUR_MARVEL_RIVALS_ID.replace('#', '_')}_match_history.csv"
        my_match_df.to_csv(csv_filename, index=False)
        print(f"\nMatch history saved to {csv_filename}")
    else:
        print("Could not retrieve match history or DataFrame is empty.")
        print("Please troubleshoot the MCP server setup and the `get_player_match_history` function's JSON parsing.")