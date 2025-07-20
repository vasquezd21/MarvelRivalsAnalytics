import subprocess
import json
import pandas as pd
import time # For potential delays if needed

# --- CONFIGURATION (ADJUST THESE) ---
# Path to your running Node.js MCP server executable.
# This is the 'dist/src/index.js' file that npm run build creates.
NODE_SERVER_EXECUTABLE_PATH = '/Users/dmv62/Projects/MarvelRivalsAnalytics/marvel-rivals-mcp-game-data/dist/src/index.js'

# User's exact in-game Marvel Rivals Name and Battletag
# IMPORTANT: Replace with an actual Marvel Rivals username for testing
# The API might require a specific format or existing player.
YOUR_MARVEL_RIVALS_ID = "Jawnjawnjawn" # Example: "Jawnjawnjawn" or "PlayerOne#NA1"

# --- Function to send MCP requests and get responses ---
def send_mcp_request(request_payload):
    """
    Sends an MCP request to the Node.js server via stdin/stdout.
    The Node.js server must be running as a subprocess.
    """
    process = None
    try:
        # Start the Node.js server as a subprocess
        # text=True handles encoding/decoding as UTF-8
        # bufsize=0 sets unbuffered I/O, important for real-time communication
        process = subprocess.Popen(
            ['node', NODE_SERVER_EXECUTABLE_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )

        # Send the JSON payload to the server's stdin, followed by a newline
        process.stdin.write(json.dumps(request_payload) + '\n')
        process.stdin.flush() # Ensure the data is sent immediately

        # Read the response from the server's stdout
        # The MCP server sends one JSON object per response, followed by a newline
        response_line = process.stdout.readline()

        # Read any stderr output from the server (for debugging server-side errors)
        # We give it a short time to finish writing stderr before closing
        time.sleep(0.1)
        stderr_output = process.stderr.read()

        if stderr_output:
            print("\n--- Node.js Server STDERR Output (for debugging) ---")
            print(stderr_output)
            print("----------------------------------------------------\n")

        # Terminate the Node.js server process after getting a response
        process.stdin.close()
        process.terminate() # Send SIGTERM
        process.wait(timeout=5) # Wait for it to terminate gracefully

        if response_line:
            return json.loads(response_line)
        else:
            print("Warning: No response received from Node.js server stdout.")
            return {"error": "No response from server"}

    except FileNotFoundError:
        print(f"Error: Node.js server executable not found at {NODE_SERVER_EXECUTABLE_PATH}")
        print("Please ensure the path is correct and 'npm run build' was successful.")
        return {"error": "Server executable not found"}
    except json.JSONDecodeError:
        print(f"Error decoding JSON response from server: {response_line.strip()}")
        print("Server might not be returning valid JSON. Check Node.js server logs.")
        return {"error": "Invalid JSON response"}
    except subprocess.TimeoutExpired:
        print("Error: Node.js server did not terminate in time.")
        process.kill() # Force kill if it doesn't terminate
        return {"error": "Server termination timeout"}
    except Exception as e:
        print(f"An unexpected error occurred during MCP communication: {e}")
        return {"error": str(e)}
    finally:
        if process and process.poll() is None: # If process is still running
            process.kill() # Ensure it's terminated


# --- Function to fetch player match history using MCP call_tool ---
def get_player_match_history_mcp(player_id):
    """
    Fetches match history for a given player ID by calling the 'getPlayerMatchHistory' tool
    on the MCP Marvel Rivals server. Returns a pandas DataFrame of processed match data.
    """
    # Construct the MCP 'call_tool' request payload
    call_tool_request = {
        "type": "request",
        "id": "match_history_request", # Unique request ID
        "params": {
            "type": "call_tool",
            "name": "getPlayerMatchHistory",
            "arguments": {
                "identifier": player_id
            }
        }
    }

    print(f"Sending 'getPlayerMatchHistory' tool call for player: {player_id}")
    response = send_mcp_request(call_tool_request)

    if response and not response.get('isError'):
        # The actual data is usually nested under 'content' and then 'text' for tool responses
        try:
            # MCP tool responses are often stringified JSON within a 'text' field
            content_text = response.get('content', [{}])[0].get('text')
            if content_text:
                raw_data = json.loads(content_text)
                print("Successfully received and parsed raw match history data from MCP server!")

                # --- DEBUGGING AID: UNCOMMENT TO SEE RAW JSON STRUCTURE ---
                # print("\n--- Raw JSON Response (first 1000 chars) ---")
                # print(json.dumps(raw_data, indent=4)[:1000])
                # print("...\n")

                # The exact key for the list of matches will depend on the actual API response.
                # Inspect the raw JSON output from the Node.js server to determine the correct key.
                # For Marvel Rivals API, match history might be directly an array or under a key like 'matches'.
                match_records = raw_data.get('matchHistory', []) # Common key, adjust if needed
                if not match_records:
                    print(f"Warning: No 'matchHistory' key found or it's empty in the response from API. Full JSON structure might be different.")
                    print("Please inspect the raw JSON output and adjust 'match_records = raw_data.get(...)' accordingly.")
                    return pd.DataFrame()

                processed_matches = []
                for match in match_records:
                    # Example of extracting common fields.
                    # YOU MUST ADJUST THESE KEYS AND ADD MORE BASED ON ACTUAL DATA IN EACH `match` OBJECT
                    processed_match = {
                        'match_id': match.get('matchId'),
                        'outcome': match.get('outcome'), # e.g., "Victory", "Defeat"
                        'map_name': match.get('mapName'),
                        'hero_played': match.get('heroPlayed'),
                        'duration_seconds': match.get('durationSeconds'),
                        'kills': match.get('kills'),
                        'deaths': match.get('deaths'),
                        'assists': match.get('assists'),
                        'damage_dealt': match.get('damageDealt'),
                        'healing_done': match.get('healingDone'),
                        'ultimate_uses': match.get('ultimateUses'),
                        'time_played_hero_seconds': match.get('timePlayedHeroSeconds'),
                        'game_mode': match.get('gameMode'),
                        'timestamp': match.get('timestamp') # Match timestamp
                    }
                    processed_matches.append(processed_match)

                return pd.DataFrame(processed_matches)
            else:
                print("Error: 'content' or 'text' field missing in MCP tool response.")
                print(f"Full MCP response: {json.dumps(response, indent=2)}")
                return pd.DataFrame()
        except json.JSONDecodeError:
            print("Error decoding inner JSON from MCP tool response 'text' field.")
            print(f"Raw 'text' content: {content_text}")
            return pd.DataFrame()
        except Exception as e:
            print(f"An unexpected error occurred during data processing: {e}")
            return pd.DataFrame()
    else:
        print(f"MCP tool call failed or returned an error: {response.get('content', [{}])[0].get('text', 'Unknown error')}")
        print(f"Full MCP response: {json.dumps(response, indent=2)}")
        return pd.DataFrame()


# --- Main execution block ---
if __name__ == "__main__":
    print("Starting Marvel Rivals Data Analysis Project.")
    print("This script will automatically start and stop the Node.js MCP server for each request.")
    print(f"Attempting to fetch data for player: {YOUR_MARVEL_RIVALS_ID}")

    # First, let's list the tools to confirm communication
    list_tools_request = {
        "type": "request",
        "id": "list_tools_initial",
        "params": {
            "type": "list_tools"
        }
    }
    print("\n--- Testing MCP Server Connection: Listing Tools ---")
    tools_response = send_mcp_request(list_tools_request)
    if tools_response and tools_response.get('tools'):
        print("MCP Server connected and listed tools successfully!")
        # print(json.dumps(tools_response.get('tools'), indent=2)) # Uncomment to see full tool list
    else:
        print("Failed to list tools from MCP Server. Check server path and logs.")
        print(json.dumps(tools_response, indent=2))
        exit() # Exit if we can't even list tools

    print("\n--- Fetching Player Match History ---")
    my_match_df = get_player_match_history_mcp(YOUR_MARVEL_RIVALS_ID)

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
        print("Please check the Node.js server's stderr output for errors and the API response structure.")
