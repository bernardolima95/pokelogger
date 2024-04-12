import streamlit as st
from bs4 import BeautifulSoup

from pokeparser import parse_log

def main():
    st.title("Battle Log Parser")

    # File uploader widget
    uploaded_file = st.file_uploader("Upload HTML file", type="html")

    if uploaded_file is not None:
        # Parse log data if file is uploaded
        log_data, pokemon_stats, player_stats = parse_log(uploaded_file)
        st.text_area("Parsed Log Data", log_data, height=400)
        display_player_stats(pokemon_stats, player_stats)

def display_player_stats(pokemon_stats, player_stats):

    # Display player stats
    st.subheader("Player Stats")
    for player_id, player_stat in player_stats.items():
        st.write(f"Player ID: {player_stat.name}")
        st.write(f"Matches Won: {player_stat.matches_won}")
        st.write(f"Matches Lost: {player_stat.matches_lost}")

        # Display Pokémon usage stats for each player
        st.write("Pokémon Usage:")
        for pokemon, usage_count in player_stat.pokemon_usage.items():
            st.write(f"{pokemon}: {usage_count}")

        st.write("---")

    # Display Pokémon stats
    st.subheader("Pokémon Stats")
    for pokemon, pokemon_stat in pokemon_stats.items():
        st.write(f"Pokemon: {pokemon}")
        st.write(f"Owner: {pokemon_stat.owner}")
        st.write(f"Fainted Count: {pokemon_stat.kill_count}")
        st.write(f"Matches Won: {pokemon_stat.matches_won}")
        st.write(f"Times Fainted: {pokemon_stat.times_fainted}")
        st.write(f"Moves Used: {pokemon_stat.moves_used}")

        st.write("---")


if __name__ == "__main__":
    main()