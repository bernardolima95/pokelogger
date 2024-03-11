from bs4 import BeautifulSoup

class PokemonStats:
    def __init__(self, owner):
        self.owner = owner
        self.fainted_count = 0
        self.matches_won = 0
        self.times_fainted = 0
        self.moves_used = {}

class PlayerStats:
    def __init__(self):
        self.pokemon_usage = {}  
        self.item_usage = {}    
        self.matches_won = 0
        self.matches_lost = 0

def parse_players(log_data):
    player_stats = {}
    for line in log_data.split('\n'):
        if line.startswith('|player|'):
            parts = line.split('|')
            player_id = parts[2]  # Extracting player ID
            player_name = parts[3]  # Extracting player name
            player_stats[player_id] = PlayerStats()  # Initialize player statistics
    return player_stats


def get_log_data(file):
    # Read the contents of the file
    content = file.read()

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')

    # Find the <script> tag with class "battle-log-data"
    script_tag = soup.find('script', {'class': 'battle-log-data'})

    # Extract the log data from the <script> tag
    if script_tag:
        log_data = script_tag.string
        return log_data
    else:
        return "Log data not found in the HTML file."

def parse_battle(log_data, player_stats):
    # Initialize dictionaries to store Pokémon and player statistics
    pokemon_stats = {}

    # Variables to track the active Pokémon for each player
    active_pokemon = {}

    for line in log_data.split('\n'):
        parts = line.split('|')
        if len(parts) < 3:
            continue

        try:
            # Check if a Pokémon is switched in
            if parts[1] == 'switch':
                player_id, active_pokemon_name, hp_info = parts[2], parts[3], parts[4]
                if ',' in active_pokemon_name:
                    pokemon_name, _ = active_pokemon_name.split(',', 1)
                else:
                    pokemon_name = active_pokemon_name

                # Store active Pokémon for each player
                active_pokemon[player_id] = pokemon_name

                # Initialize Pokémon statistics if not already present
                if pokemon_name not in pokemon_stats:
                    pokemon_stats[pokemon_name] = PokemonStats(owner=player_id)

                # Update Pokémon usage count for the player
                if player_id in player_stats:
                    if pokemon_name not in player_stats[player_id].pokemon_usage:
                        player_stats[player_id].pokemon_usage[pokemon_name] = 0
                    player_stats[player_id].pokemon_usage[pokemon_name] += 1

            # Check if a move is used
            elif parts[1] == 'move':
                player_id, move_name, target_info = parts[2], parts[3], parts[4]

                # Update move usage count for the active Pokémon
                if player_id in active_pokemon:
                    pokemon_name = active_pokemon[player_id]
                    if pokemon_name in pokemon_stats:
                        if move_name not in pokemon_stats[pokemon_name].moves_used:
                            pokemon_stats[pokemon_name].moves_used[move_name] = 0
                        pokemon_stats[pokemon_name].moves_used[move_name] += 1

            # Add logic to handle faint events and update faint counts
            elif parts[1] == 'faint':
                player_id, pokemon_info = parts[2], parts[3]

                # Extract Pokémon name
                if ':' in pokemon_info:
                    pokemon_name = ' '.join(pokemon_info.split(':')[1:])
                else:
                    pokemon_name = pokemon_info

                # Update faint count for the Pokémon
                if pokemon_name in pokemon_stats:
                    pokemon_stats[pokemon_name].fainted_count += 1

        except Exception as e:
            print("Exception:", e)
            print("Error processing line:", line)
            print(parts)

    # Return the parsed Pokémon and player statistics
    return pokemon_stats, player_stats









def parse_log(file):
    log_data = get_log_data(file)
    player_stats = parse_players(log_data)
    pokemon_stats, player_stats = parse_battle(log_data, player_stats)
    return log_data, pokemon_stats, player_stats