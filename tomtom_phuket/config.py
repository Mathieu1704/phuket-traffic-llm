"""
config.py - Corridor definitions and TomTom job parameters for Phuket traffic analysis.

4 corridors covering the main tourist and commuter routes on Phuket island.
Time sets represent typical traffic periods (AM peak, PM peak, off-peak, weekend).
"""

# Corridors - 4 key routes defined by start/end GPS coordinates
CORRIDORS = [
    {
        "id": "A_airport_road",
        "name": "Airport Road (Route 402)",
        "description": "Thepkrasattri Road - HKT Airport to Thalang. "
                       "Main tourist arrival corridor, sensitive to flight schedules.",
        "start": {"latitude": 8.1132, "longitude": 98.3017},  # HKT Airport exit
        "end":   {"latitude": 7.9975, "longitude": 98.3333},  # Thalang roundabout
    },
    {
        "id": "B_patong_hill",
        "name": "Patong Hill (Route 4029)",
        "description": "Kathu to Patong Beach via mountain pass. "
                       "Most congested corridor on Phuket, strong high/low season contrast.",
        "start": {"latitude": 7.9213, "longitude": 98.3239},  # Kathu junction Rte 4
        "end":   {"latitude": 7.8937, "longitude": 98.2982},  # Patong Beach front
    },
    {
        "id": "C_phuket_town_rawai",
        "name": "Phuket Town to Rawai (Route 4022)",
        "description": "Town center to southern beaches (Nai Harn, Rawai). "
                       "Mix of residential and beach tourist traffic.",
        "start": {"latitude": 7.8851, "longitude": 98.3921},  # Phuket Town center
        "end":   {"latitude": 7.7812, "longitude": 98.3317},  # Rawai Beach
    },
    {
        "id": "D_bypass_road",
        "name": "Bypass Road (Route 4027)",
        "description": "Eastern ring road - Kathu to Chalong. "
                       "Baseline reference corridor with relatively smooth traffic flow.",
        "start": {"latitude": 7.9519, "longitude": 98.3381},  # Kathu / Bypass north
        "end":   {"latitude": 7.8906, "longitude": 98.3981},  # Chalong Circle
    },
]

# Time sets - 24 total (TomTom API limit = 24 per job).
# 12 weekday + 12 weekend, same time windows -> direct weekday vs weekend comparison.
# 1h granularity on peaks (07-09h, 16-19h), grouped windows elsewhere.
# TomTom API constraints:
#   - Max 24 timesets per job
#   - No cross-midnight ranges -> 23:00-23:59 is the last slot
#   - "Inclusively separate" required -> all ranges end at :59
TIME_SETS = [
    # -- Weekday (Mon-Fri) : 12 windows --
    {"name": "Weekday_Night",      "label": "Mon-Fri 00:00-04:59", "timeGroups": [{"days": ["MON", "TUE", "WED", "THU", "FRI"], "times": ["0:00-4:59"]}]},
    {"name": "Weekday_Early",      "label": "Mon-Fri 05:00-06:59", "timeGroups": [{"days": ["MON", "TUE", "WED", "THU", "FRI"], "times": ["5:00-6:59"]}]},
    {"name": "Weekday_AM1",        "label": "Mon-Fri 07:00-07:59", "timeGroups": [{"days": ["MON", "TUE", "WED", "THU", "FRI"], "times": ["7:00-7:59"]}]},
    {"name": "Weekday_AM2",        "label": "Mon-Fri 08:00-08:59", "timeGroups": [{"days": ["MON", "TUE", "WED", "THU", "FRI"], "times": ["8:00-8:59"]}]},
    {"name": "Weekday_Morning",    "label": "Mon-Fri 09:00-11:59", "timeGroups": [{"days": ["MON", "TUE", "WED", "THU", "FRI"], "times": ["9:00-11:59"]}]},
    {"name": "Weekday_Midday",     "label": "Mon-Fri 12:00-13:59", "timeGroups": [{"days": ["MON", "TUE", "WED", "THU", "FRI"], "times": ["12:00-13:59"]}]},
    {"name": "Weekday_Afternoon",  "label": "Mon-Fri 14:00-15:59", "timeGroups": [{"days": ["MON", "TUE", "WED", "THU", "FRI"], "times": ["14:00-15:59"]}]},
    {"name": "Weekday_PrePM",      "label": "Mon-Fri 16:00-16:59", "timeGroups": [{"days": ["MON", "TUE", "WED", "THU", "FRI"], "times": ["16:00-16:59"]}]},
    {"name": "Weekday_PM1",        "label": "Mon-Fri 17:00-17:59", "timeGroups": [{"days": ["MON", "TUE", "WED", "THU", "FRI"], "times": ["17:00-17:59"]}]},
    {"name": "Weekday_PM2",        "label": "Mon-Fri 18:00-18:59", "timeGroups": [{"days": ["MON", "TUE", "WED", "THU", "FRI"], "times": ["18:00-18:59"]}]},
    {"name": "Weekday_Evening",    "label": "Mon-Fri 19:00-21:59", "timeGroups": [{"days": ["MON", "TUE", "WED", "THU", "FRI"], "times": ["19:00-21:59"]}]},
    {"name": "Weekday_LateNight",  "label": "Mon-Fri 22:00-23:59", "timeGroups": [{"days": ["MON", "TUE", "WED", "THU", "FRI"], "times": ["22:00-23:59"]}]},
    # -- Weekend (Sat-Sun) : 12 windows (same slots for direct comparison) --
    {"name": "Weekend_Night",      "label": "Sat-Sun 00:00-04:59", "timeGroups": [{"days": ["SAT", "SUN"], "times": ["0:00-4:59"]}]},
    {"name": "Weekend_Early",      "label": "Sat-Sun 05:00-06:59", "timeGroups": [{"days": ["SAT", "SUN"], "times": ["5:00-6:59"]}]},
    {"name": "Weekend_AM1",        "label": "Sat-Sun 07:00-07:59", "timeGroups": [{"days": ["SAT", "SUN"], "times": ["7:00-7:59"]}]},
    {"name": "Weekend_AM2",        "label": "Sat-Sun 08:00-08:59", "timeGroups": [{"days": ["SAT", "SUN"], "times": ["8:00-8:59"]}]},
    {"name": "Weekend_Morning",    "label": "Sat-Sun 09:00-11:59", "timeGroups": [{"days": ["SAT", "SUN"], "times": ["9:00-11:59"]}]},
    {"name": "Weekend_Midday",     "label": "Sat-Sun 12:00-13:59", "timeGroups": [{"days": ["SAT", "SUN"], "times": ["12:00-13:59"]}]},
    {"name": "Weekend_Afternoon",  "label": "Sat-Sun 14:00-15:59", "timeGroups": [{"days": ["SAT", "SUN"], "times": ["14:00-15:59"]}]},
    {"name": "Weekend_PrePM",      "label": "Sat-Sun 16:00-16:59", "timeGroups": [{"days": ["SAT", "SUN"], "times": ["16:00-16:59"]}]},
    {"name": "Weekend_PM1",        "label": "Sat-Sun 17:00-17:59", "timeGroups": [{"days": ["SAT", "SUN"], "times": ["17:00-17:59"]}]},
    {"name": "Weekend_PM2",        "label": "Sat-Sun 18:00-18:59", "timeGroups": [{"days": ["SAT", "SUN"], "times": ["18:00-18:59"]}]},
    {"name": "Weekend_Evening",    "label": "Sat-Sun 19:00-21:59", "timeGroups": [{"days": ["SAT", "SUN"], "times": ["19:00-21:59"]}]},
    {"name": "Weekend_LateNight",  "label": "Sat-Sun 22:00-23:59", "timeGroups": [{"days": ["SAT", "SUN"], "times": ["22:00-23:59"]}]},
]

# Aliases for backward compatibility
TIME_SETS_WEEKDAY = [ts for ts in TIME_SETS if ts["name"].startswith("Weekday")]
TIME_SETS_WEEKEND = [ts for ts in TIME_SETS if ts["name"].startswith("Weekend")]

# =============================================================================
# DATE RANGES
# =============================================================================
# Key insight (confirmed from existing JSON + Ott Pattara / TomTom):
#   - 1 single report contains all 4 corridors + all timesets + N date ranges
#   - Max 24 date ranges per report, max 1 year per date range
#   - Adding date ranges does NOT cost more (confirmed by TomTom, 2026-03-13)
#   - Cost is based on km of routes only: 60.58 km total (4 corridors)
#   - 1 year = 3 years = same price -> always use 3-year option
#
# Current status: August 2024 only (trial account)

# -- Currently active --
DATE_RANGES_CURRENT = [
    {"name": "Aug2024_Full", "from": "2024-08-01", "to": "2024-08-31"},
]

# -- OPTION 1: 1 year (2024 full) - 1 date range --
# Cheapest option. Covers full seasonal cycle (high/low/monsoon seasons).
# Recommended if 3-year option costs more.
DATE_RANGES_1Y = [
    {"name": "Year2024", "from": "2024-01-01", "to": "2024-12-31"},
]

# -- OPTION 2: 3 years (2022-2024) - 3 date ranges --
# Ideal for thesis: inter-annual variance, post-COVID recovery, trend analysis.
# Max 1 year per range -> 3 separate ranges required.
# Cost confirmed same as 1 year (Ott Pattara / TomTom, 2026-03-13). Use this.
DATE_RANGES_3Y = [
    {"name": "Year2022", "from": "2022-01-01", "to": "2022-12-31"},
    {"name": "Year2023", "from": "2023-01-01", "to": "2023-12-31"},
    {"name": "Year2024", "from": "2024-01-01", "to": "2024-12-31"},
]

# -- OPTION 3: 24 mois mensuels (Jan 2023 - Déc 2024) - 24 date ranges --
# Granularité mensuelle réelle. 24 = limite max TomTom -> 1 seul job.
# 2024 est une année bissextile -> février 2024 = 29 jours.
DATE_RANGES_MONTHLY_2Y = [
    {"name": "2023_01", "from": "2023-01-01", "to": "2023-01-31"},
    {"name": "2023_02", "from": "2023-02-01", "to": "2023-02-28"},
    {"name": "2023_03", "from": "2023-03-01", "to": "2023-03-31"},
    {"name": "2023_04", "from": "2023-04-01", "to": "2023-04-30"},
    {"name": "2023_05", "from": "2023-05-01", "to": "2023-05-31"},
    {"name": "2023_06", "from": "2023-06-01", "to": "2023-06-30"},
    {"name": "2023_07", "from": "2023-07-01", "to": "2023-07-31"},
    {"name": "2023_08", "from": "2023-08-01", "to": "2023-08-31"},
    {"name": "2023_09", "from": "2023-09-01", "to": "2023-09-30"},
    {"name": "2023_10", "from": "2023-10-01", "to": "2023-10-31"},
    {"name": "2023_11", "from": "2023-11-01", "to": "2023-11-30"},
    {"name": "2023_12", "from": "2023-12-01", "to": "2023-12-31"},
    {"name": "2024_01", "from": "2024-01-01", "to": "2024-01-31"},
    {"name": "2024_02", "from": "2024-02-01", "to": "2024-02-29"},
    {"name": "2024_03", "from": "2024-03-01", "to": "2024-03-31"},
    {"name": "2024_04", "from": "2024-04-01", "to": "2024-04-30"},
    {"name": "2024_05", "from": "2024-05-01", "to": "2024-05-31"},
    {"name": "2024_06", "from": "2024-06-01", "to": "2024-06-30"},
    {"name": "2024_07", "from": "2024-07-01", "to": "2024-07-31"},
    {"name": "2024_08", "from": "2024-08-01", "to": "2024-08-31"},
    {"name": "2024_09", "from": "2024-09-01", "to": "2024-09-30"},
    {"name": "2024_10", "from": "2024-10-01", "to": "2024-10-31"},
    {"name": "2024_11", "from": "2024-11-01", "to": "2024-11-30"},
    {"name": "2024_12", "from": "2024-12-01", "to": "2024-12-31"},
]

# =============================================================================
# JOB PLANS
# =============================================================================
# 1 job = 4 corridors + 24 timesets (12 weekday + 12 weekend) + date ranges

JOB_PLAN_CURRENT = {
    "name": "Phuket_AllCorridors_Aug2024_24ts",
    "corridors": CORRIDORS,
    "timeSets": TIME_SETS,
    "dateRanges": DATE_RANGES_CURRENT,
}

JOB_PLAN_3Y = {
    "name": "Phuket_AllCorridors_2022_2024_24ts",
    "corridors": CORRIDORS,
    "timeSets": TIME_SETS,
    "dateRanges": DATE_RANGES_3Y,
}

JOB_PLAN_MONTHLY_2Y = {
    "name": "Phuket_AllCorridors_2023_2024_24ts_Monthly_v2",
    "corridors": CORRIDORS,
    "timeSets": TIME_SETS,
    "dateRanges": DATE_RANGES_MONTHLY_2Y,
}

# Set this to the plan you want to submit
ACTIVE_JOB_PLAN = JOB_PLAN_MONTHLY_2Y

# API settings
API_BASE_URL = "https://api.tomtom.com/traffic/trafficstats"
DISTANCE_UNIT = "KILOMETERS"
ZONE_ID = "Asia/Bangkok"
PROBE_SOURCE = "ALL"
FULL_TRAVERSAL = False
