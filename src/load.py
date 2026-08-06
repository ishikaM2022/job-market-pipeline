"""
Day 5-6: Transform + Load
Reads the most recent raw_jobs_*.json file (from extract.py), transforms it,
and upserts it into Neon Postgres.

Transform steps:
1. Strip HTML tags out of the description (Arbeitnow returns descriptions as HTML)
2. Extract technical skills by keyword-matching the description against a hardcoded list
   (tags field is too broad/categorical to use for this - see schema.sql comment)
3. Convert the posted_at unix timestamp into a real datetime
4. Upsert into the `jobs` table on `slug` (so re-running this is safe / idempotent)

Run:
    python src/load.py
"""

import glob
import json
import os
import re
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

# Hardcoded skill list - simple, explainable, no ML needed.
# Extend this list any time you notice a skill you care about isn't being caught.
SKILLS = [
    "Python", "SQL", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
    "React", "Angular", "Vue", "Node.js", "Django", "Flask", "FastAPI",
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Snowflake", "BigQuery",
    "Spark", "Kafka", "Airflow", "dbt",
    "Machine Learning", "TensorFlow", "PyTorch", "NLP",
    "Git", "CI/CD", "Linux", "REST API", "GraphQL", "Excel", "Power BI", "Tableau",
]


def get_latest_raw_file():
    """Find the most recently saved raw_jobs_*.json file."""
    pattern = os.path.join(DATA_DIR, "raw_jobs_*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError("No raw_jobs_*.json files found. Run extract.py first.")
    return files[-1]


def strip_html(raw_html):
    """Remove HTML tags from a description, leaving plain readable text."""
    if not raw_html:
        return ""
    text_only = re.sub(r"<[^>]+>", " ", raw_html)
    text_only = re.sub(r"\s+", " ", text_only).strip()
    return text_only


def extract_skills(description_text):
    """Return the subset of SKILLS that appear (case-insensitive, whole-word) in the description."""
    found = []
    for skill in SKILLS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, description_text, re.IGNORECASE):
            found.append(skill)
    return found


# Known variants that should collapse into one canonical location name.
# Add to this as you spot more duplicates in the dashboard's Top Locations chart.
LOCATION_ALIASES = {
    "münchen": "Munich",
    "munich": "Munich",
    "remote": "Remote",
}


def normalize_location(raw_location):
    """Clean up location text so identical places don't fragment into separate
    chart bars due to casing/spelling differences (e.g. 'München' vs 'Munich',
    'remote' vs 'Remote')."""
    if not raw_location:
        return raw_location
    cleaned = raw_location.strip()
    key = cleaned.lower()
    if key in LOCATION_ALIASES:
        return LOCATION_ALIASES[key]
    return cleaned


def determine_remote(job, normalized_location):
    """Arbeitnow's own `remote` boolean is unreliable - some postings with
    location='remote' still have remote=false. Treat it as remote if EITHER
    the API's field says so, OR the location text itself says 'remote'."""
    api_flag = bool(job.get("remote", False))
    location_says_remote = (normalized_location or "").lower() == "remote"
    return api_flag or location_says_remote


def transform(raw_jobs):
    """Turn raw Arbeitnow job dicts into rows ready for the jobs table."""
    rows = []
    for job in raw_jobs:
        plain_description = strip_html(job.get("description"))
        skills = extract_skills(plain_description)
        location = normalize_location(job.get("location"))
        is_remote = determine_remote(job, location)

        posted_at = None
        if job.get("created_at"):
            try:
                posted_at = datetime.fromtimestamp(int(job["created_at"]), tz=timezone.utc)
            except (ValueError, TypeError):
                posted_at = None

        rows.append({
            "slug": job.get("slug"),
            "title": job.get("title"),
            "company": job.get("company_name"),
            "location": location,
            "is_remote": is_remote,
            "tags": job.get("tags", []),
            "skills": skills,
            "description": plain_description,
            "url": job.get("url"),
            "posted_at": posted_at,
        })

    # Drop any rows missing a slug - we need it as the primary key
    rows = [r for r in rows if r["slug"]]
    return rows


def ensure_schema(engine):
    """Create the jobs table if it doesn't already exist."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    with engine.begin() as conn:
        conn.execute(text(schema_sql))
    print("Schema ensured (jobs table ready).")


def upsert_jobs(engine, rows):
    """Insert rows, updating existing ones on slug conflict."""
    upsert_sql = text("""
        INSERT INTO jobs (slug, title, company, location, is_remote, tags, skills,
                           description, url, posted_at, fetched_at)
        VALUES (:slug, :title, :company, :location, :is_remote, :tags, :skills,
                :description, :url, :posted_at, now())
        ON CONFLICT (slug) DO UPDATE SET
            title = EXCLUDED.title,
            company = EXCLUDED.company,
            location = EXCLUDED.location,
            is_remote = EXCLUDED.is_remote,
            tags = EXCLUDED.tags,
            skills = EXCLUDED.skills,
            description = EXCLUDED.description,
            url = EXCLUDED.url,
            posted_at = EXCLUDED.posted_at,
            fetched_at = now();
    """)
    with engine.begin() as conn:
        for row in rows:
            conn.execute(upsert_sql, row)
    print(f"Upserted {len(rows)} rows into jobs table.")


if __name__ == "__main__":
    db_url = os.getenv("NEON_DATABASE_URL")
    if not db_url:
        raise RuntimeError("NEON_DATABASE_URL not found in .env")

    engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=300)

    latest_file = get_latest_raw_file()
    print(f"Loading raw data from {latest_file}")
    with open(latest_file, "r", encoding="utf-8") as f:
        raw_jobs = json.load(f)

    rows = transform(raw_jobs)
    print(f"Transformed {len(rows)} rows.")

    # Quick visibility into how well skill-matching is working
    with_skills = sum(1 for r in rows if r["skills"])
    print(f"{with_skills}/{len(rows)} postings had at least one matched skill.")

    ensure_schema(engine)
    upsert_jobs(engine, rows)

    print("\nDay 5-6 status: Transform + Load working.")