"""
Day 1 sanity check.
Run this to confirm:
1. The Arbeitnow API is reachable and returns job data
2. Your .env file loads correctly (Neon + Gemini keys present)

This does NOT hit Postgres or Gemini yet — that's later in the plan.
It just proves your foundations are solid before you build on them.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_arbeitnow_api():
    print("Testing Arbeitnow API...")
    url = "https://www.arbeitnow.com/api/job-board-api"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    jobs = data.get("data", [])
    print(f"  Success. Received {len(jobs)} job postings.")
    if jobs:
        sample = jobs[0]
        print("  Sample job fields:")
        for key in ["title", "company_name", "location", "tags", "remote"]:
            print(f"    {key}: {sample.get(key)}")
    return len(jobs) > 0


def test_env_vars():
    print("\nChecking .env variables...")
    neon_url = os.getenv("NEON_DATABASE_URL")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if neon_url and "xxxxx" not in neon_url:
        print("  NEON_DATABASE_URL: found")
    else:
        print("  NEON_DATABASE_URL: missing or still placeholder (fill in .env)")

    if gemini_key and gemini_key != "your_gemini_api_key_here":
        print("  GEMINI_API_KEY: found")
    else:
        print("  GEMINI_API_KEY: missing or still placeholder (fill in .env)")


if __name__ == "__main__":
    api_ok = test_arbeitnow_api()
    test_env_vars()

    print("\n--- Day 1 status ---")
    if api_ok:
        print("Data source confirmed working. You're ready for Day 3-4 (Extract).")
    else:
        print("Data source did not return results. Check your internet connection or the API status.")
