import requests
import json
import os
from datetime import datetime
from genera_lista_carte_per_espansione import get_cards_from_expansion

CARDS_DIR = "data/onepiece/expansions"

CONFIG_FILE = "config.json"
EXPANSIONS_FILE = "data/onepiece/onepiece_expansions.json"
LOG_FILE = "data/onepiece/update_log.json"
API_URL = "https://api.cardtrader.com/api/v2/expansions"
ONE_PIECE_GAME_ID = 15

def carica_token():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
    return config.get("jwt_token")

def carica_log():
    if not os.path.exists(LOG_FILE):
        return {"ultima_verifica": None, "ultimo_aggiornamento": None}
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salva_log(ultima_verifica=None, ultimo_aggiornamento=None):
    log = carica_log()
    now = datetime.now().isoformat(timespec='seconds')
    if ultima_verifica:
        log["ultima_verifica"] = now
    if ultimo_aggiornamento:
        log["ultimo_aggiornamento"] = now
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)

def scarica_espansioni_onepiece():
    token = carica_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(API_URL, headers=headers)
    response.raise_for_status()
    espansioni = response.json()
    return [e for e in espansioni if e.get("game_id") == ONE_PIECE_GAME_ID]

def carica_espansioni_locali():
    if os.path.exists(EXPANSIONS_FILE):
        with open(EXPANSIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def salva_espansioni_locali(espansioni):
    os.makedirs(os.path.dirname(EXPANSIONS_FILE), exist_ok=True)
    with open(EXPANSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(espansioni, f, indent=2, ensure_ascii=False)

def check_nuove_espansioni():
    nuove_espansioni = []
    try:
        api_expansions = scarica_espansioni_onepiece()
        local_expansions = carica_espansioni_locali()

        api_ids = {e["id"] for e in api_expansions}
        local_ids = {e["id"] for e in local_expansions}
        missing_ids = api_ids - local_ids

        nuove_espansioni = [e for e in api_expansions if e["id"] in missing_ids]

        salva_log(ultima_verifica=True)

        return nuove_espansioni  # Se vuoto → nessun popup
    except Exception as e:
        print(f"❌ Errore durante il controllo espansioni: {e}")
        return []


def aggiorna_database_con_nuove(nuove_espansioni):
    local_expansions = carica_espansioni_locali()
    local_ids = {e["id"] for e in local_expansions}

    # Filtra solo le nuove e tieni solo i campi utili
    to_add = [
        {
            "id": e["id"],
            "name": e["name"],
            "code": e["code"]
        } for e in nuove_espansioni if e["id"] not in local_ids
    ]

    updated = local_expansions + to_add
    salva_espansioni_locali(updated)
    salva_log(ultimo_aggiornamento=True)

def aggiorna_carte_in_espansioni():
    expansions = carica_espansioni_locali()

    for exp in expansions:
        exp_id = exp["id"]
        exp_name = exp["name"]
        path_file = os.path.join(CARDS_DIR, f"{exp_id}.json")

        try:
            carte_api = get_cards_from_expansion(exp_id, exp_name)
        except Exception as e:
            print(f"❌ Errore durante la richiesta per {exp_name}: {e}")
            continue

        if os.path.exists(path_file):
            with open(path_file, "r", encoding="utf-8") as f:
                carte_locali = json.load(f)
        else:
            carte_locali = []

        ids_api = {c["id"] for c in carte_api}
        ids_local = {c["id"] for c in carte_locali}

        ids_mancanti = ids_api - ids_local
        nuove_carte = [c for c in carte_api if c["id"] in ids_mancanti]

        if not nuove_carte:
            print(f"✅ Espansione \"{exp_name}\" aggiornata.")
        else:
            for carta in nuove_carte:
                carte_locali.append(carta)
            os.makedirs(os.path.dirname(path_file), exist_ok=True)
            with open(path_file, "w", encoding="utf-8") as f:
                json.dump(carte_locali, f, indent=2, ensure_ascii=False)
            print(f"🆕 Espansione \"{exp_name}\" - aggiunte {len(nuove_carte)} carte.")