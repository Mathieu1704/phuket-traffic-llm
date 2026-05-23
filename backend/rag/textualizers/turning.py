"""All_TMC_20251219.xlsx → turning movement count chunks (aggregated by hour)."""
import pandas as pd
from pathlib import Path
import glob

SENSORS_DIR = Path(__file__).resolve().parents[3] / "sensors"

# Column groups: junction_name → (L, ST, R) columns
JUNCTIONS = {
    "RuanNgam": ("RuanNgam_L", "RuanNgam_ST", "RuanNgam_R"),
    "Sena": ("Sena_L", "Sena_ST", "Sena_R"),
    "CharoenSuk": ("CharoenSuk_L", "CharoenSuk_ST", "CharoenSuk_R"),
    "Kasetsart": ("Kasetsart_L", "Kasetsart_ST", "Kasetsart_R"),
}


def _load_tmc() -> pd.DataFrame:
    # TurningMovement_Y2566_*.xlsx have a different Thai-column structure — use All_TMC only
    df = pd.read_excel(SENSORS_DIR / "All_TMC_20251219.xlsx")
    df["DateTime"] = pd.to_datetime(df["DateTime"])
    df = df.sort_values("DateTime")
    df["hour"] = df["DateTime"].dt.hour
    df["date"] = df["DateTime"].dt.date
    df["week"] = df["DateTime"].dt.isocalendar().week.astype(int)
    df["year"] = df["DateTime"].dt.year
    return df


def textualize() -> list[dict]:
    df = _load_tmc()
    chunks = []

    for junction, (l_col, st_col, r_col) in JUNCTIONS.items():
        if l_col not in df.columns:
            continue

        # Aggregate by hour-of-day across all data
        hourly = (
            df.groupby("hour")[[l_col, st_col, r_col]]
            .mean()
            .round(1)
            .reset_index()
        )

        for _, r in hourly.iterrows():
            hr = int(r["hour"])
            total = r[l_col] + r[st_col] + r[r_col]
            if total < 1:
                continue

            period = "night (low traffic)" if hr < 6 or hr >= 22 else \
                     "AM peak (07-09h)" if 7 <= hr <= 9 else \
                     "PM peak (16-19h)" if 16 <= hr <= 19 else \
                     "daytime off-peak"

            text = (
                f"[Turning Movements] {junction} junction — {hr:02d}:00h ({period}):\n"
                f"  Average per 15-min interval: "
                f"Left turn {r[l_col]:.0f} veh | Straight {r[st_col]:.0f} veh | "
                f"Right turn {r[r_col]:.0f} veh\n"
                f"  Total avg flow: {total:.0f} vehicles per 15 min "
                f"(~{total*4:.0f} veh/h)"
            )
            chunks.append({
                "text": text,
                "metadata": {
                    "source": "turning_movements",
                    "junction": junction,
                    "hour": hr,
                    "corridor_id": -1,
                },
            })

    return chunks
