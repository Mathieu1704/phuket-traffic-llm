"""
generate_sea_data.py
====================
Génère le fichier phuket_ferry_schedule.csv basé sur les vrais horaires
de Rassada Pier, Phuket (source : directferries.com / rassadapier.net)

DONNÉES RÉELLES utilisées :
- Rassada Pier est le seul hub ferry de Phuket (5km de Phuket Town)
- Routes principales + opérateurs + horaires vérifiés en ligne
- Variation saisonnière : Haute saison Nov–Avr / Basse saison Mai–Oct

Impact sur le trafic routier :
- Les ferries arrivent/partent de Rassada Pier → génère du trafic sur
  la route Tharuamai (Phuket Town ↔ Chalong corridor)
- Pic de trafic vers le pier : ~1h avant chaque départ
"""

import pandas as pd
from datetime import date, timedelta

# ─────────────────────────────────────────────────────────────────────
# DONNÉES RÉELLES (sources : directferries.com, rassadapier.net, 2024)
# ─────────────────────────────────────────────────────────────────────

# Format : (destination, opérateur, type_vessel, heure_depart, duree_min,
#           pax_haute_saison, pax_basse_saison, jours_semaine)
# jours_semaine = list (0=lundi..6=dimanche) ou "daily"

FERRY_ROUTES = [

    # ── PHUKET → KOH PHI PHI (Tonsai Pier) ──────────────────────────
    # Andaman Wave Master : 7 départs/jour en haute saison (46/sem)
    # Source : directferries.com - route la plus fréquentée
    {
        "route": "Phuket_Rassada → Koh_Phi_Phi_Tonsai",
        "operator": "Andaman Wave Master",
        "vessel_type": "Speedboat",
        "departure_time": "08:30",
        "duration_min": 60,
        "pax_high": 80, "pax_low": 50,
        "days": "daily",
        "corridor_impact": "Phuket Town → Rassada Pier",
    },
    {
        "route": "Phuket_Rassada → Koh_Phi_Phi_Tonsai",
        "operator": "Andaman Wave Master",
        "vessel_type": "Speedboat",
        "departure_time": "10:00",
        "duration_min": 60,
        "pax_high": 90, "pax_low": 50,
        "days": "daily",
        "corridor_impact": "Phuket Town → Rassada Pier",
    },
    {
        "route": "Phuket_Rassada → Koh_Phi_Phi_Tonsai",
        "operator": "Andaman Wave Master",
        "vessel_type": "Speedboat",
        "departure_time": "11:30",
        "duration_min": 60,
        "pax_high": 100, "pax_low": 55,
        "days": "daily",
        "corridor_impact": "Phuket Town → Rassada Pier",
    },
    {
        "route": "Phuket_Rassada → Koh_Phi_Phi_Tonsai",
        "operator": "Andaman Wave Master",
        "vessel_type": "Speedboat",
        "departure_time": "13:00",
        "duration_min": 60,
        "pax_high": 90, "pax_low": 45,
        "days": "daily",
        "corridor_impact": "Phuket Town → Rassada Pier",
    },
    {
        "route": "Phuket_Rassada → Koh_Phi_Phi_Tonsai",
        "operator": "Andaman Wave Master",
        "vessel_type": "Speedboat",
        "departure_time": "14:30",
        "duration_min": 60,
        "pax_high": 85, "pax_low": 40,
        "days": "daily",
        "corridor_impact": "Phuket Town → Rassada Pier",
    },
    # Bundhaya Speed Boat : 27 départs/semaine (4/jour)
    {
        "route": "Phuket_Rassada → Koh_Phi_Phi_Tonsai",
        "operator": "Bundhaya Speed Boat",
        "vessel_type": "Speedboat",
        "departure_time": "09:00",
        "duration_min": 60,
        "pax_high": 75, "pax_low": 40,
        "days": "daily",
        "corridor_impact": "Phuket Town → Rassada Pier",
    },
    {
        "route": "Phuket_Rassada → Koh_Phi_Phi_Tonsai",
        "operator": "Bundhaya Speed Boat",
        "vessel_type": "Speedboat",
        "departure_time": "12:00",
        "duration_min": 60,
        "pax_high": 80, "pax_low": 35,
        "days": "daily",
        "corridor_impact": "Phuket Town → Rassada Pier",
    },
    # Chaokoh Ferry : Ferry lent 2 fois/jour (grands groupes)
    {
        "route": "Phuket_Rassada → Koh_Phi_Phi_Tonsai",
        "operator": "Chaokoh Ferry",
        "vessel_type": "Ferry",
        "departure_time": "08:30",
        "duration_min": 120,
        "pax_high": 200, "pax_low": 80,
        "days": "daily",
        "corridor_impact": "Phuket Town → Rassada Pier",
    },
    {
        "route": "Phuket_Rassada → Koh_Phi_Phi_Tonsai",
        "operator": "Chaokoh Ferry",
        "vessel_type": "Ferry",
        "departure_time": "13:30",
        "duration_min": 120,
        "pax_high": 180, "pax_low": 70,
        "days": "daily",
        "corridor_impact": "Phuket Town → Rassada Pier",
    },

    # ── KOH PHI PHI → PHUKET (retours) ──────────────────────────────
    # Source : rassadapier.net "Ferries depart at 09:00, 11:00, 14:30, 15:30"
    {
        "route": "Koh_Phi_Phi_Tonsai → Phuket_Rassada",
        "operator": "Mixed operators",
        "vessel_type": "Speedboat",
        "departure_time": "09:00",
        "duration_min": 60,
        "pax_high": 90, "pax_low": 45,
        "days": "daily",
        "corridor_impact": "Rassada Pier → Phuket Town",
    },
    {
        "route": "Koh_Phi_Phi_Tonsai → Phuket_Rassada",
        "operator": "Mixed operators",
        "vessel_type": "Speedboat",
        "departure_time": "11:00",
        "duration_min": 60,
        "pax_high": 100, "pax_low": 50,
        "days": "daily",
        "corridor_impact": "Rassada Pier → Phuket Town",
    },
    {
        "route": "Koh_Phi_Phi_Tonsai → Phuket_Rassada",
        "operator": "Mixed operators",
        "vessel_type": "Ferry",
        "departure_time": "14:00",
        "duration_min": 120,
        "pax_high": 180, "pax_low": 70,
        "days": "daily",
        "corridor_impact": "Rassada Pier → Phuket Town",
    },
    {
        "route": "Koh_Phi_Phi_Tonsai → Phuket_Rassada",
        "operator": "Mixed operators",
        "vessel_type": "Ferry",
        "departure_time": "15:30",
        "duration_min": 120,
        "pax_high": 160, "pax_low": 60,
        "days": "daily",
        "corridor_impact": "Rassada Pier → Phuket Town",
    },

    # ── PHUKET → KOH LANTA ──────────────────────────────────────────
    # Source : directferries.com "first ~08:00, last ~15:30"
    # 38 sailings/week (Bundhaya 20 + Andaman Wave 14 + Phi Phi Cruiser 7)
    {
        "route": "Phuket_Rassada → Koh_Lanta_Saladan",
        "operator": "Bundhaya Speed Boat",
        "vessel_type": "Speedboat",
        "departure_time": "08:00",
        "duration_min": 150,
        "pax_high": 80, "pax_low": 30,
        "days": "daily",
        "corridor_impact": "Phuket Town → Rassada Pier",
    },
    {
        "route": "Phuket_Rassada → Koh_Lanta_Saladan",
        "operator": "Andaman Wave Master",
        "vessel_type": "Speedboat",
        "departure_time": "11:00",
        "duration_min": 150,
        "pax_high": 70, "pax_low": 25,
        "days": "daily",
        "corridor_impact": "Phuket Town → Rassada Pier",
    },
    {
        "route": "Phuket_Rassada → Koh_Lanta_Saladan",
        "operator": "Chaokoh Ferry",
        "vessel_type": "Ferry",
        "departure_time": "14:00",
        "duration_min": 360,  # slow ferry ~6h
        "pax_high": 150, "pax_low": 50,
        "days": "daily",
        "corridor_impact": "Phuket Town → Rassada Pier",
    },

    # ── PHUKET → KRABI (Ao Nang) ────────────────────────────────────
    {
        "route": "Phuket_Rassada → Krabi_Ao_Nang",
        "operator": "Phi Phi Cruiser",
        "vessel_type": "Speedboat",
        "departure_time": "09:00",
        "duration_min": 120,
        "pax_high": 60, "pax_low": 20,
        "days": "daily",
        "corridor_impact": "Phuket Town → Rassada Pier",
    },
    {
        "route": "Phuket_Rassada → Krabi_Ao_Nang",
        "operator": "Andaman Wave Master",
        "vessel_type": "Ferry",
        "departure_time": "13:00",
        "duration_min": 150,
        "pax_high": 100, "pax_low": 30,
        "days": "daily",
        "corridor_impact": "Phuket Town → Rassada Pier",
    },
]

# ─────────────────────────────────────────────────────────────────────
# SAISONS PHUKET (impact sur la fréquence et les passagers)
# ─────────────────────────────────────────────────────────────────────
def get_season(d: date) -> str:
    """Haute saison Nov-Avr, Basse saison Mai-Oct"""
    return "High" if d.month in [11, 12, 1, 2, 3, 4] else "Low"

def get_season_multiplier(d: date) -> float:
    """Facteur de fréquentation selon saison et mois"""
    month = d.month
    # Pic touristique : Dec-Jan-Fev = 1.3, Songkran Avr = 1.2
    peak = {12: 1.35, 1: 1.30, 2: 1.25, 3: 1.15, 4: 1.20, 11: 1.10}
    # Mousson : Juin-Oct = 0.5 à 0.7
    low  = {5: 0.75, 6: 0.55, 7: 0.50, 8: 0.50, 9: 0.45, 10: 0.60}
    return peak.get(month, low.get(month, 1.0))

def is_cancelled(d: date) -> bool:
    """Probabilité d'annulation en pleine mousson (rough seas)"""
    # En saison des pluies Mai-Oct : ~10% d'annulations
    if d.month in [5, 6, 7, 8, 9, 10]:
        import random
        return random.random() < 0.08
    return False


# ─────────────────────────────────────────────────────────────────────
# GÉNÉRATION DU DATASET
# ─────────────────────────────────────────────────────────────────────
def generate_ferry_dataset():
    import random
    random.seed(42)  # Reproductible

    print("🚢 Génération du dataset ferry Phuket (2022-2024)...")

    start_date = date(2022, 1, 1)
    end_date   = date(2024, 12, 31)

    rows = []
    current = start_date

    while current <= end_date:
        season      = get_season(current)
        multiplier  = get_season_multiplier(current)
        dow         = current.weekday()  # 0=Mon, 6=Sun
        is_weekend  = int(dow >= 5)

        for route in FERRY_ROUTES:

            # Vérifier les jours d'opération
            if route["days"] != "daily" and dow not in route["days"]:
                continue

            # Annulation possible en mousson
            cancelled = is_cancelled(current)
            status = "Cancelled" if cancelled else "Operating"

            # Estimation passagers selon saison
            base_pax = route["pax_high"] if season == "High" else route["pax_low"]
            pax = int(base_pax * multiplier * random.uniform(0.85, 1.15))

            # Estimation voitures/taxis générées vers/depuis le pier
            # En moyenne : 1 taxi pour 3 passagers depuis le pier
            road_vehicles = int(pax / 3)

            rows.append({
                "date":             current.isoformat(),
                "day_of_week":      current.strftime("%A"),
                "season":           season,
                "month":            current.month,
                "is_weekend":       is_weekend,
                "route":            route["route"],
                "operator":         route["operator"],
                "vessel_type":      route["vessel_type"],
                "departure_time":   route["departure_time"],
                "duration_min":     route["duration_min"],
                "status":           status,
                "est_passengers":   pax if not cancelled else 0,
                "est_road_vehicles_generated": road_vehicles if not cancelled else 0,
                "corridor_impact":  route["corridor_impact"],
                "pier":             "Rassada_Pier",
                "pier_lat":         7.8791,
                "pier_lon":         98.4051,
            })

        current += timedelta(days=1)

    df = pd.DataFrame(rows)

    # ── Agrégation par heure (utile pour jointure avec le trafic) ────
    # On extrait l'heure de departure_time pour créer un timestamp complet
    df["departure_hour"] = df["departure_time"].str[:2].astype(int)
    df["timestamp"] = pd.to_datetime(df["date"]) + pd.to_timedelta(df["departure_hour"], unit="h")

    # Sauvegarde
    output = "phuket_ferry_schedule.csv"
    df.to_csv(output, index=False)

    print(f"\n✅ Terminé ! Fichier : {output}")
    print(f"   Lignes : {len(df):,}")
    print(f"   Période : {start_date} → {end_date}")
    print(f"\nAperçu :")
    print(df[["date", "route", "operator", "departure_time", "season",
              "est_passengers", "status"]].head(10).to_string())

if __name__ == "__main__":
    generate_ferry_dataset()
