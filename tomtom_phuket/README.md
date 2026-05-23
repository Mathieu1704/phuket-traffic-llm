# 🚦 TomTom Phuket Traffic — Collecte & Traitement

### Thèse : Explainable LLM Framework for Tourist-Traffic Forecasting in Phuket

---

## Structure du projet

```
tomtom_phuket/
├── .env.example        ← Template de configuration (copie → .env)
├── .env                ← ⚠️ Ta vraie clé API (ne jamais commit !)
├── .gitignore
├── requirements.txt
│
├── config.py           ← Définition des 4 corridors + timeSets + dateRanges
├── submit_jobs.py      ← Soumission automatique des jobs TomTom
├── parse_existing.py   ← Intégrer des JSONs déjà téléchargés
├── parse_results.py    ← JSON → CSV propres (segments + summaries)
├── explore.py          ← Exploration et sanity checks
│
├── raw_json/           ← JSONs bruts téléchargés (auto-créé)
│   └── job_registry.json  ← Registre des jobs (évite les doublons)
├── processed/          ← CSVs traités pour ML (auto-créé)
│   ├── segments_all.csv
│   └── summaries_all.csv
└── logs/               ← Logs d'exécution (auto-créé)
```

---

## Installation rapide

```bash
# 1. Ouvrir dans VSCode
cd tomtom_phuket

# 2. Créer un environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer ta clé API
cp .env.example .env
# Ouvre .env et remplace METS_TA_CLE_ICI par ta vraie clé
```

## Les 4 corridors

| ID                  | Axe                       | Intérêt               |
| ------------------- | ------------------------- | --------------------- |
| A_airport_road      | HKT → Thalang (Rte 402)   | Arrivées touristiques |
| B_patong_hill       | Kathu → Patong (Rte 4029) | Le plus congestionné  |
| C_phuket_town_rawai | Centre → Rawai (Rte 4022) | Plages du sud         |
| D_bypass_road       | Rocade est (Rte 4027)     | Baseline fluide       |

## Les 4 timeSets

| Nom             | Créneau         |
| --------------- | --------------- |
| Weekday_AM_peak | Lun-Ven 07h-09h |
| Weekday_PM_peak | Lun-Ven 17h-19h |
| Weekday_Offpeak | Lun-Ven 10h-15h |
| Weekend_Day     | Sam-Dim 09h-18h |

## ⚠️ Contrainte trial TomTom

Fenêtre autorisée : **2024-08-01 → 2024-08-31** uniquement.
