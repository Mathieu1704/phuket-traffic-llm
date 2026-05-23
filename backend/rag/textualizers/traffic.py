"""phuket_master.csv → narrative chunks (one per corridor-month)."""
import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "phuket_master.csv"

MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

CORR_NAMES = {
    0: "Airport Road (Route 402)",
    1: "Patong Hill (Route 4029)",
    2: "Phuket Town → Rawai (Route 4022)",
    3: "Bypass Road (Route 4027)",
}

def _congestion_label(ttr: float) -> str:
    if ttr < 1.15: return "smooth"
    if ttr < 1.35: return "moderate"
    if ttr < 1.55: return "congested"
    return "very congested"


def textualize() -> list[dict]:
    df = pd.read_csv(DATA_PATH)
    chunks = []
    for _, r in df.iterrows():
        mn = MONTH_NAMES[int(r["month"]) - 1]
        yr = int(r["year"])
        cid = int(r["corr_id"])
        name = CORR_NAMES.get(cid, r["corridor"])

        am1  = float(r["tt_ratio_Weekday_AM1"])
        pm1  = float(r["tt_ratio_Weekday_PM1"])
        mid  = float(r["tt_ratio_Weekday_Midday"])
        wknd = float(r["tt_ratio_Weekend_AM1"])
        pti_mean = float(r["pti_mean"])
        pti_max  = float(r["pti_max"])

        spd_am1   = float(r["spd_Weekday_AM1"])
        spd_am2   = float(r["spd_Weekday_AM2"])
        spd_pm1   = float(r["spd_Weekday_PM1"])
        spd_pm2   = float(r["spd_Weekday_PM2"])
        spd_mid   = float(r["spd_Weekday_Midday"])
        spd_morn  = float(r["spd_Weekday_Morning"])
        spd_eve   = float(r["spd_Weekday_Evening"])
        spd_wkam1 = float(r["spd_Weekend_AM1"])
        spd_wkam2 = float(r["spd_Weekend_AM2"])
        spd_wkmid = float(r["spd_Weekend_Midday"])
        spd_wkpm1 = float(r["spd_Weekend_PM1"])

        text = (
            f"[{mn} {yr}] {name}:\n"
            f"  Weekday AM peak (07-08h): TT ratio {am1:.2f} ({_congestion_label(am1)}), "
            f"speed {spd_am1:.1f} km/h (AM2: {spd_am2:.1f} km/h)\n"
            f"  Weekday morning (08-10h): speed {spd_morn:.1f} km/h\n"
            f"  Weekday midday (12-13h): TT ratio {mid:.2f} ({_congestion_label(mid)}), "
            f"speed {spd_mid:.1f} km/h\n"
            f"  Weekday PM peak (17-18h): TT ratio {pm1:.2f} ({_congestion_label(pm1)}), "
            f"speed {spd_pm1:.1f} km/h (PM2: {spd_pm2:.1f} km/h)\n"
            f"  Weekday evening (18-20h): speed {spd_eve:.1f} km/h\n"
            f"  Weekend AM peak: TT ratio {wknd:.2f} ({_congestion_label(wknd)}), "
            f"speed {spd_wkam1:.1f} km/h (AM2: {spd_wkam2:.1f} km/h)\n"
            f"  Weekend midday: speed {spd_wkmid:.1f} km/h\n"
            f"  Weekend PM: speed {spd_wkpm1:.1f} km/h\n"
            f"  PTI mean {pti_mean:.2f} / max {pti_max:.2f} (travel time reliability)\n"
            f"  Weather: {r['wx_temp_c_mean']:.1f}°C, {r['wx_rain_mm_sum']:.0f}mm rain, "
            f"{int(r['wx_rain_days'])} rainy days\n"
            f"  Flights: {int(r['flt_total_pax']):,} total passengers at HKT airport\n"
            f"  Season: {r['season'].replace('_', ' ')} | "
            f"High season: {'yes' if r['is_high_season'] else 'no'} | "
            f"Monsoon: {'yes' if r['is_monsoon'] else 'no'}"
        )
        chunks.append({
            "text": text,
            "metadata": {
                "source": "traffic_monthly",
                "corridor_id": cid,
                "corridor_name": name,
                "year": yr,
                "month": int(r["month"]),
                "season": str(r["season"]),
            },
        })
    return chunks
