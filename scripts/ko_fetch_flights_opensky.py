"""
fetch_flights_opensky.py  —  VERSION CORRIGÉE
=============================================
Utilise state_vectors_data4 + bounding box géographique
car estArrivalAirport='VTSP' est vide dans flights_data4
(couverture ADS-B insuffisante en Asie du Sud-Est).

Partition key : 'hour' (Unix timestamp début d'heure)
Méthode       : détection avions au sol près de VTSP
"""

from pyopensky.trino import Trino
import pandas as pd
from datetime import date, datetime, timedelta
import time
import os

# ── CONFIG ─────────────────────────────────────────────────────────────
# Bounding box autour de l'aéroport de Phuket (VTSP / HKT)
# lat : 8.08 → 8.15  |  lon : 98.27 → 98.34
VTSP_LAT_MIN = 8.08
VTSP_LAT_MAX = 8.15
VTSP_LON_MIN = 98.27
VTSP_LON_MAX = 98.34

START_DATE    = date(2022, 1, 1)
END_DATE      = date(2024, 12, 31)
OUTPUT_RAW    = "phuket_flights_raw.csv"
OUTPUT_HOURLY = "phuket_flights_hourly.csv"
CHECKPOINT    = "opensky_checkpoint.txt"

# Périodes avec données manquantes (source : doc OpenSky)
MISSING_PERIODS = [
    (datetime(2023, 1, 2, 23), datetime(2023, 1, 3, 10)),
    (datetime(2023, 1, 18, 11), datetime(2023, 1, 23, 7)),
    (datetime(2023, 6, 21, 13), datetime(2023, 6, 21, 22)),
    (datetime(2023, 11, 15, 6), datetime(2023, 11, 16, 8)),
    (datetime(2023, 11, 20, 1), datetime(2023, 11, 20, 3)),
    (datetime(2023, 12, 2, 8), datetime(2023, 12, 5, 3)),
    (datetime(2024, 5, 20, 10), datetime(2024, 5, 21, 5)),
]

def date_to_unix(d: date) -> int:
    """Convertit une date en Unix timestamp UTC minuit"""
    return int(datetime(d.year, d.month, d.day).timestamp())

def is_missing_period(d: date) -> bool:
    """Vérifie si la journée est dans une période avec données manquantes"""
    dt = datetime(d.year, d.month, d.day)
    for start, end in MISSING_PERIODS:
        if start.date() <= d <= end.date():
            return True
    return False

def load_checkpoint() -> date:
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT) as f:
            d = f.read().strip()
            print(f"▶️  Reprise depuis : {d}")
            return date.fromisoformat(d)
    return START_DATE

def save_checkpoint(d: date):
    with open(CHECKPOINT, "w") as f:
        f.write(d.isoformat())

def fetch_flights():
    trino = Trino()
    all_data = []

    # Charger données existantes si reprise
    if os.path.exists(OUTPUT_RAW):
        df_existing = pd.read_csv(OUTPUT_RAW)
        all_data.append(df_existing)
        print(f"📂 {len(df_existing)} avions déjà collectés, reprise...")

    current  = load_checkpoint()
    total_days = (END_DATE - START_DATE).days + 1
    day_num  = (current - START_DATE).days

    print(f"\n✈️  Détection atterrissages à Phuket HKT (VTSP)")
    print(f"   Méthode  : state_vectors_data4 + bounding box géographique")
    print(f"   Bbox     : lat [{VTSP_LAT_MIN}–{VTSP_LAT_MAX}] lon [{VTSP_LON_MIN}–{VTSP_LON_MAX}]")
    print(f"   Période  : {current} → {END_DATE}\n")

    while current <= END_DATE:
        day_num += 1
        progress = f"[{day_num}/{total_days}]"

        # Signaler les périodes sans données
        if is_missing_period(current):
            print(f"{progress} {current} ⚠️  Données manquantes (OpenSky outage), skipped")
            save_checkpoint(current + timedelta(days=1))
            current += timedelta(days=1)
            time.sleep(0.5)
            continue

        # Calculer les timestamps Unix pour les 24 heures de la journée
        day_unix_start = date_to_unix(current)
        day_unix_end   = day_unix_start + 23 * 3600  # dernière heure du jour

        print(f"{progress} {current} ...", end=" ", flush=True)

        # ── REQUÊTE SQL ─────────────────────────────────────────────
        # On utilise 'hour' comme partition key (requis par state_vectors_data4)
        # On cherche les avions au sol dans la bounding box de l'aéroport
        # On dédoublonne par icao24 pour avoir un atterrissage par avion
        query = f"""
            SELECT
                icao24,
                callsign,
                MIN(time)  AS first_seen,
                MAX(time)  AS last_seen,
                AVG(lat)   AS avg_lat,
                AVG(lon)   AS avg_lon
            FROM state_vectors_data4
            WHERE
                hour >= {day_unix_start}
                AND hour <= {day_unix_end}
                AND onground = true
                AND lat  BETWEEN {VTSP_LAT_MIN} AND {VTSP_LAT_MAX}
                AND lon  BETWEEN {VTSP_LON_MIN} AND {VTSP_LON_MAX}
                AND time - lastcontact <= 15
            GROUP BY icao24, callsign
        """

        try:
            df = trino.query(query)

            if df is not None and len(df) > 0:
                df["date"]      = current.isoformat()
                df["day_unix"]  = day_unix_start

                # Convertir first_seen en heure locale Bangkok (UTC+7)
                df["arrival_dt"] = pd.to_datetime(
                    df["first_seen"], unit="s", utc=True
                ).dt.tz_convert("Asia/Bangkok")
                df["arrival_hour"]    = df["arrival_dt"].dt.hour
                df["arrival_weekday"] = df["arrival_dt"].dt.day_name()

                all_data.append(df)
                print(f"✅ {len(df)} avions détectés au sol")
            else:
                print(f"⚠️  0 avion détecté")

            save_checkpoint(current + timedelta(days=1))

            # Sauvegarde intermédiaire tous les 30 jours
            if day_num % 30 == 0:
                _save_intermediate(all_data, OUTPUT_RAW)

            # Pause respectueuse (doc : max 2 queries concurrentes)
            time.sleep(3)

        except Exception as e:
            print(f"\n❌ Erreur : {e}")
            print("   Pause 60s et on réessaie la même journée...")
            time.sleep(60)
            continue  # On ne bouge pas le checkpoint → on réessaie ce jour

        current += timedelta(days=1)

    # ── SAUVEGARDE FINALE ───────────────────────────────────────────────
    print("\n💾 Sauvegarde finale en cours...")
    _save_intermediate(all_data, OUTPUT_RAW)
    _build_hourly_aggregation(OUTPUT_RAW, OUTPUT_HOURLY)

    if os.path.exists(CHECKPOINT):
        os.remove(CHECKPOINT)

    print(f"\n🎉 TERMINÉ !")
    print(f"   → {OUTPUT_RAW}    (données brutes, un avion par ligne)")
    print(f"   → {OUTPUT_HOURLY} (agrégé par heure, prêt pour le modèle)")


def _save_intermediate(all_data: list, output: str):
    if not all_data:
        return
    df = pd.concat(all_data, ignore_index=True)
    # Dédoublonnage : même avion même jour
    df = df.drop_duplicates(subset=["icao24", "date"])
    df.to_csv(output, index=False)
    print(f"\n   💾 Intermédiaire : {len(df)} enregistrements → {output}")


def _build_hourly_aggregation(raw_file: str, hourly_file: str):
    """Agrège par heure → format final pour le modèle LLM"""
    df = pd.read_csv(raw_file)

    df_hourly = (
        df.groupby(["date", "arrival_hour"])
        .agg(
            flight_arrivals=("icao24", "count"),
            unique_callsigns=("callsign", "nunique"),
        )
        .reset_index()
    )
    df_hourly.columns = ["date", "hour", "flight_arrivals", "unique_callsigns"]

    # Enrichissement
    df_hourly["month"] = pd.to_datetime(df_hourly["date"]).dt.month
    df_hourly["season"] = df_hourly["month"].apply(
        lambda m: "High" if m in [11, 12, 1, 2, 3, 4] else "Low"
    )
    df_hourly["day_of_week"] = pd.to_datetime(df_hourly["date"]).dt.day_name()
    df_hourly["is_weekend"]  = pd.to_datetime(
        df_hourly["date"]).dt.weekday.apply(lambda x: int(x >= 5))

    df_hourly.to_csv(hourly_file, index=False)
    print(f"   ✅ Fichier horaire : {len(df_hourly)} lignes → {hourly_file}")
    print(f"\nAperçu :")
    print(df_hourly.head(10).to_string())


if __name__ == "__main__":
    fetch_flights()