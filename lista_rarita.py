import os
import json

# Percorsi delle cartelle
EXPANSIONS_FOLDER = "data/onepiece/expansions"
RARITIES_FILE = "data/onepiece/onepiece_rarities.txt"

def extract_rarities():
    """Estrae tutte le rarità dai file JSON delle espansioni e le salva in un file di testo."""
    rarities = set()  # Usiamo un set per evitare duplicati

    # Controlliamo che la cartella delle espansioni esista
    if not os.path.exists(EXPANSIONS_FOLDER):
        print(f"❌ Errore: La cartella '{EXPANSIONS_FOLDER}' non esiste.")
        return

    # Scansiona tutti i file nella cartella delle espansioni
    for filename in os.listdir(EXPANSIONS_FOLDER):
        if filename.endswith(".json"):  # Controlliamo che sia un file JSON
            file_path = os.path.join(EXPANSIONS_FOLDER, filename)

            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    data = json.load(file)

                    # Estrarre la rarità da ogni carta
                    for card in data:
                        rarity = card.get("rarity", "Unknown").strip()
                        if rarity:
                            rarities.add(rarity)

            except json.JSONDecodeError:
                print(f"⚠ Errore nel leggere {filename}, potrebbe essere corrotto.")

    # Ordiniamo alfabeticamente la lista delle rarità
    sorted_rarities = sorted(rarities)

    # Salviamo la lista nel file di testo
    with open(RARITIES_FILE, "w", encoding="utf-8") as file:
        for rarity in sorted_rarities:
            file.write(rarity + "\n")

    print(f"✅ Rarità estratte e salvate in '{RARITIES_FILE}'")
    print(f"🔍 Totale rarità trovate: {len(sorted_rarities)}")

if __name__ == "__main__":
    extract_rarities()
