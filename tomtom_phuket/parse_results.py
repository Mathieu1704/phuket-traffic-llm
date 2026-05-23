"""
parse_results.py - Parse TomTom JSON reports into ML-ready CSV files.

Produces 2 output files:
  processed/segments_all.csv   -> one row per (segment x timeSet x dateRange)
  processed/summaries_all.csv  -> one row per (route x timeSet x dateRange)

Usage:
    python parse_results.py                         # Parse all JSONs in raw_json/
    python parse_results.py --file raw_json/X.json  # Parse a single file
"""

import os
import json
import gzip
import argparse
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv

load_dotenv()
RAW_DIR     = Path(os.getenv("RAW_OUTPUT_DIR", "raw_json"))
PROC_DIR    = Path(os.getenv("PROCESSED_OUTPUT_DIR", "processed"))
PROC_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# TomTom returns 19 percentile values: 5%, 10%, ..., 95%
PERCENTILE_LABELS = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95]


def load_json(path: Path) -> dict:
    """Load a TomTom JSON file (plain or gzip-compressed)."""
    raw = path.read_bytes()
    try:
        text = gzip.decompress(raw).decode("utf-8")
    except Exception:
        text = raw.decode("utf-8")
    return json.loads(text)


def parse_file(path: Path) -> tuple[list[dict], list[dict]]:
    """
    Parse a TomTom JSON report and return:
      - segment_rows: list of dicts (one row per segment x timeResult)
      - summary_rows: list of dicts (one row per route summary)
    """
    d = load_json(path)
    job_name      = d.get("jobName", path.stem)
    creation_time = d.get("creationTime", "")

    timeset_map   = {ts["@id"]: ts["name"] for ts in d.get("timeSets", [])}
    daterange_map = {dr["@id"]: {"name": dr["name"], "from": dr["from"], "to": dr["to"]}
                     for dr in d.get("dateRanges", [])}

    segment_rows = []
    summary_rows = []

    for route in d.get("routes", []):
        route_name   = route.get("routeName", "")
        probe_source = route.get("probeSource", "")
        zone_id      = route.get("zoneId", "")

        # Segments
        for seg in route.get("segmentResults", []):
            shape     = seg.get("shape", [])
            start_lat = shape[0]["latitude"]  if shape else None
            start_lon = shape[0]["longitude"] if shape else None
            end_lat   = shape[-1]["latitude"]  if len(shape) > 1 else start_lat
            end_lon   = shape[-1]["longitude"] if len(shape) > 1 else start_lon
            mid_idx   = len(shape) // 2
            mid_lat   = shape[mid_idx]["latitude"]  if shape else None
            mid_lon   = shape[mid_idx]["longitude"] if shape else None

            base = {
                "source_file":    path.name,
                "job_name":       job_name,
                "created_at":     creation_time,
                "route_name":     route_name,
                "probe_source":   probe_source,
                "zone_id":        zone_id,
                "segment_id":     seg.get("segmentId"),
                "new_segment_id": seg.get("newSegmentId"),
                "speed_limit":    seg.get("speedLimit"),
                "frc":            seg.get("frc"),
                "distance_m":     seg.get("distance"),
                "start_lat":      start_lat,
                "start_lon":      start_lon,
                "mid_lat":        mid_lat,
                "mid_lon":        mid_lon,
                "end_lat":        end_lat,
                "end_lon":        end_lon,
                "n_shape_pts":    len(shape),
            }

            for tr in seg.get("segmentTimeResults", []):
                ts_id = tr.get("timeSet")
                dr_id = tr.get("dateRange")

                row = base.copy()
                row.update({
                    "timeset_id":     ts_id,
                    "timeset_name":   timeset_map.get(ts_id, str(ts_id)),
                    "daterange_id":   dr_id,
                    "daterange_name": daterange_map.get(dr_id, {}).get("name", str(dr_id)),
                    "date_from":      daterange_map.get(dr_id, {}).get("from"),
                    "date_to":        daterange_map.get(dr_id, {}).get("to"),
                    # Speed metrics
                    "harmonic_avg_speed":   tr.get("harmonicAverageSpeed"),
                    "median_speed":         tr.get("medianSpeed"),
                    "avg_speed":            tr.get("averageSpeed"),
                    # Travel time metrics
                    "avg_travel_time_s":    tr.get("averageTravelTime"),
                    "median_travel_time_s": tr.get("medianTravelTime"),
                    "travel_time_ratio":    tr.get("travelTimeRatio"),
                    # Sample size
                    "sample_size":          tr.get("sampleSize"),
                    "norm_sample_size":     tr.get("normalizedSampleSize"),
                })

                # Speed percentiles
                sp = tr.get("speedPercentiles", [])
                for i, label in enumerate(PERCENTILE_LABELS):
                    row[f"speed_p{label:02d}"] = sp[i] if i < len(sp) else None

                # Derived feature: congestion ratio (actual speed / speed limit)
                row["congestion_ratio"] = (
                    row["harmonic_avg_speed"] / row["speed_limit"]
                    if row["speed_limit"] and row["speed_limit"] > 0
                    and row["harmonic_avg_speed"] is not None
                    else None
                )

                segment_rows.append(row)

        # Route-level summaries
        for s in route.get("summaries", []):
            ts_id = s.get("timeSet")
            dr_id = s.get("dateRange")

            row = {
                "source_file":           path.name,
                "job_name":              job_name,
                "created_at":            creation_time,
                "route_name":            route_name,
                "probe_source":          probe_source,
                "timeset_id":            ts_id,
                "timeset_name":          timeset_map.get(ts_id, str(ts_id)),
                "daterange_id":          dr_id,
                "daterange_name":        daterange_map.get(dr_id, {}).get("name", str(dr_id)),
                "date_from":             daterange_map.get(dr_id, {}).get("from"),
                "date_to":               daterange_map.get(dr_id, {}).get("to"),
                "distance_m":            s.get("distance"),
                "covered_distance_m":    s.get("coveredDistance"),
                "avg_sample_size":       s.get("averageSampleSize"),
                "harmonic_avg_speed":    s.get("harmonicAverageSpeed"),
                "avg_travel_time_s":     s.get("averageTravelTime"),
                "median_travel_time_s":  s.get("medianTravelTime"),
                "avg_travel_time_ratio": s.get("averageTravelTimeRatio"),
                "planning_time_index":   s.get("planningTimeIndex"),
            }

            # Travel time percentiles (route level)
            ttp = s.get("travelTimePercentiles", [])
            for i, label in enumerate(PERCENTILE_LABELS):
                row[f"tt_p{label:02d}_s"] = ttp[i] if i < len(ttp) else None

            # Speed percentiles (route level)
            sp = s.get("speedPercentiles", [])
            for i, label in enumerate(PERCENTILE_LABELS):
                row[f"speed_p{label:02d}"] = sp[i] if i < len(sp) else None

            summary_rows.append(row)

    return segment_rows, summary_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default=None, help="Parse a single JSON file")
    args = parser.parse_args()

    if args.file:
        files = [Path(args.file)]
    else:
        files = sorted(RAW_DIR.glob("*.json"))
        files = [f for f in files if f.name != "job_registry.json"]

    if not files:
        log.warning(f"No JSON files found in {RAW_DIR}/")
        return

    log.info(f"{len(files)} file(s) to parse...")

    all_segments  = []
    all_summaries = []

    for f in files:
        log.info(f"  -> {f.name}")
        try:
            segs, sums = parse_file(f)
            all_segments.extend(segs)
            all_summaries.extend(sums)
            log.info(f"     {len(segs)} segments, {len(sums)} summaries")
        except Exception as e:
            log.error(f"Error: {e}")

    if all_segments:
        df_seg = pd.DataFrame(all_segments)
        out_seg = PROC_DIR / "segments_all.csv"
        df_seg.to_csv(out_seg, index=False, encoding="utf-8")
        log.info(f"\n segments_all.csv -> {len(df_seg)} rows x {len(df_seg.columns)} columns")
        log.info(f"   -> {out_seg}")

        num_cols = ["harmonic_avg_speed", "median_speed", "travel_time_ratio",
                    "sample_size", "congestion_ratio"]
        log.info(f"\n Descriptive stats (segments):")
        log.info(df_seg[num_cols].describe().to_string())

    if all_summaries:
        df_sum = pd.DataFrame(all_summaries)
        out_sum = PROC_DIR / "summaries_all.csv"
        df_sum.to_csv(out_sum, index=False, encoding="utf-8")
        log.info(f"\n summaries_all.csv -> {len(df_sum)} rows x {len(df_sum.columns)} columns")
        log.info(f"   -> {out_sum}")

    log.info(f"\n Parsing complete.")


if __name__ == "__main__":
    main()
