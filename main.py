import streamlit as st
import requests
import pandas as pd
import time
from io import BytesIO
import base64
import altair as alt

# Function to make API requests with retries
def make_api_request(url, max_retries=5, retry_delay=1):
    retries = 0
    while retries < max_retries:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            retries += 1
            time.sleep(retry_delay)
    return None

# Function to fetch Pokémon egg groups from the PokeAPI
@st.cache_data
def fetch_pokemon_egg_groups():
    url = "https://pokeapi.co/api/v2/egg-group"
    data = make_api_request(url)
    if data:
        return [egg_group["name"] for egg_group in data["results"]]
    else:
        return []

# Function to fetch Pokémon species details
def fetch_pokemon_species_details(pokemon_name):
    url = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_name}"
    return make_api_request(url)

# Function to fetch Pokémon types from the PokeAPI
@st.cache_data
def fetch_pokemon_types():
    url = "https://pokeapi.co/api/v2/type"
    data = make_api_request(url)
    if data:
        return [type_data["name"] for type_data in data["results"]]
    else:
        return []

# Function to fetch Pokémon regions from the PokeAPI
@st.cache_data
def fetch_pokemon_regions():
    url = "https://pokeapi.co/api/v2/pokedex"
    data = make_api_request(url)
    if data:
        return [region_data["name"] for region_data in data["results"]]
    else:
        return []

# Function to fetch Pokémon abilities from the PokeAPI
@st.cache_data
def fetch_pokemon_abilities():
    url = "https://pokeapi.co/api/v2/ability?limit=1000"  # Fetch up to 1000 abilities
    data = make_api_request(url)
    if data:
        abilities = []
        while data:
            abilities.extend([ability["name"] for ability in data["results"]])
            if data["next"]:
                data = make_api_request(data["next"])
            else:
                break
        return abilities
    else:
        return []


# Function to fetch Pokémon data from the PokeAPI based on type, region, and ability
@st.cache_data
def fetch_pokemon_data(pokemon_type, pokemon_type2, pokemon_region, pokemon_ability, pokemon_egg_group):
    print("Fetching pokemon data")
    pokemon_list = []

    # Fetch Pokémon by type
    url = f"https://pokeapi.co/api/v2/type/{pokemon_type}"
    type_data = make_api_request(url)
    if type_data:
        pokemon_list = [pokemon["pokemon"]["name"] for pokemon in type_data["pokemon"]]

    # Fetch Pokémon by secondary type (if provided)
    if pokemon_type2:
        url = f"https://pokeapi.co/api/v2/type/{pokemon_type2}"
        type2_data = make_api_request(url)
        if type2_data:
            type2_pokemon_list = [pokemon["pokemon"]["name"] for pokemon in type2_data["pokemon"]]
            pokemon_list = list(set(pokemon_list) & set(type2_pokemon_list))

    # Fetch Pokémon by region (if provided)
    if pokemon_region:
        url = f"https://pokeapi.co/api/v2/pokedex/{pokemon_region}"
        region_data = make_api_request(url)
        if region_data:
            region_pokemon_list = [entry["pokemon_species"]["name"] for entry in region_data["pokemon_entries"]]
            pokemon_list = list(set(pokemon_list) & set(region_pokemon_list))

    # Fetch Pokémon by ability (if provided)
    if pokemon_ability:
        url = f"https://pokeapi.co/api/v2/ability/{pokemon_ability}"
        ability_data = make_api_request(url)
        if ability_data:
            ability_pokemon_list = [pokemon["pokemon"]["name"] for pokemon in ability_data["pokemon"]]
            pokemon_list = list(set(pokemon_list) & set(ability_pokemon_list))

    # Fetch Pokémon by egg group (if provided)
    if pokemon_egg_group:
        url = f"https://pokeapi.co/api/v2/egg-group/{pokemon_egg_group}"
        egg_group_data = make_api_request(url)
        if egg_group_data:
            egg_group_pokemon_list = [pokemon["name"] for pokemon in egg_group_data["pokemon_species"]]
            pokemon_list = list(set(pokemon_list) & set(egg_group_pokemon_list))

    return pokemon_list

# Function to fetch additional Pokémon details
def fetch_pokemon_details(pokemon_name):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}"
    return make_api_request(url)

# Function to convert image to HTML image tag
def image_to_html(image_url):
    response = requests.get(image_url)
    img_data = response.content
    b64_img_data = base64.b64encode(img_data).decode('utf-8')
    return f'<img src="data:image/png;base64,{b64_img_data}" width="80">'

# Function to fetch Pokémon generation details
@st.cache_data
def fetch_pokemon_generation_details(pokemon_id):
    generation_id = (pokemon_id - 1) // 156 + 1
    return generation_id

# Function to fetch Pokémon type details
@st.cache_data
def fetch_pokemon_type_details(pokemon_name):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}"
    data = make_api_request(url)
    if data:
        types = [type_info["type"]["name"] for type_info in data["types"]]
        return types
    else:
        return []

# Function to calculate weaknesses, resistances, and immunities
@st.cache_data
def calculate_type_effectiveness(types):
    effectiveness = {
        "normal": 1, "fire": 1, "water": 1, "electric": 1, "grass": 1, "ice": 1,
        "fighting": 1, "poison": 1, "ground": 1, "flying": 1, "psychic": 1,
        "bug": 1, "rock": 1, "ghost": 1, "dragon": 1, "dark": 1, "steel": 1, "fairy": 1
    }

    for type_ in types:
        url = f"https://pokeapi.co/api/v2/type/{type_}"
        data = make_api_request(url)
        if data:
            damage_relations = data["damage_relations"]
            for relation, effectiveness_factor in [
                ("no_damage_from", 0),
                ("half_damage_from", 0.5),
                ("double_damage_from", 2)
            ]:
                for type_info in damage_relations[relation]:
                    effectiveness[type_info["name"]] *= effectiveness_factor

    weaknesses = [type_ for type_, value in effectiveness.items() if value > 1]
    resistances = [type_ for type_, value in effectiveness.items() if 0 < value < 1]
    immunities = [type_ for type_, value in effectiveness.items() if value == 0]

    return weaknesses, resistances, immunities
@st.cache_data
def get_pokemon_data(pokemon_list, selected_generation):
    print("Getting pokemon data")
    # Fetch additional details for each Pokémon
    pokemon_data = []
    for pokemon_name in pokemon_list:
        details = fetch_pokemon_details(pokemon_name)
        species_details = fetch_pokemon_species_details(pokemon_name)

        if details and species_details:
            generation = fetch_pokemon_generation_details(details["id"])
            if selected_generation and str(generation) != selected_generation:
                continue
            weaknesses, resistances, immunities = calculate_type_effectiveness(fetch_pokemon_type_details(pokemon_name))
            pokemon_data.append({
                "Name": details["name"].capitalize(),
                "National Dex #": details["id"],
                "Sprite": details["sprites"]["front_default"],
                "Shiny Sprite": details["sprites"]["front_shiny"],
                "Generation": generation,
                "Types": fetch_pokemon_type_details(pokemon_name),
                "Abilities": [ability["ability"]["name"] for ability in details["abilities"] if
                              not ability["is_hidden"]],
                "Hidden Ability": next(
                    (ability["ability"]["name"] for ability in details["abilities"] if ability["is_hidden"]), ""),
                "Egg Groups": [egg_group["name"] for egg_group in species_details.get("egg_groups", [])],
                "Stats": {
                    "HP": details["stats"][0]["base_stat"],
                    "Attack": details["stats"][1]["base_stat"],
                    "Defense": details["stats"][2]["base_stat"],
                    "Special Attack": details["stats"][3]["base_stat"],
                    "Special Defense": details["stats"][4]["base_stat"],
                    "Speed": details["stats"][5]["base_stat"]
                },
                "Weaknesses": weaknesses,
                "Resistances": resistances,
                "Immunities": immunities
            })
    return pokemon_data

# Streamlit app
# Streamlit app
def main():
    st.title("Pokémon Query App")

    # Fetch Pokémon types, regions, abilities, egg groups, and generations
    pokemon_types = fetch_pokemon_types()
    pokemon_regions = fetch_pokemon_regions()
    pokemon_abilities = fetch_pokemon_abilities()
    pokemon_egg_groups = fetch_pokemon_egg_groups()
    pokemon_generations = list(range(1, 9))

    # User input for filters
    selected_type = st.selectbox("Select the primary Pokémon type:", [""] + pokemon_types)
    selected_type2 = st.selectbox("Select the secondary Pokémon type (optional):", [""] + pokemon_types)
    selected_region = st.selectbox("Select a Pokémon region:", [""] + pokemon_regions)
    selected_ability = st.selectbox("Select a Pokémon ability:", [""] + pokemon_abilities)
    selected_egg_group = st.selectbox("Select a Pokémon egg group:", [""] + pokemon_egg_groups)
    selected_generation = st.selectbox("Select a Pokémon generation:", [""] + [str(gen) for gen in pokemon_generations])

    if selected_type:
        # Fetch Pokémon data based on filters
        pokemon_list = fetch_pokemon_data(selected_type, selected_type2, selected_region, selected_ability, selected_egg_group)

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
                        detail_tile.table(details_df)
                        detail_tile.table(stat_df)

                        # Display weaknesses, resistances, and immunities
                        weaknesses, resistances, immunities = pokemon_info['Weaknesses'], pokemon_info['Resistances'], pokemon_info['Immunities']
                        data = [", ".join(weaknesses) if weaknesses else "None", ", ".join(resistances) if resistances else "None", ", ".join(immunities) if immunities else "None"]
                        type_matchup_df = pd.DataFrame(data, index=['Weaknesses', 'Resistances', 'Immunities'], columns=['Types'])
                        detail_tile.table(type_matchup_df)

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

            else:
                st.warning("No Pokémon found for the specified filters.")
        else:
            st.warning("No Pokémon found for the specified filters.")

if __name__ == "__main__":
    main()