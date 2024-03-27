import streamlit as st
import pandas as pd
from io import BytesIO
import altair as alt
from utils.poke_api import *

# Function to convert image to HTML image tag
def image_to_html(image_url):
    response = requests.get(image_url)
    img_data = response.content
    b64_img_data = base64.b64encode(img_data).decode('utf-8')
    return f'<img src="data:image/png;base64,{b64_img_data}" width="80">'

def chart_visualization(df):
    # Create DataFrames for distribution visualizations
    type_data = {"Type": [t for types in df["Types"] for t in types]}
    type_df = pd.DataFrame(type_data)

    ability_data = {"Ability": [a for abilities in df["Abilities"] for a in abilities]}
    ability_df = pd.DataFrame(ability_data)

    egg_group_data = {"Egg Group": [e for egg_groups in df["Egg Groups"] for e in egg_groups]}
    egg_group_df = pd.DataFrame(egg_group_data)

    # Create Altair charts for distribution visualizations
    type_chart = alt.Chart(type_df).mark_bar().encode(
        x=alt.X("Type", axis=alt.Axis(labelAngle=0)),
        y="count()",
        tooltip=["Type", "count()"]
    ).properties(
        title="Type Distribution"
    )

    ability_chart = alt.Chart(ability_df).mark_bar().encode(
        x=alt.X("Ability", axis=alt.Axis(labelAngle=0)),
        y="count()",
        tooltip=["Ability", "count()"]
    ).properties(
        title="Ability Distribution"
    )

    egg_group_chart = alt.Chart(egg_group_df).mark_bar().encode(
        x=alt.X("Egg Group", axis=alt.Axis(labelAngle=0)),
        y="count()",
        tooltip=["Egg Group", "count()"]
    ).properties(
        title="Egg Group Distribution"
    )

    with st.expander("Distribution Charts"):
        # Display the distribution charts
        st.altair_chart(type_chart, use_container_width=True)
        st.altair_chart(ability_chart, use_container_width=True)
        st.altair_chart(egg_group_chart, use_container_width=True)



if __name__ == "__main__":
    st.set_page_config(layout="wide")
    st.title("Pokémon Team Builder")

    if "team" not in st.session_state:
        st.session_state.team = []

    # Fetch Pokémon types, regions, abilities, egg groups, and generations
    pokemon_types = fetch_pokemon_types()
    pokemon_regions = fetch_pokemon_regions()
    pokemon_abilities = fetch_pokemon_abilities()
    pokemon_egg_groups = fetch_pokemon_egg_groups()
    pokemon_generations = list(range(1, 9))
    # Fetch all Pokémon names
    pokemon_names = fetch_all_pokemon_names()

    # User input for filters
    selected_name = st.sidebar.selectbox("Select the Pokémon:", [""] + pokemon_names)
    selected_type = st.sidebar.selectbox("Select the primary Pokémon type:", [""] + pokemon_types)
    selected_type2 = st.sidebar.selectbox("Select the secondary Pokémon type (optional):", [""] + pokemon_types)
    selected_region = st.sidebar.selectbox("Select a Pokémon region:", [""] + pokemon_regions)
    selected_ability = st.sidebar.selectbox("Select a Pokémon ability:", [""] + pokemon_abilities)
    selected_egg_group = st.sidebar.selectbox("Select a Pokémon egg group:", [""] + pokemon_egg_groups)
    selected_generation = st.sidebar.selectbox("Select a Pokémon generation:",
                                       [""] + [str(gen) for gen in pokemon_generations])

    if selected_name or selected_type:
        # Fetch Pokémon data based on filters
        pokemon_list = fetch_pokemon_data(selected_name, selected_type, selected_type2, selected_region, selected_ability, selected_egg_group)
        if selected_name:
            pokemon_list = [pokemon for pokemon in pokemon_list if selected_name.lower() in pokemon.lower()]

        if pokemon_list:
            pokemon_data = get_pokemon_data(pokemon_list, selected_generation)

            if pokemon_data:
                df = pd.DataFrame(pokemon_data)

                col1, col2 = st.columns([2, 4])


                with col1:
                    select_tile = st.container(height=600)
                    # Display Pokémon names and radio buttons
                    selected_pokemon = select_tile.radio("Select a Pokémon", [data["Name"] for data in pokemon_data])


                with col2:
                    # Display Pokémon detail view
                    if selected_pokemon:
                        detail_tile = st.container(height=600)

                        pokemon_info = next(data for data in pokemon_data if data["Name"] == selected_pokemon)
                        detail_tile.subheader(f"Nat Dex No. {pokemon_info['National Dex #']} {selected_pokemon}")
                        try:
                            detail_tile.image([pokemon_info["Sprite"], pokemon_info["Shiny Sprite"]], width=100)
                        except:
                            detail_tile.write("Image not found :(")

                        # Create a DataFrame for the Pokémon details
                        details_dict = [
                            ["Gen", "Types", "Abilities", "Hidden Ability", "Egg Groups"],
                            [
                                pokemon_info["Generation"],
                                ", ".join(pokemon_info["Types"]),
                                ", ".join(pokemon_info["Abilities"]),
                                pokemon_info["Hidden Ability"],
                                ", ".join(pokemon_info["Egg Groups"])
                            ]
                        ]

                        # Add stats to the DataFrame
                        stats_dict = [[stat_name for stat_name in pokemon_info["Stats"]], [pokemon_info["Stats"][stat_name] for stat_name in pokemon_info["Stats"]]]

                        details_df = pd.DataFrame(details_dict[1:],columns=details_dict[0])
                        stat_df = pd.DataFrame(stats_dict[1:], columns=stats_dict[0])

                        # Display the DataFrame as a table
                        detail_tile.dataframe(details_df, hide_index=True, use_container_width=True)
                        detail_tile.dataframe(stat_df, hide_index=True, use_container_width=True)

                        # Display weaknesses, resistances, and immunities
                        weaknesses, resistances, immunities = pokemon_info['Weaknesses'], pokemon_info['Resistances'], pokemon_info['Immunities']
                        data = [", ".join(weaknesses) if weaknesses else "None", ", ".join(resistances) if resistances else "None", ", ".join(immunities) if immunities else "None"]
                        type_matchup_df = pd.DataFrame(data, index=['Weaknesses', 'Resistances', 'Immunities'], columns=['Types'])
                        detail_tile.dataframe(type_matchup_df, use_container_width=True)

                        chart_visualization(df)

                if col1.button("Add to Team"):
                    if len(st.session_state.team) == 6:
                        st.error("NO MORE")
                    else:
                        st.session_state.team.append(pokemon_info)
                        st.success(f"{selected_pokemon} added to the team!")

        else:
            st.warning("No Pokémon found for the specified filters.")
    else:
        st.warning("No Pokémon found for the specified filters.")

    shiny_team = st.toggle("Shiny Team")

    if len(st.session_state.team) > 0:
        team_data = []
        team_data.append([pokemon_details['Name']  for pokemon_details in st.session_state.team])
        if shiny_team:
            team_data.append([image_to_html(pokemon_details['Shiny Sprite']) for pokemon_details in st.session_state.team])
        else:
            team_data.append([image_to_html(pokemon_details['Sprite'])  for pokemon_details in st.session_state.team])
        team_data.append([', '.join(pokemon_details['Types'])  for pokemon_details in st.session_state.team])
        team_data.append([', '.join(pokemon_details['Abilities'] + [pokemon_details['Hidden Ability']])  for pokemon_details in st.session_state.team])

        # Convert the Pokémon data to a DataFrame
        team_df = pd.DataFrame(team_data, index=['Name', 'Sprite', 'Types', 'Abilities'])

        # Display the DataFrame as an HTML table
        st.write(team_df.to_html(escape=False, index=True), unsafe_allow_html=True)

        team_weaknesses, team_resistances, team_coverage = calculate_team_effectiveness(st.session_state.team)

        weakness_text = ", ".join([f"{type_}: {multiplier}x" for type_, multiplier in team_weaknesses.items()])
        team_weakness = ["Weaknesses", weakness_text]

        resistance_text = ", ".join([f"{type_}: {multiplier}x" for type_, multiplier in team_resistances.items()])
        team_resistance = ["Resistances", resistance_text]

        coverage_text = ", ".join([f"{type_}: {multiplier}x" for type_, multiplier in team_coverage.items()])
        team_cover= ["Coverage", coverage_text]

        team_calc = pd.DataFrame([team_weakness, team_resistance, team_cover], columns=['', 'Types'])
        st.dataframe(team_calc, hide_index=True, use_container_width=True)


    else:
        st.write("No Team :(")
    if st.button("Clear Team"):
        st.session_state.team = []