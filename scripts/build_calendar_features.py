import requests
import pandas as pd
import os
from dotenv import load_dotenv

# --- 1. CONFIGURATION ET CHARGEMENT CLÉ ---
load_dotenv()
CAL_KEY = os.getenv("CALENDAR_API_KEY")

# --- 2. DONNÉES MANUELLES (HARDCODED) ---
PHUKET_CUSTOM_EVENTS = [
    # --- 2023 ---
    {"date": "2023-04-13", "event_name": "Songkran Festival (Water Fight)", "type": "Local Festival", "impact": "High", "affected_area": "All"},
    {"date": "2023-04-14", "event_name": "Songkran Festival (Water Fight)", "type": "Local Festival", "impact": "High", "affected_area": "All"},
    {"date": "2023-04-15", "event_name": "Songkran Festival (Water Fight)", "type": "Local Festival", "impact": "High", "affected_area": "All"},
    {"date": "2023-10-15", "event_name": "Phuket Vegetarian Festival (Start)", "type": "Local Festival", "impact": "High", "affected_area": "Phuket Town"},
    {"date": "2023-10-23", "event_name": "Phuket Vegetarian Festival (End)", "type": "Local Festival", "impact": "High", "affected_area": "Phuket Town"},
    {"date": "2023-11-27", "event_name": "Loy Krathong", "type": "Cultural", "impact": "Medium", "affected_area": "Near Water/Piers"},
    {"date": "2023-12-31", "event_name": "New Year Eve (Countdown)", "type": "Global Event", "impact": "High", "affected_area": "Patong_Beach"},
    
    # --- 2024 ---
    {"date": "2024-02-15", "event_name": "Old Town Festival", "type": "Local Festival", "impact": "Medium", "affected_area": "Phuket Town"},
    {"date": "2024-02-16", "event_name": "Old Town Festival", "type": "Local Festival", "impact": "Medium", "affected_area": "Phuket Town"},
    {"date": "2024-04-13", "event_name": "Songkran Festival (Water Fight)", "type": "Local Festival", "impact": "High", "affected_area": "All"},
    {"date": "2024-04-14", "event_name": "Songkran Festival (Water Fight)", "type": "Local Festival", "impact": "High", "affected_area": "All"},
    {"date": "2024-04-15", "event_name": "Songkran Festival (Water Fight)", "type": "Local Festival", "impact": "High", "affected_area": "All"},
    {"date": "2024-10-02", "event_name": "Phuket Vegetarian Festival (Start)", "type": "Local Festival", "impact": "High", "affected_area": "Phuket Town"},
    {"date": "2024-10-11", "event_name": "Phuket Vegetarian Festival (End)", "type": "Local Festival", "impact": "High", "affected_area": "Phuket Town"},
    {"date": "2024-11-15", "event_name": "Loy Krathong", "type": "Cultural", "impact": "Medium", "affected_area": "Near Water/Piers"},
    {"date": "2024-12-31", "event_name": "New Year Eve (Countdown)", "type": "Global Event", "impact": "High", "affected_area": "Patong_Beach"},
]

def get_calendarific_holidays(year):
    """Récupère les jours fériés officiels nationaux via API"""
    if not CAL_KEY:
        print("⚠️ Pas de clé API Calendarific trouvée. On saute l'étape API.")
        return pd.DataFrame()

    print(f"   ☁️ Interrogation de l'API Calendarific pour {year}...")
    url = f"https://calendarific.com/api/v2/holidays?&api_key={CAL_KEY}&country=TH&year={year}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        holidays = []
        if 'response' in data and 'holidays' in data['response']:
            for h in data['response']['holidays']:
                if 'National holiday' in h.get('type', []) or True: 
                    holidays.append({
                        'date': h['date']['iso'], # Parfois c'est une ISO string avec timezone
                        'event_name': h['name'],
                        'type': 'National Holiday',
                        'impact': 'Medium',
                        'affected_area': 'All'
                    })
        return pd.DataFrame(holidays)
    except Exception as e:
        print(f"   ❌ Erreur API : {e}")
        return pd.DataFrame()

def generate_hybrid_calendar():
    print("📅 Démarrage de la génération du Calendrier Hybride...")
    
    # 1. Récupération API
    df_2023 = get_calendarific_holidays(2023)
    df_2024 = get_calendarific_holidays(2024)
    df_api = pd.concat([df_2023, df_2024], ignore_index=True)
    
    print(f"   ✅ API : {len(df_api)} jours fériés récupérés.")

    # 2. Intégration Données Manuelles
    df_custom = pd.DataFrame(PHUKET_CUSTOM_EVENTS)
    print(f"   ✅ MANUEL : {len(df_custom)} événements locaux injectés.")

    # 3. Fusion
    df_final = pd.concat([df_api, df_custom], ignore_index=True)

    # 4. Nettoyage et Tri (LA CORRECTION EST ICI)
    # On utilise format='mixed' pour gérer les dates simples ET les dates avec heures
    # On utilise utc=True pour uniformiser les timezones
    df_final['date'] = pd.to_datetime(df_final['date'], format='mixed', utc=True)
    
    # On ne garde que la partie DATE (YYYY-MM-DD) pour enlever les heures bizarres
    df_final['date'] = df_final['date'].dt.date
    
    # Tri final
    df_final = df_final.sort_values(by='date')
    
    # Supprimer les doublons (priorité au manuel qui est en dernier dans la liste concaténée si on ne trie pas, mais ici on gère avec keep='last')
    df_final = df_final.drop_duplicates(subset=['date', 'event_name'], keep='last')

    # 5. Export
    output_file = "phuket_calendar_features.csv"
    df_final.to_csv(output_file, index=False)
    
    print("\n" + "="*40)
    print(f"🚀 SUCCÈS ! Fichier généré : {output_file}")
    print(f"📊 Total événements : {len(df_final)}")
    print("="*40)
    print("Aperçu des 5 premières lignes :")
    print(df_final.head())

if __name__ == "__main__":
    generate_hybrid_calendar()