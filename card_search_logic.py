import json
import requests
import time
import os
from datetime import datetime



# === CONFIG ===
CONFIG_FILE = "config.json"
DATA_FOLDER = "data/onepiece/expansions"
OUTPUT_FILE = "report_convenienza.txt"
LINGUE_AMMESSE = {"it", "en"}
CONDIZIONE_RICHIESTA = "Near Mint"
RARITA_DA_ESCLUDERE = {"Common", "Uncommon", "Rare", "Unknown"}
SOGLIA_PERCENTUALE = 20.0
COSTO_SPEDIZIONE = 3.5
DELAY = 0.4
API_URL = "https://api.cardtrader.com/api/v2/marketplace/products"

# === CARICAMENTO TOKEN ===
with open(CONFIG_FILE, encoding='utf-8') as f:
    TOKEN_JWT = json.load(f)["jwt_token"]
HEADERS = {"Authorization": f"Bearer {TOKEN_JWT}"}

# Queste variabili saranno riempite dalla GUI
expansion_label_refs = {}  # es: {3828: Label o Checkbutton associato}

stop_ricerca = False

#Funzione Stop Ricerca
def interrompere():
    global stop_ricerca
    return stop_ricerca


def imposta_stop(valore: bool):
    global stop_ricerca
    stop_ricerca = valore

def ricerca_interrotta():
    return stop_ricerca


def controlla_espansioni(id_espansioni, rarita_permesse, prezzo_min, prezzo_max, name_map, expansion_label_refs, root, solo_ct_zero=False):

    risultati = []

    for exp_id in id_espansioni:
        file_path = os.path.join(DATA_FOLDER, f"{exp_id}.json")
        if not os.path.exists(file_path):
            print(f"❌ File mancante: {file_path}")
            continue

        if exp_id in expansion_label_refs:
            try:
                root.after(0, lambda eid=exp_id: expansion_label_refs[eid].config(fg="blue"))
            except:
                pass

        with open(file_path, encoding="utf-8") as f:
            carte = json.load(f)

        trovate = 0
        for i, carta in enumerate(carte, 1):
            if interrompere():
                print(f"⛔ Interrotto durante l'espansione {name_map.get(exp_id, exp_id)}")

                break  # interrompe il ciclo delle carte
            card_id = carta["id"]
            nome = carta["name"]
            codice = carta["collector_number"]
            rarita = carta["rarity"]

            if rarita in RARITA_DA_ESCLUDERE or rarita not in rarita_permesse:
                continue

            try:
                response = requests.get(API_URL, headers=HEADERS, params={"blueprint_id": card_id})
                if response.status_code != 200:
                    time.sleep(DELAY)
                    if interrompere():
                        break

                    continue

                data = response.json().get(str(card_id), [])

                filtrate = [
                    o for o in data
                    if o["properties_hash"]["condition"] == CONDIZIONE_RICHIESTA
                    and o["properties_hash"]["onepiece_language"] in LINGUE_AMMESSE
                    and o["graded"] is None
                ]

                filtrate.sort(key=lambda x: x["price"]["cents"])

                if len(filtrate) < 2:
                    continue

                if solo_ct_zero and not filtrate[0]["user"].get("can_sell_sealed_with_ct_zero", False):
                    continue

                prezzo1_raw = filtrate[0]["price"]["cents"] / 100
                ct_zero = filtrate[0]["user"].get("can_sell_sealed_with_ct_zero", False)
                prezzo1_effettivo = prezzo1_raw + (0 if ct_zero else COSTO_SPEDIZIONE)


                prezzo2 = filtrate[1]["price"]["cents"] / 100
                diff_assoluta = round(prezzo2 - prezzo1_effettivo, 2)
                if not (prezzo_min <= prezzo1_effettivo <= prezzo_max):
                    continue

                diff_percentuale = round(((prezzo2 - prezzo1_effettivo) / prezzo2) * 100, 2)

                if diff_percentuale >= SOGLIA_PERCENTUALE:
                    trovate += 1
                    risultati.append({
                        "nome": nome,
                        "codice": codice,
                        "rarita": rarita,
                        "prezzo1": prezzo1_effettivo,
                        "prezzo2": prezzo2,
                        "differenza": diff_assoluta,
                        "percentuale": diff_percentuale,
                        "espansione": exp_id,
                        "product_id": filtrate[0]["id"],
                        "quantita": filtrate[0].get("quantity", 1),
                        "venditore_in_vacanza": filtrate[0].get("on_vacation", False),
                        "ct_zero": ct_zero
                    })

            except Exception as e:
                print(f"❌ Errore per {nome}: {e}")

            carte_len = len(carte)

            if exp_id in expansion_label_refs:
                try:
                    def aggiorna_label(exp_id, i, t, total):
                        testo = f"{name_map.get(exp_id, exp_id)} – Carte: {i}/{total} – Convenienti trovate: {t}"
                        expansion_label_refs[exp_id].config(text=testo, fg="blue")

                    root.after(0, aggiorna_label, exp_id, i, trovate, len(carte))


                except:
                    pass

            time.sleep(DELAY)

            if interrompere():
                print("🛑 Ricerca interrotta manualmente.")
                break

        if interrompere():
            break

        if exp_id in expansion_label_refs:
            try:
                base_name = name_map.get(exp_id, f"Espansione {exp_id}")
                root.after(0, lambda eid=exp_id, b=base_name, t=trovate: expansion_label_refs[eid].config(
                    text=f"{b} ✔️ – Convenienti trovate: {t}",
                    fg="green"
                ))

            except:
                pass

    # 🔁 Mostra il popup solo dopo tutte le espansioni
    mostra_popup(risultati)

def mostra_popup(risultati):
    import tkinter as tk
    from tkinter import Toplevel, Button, Label, Scrollbar, Frame, Canvas, messagebox

    if not risultati:
        messagebox.showinfo("Nessuna carta conveniente", "Nessuna carta ha superato i criteri di convenienza.")
        return

    # Ordina per percentuale di convenienza (discendente)
    risultati = sorted(risultati, key=lambda x: x["percentuale"], reverse=True)

    popup = Toplevel()
    popup.title("Carte convenienti trovate")
    popup.geometry("600x500")

    canvas = Canvas(popup)
    scrollbar = Scrollbar(popup, orient="vertical", command=canvas.yview)
    scrollable_frame = Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

    def aggiungi_al_carrello(product_id, bottone, usa_ct_zero=True):
        try:
            url = "https://api.cardtrader.com/api/v2/cart/add"

            # === Primo tentativo: via CardTrader Zero (se richiesto)
            payload = {
                "product_id": product_id,
                "quantity": 1,
                "via_cardtrader_zero": usa_ct_zero
            }

            response = requests.post(url, headers=HEADERS, json=payload)

            if response.status_code == 200:
                bottone.config(text="Aggiunto ✅", bg="lightgreen", state="disabled")
                return

            msg = response.text

            # === Se CardTrader Zero fallisce, riprova senza
            if usa_ct_zero:
                # Verifica se è errore tipico del CT Zero non supportato
                if (
                        "cannot be sold via cardtrader zero" in msg.lower()
                        or "is not available via cardtrader zero" in msg.lower()
                ):
                    # Riprova senza CardTrader Zero
                    payload["via_cardtrader_zero"] = False
                    response = requests.post(url, headers=HEADERS, json=payload)

                    if response.status_code == 200:
                        bottone.config(text="Aggiunto ✅", bg="lightgreen", state="disabled")
                        return

                    # Se anche il secondo tentativo fallisce, continua con gestione errore

            # === Se venditore in vacanza
            if "seller is on vacation" in msg:
                bottone.config(text="Venditore in vacanza 💤", bg="orange", state="disabled")
            elif "quantity is not available" in msg:
                bottone.config(text="Non disponibile", bg="gray", state="disabled")
            else:
                bottone.config(text="Errore ❌", bg="red")
            print(f"❌ Aggiunta fallita - Status: {response.status_code}, Messaggio: {msg}")

        except Exception as e:
            bottone.config(text="Errore ❌", bg="red")
            print(f"Errore aggiunta al carrello: {e}")

    for r in risultati:
        frame = Frame(scrollable_frame, bd=1, relief="groove", padx=5, pady=5)
        frame.pack(fill="x", pady=3)

        playset = " [PLAYSET]" if r.get("quantita", 1) > 1 else ""
        descrizione = (
            f"{r['nome']} ({r['codice']} - {r['rarita']}){playset}\n"
            f"1° Prezzo effettivo: {r['prezzo1']:.2f} € | 2° Prezzo: {r['prezzo2']:.2f} €\n"
            f"Differenza: {r['differenza']:.2f} € | {r['percentuale']:.2f}%"
        )

        Label(frame, text=descrizione, justify="left", anchor="w").pack(side="left", fill="x", expand=True)

        # Se il venditore è in vacanza, mostra etichetta
        if r.get("venditore_in_vacanza"):
            Label(frame, text="Venditore in vacanza 💤", fg="orange").pack(side="right", padx=5)
        else:
            btn = Button(frame, text="Aggiungi al carrello", bg="lightgray")
            btn.pack(side="right")
            btn.configure(
                command=lambda pid=r.get("product_id"), b=btn, zero=r.get("ct_zero", False): aggiungi_al_carrello(pid,
                                                                                                                  b,
                                                                                                                  zero)
            )
