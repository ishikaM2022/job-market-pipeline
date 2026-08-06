"""
Day 11-12: Dashboard
Streamlit app showing job market metrics and the latest AI-generated insight.

Run locally:
    streamlit run src/app.py

When deployed on Streamlit Community Cloud, database credentials come from
st.secrets instead of .env (set these in the app's Settings > Secrets).
"""

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

st.set_page_config(
    page_title="Tech Job Market Pipeline",
    page_icon="📊",
    layout="wide",
)


def get_db_url():
    """Prefer Streamlit secrets (cloud deployment), fall back to .env (local dev).
    Wrapped in try/except because st.secrets raises an error (not just a missing key)
    when no secrets.toml file exists at all, which is the case for local dev without one."""
    try:
        if "NEON_DATABASE_URL" in st.secrets:
            return st.secrets["NEON_DATABASE_URL"]
    except Exception:
        pass
    return os.getenv("NEON_DATABASE_URL")


@st.cache_resource
def get_engine():
    db_url = get_db_url()
    if not db_url:
        st.error("NEON_DATABASE_URL not found. Set it in .env (local) or Secrets (cloud).")
        st.stop()
    return create_engine(db_url)


@st.cache_data(ttl=600)  # refresh every 10 minutes, avoids hammering the DB on every interaction
def load_summary_stats(_engine):
    with _engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM jobs")).scalar()
        remote = conn.execute(text("SELECT COUNT(*) FROM jobs WHERE is_remote = true")).scalar()
        companies = conn.execute(text("SELECT COUNT(DISTINCT company) FROM jobs")).scalar()
    return {
        "total": total or 0,
        "remote": remote or 0,
        "remote_pct": round((remote / total) * 100, 1) if total else 0,
        "companies": companies or 0,
    }


@st.cache_data(ttl=600)
def load_top_skills(_engine, limit=15):
    query = text("""
        SELECT skill, COUNT(*) as postings
        FROM jobs, unnest(skills) AS skill
        GROUP BY skill
        ORDER BY postings DESC
        LIMIT :limit
    """)
    with _engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"limit": limit})
    return df


@st.cache_data(ttl=600)
def load_top_locations(_engine, limit=10):
    query = text("""
        SELECT location, COUNT(*) as postings
        FROM jobs
        WHERE location IS NOT NULL AND location != ''
        GROUP BY location
        ORDER BY postings DESC
        LIMIT :limit
    """)
    with _engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"limit": limit})
    return df


@st.cache_data(ttl=600)
def load_latest_insight(_engine):
    query = text("SELECT summary, generated_at FROM insights ORDER BY generated_at DESC LIMIT 1")
    with _engine.connect() as conn:
        result = conn.execute(query).fetchone()
    return result


@st.cache_data(ttl=600)
def load_recent_jobs(_engine, limit=20):
    query = text("""
        SELECT title, company, location, is_remote, skills, posted_at
        FROM jobs
        ORDER BY fetched_at DESC
        LIMIT :limit
    """)
    with _engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"limit": limit})
    return df


# --- Page layout ---

engine = get_engine()

st.title("📊 Tech Job Market Pipeline")
st.caption("Live data pulled daily from Arbeitnow, analyzed with Gemini")

# AI Insight banner
insight = load_latest_insight(engine)
if insight:
    summary, generated_at = insight
    st.info(f"**Latest AI Insight** ({generated_at.strftime('%Y-%m-%d %H:%M UTC')})\n\n{summary}")
else:
    st.warning("No AI insight generated yet. Run src/insights.py or src/pipeline.py first.")

# Metric cards
stats = load_summary_stats(engine)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Postings", stats["total"])
col2.metric("Remote Postings", stats["remote"], f"{stats['remote_pct']}%")
col3.metric("Unique Companies", stats["companies"])
col4.metric("Data Source", "Arbeitnow API")

st.divider()

# Charts
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Top Skills in Demand")
    skills_df = load_top_skills(engine)
    if not skills_df.empty:
        st.bar_chart(skills_df.set_index("skill")["postings"])
    else:
        st.write("No skill data yet.")

with chart_col2:
    st.subheader("Top Locations")
    locations_df = load_top_locations(engine)
    if not locations_df.empty:
        st.bar_chart(locations_df.set_index("location")["postings"])
    else:
        st.write("No location data yet.")

st.divider()

# Recent postings table
st.subheader("Recent Postings")
recent_df = load_recent_jobs(engine)
st.dataframe(recent_df, use_container_width=True)