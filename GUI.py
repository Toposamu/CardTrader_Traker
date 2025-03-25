import tkinter as tk
from tkinter import messagebox, ttk, BooleanVar, StringVar
import json
import os
from card_search_logic import controlla_espansioni, expansion_label_refs, imposta_stop
from update_expansions import check_nuove_espansioni, aggiorna_database_con_nuove, carica_log
from update_expansions import aggiorna_carte_in_espansioni
from tkinter.ttk import Progressbar
from PIL import Image, ImageTk
import threading



# === Percorsi file ===
EXPANSIONS_FILE = "data/onepiece/onepiece_expansions.json"
RARITIES_FILE = "data/onepiece/onepiece_rarities.json"
HIDDEN_EXPANSIONS_FILE = "data/onepiece/hidden_expansions.json"

# === Caricamento dati ===
def load_json(path, fallback):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return fallback
    return fallback


expansions = load_json(EXPANSIONS_FILE, [])
rarities = load_json(RARITIES_FILE, [])
hidden_expansions = load_json(HIDDEN_EXPANSIONS_FILE, [])

# === Mappa ID → Nome espansione ===
expansion_name_map = {exp["id"]: exp["name"] for exp in expansions}

# === GUI ===
root = tk.Tk()
root.title("CardTrader Tracker")
root.geometry("1000x650")

status_var = StringVar()
status_label = tk.Label(root, textvariable=status_var, anchor="e", justify="right")
status_label.pack(side="bottom", anchor="e", padx=10, pady=5)
status_label.config(font=("Arial", 9), fg="gray")


# Carica le immagini
img_off = Image.open("data/img/cardzero_off.png").resize((120, 40))
img_on = Image.open("data/img/cardzero_on.png").resize((120, 40))
cardzero_img_off = ImageTk.PhotoImage(img_off)
cardzero_img_on = ImageTk.PhotoImage(img_on)



# Funzione toggle
def toggle_cardzero():
    stato = not cardtrader_zero_attivo.get()
    cardtrader_zero_attivo.set(stato)
    cardzero_btn.config(image=cardzero_img_on if stato else cardzero_img_off)

# === Frame rarità ===
frame_rarities = tk.LabelFrame(root, text="Seleziona Rarità", padx=10, pady=10)
frame_rarities.pack(side="left", fill="both", expand=True, padx=10, pady=10)

excluded_rarities = {"Common", "Uncommon", "Rare", "Unknown"}
rarity_selected = {rar: BooleanVar(value=(rar not in excluded_rarities)) for rar in rarities}

for rar in rarities:
    tk.Checkbutton(frame_rarities, text=rar, variable=rarity_selected[rar]).pack(anchor="w")

# Crea il pulsante immagine
cardzero_btn = tk.Button(frame_rarities, image=cardzero_img_off, command=toggle_cardzero, borderwidth=0)
cardzero_btn.pack(pady=10)

# === Variabili dinamiche ===
exp_selected = {exp["id"]: BooleanVar() for exp in expansions}
budget_min_var = StringVar(value="1.00")
budget_max_var = StringVar(value="1000")


# === Progress Bar ===
progress_var = tk.DoubleVar()
progress_bar = Progressbar(root, variable=progress_var, maximum=100, length=250, mode="determinate")


# === Frame Espansioni ===
frame_expansions = tk.LabelFrame(root, text="Seleziona Espansioni", padx=10, pady=10)
frame_expansions.pack(side="left", fill="both", expand=True, padx=10, pady=10)

frame_expansions_canvas = tk.Canvas(frame_expansions)
scrollbar_expansions = ttk.Scrollbar(frame_expansions, orient="vertical", command=frame_expansions_canvas.yview)
frame_expansions_inner = tk.Frame(frame_expansions_canvas)

frame_expansions_inner.bind("<Configure>", lambda e: frame_expansions_canvas.configure(scrollregion=frame_expansions_canvas.bbox("all")))
frame_expansions_canvas.create_window((0, 0), window=frame_expansions_inner, anchor="nw")
def _on_mousewheel(event):
    frame_expansions_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

frame_expansions_canvas.bind_all("<MouseWheel>", _on_mousewheel)

frame_expansions_canvas.configure(yscrollcommand=scrollbar_expansions.set)

frame_expansions_canvas.pack(side="left", fill="both", expand=True)
scrollbar_expansions.pack(side="right", fill="y")

# === Funzioni espansioni ===
def aggiorna_etichetta_stato():
    log = carica_log()
    verifica = log.get("ultima_verifica", "N/A")
    aggiornamento = log.get("ultimo_aggiornamento", "N/A")

    def formatta(ts):
        if not ts:
            return "N/A"
        return ts.replace("T", " ")

    testo = f"Database controllato il: {formatta(verifica)} | Ultimo aggiornamento: {formatta(aggiornamento)}"
    status_var.set(testo)

def mostra_popup_espansioni(nuove):
    from tkinter import Toplevel, Label, Button

    popup = Toplevel(root)
    popup.title("Nuove espansioni trovate")
    popup.geometry("450x300")
    popup.transient(root)
    popup.attributes("-topmost", True)
    popup.grab_set()  # Opzionale, ma utile a bloccare l’interazione con la finestra principale


    Label(popup, text="Sono state trovate nuove espansioni:", font=("Arial", 12)).pack(pady=10)

    for exp in nuove:
        Label(popup, text=f"- {exp['name']} (ID: {exp['id']})", anchor="w", justify="left").pack(anchor="w", padx=20)

    def conferma_aggiunta():
        aggiorna_database_con_nuove(nuove)
        popup.destroy()
        aggiorna_etichetta_stato()

        # 🔁 Ricarica espansioni da file aggiornato
        global expansions, exp_selected
        from update_expansions import carica_espansioni_locali
        expansions = carica_espansioni_locali()

        # 🔄 Ricostruisci le variabili dinamiche
        exp_selected = {exp["id"]: BooleanVar() for exp in expansions}
        update_expansion_list()

    Button(popup, text="Aggiungi al database", bg="green", fg="white", command=conferma_aggiunta).pack(pady=15)


def save_hidden_expansions():
    with open(HIDDEN_EXPANSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(hidden_expansions, f, indent=2)

def toggle_expansion_visibility(exp_id):
    if exp_id in hidden_expansions:
        hidden_expansions.remove(exp_id)
    else:
        hidden_expansions.append(exp_id)
    save_hidden_expansions()
    update_expansion_list()

def update_expansion_list():
    for widget in frame_expansions_inner.winfo_children():
        widget.destroy()

    visible = sorted(
        [e for e in expansions if e["id"] not in hidden_expansions],
        key=lambda x: x["name"].lower()
    )
    hidden = [e for e in expansions if e["id"] in hidden_expansions]

    for exp in visible + hidden:
        eid = exp["id"]
        var = exp_selected.setdefault(eid, BooleanVar(value=False))

        if eid in hidden_expansions:
            lbl = tk.Label(frame_expansions_inner, text=f"❌ {exp['name']}", fg="gray", cursor="hand2")
            lbl.pack(anchor="w", padx=5, pady=2)
            lbl.bind("<Double-1>", lambda e, eid=eid: toggle_expansion_visibility(eid))
            expansion_label_refs[eid] = lbl
        else:
            chk = tk.Checkbutton(frame_expansions_inner, text=exp["name"], variable=var, anchor="w", cursor="hand2")
            chk.pack(anchor="w", padx=5, pady=2)
            chk.bind("<Double-1>", lambda e, eid=eid: toggle_expansion_visibility(eid))
            expansion_label_refs[eid] = chk

    frame_expansions_canvas.update_idletasks()
    frame_expansions_canvas.config(scrollregion=frame_expansions_canvas.bbox("all"))

# === Pulsante selezione tutte ===
def toggle_all_expansions():
    all_selected = all(exp_selected[exp["id"]].get() for exp in expansions if exp["id"] not in hidden_expansions)
    for exp in expansions:
        if exp["id"] not in hidden_expansions:
            exp_selected[exp["id"]].set(not all_selected)
    update_expansion_list()

btn_select_all = tk.Button(root, text="Seleziona Tutte", command=toggle_all_expansions)
btn_select_all.pack(pady=5)





img_off = Image.open("data/img/cardzero_off.png").resize((120, 40))
img_on = Image.open("data/img/cardzero_on.png").resize((120, 40))
cardzero_img_off = ImageTk.PhotoImage(img_off)
cardzero_img_on = ImageTk.PhotoImage(img_on)

cardtrader_zero_attivo = tk.BooleanVar(value=False)

def toggle_cardzero():
    stato = not cardtrader_zero_attivo.get()
    cardtrader_zero_attivo.set(stato)
    cardzero_btn.config(image=cardzero_img_on if stato else cardzero_img_off)

cardzero_btn = tk.Button(frame_rarities, image=cardzero_img_off, command=toggle_cardzero, borderwidth=0)
cardzero_btn.pack(pady=10)

# === Budget ===
frame_budget = tk.LabelFrame(root, text="Range Prezzo (€)", padx=10, pady=10)
frame_budget.pack(side="left", fill="both", expand=True, padx=10, pady=10)

tk.Label(frame_budget, text="Minimo:").pack(anchor="w")
tk.Entry(frame_budget, textvariable=budget_min_var, width=10).pack()

tk.Label(frame_budget, text="Massimo:").pack(anchor="w")
tk.Entry(frame_budget, textvariable=budget_max_var, width=10).pack()


# === Avvio ricerca ===
def start_search():
    selected_ids = [
        exp["id"] for exp in sorted(expansions, key=lambda e: e["name"])
        if exp_selected[exp["id"]].get()
    ]
    selected_rarities = [r for r, v in rarity_selected.items() if v.get()]
    min_budget = budget_min_var.get()
    max_budget = budget_max_var.get()

    if not selected_ids:
        messagebox.showerror("Errore", "Seleziona almeno un'espansione!")
        return
    if not selected_rarities:
        messagebox.showerror("Errore", "Seleziona almeno una rarità!")
        return
    if not min_budget.replace('.', '', 1).isdigit() or not max_budget.replace('.', '', 1).isdigit():
        messagebox.showerror("Errore", "Inserisci un budget valido!")
        return

        # Disabilita pulsante Cerca, attiva Stop
    btn_search.config(state="disabled")
    btn_stop.config(state="normal")

    def esegui_ricerca():
        imposta_stop(False)
        try:
            controlla_espansioni(
                selected_ids,
                selected_rarities,
                float(min_budget),
                float(max_budget),
                expansion_name_map,
                expansion_label_refs,
                root,
                cardtrader_zero_attivo.get()
            )
        finally:
            # Riabilita i pulsanti quando finisce
            root.after(0, lambda: btn_search.config(state="normal"))
            root.after(0, lambda: btn_stop.config(state="disabled"))


    # Avvia la ricerca in un thread separato
    thread = threading.Thread(target=esegui_ricerca)
    thread.start()

def stop_ricerca():
    imposta_stop(True)
    btn_stop.config(state="disabled")
    btn_stop.config(command=stop_ricerca)



btn_search = tk.Button(root, text="Cerca", command=start_search, bg="green", fg="white", font=("Arial", 14))
btn_search.pack(pady=20)

btn_stop = tk.Button(root, text="🛑 Stop Ricerca", state="disabled", bg="red", fg="white", font=("Arial", 12))
btn_stop.pack(pady=5)


nuove_espansioni = check_nuove_espansioni()
if nuove_espansioni:
    mostra_popup_espansioni(nuove_espansioni)
else:
    aggiorna_etichetta_stato()

def avvia_aggiornamento_carte():
    from update_expansions import carica_espansioni_locali, get_cards_from_expansion

    expansions = carica_espansioni_locali()
    totale = len(expansions)
    progress_bar.pack(side="bottom", pady=5)
    root.update_idletasks()

    for i, exp in enumerate(expansions, 1):
        exp_id = exp["id"]
        exp_name = exp["name"]
        path_file = os.path.join("data/onepiece/expansions", f"{exp_id}.json")

        try:
            carte_api = get_cards_from_expansion(exp_id, exp_name)
        except Exception as e:
            print(f"❌ Errore durante {exp_name}: {e}")
            continue

        if os.path.exists(path_file):
            with open(path_file, "r", encoding="utf-8") as f:
                carte_locali = json.load(f)
        else:
            carte_locali = []

        ids_api = {c["id"] for c in carte_api}
        ids_local = {c["id"] for c in carte_locali}
        ids_mancanti = ids_api - ids_local
        nuove = [c for c in carte_api if c["id"] in ids_mancanti]

        if nuove:
            carte_locali += nuove
            with open(path_file, "w", encoding="utf-8") as f:
                json.dump(carte_locali, f, indent=2, ensure_ascii=False)
            print(f"🆕 {exp_name} - aggiunte {len(nuove)} carte.")
        else:
            print(f"✅ {exp_name} aggiornata.")

        progress_var.set((i / totale) * 100)
        root.update_idletasks()

    messagebox.showinfo("Fatto", "Aggiornamento carte completato.")
    progress_bar.pack_forget()

btn_update_cards = tk.Button(root, text="Aggiorna Carte", command=avvia_aggiornamento_carte)
btn_update_cards.pack(side="left", padx=10, pady=5)


update_expansion_list()
root.mainloop()