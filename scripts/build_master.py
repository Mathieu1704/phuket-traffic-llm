"""
build_master.py
Fusionne tous les datasets Phuket en une table master prête pour le modèle.

Architecture de la table :
  Clé temporelle  : year, month (2023-2024, 24 mois — granularité TomTom)
  Clé spatiale    : corridor (4 corridors TomTom)
  Features trafic : réelles, mensuelles, dynamiques par corridor × timeset group
  Features contexte: météo mensuelle, vols, social, calendrier

Sortie : data/phuket_master.csv  (96 lignes × N colonnes)
"""

import pandas as pd
import numpy as np
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ROOT       = SCRIPT_DIR.parent
DATA       = ROOT / "data"
TOMTOM     = ROOT / "tomtom_phuket" / "processed"
OUT        = ROOT / "data"

# ─── Mapping nom JSON → nom interne corridor ──────────────────────────────────
# Le JSON TomTom utilise "to" ; le reste du projet utilise "→"
CORR_NAME_MAP = {
    "Airport Road (Route 402)":           "Airport Road (Route 402)",
    "Patong Hill (Route 4029)":            "Patong Hill (Route 4029)",
    "Phuket Town to Rawai (Route 4022)":   "Phuket Town → Rawai (Route 4022)",
    "Bypass Road (Route 4027)":            "Bypass Road (Route 4027)",
}

CORRIDORS = list(CORR_NAME_MAP.values())

CORR_META = {
    "Airport Road (Route 402)":          {"corr_id": 0, "corr_tourist_access": 1, "corr_length_km": 20},
    "Patong Hill (Route 4029)":           {"corr_id": 1, "corr_tourist_access": 1, "corr_length_km":  9},
    "Phuket Town → Rawai (Route 4022)":  {"corr_id": 2, "corr_tourist_access": 1, "corr_length_km": 18},
    "Bypass Road (Route 4027)":           {"corr_id": 3, "corr_tourist_access": 0, "corr_length_km": 15},
}

# Métriques trafic à conserver par timeset
TRAFFIC_METRICS = {
    "harmonic_avg_speed":    "spd",
    "avg_travel_time_ratio": "tt_ratio",
    "planning_time_index":   "pti",
}

# ─── 1. BACKBONE : grille 2023-2024 × 4 corridors ────────────────────────────
# Note: summaries_all.csv covers 2023-2024 (24 months × 4 corridors × 24 timesets)
# 2022 data not available from TomTom trial → backbone starts 2023

months = pd.date_range("2023-01-01", "2024-12-01", freq="MS")
backbone = pd.MultiIndex.from_product(
    [months, CORRIDORS], names=["month_date", "corridor"]
).to_frame(index=False)
backbone["year"]  = backbone["month_date"].dt.year
backbone["month"] = backbone["month_date"].dt.month

print(f"Backbone : {len(backbone)} lignes ({len(months)} mois × {len(CORRIDORS)} corridors)")

# ─── 2. TRAFIC TomTom — 24 timesets réels par corridor × mois ────────────────

summ = pd.read_csv(TOMTOM / "summaries_all.csv")

# Normaliser les noms de corridor
summ["corridor"] = summ["route_name"].map(CORR_NAME_MAP)
summ = summ[summ["corridor"].notna()].copy()

# Extraire year + month depuis daterange_name ("2023_01" → year=2023, month=1)
summ["year"]  = summ["daterange_name"].str[:4].astype(int)
summ["month"] = summ["daterange_name"].str[5:7].astype(int)

# Pivoter directement sur timeset_name (24 timesets × 3 métriques = 72 colonnes)
traffic_wide = summ.pivot_table(
    index=["corridor", "year", "month"],
    columns="timeset_name",
    values=list(TRAFFIC_METRICS.keys()),
    aggfunc="mean",
).round(3)

# Renommer colonnes : metric_TimsetName → shortname_TimsetName
metric_rename = {v: k for k, v in TRAFFIC_METRICS.items()}  # original_col → short
traffic_wide.columns = [
    f"{TRAFFIC_METRICS[metric]}_{ts}" for metric, ts in traffic_wide.columns
]
traffic_wide = traffic_wide.reset_index()

# PTI global par corridor × mois (mean + max sur tous les 24 timesets)
pti_global = (
    summ.groupby(["corridor", "year", "month"])
    .agg(pti_mean=("planning_time_index", "mean"),
         pti_max =("planning_time_index", "max"))
    .reset_index()
    .round(3)
)
traffic_wide = traffic_wide.merge(pti_global, on=["corridor", "year", "month"], how="left")

print(f"Traffic wide : {traffic_wide.shape} — cols sample: {list(traffic_wide.columns)[:6]}...")

# Joindre au backbone
master = backbone.merge(traffic_wide, on=["corridor", "year", "month"], how="left")
n_nan = master["tt_ratio_Weekday_AM1"].isna().sum()
print(f"Après join trafic : {master.shape} — NaN tt_ratio_Weekday_AM1 : {n_nan}")

# ─── 3. VOLS — filtre 2023-2024 ──────────────────────────────────────────────

flt = pd.read_csv(DATA / "phuket_flights_monthly.csv")
flt["month_date"] = pd.to_datetime(flt["date"])
flt = flt[flt["month_date"].dt.year.isin([2023, 2024])].copy()
flt = flt[["month_date", "intl_arrivals_flights", "intl_departures_flights",
           "total_passengers", "dom_total_flights"]].copy()
flt.columns = ["month_date", "flt_intl_arrivals", "flt_intl_departures",
               "flt_total_pax", "flt_domestic"]

master = master.merge(flt, on="month_date", how="left")
print(f"Après join vols : {master.shape} — NaN vols : {master.flt_total_pax.isna().sum()}")

# ─── 4. MÉTÉO — horaire → agrégat mensuel ────────────────────────────────────

wx = pd.read_csv(DATA / "phuket_weather_history_2023_2024.csv")
wx["month_date"] = pd.to_datetime(wx["timestamp"].str[:7] + "-01")
wx = wx[wx["month_date"].dt.year.isin([2023, 2024])].copy()

wx_monthly = (
    wx.groupby("month_date")
    .agg(
        wx_temp_c_mean =("temp_c",   "mean"),
        wx_rain_mm_sum =("rain_mm",  "sum"),
        wx_rain_days   =("rain_mm",  lambda x: (x > 0.1).sum()),
        wx_wind_kmh    =("wind_kmh", "mean"),
    )
    .reset_index()
    .round(2)
)

master = master.merge(wx_monthly, on="month_date", how="left")
print(f"Après join météo : {master.shape} — NaN météo : {master.wx_temp_c_mean.isna().sum()}")

# ─── 5. SOCIAL Google Trends — hebdo → mensuel ───────────────────────────────

soc = pd.read_csv(DATA / "phuket_social_trends.csv")
soc["month_date"] = pd.to_datetime(soc["week_start"]).dt.to_period("M").dt.to_timestamp()
soc = soc[soc["month_date"].dt.year.isin([2023, 2024])].copy()

soc_monthly = (
    soc.groupby(["month_date", "keyword"])["interest_score"]
    .mean()
    .reset_index()
)
soc_wide = soc_monthly.pivot_table(
    index="month_date", columns="keyword", values="interest_score", aggfunc="mean"
).reset_index().round(1)
soc_wide.columns = ["month_date"] + [
    f"soc_{k.lower().replace(' ', '_')}" for k in soc_wide.columns[1:]
]

master = master.merge(soc_wide, on="month_date", how="left")
print(f"Après join social : {master.shape} — NaN social : {master.filter(like='soc_').isna().sum().sum()}")

# ─── 6. CALENDRIER ───────────────────────────────────────────────────────────

cal = pd.read_csv(DATA / "phuket_calendar_features.csv")
cal["month_date"] = pd.to_datetime(cal["date"]).dt.to_period("M").dt.to_timestamp()

cal_monthly = (
    cal.groupby("month_date")
    .agg(
        cal_n_holidays  =("type",   lambda x: (x == "National Holiday").sum()),
        cal_n_events    =("type",   "count"),
        cal_high_impact =("impact", lambda x: (x == "High").sum()),
    )
    .reset_index()
)

master = master.merge(cal_monthly, on="month_date", how="left")
master[["cal_n_holidays", "cal_n_events", "cal_high_impact"]] = (
    master[["cal_n_holidays", "cal_n_events", "cal_high_impact"]].fillna(0).astype(int)
)
print(f"Après join calendrier : {master.shape}")

# ─── 7. FEATURES TEMPORELLES DÉRIVÉES ────────────────────────────────────────

master["is_high_season"] = master["month"].isin([11, 12, 1, 2, 3]).astype(int)
master["is_monsoon"]     = master["month"].isin([5, 6, 7, 8, 9, 10]).astype(int)
master["month_sin"]      = np.sin(2 * np.pi * master["month"] / 12).round(4)
master["month_cos"]      = np.cos(2 * np.pi * master["month"] / 12).round(4)

def season(m):
    if m in [12, 1, 2, 3]:    return "high_peak"
    if m in [4, 5]:            return "shoulder"
    if m in [6, 7, 8, 9, 10]: return "monsoon"
    return "shoulder"  # novembre

master["season"] = master["month"].apply(season)

# ─── 8. CORRIDOR FEATURES STATIQUES ──────────────────────────────────────────

meta_df = pd.DataFrame(CORR_META).T.reset_index().rename(columns={"index": "corridor"})
meta_df = meta_df.astype({"corr_id": int, "corr_tourist_access": int, "corr_length_km": int})
master  = master.merge(meta_df, on="corridor", how="left")

# ─── 9. NETTOYAGE FINAL ───────────────────────────────────────────────────────

master = master.drop(columns=["month_date"])

id_cols      = ["year", "month", "corridor", "corr_id", "season",
                "is_high_season", "is_monsoon", "month_sin", "month_cos"]
traffic_cols = [c for c in master.columns if any(
                c.startswith(p) for p in ["spd_", "tt_", "pti_", "sample_", "corr_l", "corr_t"])]
flight_cols  = [c for c in master.columns if c.startswith("flt_")]
weather_cols = [c for c in master.columns if c.startswith("wx_")]
social_cols  = [c for c in master.columns if c.startswith("soc_")]
cal_cols     = [c for c in master.columns if c.startswith("cal_")]

ordered   = id_cols + traffic_cols + flight_cols + weather_cols + social_cols + cal_cols
remaining = [c for c in master.columns if c not in ordered]
master    = master[ordered + remaining]
master    = master.sort_values(["year", "month", "corr_id"]).reset_index(drop=True)

# ─── 10. EXPORT ───────────────────────────────────────────────────────────────

out_path = OUT / "phuket_master.csv"
master.to_csv(out_path, index=False)

print(f"\n{'='*60}")
print(f"✅  phuket_master.csv exporté")
print(f"    Dimensions : {master.shape[0]} lignes × {master.shape[1]} colonnes")
print(f"    Période    : {master.year.min()}-{master.month.min():02d} → "
      f"{master.year.max()}-{master.month.max():02d}")
print(f"    Corridors  : {master.corridor.nunique()}")
print(f"\n📊  Colonnes par groupe :")
print(f"    Identifiant : {len(id_cols)}")
print(f"    Trafic      : {len(traffic_cols)}")
print(f"    Vols        : {len(flight_cols)}")
print(f"    Météo       : {len(weather_cols)}")
print(f"    Social      : {len(social_cols)}")
print(f"    Calendrier  : {len(cal_cols)}")
print(f"\n🔍  Valeurs manquantes :")
missing = master.isna().sum()
missing = missing[missing > 0]
print(missing.to_string() if len(missing) else "    ✅  Aucune !")
print(f"\n📋  Aperçu (Airport Road, jan 2023) :")
row = master[(master.corr_id == 0) & (master.year == 2023) & (master.month == 1)]
cols_show = ["year", "month", "corridor", "season",
             "tt_ratio_Weekday_AM1", "tt_ratio_Weekday_PM1", "tt_ratio_Weekday_Night",
             "tt_ratio_Weekend_AM1", "pti_mean", "flt_total_pax", "wx_rain_mm_sum"]
print(row[cols_show].to_string(index=False))
