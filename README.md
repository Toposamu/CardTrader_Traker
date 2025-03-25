# 🎴 CardTrader Tracker

🕵️‍♂️ Un'applicazione Python con interfaccia grafica per trovare le carte più convenienti sul marketplace **CardTrader**, con filtri avanzati, notifiche visive e possibilità di aggiungere direttamente al carrello.

---

## 🇮🇹 Descrizione (Italiano)

Questo progetto ti permette di:

- Analizzare le carte presenti su CardTrader tramite API ufficiali
- Filtrare per rarità, lingua, prezzo minimo/massimo
- Evidenziare carte convenienti con differenze di prezzo significative
- Usare solo il servizio **CardTrader Zero** (opzionale)
- Aggiornare in automatico il database delle espansioni e delle carte
- Aggiungere le carte trovate direttamente al carrello con un clic

💡 Il progetto include una GUI realizzata con `Tkinter` che mostra lo stato di avanzamento, messaggi popup e controlli in tempo reale.

---

## 🇬🇧 Description (English)

This Python project helps you:

- Analyze cards from CardTrader using their official API
- Filter by rarity, language, and price range
- Detect cards with significant price gaps (good deals)
- Optional: filter only CardTrader Zero compatible products
- Auto-update the database of expansions and cards
- Add cards directly to your cart with a click

💡 Includes a GUI built with `Tkinter` to track progress and provide real-time interaction.

---

## 🔧 Requisiti / Requirements

- Python 3.10+
- `requests`
- `tkinter` (incluso nella maggior parte delle installazioni Python)
- Una API Key JWT di CardTrader (da inserire in `config.json`)

---

## 📁 File di configurazione

Non dimenticare di creare un file `config.json` (NON incluso nel progetto) con questo contenuto:

```json
{
  "jwt_token": "INSERISCI_IL_TUO_TOKEN_JWT_DI_CARDTRADER"
}
