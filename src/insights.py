"""
Day 9-10: AI Insights
Queries aggregated stats from the jobs table (top skills, remote %, top locations),
sends them to Gemini with a tight prompt, and stores the natural-language summary
in the insights table.

Run:
    python src/insights.py
"""

import json
import os

from dotenv import load_dotenv
from google import genai
from sqlalchemy import create_engine, text

from load import ensure_schema

load_dotenv()

MODEL_NAME = "gemini-flash-latest"  # Google auto-updates this alias to their newest Flash model


def get_engine():
    db_url = os.getenv("NEON_DATABASE_URL")
    if not db_url:
        raise RuntimeError("NEON_DATABASE_URL not found in .env")
    return create_engine(db_url, pool_pre_ping=True, pool_recycle=300)


def gather_stats(engine):
    """Pull aggregated numbers out of Postgres - this is what we hand to the LLM,
    not raw rows. Keeping this structured (not free text) keeps the prompt small
    and the output grounded in real numbers instead of the model guessing."""

    with engine.connect() as conn:
        total_jobs = conn.execute(text("SELECT COUNT(*) FROM jobs")).scalar()

        remote_count = conn.execute(
            text("SELECT COUNT(*) FROM jobs WHERE is_remote = true")
        ).scalar()

        # unnest() expands the skills array into rows so we can COUNT + GROUP BY it
        top_skills = conn.execute(text("""
            SELECT skill, COUNT(*) as postings
            FROM jobs, unnest(skills) AS skill
            GROUP BY skill
            ORDER BY postings DESC
            LIMIT 10
        """)).fetchall()

        top_locations = conn.execute(text("""
            SELECT location, COUNT(*) as postings
            FROM jobs
            WHERE location IS NOT NULL AND location != ''
            GROUP BY location
            ORDER BY postings DESC
            LIMIT 5
        """)).fetchall()

    remote_pct = round((remote_count / total_jobs) * 100, 1) if total_jobs else 0

    stats = {
        "total_jobs": total_jobs,
        "remote_count": remote_count,
        "remote_pct": remote_pct,
        "top_skills": [{"skill": s, "postings": c} for s, c in top_skills],
        "top_locations": [{"location": l, "postings": c} for l, c in top_locations],
    }
    return stats


def build_prompt(stats):
    """Turn the structured stats into a tight, specific prompt.
    Keeping instructions explicit (length, tone, no fluff) avoids generic LLM filler."""
    return f"""You are analyzing tech job market data scraped today. Here are the aggregated stats:

Total postings analyzed: {stats['total_jobs']}
Remote postings: {stats['remote_count']} ({stats['remote_pct']}%)

Top skills by number of postings mentioning them:
{json.dumps(stats['top_skills'], indent=2)}

Top locations by posting count:
{json.dumps(stats['top_locations'], indent=2)}

Write a 3-4 sentence natural-language market summary a job seeker or recruiter
would find useful. Mention specific skills and numbers/percentages from the data
above. Be concrete, not generic - no filler like "the job market is dynamic."
Do not invent any numbers not present in the data above.
"""


def generate_insight(prompt):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in .env")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    return response.text.strip()


def save_insight(engine, summary, stats):
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO insights (summary, stats) VALUES (:summary, :stats)"),
            {"summary": summary, "stats": json.dumps(stats)},
        )
    print("Saved insight to insights table.")


if __name__ == "__main__":
    engine = get_engine()
    ensure_schema(engine)

    print("Gathering aggregated stats from jobs table...")
    stats = gather_stats(engine)
    print(f"  {stats['total_jobs']} total postings, {stats['remote_pct']}% remote")
    print(f"  Top skill: {stats['top_skills'][0] if stats['top_skills'] else 'none found'}")

    prompt = build_prompt(stats)

    print("\nCalling Gemini...")
    summary = generate_insight(prompt)

    print("\n--- Generated Insight ---")
    print(summary)

    save_insight(engine, summary, stats)

    print("\nDay 9-10 status: AI insights layer working.")