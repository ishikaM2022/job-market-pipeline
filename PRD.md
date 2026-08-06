# PRD: Tech Job Market Insights Pipeline

**Author:** Ishika Wadagbalkar
**Status:** Shipped (v1)
**Last updated:** August 2026

## Problem

Job seekers and recruiters trying to understand tech hiring trends today rely on
scattered, manual signal: browsing individual job boards, reading anecdotal
LinkedIn posts, or trusting stale annual industry reports. There's no lightweight,
current, and specific view of "what skills are actually in demand right now, and
where."

This creates two concrete pains:

- **Job seekers** don't know which skills to prioritize learning or highlighting
  on their resume for the current market, not last year's.
- **Recruiters/hiring managers** lack a quick way to benchmark whether their
  own job requirements and locations align with what the broader market is doing.

## Users

| User                                        | Need                                                                                 |
| ------------------------------------------- | ------------------------------------------------------------------------------------ |
| Job seeker (e.g. new grad, career switcher) | "What skills should I learn or emphasize right now?"                                 |
| Recruiter / talent sourcer                  | "Are my role requirements competitive with the market?"                              |
| AI/data-curious hiring manager (secondary)  | Wants to see a live example of an AI-augmented data product, not just a static chart |

## Solution

An automated pipeline that pulls live tech job postings daily, extracts structured
signal (skills, location, remote status) from unstructured listing data, and uses
an LLM to translate the aggregated numbers into a plain-language market summary -
displayed on a public, always-current dashboard.

**Why an LLM layer, not just charts?** Charts show _what_ the data says; the AI
summary explains _what it means_ in a sentence a non-analyst can immediately use.
This is the same "insight over raw metrics" gap that AI-augmented BI products in
industry are increasingly built to close.

## Success metrics

Since this is a portfolio/demo project rather than a monetized product, success is
measured by functional and demonstration criteria rather than business KPIs:

- **Pipeline reliability:** runs daily without manual intervention (via GitHub
  Actions cron), for a sustained multi-week period without failure
- **Data freshness:** dashboard reflects postings no more than 24 hours old
- **Insight quality:** AI-generated summaries are specific (cite real numbers/skills
  from that day's data) rather than generic filler - manually spot-checked
- **Artifact completeness:** a stranger can clone the repo, follow the README, and
  get the full pipeline running locally without needing to ask questions

_(In a production/monetized version, real success metrics would instead track
dashboard weekly active users, session depth, and downstream actions taken - e.g.
resume edits or job applications - which would require product analytics
instrumentation not built in this v1.)_

## Non-goals (v1)

- Not attempting full labor-market statistical rigor (single free data source,
  not a stratified/representative sample)
- Not building user accounts, saved searches, or personalization
- Not covering non-tech roles, despite the underlying data source including them
  (see Future Work)

## Future work

- Filter ingestion to tech-relevant postings only (currently ingests all
  categories from the source API and lets skill-matching implicitly filter signal)
- Add week-over-week trend comparison ("Python demand up 12% vs last week") rather
  than only a current-snapshot summary
- Expand beyond a single data source to reduce sampling bias
- Add basic user-facing filters (by location, by skill) on the dashboard itself
