"""Offline sample in the same shape as the NYC Open Data API response.

Used for demos without internet and for tests. Clearly synthetic; the real
run uses the API.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

BOROUGHS = ["MANHATTAN", "BROOKLYN", "QUEENS", "BRONX", "STATEN ISLAND", "Unspecified"]
COMPLAINTS = [
    ("NYPD", "Noise - Residential", "Loud Music/Party"),
    ("NYPD", "Illegal Parking", "Blocked Hydrant"),
    ("HPD", "HEAT/HOT WATER", "ENTIRE BUILDING"),
    ("DSNY", "Dirty Condition", "Trash"),
    ("DOT", "Street Condition", "Pothole"),
    ("DEP", "Water System", "Leak (Use Comments) (WA2)"),
]


def generate(day: str, rows: int = 500, seed: int | None = None) -> list[dict]:
    rng = random.Random(seed if seed is not None else day)
    start = datetime.fromisoformat(day)
    base_key = int(start.strftime("%Y%m%d")) * 1000
    out = []
    for i in range(rows):
        created = start + timedelta(seconds=rng.randint(0, 86_399))
        agency, ctype, desc = rng.choice(COMPLAINTS)
        closed = created + timedelta(hours=rng.uniform(0.2, 96)) if rng.random() < 0.8 else None
        out.append(
            {
                "unique_key": str(base_key + i),
                "created_date": created.strftime("%Y-%m-%dT%H:%M:%S.000"),
                "closed_date": closed.strftime("%Y-%m-%dT%H:%M:%S.000") if closed else None,
                "agency": agency,
                "complaint_type": ctype,
                "descriptor": desc,
                "status": "Closed" if closed else "In Progress",
                "borough": rng.choice(BOROUGHS),
                "incident_zip": str(rng.randint(10001, 11697)),
                "latitude": f"{rng.uniform(40.50, 40.91):.6f}",
                "longitude": f"{rng.uniform(-74.25, -73.70):.6f}",
            }
        )
    # The live API sometimes repeats a row across pages; mimic that.
    out.append(dict(out[0]))
    return out
