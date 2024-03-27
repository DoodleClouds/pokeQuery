import requests
import time
import streamlit as st
import base64


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

@st.cache_data
def fetch_all_pokemon_names():
    print("Fetching all pokemon names")
    pokemon_names = []
    url = "https://pokeapi.co/api/v2/pokemon?limit=1000"
    data = make_api_request(url)
    if data:
        pokemon_names = [pokemon["name"] for pokemon in data["results"]]
    return pokemon_names

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
@st.cache_data
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
def fetch_pokemon_data(pokemon_name, pokemon_type, pokemon_type2, pokemon_region, pokemon_ability, pokemon_egg_group):
    print("Fetching pokemon data")
    pokemon_list = []

    # Fetch Pokémon by name (if provided)
    if pokemon_name:
        url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
        data = make_api_request(url)
        if data:
            pokemon_list.append(data["name"])

    # Fetch Pokémon by type
    if pokemon_type:
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
@st.cache_data
def fetch_pokemon_details(pokemon_name):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}"
    return make_api_request(url)


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

def get_super_effective_types(type_):
    url = f"https://pokeapi.co/api/v2/type/{type_}"
    data = make_api_request(url)
    if data:
        damage_relations = data["damage_relations"]
        super_effective_types = [type_info["name"] for type_info in damage_relations["double_damage_to"]]
        return super_effective_types
    else:
        return []
def calculate_team_effectiveness(team):
    team_coverage = {}
    team_weaknesses = {}
    team_resistances = {}
    for pokemon_info in team:
        weaknesses, resistances, immunities = pokemon_info['Weaknesses'], pokemon_info['Resistances'], pokemon_info['Immunities']

        for type in weaknesses:
            if type in team_weaknesses:
                team_weaknesses[type] += 1
            else:
                team_weaknesses[type] = 1

        for type in resistances:
            if type in team_resistances:
                team_resistances[type] += 1
            else:
                team_resistances[type] = 1

        for type in pokemon_info["Types"]:
            coverage = get_super_effective_types(type)
            for type_cov in coverage:
                if type_cov in team_coverage:
                    team_coverage[type_cov] += 1
                else:
                    team_coverage[type_cov] = 1

    return team_weaknesses, team_resistances, team_coverage