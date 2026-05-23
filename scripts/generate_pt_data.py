"""
generate_pt_data.py
===================
Génère phuket_public_transport.csv basé sur les vrais horaires du
Phuket Smart Bus (source : phuketsmartbus.com / phuket101.net)

DONNÉES RÉELLES utilisées :
- Route 1 : Airport → Rawai, toutes les heures, 08:15–23:30, tous les jours
- Route 2 : Bus Terminal 1 (Phuket Town) → Patong, 06:00–20:00, tous les jours
- Dragon Line : Old Town loop gratuit, 10:00–21:00 (depuis mai 2024)

Impact sur le trafic routier :
- Route 1 traverse les corridors Airport–Patong et Patong–Town
- Route 2 traverse le corridor Patong–Phuket Town
- Chaque bus = ~30-50 passagers qui N'utilisent PAS de taxi/voiture
"""

import pandas as pd
from datetime import date, timedelta, time

# ─────────────────────────────────────────────────────────────────────
# DÉFINITION DES ROUTES (données réelles phuketsmartbus.com)
# ─────────────────────────────────────────────────────────────────────

ROUTES = {

    "Route_1_Northbound": {
        "name": "Phuket Smart Bus Route 1 (Northbound)",
        "from": "Rawai Beach",
        "to": "Phuket Airport",
        "fare_thb": 100,
        "frequency_min": 60,       # toutes les heures
        "first_departure": "07:15", # depuis Rawai vers Airport
        "last_departure": "22:30",
        "days": "daily",
        "corridor": "Rawai → Kata → Patong → Airport",
        "stops": [
            "Rawai Beach", "Promthep Cape", "Kata Beach",
            "Karon Circle", "Patong Beach", "Kamala Beach",
            "Surin Beach", "Cherng Talay", "Phuket Airport"
        ],
        "avg_passengers_high": 35,
        "avg_passengers_low": 18,
        "duration_min": 90,
    },

    "Route_1_Southbound": {
        "name": "Phuket Smart Bus Route 1 (Southbound)",
        "from": "Phuket Airport",
        "to": "Rawai Beach",
        "fare_thb": 100,
        "frequency_min": 60,
        "first_departure": "08:15", # depuis Airport, source : phuket101.net
        "last_departure": "23:30",
        "days": "daily",
        "corridor": "Airport → Patong → Rawai",
        "stops": [
            "Phuket Airport", "Cherng Talay", "Surin Beach",
            "Kamala Beach", "Patong Beach", "Karon Circle",
            "Kata Beach", "Promthep Cape", "Rawai Beach"
        ],
        "avg_passengers_high": 40,
        "avg_passengers_low": 20,
        "duration_min": 90,
    },

    "Route_2_ToPatong": {
        "name": "Phuket Smart Bus Route 2 (To Patong)",
        "from": "Bus Terminal 1 (Phuket Town)",
        "to": "Patong Beach",
        "fare_thb": 50,
        "frequency_min": 60,
        "first_departure": "06:00",  # source : phuket101.net
        "last_departure": "20:00",
        "days": "daily",
        "corridor": "Phuket Town → Patong",
        "stops": [
            "Bus Terminal 1", "Bangkok Hospital Phuket",
            "Chillva Market", "Lotus Samkong",
            "Andamanda Waterpark", "Kathu Market",
            "Makro Patong", "Malin Plaza", "Patong Beach"
        ],
        "avg_passengers_high": 28,
        "avg_passengers_low": 12,
        "duration_min": 45,
    },

    "Route_2_FromPatong": {
        "name": "Phuket Smart Bus Route 2 (From Patong)",
        "from": "Patong Beach",
        "to": "Bus Terminal 1 (Phuket Town)",
        "fare_thb": 50,
        "frequency_min": 60,
        "first_departure": "07:00",
        "last_departure": "21:00",
        "days": "daily",
        "corridor": "Patong → Phuket Town",
        "stops": [
            "Patong Beach", "Malin Plaza", "Makro Patong",
            "Kathu Market", "Andamanda Waterpark",
            "Lotus Samkong", "Chillva Market",
            "Bangkok Hospital Phuket", "Bus Terminal 1"
        ],
        "avg_passengers_high": 25,
        "avg_passengers_low": 10,
        "duration_min": 45,
    },

    "Dragon_Line": {
        "name": "Dragon Line (Old Town Free Bus)",
        "from": "PKCD Parking Lot",
        "to": "PKCD Parking Lot",  # boucle
        "fare_thb": 0,             # GRATUIT
        "frequency_min": 30,       # toutes les 30 min
        "first_departure": "10:00",
        "last_departure": "21:00",
        "days": "daily",
        "corridor": "Phuket Old Town Loop",
        "stops": [
            "PKCD Parking Lot", "Queen Sirikit Park",
            "Old Town Intersection", "Government Savings Bank",
            "Royal Phuket City", "Pearl Hotel",
            "Municipal Parking", "Krungsri Bank",
            "Suriyadet Circle", "Thai Hua Museum",
            "Mongkhonnimit Temple", "Limelight Avenue"
        ],
        "avg_passengers_high": 20,
        "avg_passengers_low": 8,
        "duration_min": 40,
        # Dragon Line lancé le 9 mai 2024 seulement
        "launch_date": date(2024, 5, 9),
    },
}


def generate_departures_for_route(route_key: str, route: dict,
                                   current_date: date,
                                   season: str) -> list:
    """Génère toutes les courses d'une route pour une journée donnée"""
    import random

    rows = []

    # Dragon Line : opérationnel seulement depuis le 9 mai 2024
    if route_key == "Dragon_Line":
        launch = route.get("launch_date", date(2022, 1, 1))
        if current_date < launch:
            return []

    # Générer les horaires de départ
    first_h, first_m = map(int, route["first_departure"].split(":"))
    last_h,  last_m  = map(int, route["last_departure"].split(":"))
    freq_min = route["frequency_min"]

    current_min = first_h * 60 + first_m
    last_min    = last_h  * 60 + last_m

    while current_min <= last_min:
        h = current_min // 60
        m = current_min % 60
        departure_time = f"{h:02d}:{m:02d}"

        arr_min = current_min + route["duration_min"]
        ah = arr_min // 60
        am = arr_min % 60
        arrival_time = f"{ah:02d}:{am:02d}"

        # Passagers selon saison + aléatoire
        base_pax = (route["avg_passengers_high"] if season == "High"
                    else route["avg_passengers_low"])
        # Week-end : +20% (touristes)
        if current_date.weekday() >= 5:
            base_pax = int(base_pax * 1.2)
        pax = int(base_pax * random.uniform(0.7, 1.3))
        pax = max(1, min(pax, 60))  # Capacité max ~60 pax

        # Voitures évitées grâce au bus
        cars_avoided = int(pax * 0.6)  # ~60% auraient pris voiture/taxi

        rows.append({
            "date":              current_date.isoformat(),
            "day_of_week":       current_date.strftime("%A"),
            "season":            season,
            "is_weekend":        int(current_date.weekday() >= 5),
            "route_id":          route_key,
            "route_name":        route["name"],
            "direction":         f"{route['from']} → {route['to']}",
            "corridor":          route["corridor"],
            "departure_time":    departure_time,
            "arrival_time":      arrival_time,
            "departure_hour":    h,
            "duration_min":      route["duration_min"],
            "frequency_min":     freq_min,
            "fare_thb":          route["fare_thb"],
            "est_passengers":    pax,
            "cars_avoided":      cars_avoided,
            "nb_stops":          len(route["stops"]),
        })

        current_min += freq_min

    return rows


def get_season(d: date) -> str:
    return "High" if d.month in [11, 12, 1, 2, 3, 4] else "Low"


def generate_pt_dataset():
    import random
    random.seed(42)

    print("🚌 Génération du dataset transport public Phuket (2022-2024)...")

    start_date = date(2022, 1, 1)
    end_date   = date(2024, 12, 31)

    all_rows = []
    current = start_date

    while current <= end_date:
        season = get_season(current)

        for route_key, route in ROUTES.items():
            day_rows = generate_departures_for_route(route_key, route,
                                                     current, season)
            all_rows.extend(day_rows)

        current += timedelta(days=1)

    df = pd.DataFrame(all_rows)

    output = "phuket_public_transport.csv"
    df.to_csv(output, index=False)

    print(f"\n✅ Terminé ! Fichier : {output}")
    print(f"   Total courses : {len(df):,}")
    print(f"   Routes couvertes : {df['route_id'].nunique()}")
    print(f"\nAperçu :")
    print(df[["date", "route_id", "corridor", "departure_time",
              "season", "est_passengers", "cars_avoided"]].head(12).to_string())

    # Résumé par route
    print("\nRésumé par route :")
    summary = df.groupby("route_id").agg(
        total_courses=("date", "count"),
        total_pax=("est_passengers", "sum"),
        total_cars_avoided=("cars_avoided", "sum")
    )
    print(summary.to_string())

if __name__ == "__main__":
    generate_pt_dataset()
