from bs4 import BeautifulSoup
import re
from typing import Dict

class PokemonStats:
    def __init__(self, owner, species, curr_hp, max_hp):
        self.species = species
        self.owner = owner
        self.kill_count = 0
        self.matches_won = 0
        self.matches_lost = 0
        self.matches_played = 0
        self.times_fainted = 0
        self.moves_used = {}
        self.total_damage_taken = 0
        self.total_damage_dealt = 0
        self.max_hp = curr_hp
        self.curr_hp = max_hp

class PlayerStats:
    def __init__(self, name, id):
        self.name = name
        self.curr_id = id
        self.pokemon_usage = {}  
        self.item_usage = {}    
        self.matches_won = 0
        self.matches_lost = 0
        self.matches_played = 0

def parse_players(log_data):
    player_stats = {}
    for line in log_data.split('\n'):
        if line.startswith('|player|'):
            parts = line.split('|')
            player_id = parts[2]  # Extracting player ID
            player_name = parts[3]  # Extracting player name
            player_stats[player_name] = PlayerStats(name = player_name, # Initialize player statistics
                                                    id = player_id)  
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
    match_id = None

    # Variables to track the active Pokémon for each player
    active_pokemon = {}

    for line in log_data.split('\n'):
        parts = line.split('|')
        if len(parts) < 3:
            continue

        try:
            # Gets the timestamp for the of the match - Which makes it unique
            if parts[1] == 't:' and not match_id:
                match_id = parts[2]
            # Checks if a Pokémon is switched in
            if parts[1] == 'switch':
                trainer_pair, pokemon_species, hp_info = parts[2], parts[3], get_hp_info(parts[4])
                trainer_id, pokemon_name = break_up_trainer_pair(trainer_pair)
                player = get_player_by_id(trainer_id, player_stats)
                
                if ',' in pokemon_species:
                    pokemon_species, _ = pokemon_species.split(',', 1)
                else:
                    pokemon_species = pokemon_species

                # Stores active Pokémon for each player
                active_pokemon[trainer_id] = pokemon_name

                # Initializes Pokémon statistics if not already present
                if pokemon_name not in pokemon_stats:
                    pokemon_stats[pokemon_name] = PokemonStats(owner=player.name, 
                                                            species = pokemon_species,
                                                            curr_hp = hp_info['curr_hp'],
                                                            max_hp = hp_info['max_hp'])


            # Checks if a move is used
            elif parts[1] == 'move':
                trainer_pair, move_name, target_info = parts[2], parts[3], parts[4]
                trainer_id, attacking_pokemon_name = break_up_trainer_pair(trainer_pair)

                # Update move usage count for the active Pokémon
                if attacking_pokemon_name in active_pokemon.values():
                    if attacking_pokemon_name in pokemon_stats:
                        if move_name not in pokemon_stats[attacking_pokemon_name].moves_used:
                            pokemon_stats[attacking_pokemon_name].moves_used[move_name] = 0
                        pokemon_stats[attacking_pokemon_name].moves_used[move_name] += 1

            elif parts[1] == '-damage':
                trainer_pair, damage_str = parts[2], parts[3]
                trainer_id, target_pokemon_name = break_up_trainer_pair(trainer_pair)
                target_pokemon = pokemon_stats.get(target_pokemon_name)

                # Extract the damage taken and check if it results in fainting
                if damage_str != '0 fnt':
                    damage_taken = calculate_damage_info(damage_str, pokemon = target_pokemon)                 

                if 'fnt' in line:
                    # Update faint count for the target Pokémon
                    damage_taken = calculate_damage_info(damage_str, pokemon = target_pokemon, fainted = True)  
                    pokemon_stats[target_pokemon_name].times_fainted += 1

                    # Update kill count for the attacking Pokémon
                    if attacking_pokemon_name in active_pokemon.values():
                        if attacking_pokemon_name in pokemon_stats:
                            pokemon_stats[attacking_pokemon_name].kill_count += 1

                # Update total damage taken for the target Pokémon
                if target_pokemon_name in pokemon_stats:
                    pokemon_stats[target_pokemon_name].total_damage_taken += int(damage_taken)
            
            elif parts[1] == 'win':
                winner_name = parts[2]
                for player in player_stats.values():
                    player.matches_played += 1
                    if player.name == winner_name:
                        player.matches_won += 1
                    else:
                        player.matches_lost += 1
                for pokemon_name, pokemon in pokemon_stats.items():
                    pokemon.matches_played += 1
                    if pokemon.owner == winner_name:
                        pokemon.matches_won += 1
                    else:
                        pokemon.matches_lost += 1

                    pokemon_owner = player_stats[pokemon.owner]
                    if pokemon_name not in pokemon_owner.pokemon_usage:
                        pokemon_owner.pokemon_usage[pokemon_name] = 0
                    pokemon_owner.pokemon_usage[pokemon_name] += 1
                


        except Exception as e:
            print("Exception:", e)
            print("Error processing line:", line)
            print(parts)

    # Return the parsed Pokémon and player statistics
    return pokemon_stats, player_stats, match_id


def get_player_by_id(trainer_id: str, player_stats: Dict[str, PlayerStats]):
    for key, player in player_stats.items():
        if player.curr_id == trainer_id:
            return player

def break_up_trainer_pair(trainer_pair: str):
    """
    Splits up a trainer-poké pair string using regex.
    Example: 'p1a: Fedoregis The Drifblim' into ['p1', 'Fedoregis The Drifblim'].

    Args:
        trainer_pair (str): The trainer-poké pair string.

    Returns:
        trainer: The trainer id.
        pokemon_name: The Pokémon's given name.
    """
    trainer, pokemon_name = re.split(r':\s*', trainer_pair, maxsplit=1)
    trainer = trainer[:2]

    return trainer, pokemon_name


def get_hp_info(hp_string: str):
    hp_arr = [int(x) for x in hp_string.split('\\/')]

    hp_info = {'curr_hp': hp_arr[0],
                'max_hp': hp_arr[1]}

    return hp_info

def calculate_damage_info(hp_string: str, pokemon: PokemonStats, fainted = False):
    if not fainted:
        hp_info = get_hp_info(hp_string)
        curr_hp = hp_info['curr_hp']
    else:
        curr_hp = 0

    damage_dealt = pokemon.curr_hp - curr_hp

    return damage_dealt



def parse_log(file):
    log_data = get_log_data(file)
    player_stats = parse_players(log_data)
    pokemon_stats, player_stats, match_id = parse_battle(log_data, player_stats)
    return log_data, pokemon_stats, player_stats, match_id