import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import time

# Charger les clés depuis le fichier .env
load_dotenv()
OWM_KEY = os.getenv("OWM_API_KEY")
CAL_KEY = os.getenv("CALENDAR_API_KEY")

# --- CONFIGURATION DES CORRIDORS (Granularité) ---
LOCATIONS = {
    "Airport_HKT": {"lat": 8.1112, "lon": 98.3065},  # Nord
    "Patong_Beach": {"lat": 7.8960, "lon": 98.2953}, # Ouest
    "Phuket_Town": {"lat": 7.8804, "lon": 98.3923},  # Centre
    "Chalong_Pier": {"lat": 7.8213, "lon": 98.3443}  # Sud
}

def test_weather_live_and_history():
    print("\n--- 1. TEST MÉTÉO (OpenWeatherMap) ---")
    
    # URL pour One Call API 3.0
    base_url = "https://api.openweathermap.org/data/3.0/onecall"
    
    # Pour l'historique, on teste une date précise : 1er Janvier 2024 à midi
    # Conversion en Timestamp UNIX
    date_test = int(datetime(2024, 1, 1, 12, 0).timestamp()) 
    
    for loc_name, coords in LOCATIONS.items():
        print(f"\n📍 Test pour : {loc_name}")
        
        # A. Test LIVE
        url_live = f"{base_url}?lat={coords['lat']}&lon={coords['lon']}&exclude=minutely,daily&units=metric&appid={OWM_KEY}"
        response_live = requests.get(url_live)
        
        if response_live.status_code == 200:
            data = response_live.json()
            temp = data['current']['temp']
            weather = data['current']['weather'][0]['description']
            print(f"   [LIVE] Succès ! Température actuelle: {temp}°C, Ciel: {weather}")
        else:
            print(f"   [LIVE] Erreur: {response_live.status_code} - {response_live.text}")

        # B. Test HISTORIQUE (Time Machine)
        url_hist = f"{base_url}/timemachine?lat={coords['lat']}&lon={coords['lon']}&dt={date_test}&units=metric&appid={OWM_KEY}"
        response_hist = requests.get(url_hist)
        
        if response_hist.status_code == 200:
            data = response_hist.json()
            # Note: l'historique retourne une liste 'data'
            hist_temp = data['data'][0]['temp']
            print(f"   [HISTORIQUE 01/01/24] Succès ! Il faisait: {hist_temp}°C")
        else:
            print(f"   [HISTORIQUE] Erreur (Vérifie ton abonnement OneCall 3.0): {response_hist.status_code}")

def test_holidays():
    print("\n--- 2. TEST CALENDRIER (Calendarific) ---")
    url = f"https://calendarific.com/api/v2/holidays?&api_key={CAL_KEY}&country=TH&year=2024"
    
    response = requests.get(url)
    if response.status_code == 200:
        holidays = response.json()['response']['holidays']
        print(f"✅ Succès ! {len(holidays)} jours fériés trouvés pour la Thaïlande en 2024.")
        # Afficher les 3 premiers pour l'exemple
        for h in holidays[:3]:
            print(f"   - {h['date']['iso']} : {h['name']}")
    else:
        print(f"❌ Erreur: {response.status_code}")

if __name__ == "__main__":
    if not OWM_KEY or not CAL_KEY:
        print("ERREUR: Clés API manquantes dans le fichier .env")
    else:
        test_weather_live_and_history()
        test_holidays()