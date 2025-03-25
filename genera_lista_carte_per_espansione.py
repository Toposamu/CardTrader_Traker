import requests
import json
import os
import time

# Carica il token API
API_TOKEN = "eyJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJjYXJkdHJhZGVyLXByb2R1Y3Rpb24iLCJzdWIiOiJhcHA6MTQ0MjAiLCJhdWQiOiJhcHA6MTQ0MjAiLCJleHAiOjQ4OTgwNzkyMzcsImp0aSI6ImZlN2JkYThiLTY3ZGYtNDZjYy04ZTIwLWJlZDZjMjRlZTA3MCIsImlhdCI6MTc0MjQwNTYzNywibmFtZSI6IlRvcG9zYW11ODggQXBwIDIwMjUwMzEyMDAzNjA3In0.gv-aou5pYn8T-L_rz3-j50QL90vuh_kkOBcGRoccS-FP3KO9OOLTzSliv1Dj71loevBVftQBif5Ob00VKlywuirb36TPtMBe8g_3n5Yeiwy8enkot1sV6qDiKJkq5MgDmJScLZ8b5alnNoFPQ67v8LTA7HcjmZW2wkRvLdlXyQdiSMhUgcM3LaBPxwJcypCwCrcfY97JAHKLKwiW3OJq4FRv8dLDVE0kbV324eiLYSxRRV6_ybVmnjfL0rlZ8xfE9z9YKkpIsGTztxWuz0VrPvDi6h3CFM5upukOHl4JLKZkYyAcIYtZ4_0EzuhseR7rWaqZbuvQzuIVQAQ3PwffZg"  # 🔴 Sostituisci con il tuo API Token
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

# Percorso della cartella dati
EXPANSIONS_FILE = "data/onepiece_expansions.json"
EXPANSIONS_FOLDER = "data/expansions"

# Assicuriamoci che la cartella per salvare le carte esista
os.makedirs(EXPANSIONS_FOLDER, exist_ok=True)


def get_cards_from_expansion(expansion_id, expansion_name):
    """Recupera tutte le carte di una determinata espansione"""
    url = f"https://api.cardtrader.com/api/v2/marketplace/products"
    params = {"expansion_id": expansion_id, "only_cards": True}  # Richiesta solo carte, escludendo altri prodotti

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        if not data:  # Se la risposta è vuota, non ci sono carte
            print(f"⚠ Nessuna carta trovata per {expansion_name} (ID: {expansion_id})")
            return []

        unique_cards = {}  # Dizionario per evitare duplicati

        for product_id, product_variants in data.items():
            for variant in product_variants:
                blueprint_id = variant["blueprint_id"]
                name_en = variant["name_en"]
                collector_number = variant["properties_hash"].get("collector_number", "N/A")
                rarity = variant["properties_hash"].get("onepiece_rarity", "Unknown")
                image_url = variant.get("image_url", "")

                # Salviamo la carta solo se non è già nel dizionario
                if blueprint_id not in unique_cards:
                    unique_cards[blueprint_id] = {
                        "id": blueprint_id,
                        "name": name_en,
                        "collector_number": collector_number,
                        "rarity": rarity,
                        "expansion_id": expansion_id,
                        "expansion_name": expansion_name,
                        "image_url": image_url
                    }

        return list(unique_cards.values())  # Convertiamo in lista

    except requests.exceptions.RequestException as e:
        print(f"❌ Errore nella richiesta API per {expansion_name} (ID: {expansion_id}): {e}")
        return []


def save_cards_for_expansions():
    """Scarica e salva le carte di ogni espansione nel database"""
    with open(EXPANSIONS_FILE, "r", encoding="utf-8") as f:
        expansions = json.load(f)

    for exp in expansions:
        expansion_id = exp["id"]
        expansion_name = exp["name"]

        file_path = os.path.join(EXPANSIONS_FOLDER, f"{expansion_id}.json")

        # Se il file esiste già, saltiamo l'espansione per non rifare la richiesta
        if os.path.exists(file_path):
            print(f"✅ {expansion_name} (ID: {expansion_id}) già salvata. Salto...")
            continue

        print(f"🔍 Scaricando carte per {expansion_name} (ID: {expansion_id})...")

        # Otteniamo le carte dell'espansione
        cards = get_cards_from_expansion(expansion_id, expansion_name)

        if cards:
            # Salviamo il file JSON
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(cards, f, indent=4, ensure_ascii=False)

            # Contiamo quante carte per rarità sono presenti
            rarity_counts = {}
            for card in cards:
                rarity_counts[card["rarity"]] = rarity_counts.get(card["rarity"], 0) + 1

            print(f"✅ {len(cards)} carte salvate per {expansion_name} (ID: {expansion_id})")
            print("📊 Riepilogo per rarità:")
            for rarity, count in rarity_counts.items():
                print(f"   - {rarity}: {count} carte")
        else:
            print(f"⚠ Nessuna carta trovata per {expansion_name} (ID: {expansion_id})")

        # Attendere 0.4 secondi per evitare limiti API
        time.sleep(0.4)


if __name__ == "__main__":
    save_cards_for_expansions()
