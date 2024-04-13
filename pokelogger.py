import streamlit as st
from collections import Counter
import pandas as pd
import base64
from PIL import Image
from io import BytesIO

from pokeparser import parse_log

pokemon_images_folder = 'icons'

matches = {}

def main():
    st.title("Battle Log Parser")

    # File uploader widget
    uploaded_files = st.file_uploader("Upload HTML file", type="html", accept_multiple_files=True)

    if uploaded_files:

        for file in uploaded_files:
            log_data, pokemon_stats, player_stats, match_id = parse_log(file)
            if match_id not in matches:
                matches[match_id] = {'pokemon_stats': pokemon_stats, 
                                    'player_stats': player_stats,
                                    'log_data': log_data}
        
        pokemon_stats_agg, player_stats_agg, moves_used_agg, pokemon_usage_agg = aggregate_data(matches)
        print(matches)

        #st.text_area("Parsed Log Data", log_data, height=400)
        display_player_stats(pokemon_stats_agg, player_stats_agg)

def aggregate_data(matches):
    pokemon_stats_agg = {}
    player_stats_agg = {}
    moves_used_agg = {}
    pokemon_usage_agg = {}

    for match_data in matches.values():
        pokemon_stats = match_data['pokemon_stats']
        player_stats = match_data['player_stats']

        # Aggregate Pokemon stats
        for pokemon_handle, stats in pokemon_stats.items():
            key = (pokemon_handle, stats.owner)
            if key not in pokemon_stats_agg:
                pokemon_stats_agg[key] = stats
            else:
                agg_stats = pokemon_stats_agg[key]
                agg_stats.kill_count += stats.kill_count
                agg_stats.matches_won += stats.matches_won
                agg_stats.matches_lost += stats.matches_lost
                agg_stats.matches_played += stats.matches_played
                agg_stats.times_fainted += stats.times_fainted
                agg_stats.total_damage_taken += stats.total_damage_taken
                agg_stats.total_damage_dealt += stats.total_damage_dealt
                agg_stats.moves_used = Counter(agg_stats.moves_used) + Counter(stats.moves_used)

                for move, count in stats.moves_used.items():
                    moves_used_agg[move] = moves_used_agg.get(move, 0) + count

        # Aggregate Player stats
        for player_name, player_stat in player_stats.items():
            if player_name not in player_stats_agg:
                 player_stats_agg[player_name] = player_stat
            else:
                agg_stats = player_stats_agg[player_name]
                agg_stats.matches_won += player_stat.matches_won
                agg_stats.matches_lost += player_stat.matches_lost
                agg_stats.matches_played += player_stat.matches_played
                agg_stats.pokemon_usage = Counter(agg_stats.pokemon_usage) + Counter(player_stat.pokemon_usage)

                for pokemon, count in player_stat.pokemon_usage.items():
                    pokemon_usage_agg[pokemon] = pokemon_usage_agg.get(pokemon, 0) + count

    return pokemon_stats_agg, player_stats_agg, moves_used_agg, pokemon_usage_agg

def display_player_stats(pokemon_stats, player_stats):
    st.subheader("Player Stats")

    player_data = []
    for player_stat in player_stats.values():
        win_ratio = player_stat.matches_won / player_stat.matches_played
        player_row = {
            "Player ID": player_stat.name,
            "Matches Played": player_stat.matches_played,
            "Matches Won": player_stat.matches_won,
            "Matches Lost": player_stat.matches_lost,
            "Win Ratio": win_ratio,
            "Pokémon Usage": ', '.join([f"{pokemon}: {count}" for pokemon, count in player_stat.pokemon_usage.items()])
        }
        player_data.append(player_row)

    player_df = pd.DataFrame(player_data)
    st.write(player_df)

    st.write("---")

    # Display Pokémon stats
    st.subheader("Pokémon Stats")

    # Create a DataFrame for Pokémon stats
    pokemon_data = []
    for pokemon, pokemon_stat in pokemon_stats.items():
        species_name = clean_species_name(pokemon_stat.species)
        pokemon_image_path = f"{pokemon_images_folder}/{species_name}.png"
        try:
            img_data = base64.b64encode(open(pokemon_image_path, "rb").read()).decode()
        except Exception as e:
            print(f"Error reading image for {pokemon_stat.species}: {e}")
            img_data = None

        k_d_ratio = pokemon_stat.kill_count / pokemon_stat.times_fainted if pokemon_stat.times_fainted != 0 else pokemon_stat.kill_count / 1
        win_ratio = pokemon_stat.matches_won / pokemon_stat.matches_played

        pokemon_row = {
            "Icon": f"data:image/png;base64,{img_data}",
            "Pokemon": pokemon[0],
            "Species": pokemon_stat.species,
            "Owner": pokemon_stat.owner,
            "Kill Count": pokemon_stat.kill_count,
            "Times Fainted": pokemon_stat.times_fainted,
            "K/D": k_d_ratio,
            "Matches Won": pokemon_stat.matches_won,
            "Matches Lost": pokemon_stat.matches_lost,
            "Matches Played": pokemon_stat.matches_played,
            "Win Ratio": win_ratio,
            "Moves Used": ', '.join([f"{move}: {count}" for move, count in pokemon_stat.moves_used.items()])
        }

        pokemon_data.append(pokemon_row)

    pokemon_df = pd.DataFrame(pokemon_data)

    st.dataframe(
        pokemon_df,
        column_config = {"Icon": st.column_config.ImageColumn()}
    )

def clean_species_name(name):
    cleaned_name = name.lower().replace(" ", "-")
    substr_to_remove = [":", ".", "-East", "-Three-Segment", "-Blue", "-Four", "-Three"]
    for substr in substr_to_remove:
        cleaned_name = cleaned_name.replace(substr, "")

    return cleaned_name.lower()

if __name__ == "__main__":
    main()