"""
Day 7-8: Combined pipeline
Runs extract -> transform -> load as a single command with basic logging.
This is what both Docker and GitHub Actions will invoke.

Run:
    python src/pipeline.py
"""

import logging
import sys

from extract import fetch_jobs, save_raw
from load import (
    ensure_schema,
    transform,
    upsert_jobs,
)
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run():
    load_dotenv()
    db_url = os.getenv("NEON_DATABASE_URL")
    if not db_url:
        logger.error("NEON_DATABASE_URL not set. Aborting.")
        sys.exit(1)

    logger.info("Pipeline started.")

    try:
        jobs = fetch_jobs()
    except Exception as e:
        logger.error(f"Extract failed: {e}")
        sys.exit(1)

    if not jobs:
        logger.warning("No jobs returned from API. Nothing to load.")
        return

    save_raw(jobs)
    logger.info(f"Extracted {len(jobs)} postings.")

    rows = transform(jobs)
    with_skills = sum(1 for r in rows if r["skills"])
    logger.info(f"Transformed {len(rows)} rows ({with_skills} with matched skills).")

    try:
        engine = create_engine(db_url)
        ensure_schema(engine)
        upsert_jobs(engine, rows)
    except Exception as e:
        logger.error(f"Load failed: {e}")
        sys.exit(1)

    logger.info("Pipeline completed successfully.")


if __name__ == "__main__":
    run()