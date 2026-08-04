# Job Market Pipeline + AI Insights Dashboard

An end-to-end data pipeline that pulls tech job postings, stores them in Postgres,
generates AI-written market insights with Gemini, and displays everything on a
Streamlit dashboard. Runs on a daily schedule via GitHub Actions.

**Status:** 🚧 In progress — Day 1 of 14

## Architecture
```
Arbeitnow API → extract.py → transform → Neon Postgres → Gemini insights → Streamlit dashboard
                                                ^
                                    GitHub Actions (daily cron)
```

## Stack
- **Data source:** Arbeitnow Job Board API (free, no auth)
- **Database:** Neon.tech (serverless Postgres, free tier)
- **AI insights:** Google Gemini API (free tier)
- **Scheduling:** GitHub Actions cron
- **Dashboard:** Streamlit + Streamlit Community Cloud
- **Containerization:** Docker

## Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your real Neon + Gemini keys
python src/test_setup.py
```

## Progress log
- [x] Day 1-2: Project setup, accounts (Neon, Gemini), repo scaffold
- [ ] Day 3-4: Extract job data
- [ ] Day 5-6: Transform + load into Postgres
- [ ] Day 7-8: Automate + containerize
- [ ] Day 9-10: AI insights layer
- [ ] Day 11-12: Streamlit dashboard
- [ ] Day 13-14: PRD, polish, demo

## PRD
See `PRD.md` (added Day 13).
