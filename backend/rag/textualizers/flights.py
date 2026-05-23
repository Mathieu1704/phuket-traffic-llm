"""phuket_flights_monthly.csv → narrative chunks (one per month)."""
import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "phuket_flights_monthly.csv"

MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]


def textualize() -> list[dict]:
    df = pd.read_csv(DATA_PATH)
    chunks = []
    for _, r in df.iterrows():
        mn = MONTH_NAMES[int(r["month"]) - 1]
        yr = int(r["year"])
        total = int(r["total_passengers"])
        intl = int(r["intl_passengers"])
        dom = int(r["dom_passengers"])
        intl_fl = int(r["intl_total_flights"])
        dom_fl = int(r["dom_total_flights"])

        if total > 1_100_000:
            impact = "peak season — very high passenger volume"
        elif total > 800_000:
            impact = "high season — above average passenger volume"
        elif total > 500_000:
            impact = "moderate passenger volume"
        else:
            impact = "low season — reduced air traffic"

        text = (
            f"[{mn} {yr}] HKT Airport (Phuket International):\n"
            f"  Total passengers: {total:,} ({impact})\n"
            f"  International: {intl:,} pax on {intl_fl:,} flights\n"
            f"  Domestic: {dom:,} pax on {dom_fl:,} flights\n"
            f"  Traffic implication: high passenger volumes correlate with increased "
            f"congestion on Airport Road (Route 402) during arrival/departure peaks"
        )
        chunks.append({
            "text": text,
            "metadata": {
                "source": "flights",
                "year": yr,
                "month": int(r["month"]),
                "total_passengers": total,
            },
        })
    return chunks
