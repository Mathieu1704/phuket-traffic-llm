"""
submit_jobs.py - Submit, poll and download TomTom Traffic Stats jobs for Phuket corridors.

Usage:
    python submit_jobs.py              # Run all jobs (priority 1 first)
    python submit_jobs.py --dry-run    # Preview jobs without submitting
    python submit_jobs.py --priority 1 # Run priority 1 jobs only
"""

import os
import sys
import json
import time
import gzip
import argparse
import logging
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

from config import (
    CORRIDORS, TIME_SETS, DATE_RANGES_CURRENT, ACTIVE_JOB_PLAN,
    API_BASE_URL, DISTANCE_UNIT, ZONE_ID, PROBE_SOURCE, FULL_TRAVERSAL
)

load_dotenv()
API_KEY = os.getenv("TOMTOM_API_KEY")
RAW_DIR = Path(os.getenv("RAW_OUTPUT_DIR", "raw_json"))
LOG_DIR = Path("logs")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "20"))
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT_JOBS", "5"))

RAW_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / f"submit_{datetime.now():%Y%m%d_%H%M%S}.log")
    ]
)
log = logging.getLogger(__name__)

def get_corridor(corridor_id: str) -> dict:
    return next(c for c in CORRIDORS if c["id"] == corridor_id)

def get_time_set(name: str) -> dict:
    return next(ts for ts in TIME_SETS if ts["name"] == name)

def get_date_range(name: str) -> dict:
    return next(dr for dr in DATE_RANGES_CURRENT if dr["name"] == name)

def build_job_payload(corridor: dict, date_range: dict, time_set: dict) -> dict:
    job_name = f"Phuket_{corridor['id']}_{date_range['name']}_{time_set['name']}"
    return {
        "jobName": job_name,
        "distanceUnit": DISTANCE_UNIT,
        "routes": [{
            "name": corridor["name"],
            "start": corridor["start"],
            "end": corridor["end"],
            "fullTraversal": FULL_TRAVERSAL,
            "zoneId": ZONE_ID,
            "probeSource": PROBE_SOURCE,
        }],
        "dateRanges": [{
            "name": date_range["name"],
            "from": date_range["from"],
            "to": date_range["to"],
            "exclusions": []
        }],
        "timeSets": [{
            "name": time_set["name"],
            "timeGroups": time_set["timeGroups"]
        }]
    }

def build_combined_payload(corridor: dict, date_range: dict, time_sets: list) -> dict:
    """Build a single job payload with all time sets combined (4 timeSets in one job).
    Reduces 576 jobs → 144 jobs if the API supports it."""
    job_name = f"Phuket_{corridor['id']}_{date_range['name']}_AllTimeSets"
    return {
        "jobName": job_name,
        "distanceUnit": DISTANCE_UNIT,
        "routes": [{
            "name": corridor["name"],
            "start": corridor["start"],
            "end": corridor["end"],
            "fullTraversal": FULL_TRAVERSAL,
            "zoneId": ZONE_ID,
            "probeSource": PROBE_SOURCE,
        }],
        "dateRanges": [{
            "name": date_range["name"],
            "from": date_range["from"],
            "to": date_range["to"],
            "exclusions": []
        }],
        "timeSets": [
            {"name": ts["name"], "timeGroups": ts["timeGroups"]}
            for ts in time_sets
        ]
    }

def submit_job(payload: dict) -> str | None:
    """Submit a job and return the jobId, or None on error."""
    url = f"{API_BASE_URL}/routeanalysis/1?key={API_KEY}"
    try:
        r = requests.post(url, json=payload, timeout=30)
        data = r.json()
        if data.get("responseStatus") == "OK":
            job_id = data["jobId"]
            log.info(f"Job submitted -> jobId={job_id}  name={payload['jobName']}")
            return job_id
        else:
            log.error(f"Submission error [{payload['jobName']}]: {data.get('messages')}")
            return None
    except Exception as e:
        log.error(f"Submission exception: {e}")
        return None

def poll_job(job_id: str) -> dict:
    """Poll job status until DONE or FAILED. Returns the status dict."""
    url = f"{API_BASE_URL}/status/1/{job_id}?key={API_KEY}"
    while True:
        try:
            r = requests.get(url, timeout=30)
            data = r.json()
            state = data.get("jobState", "UNKNOWN")
            log.info(f"Job {job_id} -> {state}")

            if state == "DONE":
                return data
            elif state in ("FAILED", "CANCELLED", "REJECTED"):
                log.error(f"Job {job_id} ended with state {state}: {data}")
                return data
            elif state == "NEED_CONFIRMATION":
                accept_url = f"{API_BASE_URL}/status/1/{job_id}/accept?key={API_KEY}"
                requests.post(accept_url, timeout=30)
                log.info(f"Job {job_id} -> NEED_CONFIRMATION -> accept sent")

        except Exception as e:
            log.warning(f"Poll exception: {e}")

        time.sleep(POLL_INTERVAL)

def download_json(job_id: str, job_name: str, urls: list) -> Path | None:
    """Download the job JSON file and save it locally."""
    json_url = next((u for u in urls if u.split("?")[0].endswith(".json")), None)
    if not json_url:
        log.error(f"No .json URL found for job {job_id}")
        return None

    safe_name = job_name.replace(" ", "_").replace("/", "-")
    out_path = RAW_DIR / f"{safe_name}.json"

    try:
        r = requests.get(json_url, timeout=60)
        r.raise_for_status()

        # TomTom may return gzip even if the URL ends with .json
        content = r.content
        try:
            text = gzip.decompress(content).decode("utf-8")
        except Exception:
            text = content.decode("utf-8")

        out_path.write_text(text, encoding="utf-8")
        log.info(f"Saved -> {out_path}  ({len(text)//1024} KB)")
        return out_path

    except Exception as e:
        log.error(f"Download error: {e}")
        return None

def save_job_registry(registry: dict):
    """Save the job registry (jobId -> metadata) for resume support."""
    reg_path = RAW_DIR / "job_registry.json"
    reg_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False))

def main():
    parser = argparse.ArgumentParser(description="Submit TomTom Traffic Stats jobs for Phuket")
    parser.add_argument("--dry-run", action="store_true", help="Preview jobs without submitting")
    parser.add_argument("--priority", type=int, default=None, help="Filter by priority (1, 2 or 3)")
    parser.add_argument("--max", type=int, default=None, help="Maximum number of jobs to submit")
    parser.add_argument("--test-combined", action="store_true",
                        help="TEST: submit 1 combined job for corridor A with all 4 time sets")
    parser.add_argument("--test-all-corridors", action="store_true",
                        help="TEST: submit 1 job with ALL 4 corridors + ALL 4 time sets (576→36 jobs if OK)")
    parser.add_argument("--test-date-ranges", action="store_true",
                        help="TEST: 2 jobs — 1 dateRange (4 weeks) vs 4 dateRanges (1 week each) — same total, compare cost")
    parser.add_argument("--test-date-ranges-b", action="store_true",
                        help="TEST: only the 4x1week job (use with a different API key)")
    parser.add_argument("--test-date-ranges-c", action="store_true",
                        help="TEST: 1 dateRange x 1 week (exact salesman test #1)")
    parser.add_argument("--api-key", type=str, default=None,
                        help="Override TOMTOM_API_KEY from .env")
    args = parser.parse_args()

    global API_KEY
    if args.api_key:
        API_KEY = args.api_key

    # ── TEST: 1 dateRange x 1 week (exact salesman test #1) ─────────────────────
    if args.test_date_ranges_c:
        corridor_a = next(c for c in CORRIDORS if c["id"] == "A_airport_road")
        ts_am = next(ts for ts in TIME_SETS if ts["name"] == "Weekday_AM_peak")
        payload = {
            "jobName": "Phuket_DateRangeTest_1x1week",
            "distanceUnit": DISTANCE_UNIT,
            "routes": [{"name": corridor_a["name"], "start": corridor_a["start"],
                        "end": corridor_a["end"], "fullTraversal": FULL_TRAVERSAL,
                        "zoneId": ZONE_ID, "probeSource": PROBE_SOURCE}],
            "dateRanges": [{"name": "Week1only", "from": "2024-08-01", "to": "2024-08-07", "exclusions": []}],
            "timeSets": [{"name": ts_am["name"], "timeGroups": ts_am["timeGroups"]}],
        }
        log.info(f"TEST C — {payload['jobName']} (1 dateRange × 1 week)")
        if args.dry_run:
            log.info("DRY RUN — not submitted.")
            return
        if not API_KEY or API_KEY == "METS_TA_CLE_ICI":
            log.error("TOMTOM_API_KEY not set!"); sys.exit(1)
        job_id = submit_job(payload)
        if job_id:
            status = poll_job(job_id)
            if status.get("jobState") == "DONE":
                download_json(job_id, payload["jobName"], status.get("urls", []))
                log.info("SUCCESS — compare Total length with the 4x1week job")
        return

    # ── TEST: dateRanges multiples — même total, nombre d'entrées différent ───
    if args.test_date_ranges or args.test_date_ranges_b:
        corridor_a = next(c for c in CORRIDORS if c["id"] == "A_airport_road")
        ts_am = next(ts for ts in TIME_SETS if ts["name"] == "Weekday_AM_peak")
        base_route = {
            "name": corridor_a["name"],
            "start": corridor_a["start"],
            "end": corridor_a["end"],
            "fullTraversal": FULL_TRAVERSAL,
            "zoneId": ZONE_ID,
            "probeSource": PROBE_SOURCE,
        }
        base_ts = [{"name": ts_am["name"], "timeGroups": ts_am["timeGroups"]}]

        payload_a = {
            "jobName": "Phuket_DateRangeTest_1x4weeks",
            "distanceUnit": DISTANCE_UNIT,
            "routes": [base_route],
            "dateRanges": [{"name": "Aug4Weeks", "from": "2024-08-01", "to": "2024-08-28", "exclusions": []}],
            "timeSets": base_ts,
        }
        payload_b = {
            "jobName": "Phuket_DateRangeTest_4x1week",
            "distanceUnit": DISTANCE_UNIT,
            "routes": [base_route],
            "dateRanges": [
                {"name": "Week1", "from": "2024-08-01", "to": "2024-08-07", "exclusions": []},
                {"name": "Week2", "from": "2024-08-08", "to": "2024-08-14", "exclusions": []},
                {"name": "Week3", "from": "2024-08-15", "to": "2024-08-21", "exclusions": []},
                {"name": "Week4", "from": "2024-08-22", "to": "2024-08-28", "exclusions": []},
            ],
            "timeSets": base_ts,
        }

        payloads = [payload_b] if args.test_date_ranges_b else [payload_a, payload_b]
        for payload in payloads:
            log.info(f"\nTEST DATE RANGES — {payload['jobName']}")
            log.info(f"  dateRanges count: {len(payload['dateRanges'])}")
            if args.dry_run:
                log.info("DRY RUN — not submitted.")
                continue
            if not API_KEY or API_KEY == "METS_TA_CLE_ICI":
                log.error("TOMTOM_API_KEY not set!"); sys.exit(1)
            job_id = submit_job(payload)
            if job_id:
                status = poll_job(job_id)
                if status.get("jobState") == "DONE":
                    download_json(job_id, payload["jobName"], status.get("urls", []))
                    log.info(f"SUCCESS — {payload['jobName']}")
                else:
                    log.error(f"Job ended with state: {status.get('jobState')}")
        log.info("\nCheck TomTom dashboard: do both jobs consume the same credits?")
        log.info("  If YES → can combine all 36 months in 1 job (576 → 1)")
        log.info("  If NO  → cost per dateRange → keep 36 jobs (1 per month)")
        return

    # ── TEST: 4 corridors + 4 time sets in ONE job ────────────────────────────
    if args.test_all_corridors:
        date_range = next(dr for dr in DATE_RANGES_CURRENT if dr["name"] == "Aug2024_Full")
        job_name   = f"Phuket_AllCorridors_{date_range['name']}_AllTimeSets"
        payload    = {
            "jobName": job_name,
            "distanceUnit": DISTANCE_UNIT,
            "routes": [
                {
                    "name": c["name"],
                    "start": c["start"],
                    "end": c["end"],
                    "fullTraversal": FULL_TRAVERSAL,
                    "zoneId": ZONE_ID,
                    "probeSource": PROBE_SOURCE,
                }
                for c in CORRIDORS
            ],
            "dateRanges": [{
                "name": date_range["name"],
                "from": date_range["from"],
                "to": date_range["to"],
                "exclusions": []
            }],
            "timeSets": [
                {"name": ts["name"], "timeGroups": ts["timeGroups"]}
                for ts in TIME_SETS
            ],
        }
        log.info(f"TEST ALL CORRIDORS — {len(CORRIDORS)} routes × {len(TIME_SETS)} timeSets")
        log.info(json.dumps(payload, indent=2))
        if args.dry_run:
            log.info("DRY RUN — not submitted.")
            return
        if not API_KEY or API_KEY == "METS_TA_CLE_ICI":
            log.error("TOMTOM_API_KEY not set!"); sys.exit(1)
        job_id = submit_job(payload)
        if job_id:
            status = poll_job(job_id)
            if status.get("jobState") == "DONE":
                download_json(job_id, job_name, status.get("urls", []))
                log.info("SUCCESS — check raw_json/ for the output.")
                log.info("Verify: response should contain 4 routes × 4 timeSets = 16 summaries.")
            else:
                log.error(f"Job ended with state: {status.get('jobState')}")
        return

    # ── TEST: combined job (corridor A, Aug2024, all 4 time sets in one job) ──
    if args.test_combined:
        corridor_a  = next(c for c in CORRIDORS if c["id"] == "A_airport_road")
        date_range  = next(dr for dr in DATE_RANGES_CURRENT if dr["name"] == "Aug2024_Full")
        payload     = build_combined_payload(corridor_a, date_range, TIME_SETS)
        log.info(f"TEST COMBINED JOB — payload:")
        log.info(json.dumps(payload, indent=2))
        if args.dry_run:
            log.info("DRY RUN — not submitted.")
            return
        if not API_KEY or API_KEY == "METS_TA_CLE_ICI":
            log.error("TOMTOM_API_KEY not set!"); sys.exit(1)
        job_id = submit_job(payload)
        if job_id:
            status = poll_job(job_id)
            if status.get("jobState") == "DONE":
                download_json(job_id, payload["jobName"], status.get("urls", []))
                log.info("Combined job SUCCESS — check raw_json/ for the output file.")
                log.info("If it contains all 4 timeSets → confirmed, we can use combined jobs for all 576.")
            else:
                log.error(f"Job ended with state: {status.get('jobState')}")
        return

    # Build single all-in-one payload from ACTIVE_JOB_PLAN
    job_plan = ACTIVE_JOB_PLAN
    payload = {
        "jobName": job_plan["name"],
        "distanceUnit": DISTANCE_UNIT,
        "routes": [
            {
                "name": c["name"],
                "start": c["start"],
                "end": c["end"],
                "fullTraversal": FULL_TRAVERSAL,
                "zoneId": ZONE_ID,
                "probeSource": PROBE_SOURCE,
            }
            for c in job_plan["corridors"]
        ],
        "dateRanges": [
            {"name": dr["name"], "from": dr["from"], "to": dr["to"], "exclusions": []}
            for dr in job_plan["dateRanges"]
        ],
        "timeSets": [
            {"name": ts["name"], "timeGroups": ts["timeGroups"]}
            for ts in job_plan["timeSets"]
        ],
    }

    log.info(f"Active job plan: {job_plan['name']}")
    log.info(f"  Corridors  : {len(job_plan['corridors'])}")
    log.info(f"  TimeSets   : {len(job_plan['timeSets'])}")
    log.info(f"  DateRanges : {len(job_plan['dateRanges'])}")
    log.info(json.dumps(payload, indent=2))

    if args.dry_run:
        log.info("DRY RUN - job not submitted.")
        return

    if not API_KEY or API_KEY == "METS_TA_CLE_ICI":
        log.error("TOMTOM_API_KEY not set in .env!")
        sys.exit(1)

    reg_path = RAW_DIR / "job_registry.json"
    registry = json.loads(reg_path.read_text()) if reg_path.exists() else {}

    job_name = payload["jobName"]
    if job_name in registry and registry[job_name].get("status") == "DONE":
        log.info(f"Already done: {job_name}")
        return

    log.info(f"\nSubmitting: {job_name}")
    job_id = submit_job(payload)
    if not job_id:
        registry[job_name] = {"status": "SUBMIT_FAILED"}
        save_job_registry(registry)
        return

    registry[job_name] = {
        "jobId": job_id,
        "status": "SUBMITTED",
        "submitted_at": datetime.now().isoformat()
    }
    save_job_registry(registry)

    status = poll_job(job_id)

    if status.get("jobState") == "DONE":
        urls = status.get("urls", [])
        out_path = download_json(job_id, job_name, urls)
        registry[job_name].update({
            "status": "DONE",
            "output_file": str(out_path) if out_path else None,
            "urls": urls,
            "done_at": datetime.now().isoformat()
        })
    else:
        registry[job_name]["status"] = status.get("jobState", "FAILED")

    save_job_registry(registry)
    log.info(f"\nJob done: {job_name}")
    log.info(f"Registry: {reg_path}")
    log.info("-> Run next: python parse_results.py")


if __name__ == "__main__":
    main()
