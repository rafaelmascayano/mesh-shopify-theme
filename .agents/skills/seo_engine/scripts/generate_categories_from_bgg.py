import time

import requests
import xmltodict

BGG_SEARCH = "https://boardgamegeek.com/xmlapi2/search"
BGG_GAME = "https://boardgamegeek.com/xmlapi2/thing"


def safe_xml_parse(text):
    if not text.strip().startswith("<"):
        return None

    try:
        return xmltodict.parse(text)
    except Exception:
        return None


def search_game(name):

    params = {"query": name, "type": "boardgame"}

    r = requests.get(BGG_SEARCH, params=params)

    data = safe_xml_parse(r.text)

    if not data:
        print("BGG returned invalid response")
        return None

    items = data.get("items", {}).get("item")

    if not items:
        return None

    if isinstance(items, list):
        return items[0]["@id"]

    return items["@id"]


def get_game_data(game_id):

    while True:
        r = requests.get(BGG_GAME, params={"id": game_id})

        # BGG sometimes responds 202 while preparing data
        if r.status_code == 202:
            print("BGG preparing data, waiting...")
            time.sleep(2)
            continue

        break

    data = safe_xml_parse(r.text)

    if not data:
        print("Invalid XML for game:", game_id)
        return None

    item = data["items"]["item"]

    categories = []
    mechanics = []

    links = item.get("link", [])

    if not isinstance(links, list):
        links = [links]

    for link in links:
        if link["@type"] == "boardgamecategory":
            categories.append(link["@value"])

        if link["@type"] == "boardgamemechanic":
            mechanics.append(link["@value"])

    return {"categories": categories, "mechanics": mechanics}


def process_games(games):

    category_map = {}

    for game in games:
        print("Buscando:", game)

        game_id = search_game(game)

        if not game_id:
            print("No encontrado:", game)
            continue

        time.sleep(1)

        data = get_game_data(game_id)

        if not data:
            continue

        categories = data["categories"]

        for cat in categories:
            if cat not in category_map:
                category_map[cat] = []

            category_map[cat].append(game)

    return category_map


if __name__ == "__main__":
    games = [
        "Virus",
        "Doble",
        "Código Secreto",
        "Fantasma Blitz",
        "Catan",
        "Throw Throw Burrito",
        "Patchwork",
        "Unstable Unicorns",
        "Trio",
        "Sushi Go Party",
        "Heat",
        "Bang",
        "Abyss",
        "Terraforming Mars",
        "7 Wonders",
        "MUSE",
        "Pandemic",
        "Siege of Runedar",
        "Mall Madness",
        "Hidden Leaders",
        "Oltréé",
        "Marvel United",
    ]

    categories = process_games(games)

    print("\nCategorias detectadas:\n")

    for cat, games in categories.items():
        print(cat)

        for g in games:
            print("  -", g)

        print()
