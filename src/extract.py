"""
Day 3-4: Extract
Pulls job postings from the Arbeitnow API and saves the raw response
to data/ as a timestamped JSON file.

Why save raw JSON first (instead of going straight to Postgres)?
- Lets you debug transform/load logic without re-hitting the API
- Gives you a paper trail / backup of exactly what the API returned
- Standard ETL practice: land raw data first, transform later

Run:
    python src/extract.py
"""

import json
import os
from datetime import datetime, timezone

import requests

API_URL = "https://www.arbeitnow.com/api/job-board-api"
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def fetch_jobs():
    """Fetch all job postings from the Arbeitnow API (single page, no auth needed)."""
    print(f"Fetching jobs from {API_URL} ...")
    resp = requests.get(API_URL, timeout=15)
    resp.raise_for_status()
    payload = resp.json()
    jobs = payload.get("data", [])
    print(f"Fetched {len(jobs)} job postings.")
    return jobs


def save_raw(jobs):
    """Save raw job data to data/raw_jobs_<timestamp>.json"""
    os.makedirs(DATA_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"raw_jobs_{timestamp}.json"
    filepath = os.path.join(DATA_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    print(f"Saved raw data to {filepath}")
    return filepath


def preview(jobs, n=3):
    """Print a quick preview of the first n jobs so you can sanity-check the fields."""
    print(f"\n--- Preview of first {n} jobs ---")
    for job in jobs[:n]:
        print(f"  Title:    {job.get('title')}")
        print(f"  Company:  {job.get('company_name')}")
        print(f"  Location: {job.get('location')}")
        print(f"  Remote:   {job.get('remote')}")
        print(f"  Tags:     {job.get('tags')}")
        print(f"  Posted:   {job.get('created_at')}")
        print("  ---")


if __name__ == "__main__":
    jobs = fetch_jobs()
    if not jobs:
        print("No jobs returned. Check the API or your connection.")
    else:
        save_raw(jobs)
        preview(jobs)
        print(f"\nDay 3-4 status: Extract working. {len(jobs)} postings captured.")