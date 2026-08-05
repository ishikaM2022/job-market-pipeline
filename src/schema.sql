-- Day 5-6: Schema
-- Table storing transformed job postings pulled from Arbeitnow.
-- `slug` is Arbeitnow's own unique identifier for a posting, so we use it as our primary key
-- to make loading idempotent (re-running load.py updates existing rows instead of duplicating).

CREATE TABLE IF NOT EXISTS jobs (
    slug            TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    company         TEXT,
    location        TEXT,
    is_remote       BOOLEAN,
    tags            TEXT[],          -- Arbeitnow's own broad category tags (e.g. "Product", "Marketing")
    skills          TEXT[],          -- our extracted technical skills (e.g. "Python", "SQL", "AWS")
    description     TEXT,            -- HTML stripped to plain text
    url             TEXT,
    posted_at       TIMESTAMPTZ,      -- when the job was originally posted
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT now()  -- when OUR pipeline pulled it
);

-- Speeds up "top skills this week" style queries in the AI insights step (Days 9-10)
CREATE INDEX IF NOT EXISTS idx_jobs_posted_at ON jobs (posted_at);