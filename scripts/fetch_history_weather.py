import requests
import pandas as pd
from datetime import datetime
import time

# --- CONFIGURATION ---
START_DATE = "2023-01-01"
END_DATE = datetime.now().strftime("%Y-%m-%d") # Jusqu'à aujourd'hui

LOCATIONS = {
    "Airport_HKT": {"lat": 8.1112, "lon": 98.3065},
    "Patong_Beach": {"lat": 7.8960, "lon": 98.2953},
    "Phuket_Town": {"lat": 7.8804, "lon": 98.3923},
    "Chalong_Pier": {"lat": 7.8213, "lon": 98.3443}
}

def fetch_open_meteo_history():
    print("⏳ Démarrage du téléchargement de l'historique météo...")
    all_data = []

    for loc_name, coords in LOCATIONS.items():
        print(f"   ... Récupération pour {loc_name}")
        
        # API Open-Meteo
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "start_date": START_DATE,
            "end_date": END_DATE,
            "hourly": "temperature_2m,rain,precipitation,cloud_cover,wind_speed_10m",
            "timezone": "Asia/Bangkok"
        }
        
        try:
            r = requests.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            
            # Transformation en DataFrame
            hourly = data['hourly']
            df = pd.DataFrame(hourly)
            df['location'] = loc_name
            df['latitude'] = coords['lat']
            df['longitude'] = coords['lon']
            
            all_data.append(df)
            
        except Exception as e:
            print(f"❌ Erreur pour {loc_name}: {e}")

    # Fusion et Sauvegarde
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        # Renommer les colonnes pour faire propre
        final_df.rename(columns={
            "time": "timestamp",
            "temperature_2m": "temp_c",
            "rain": "rain_mm",
            "precipitation": "precip_mm",
            "cloud_cover": "cloud_cover_pct",
            "wind_speed_10m": "wind_kmh"
        }, inplace=True)
        
        filename = "phuket_weather_history_2023_2024.csv"
        final_df.to_csv(filename, index=False)
        print(f"\n✅ Terminé ! Fichier sauvegardé : {filename}")
        print(f"📊 Total lignes : {len(final_df)}")
    else:
        print("❌ Aucune donnée récupérée.")

if __name__ == "__main__":
    fetch_open_meteo_history()