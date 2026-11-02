# Job Agent v2

A personal job-search assistant built with Python and Flask. It collects graduate and junior software roles, scores each one against my resume with an LLM, and drafts a tailored resume and cover letter for the strongest matches, so I spend my time reviewing and applying instead of searching.

> Personal-use tool. Every generated document is reviewed and edited by hand before it is sent.

## What it does

1. **Collects listings** from job boards (Seek, GradConnection, Indeed) for a set of keywords and a location.
2. **Stores them in SQLite**, de-duplicated by URL.
3. **Scores each job 0–100** against my resume using `gpt-4o-mini`, returning a fit reason, matching skills, missing skills and an apply / consider / skip recommendation.
4. **Drafts a tailored resume and cover letter** for jobs above a configurable score threshold.
5. **Shows everything in a Flask dashboard** with filters by score, source and status, plus per-job notes and application tracking.
6. **Runs daily at 8:00 am** via APScheduler, or on demand from the dashboard.

In a two-day trial run in June 2026 it collected and scored 42 listings and drafted documents for 41 of them.

## Architecture

```
scrapers/          Seek, GradConnection, Indeed collectors  ->  database.save_job()
database.py        SQLite: jobs, generated_docs, settings
ai/analyser.py     OpenAI calls: score job, tailor resume, write cover letter
ai/parsing.py      Validates model output (clamps scores, enforces enums, safe defaults)
runner.py          One pipeline run: collect -> score -> draft documents
scheduler.py       Daily cron trigger
app.py             Flask dashboard and settings UI
config.py          Settings loaded from .env and a local resume file
```

**Design decisions**

- **Model output is treated as untrusted input.** `ai/parsing.py` strips markdown fences, clamps `fit_score` to 0–100, forces the recommendation to `apply | consider | skip`, and falls back to a safe "skip" result on malformed JSON, so one bad response cannot break a run or corrupt the database.
- **No secrets or personal data in source control.** API keys, the Flask secret and contact details come from `.env`; the resume is read from a gitignored `resume.txt`.
- **Duplicates are handled by the database** (`UNIQUE` constraint on URL with `INSERT OR IGNORE`) rather than in application code.
- **Thresholds are configurable** from the settings page, so the expensive drafting step only runs for strong matches.

## Setup

Requires Python 3.10+.

```bash
git clone https://github.com/Vamshi-Gollapelly/job_agent_v2.git
cd job_agent_v2
python -m venv venv
venv\Scripts\activate            # Windows   (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt

copy .env.example .env           # macOS/Linux: cp .env.example .env
copy resume.example.txt resume.txt
```

Fill in `.env` (OpenAI key, a random Flask secret, your contact details) and `resume.txt`, then:

```bash
python app.py
```

Open http://127.0.0.1:5000.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

The tests cover model-output validation, the SQLite layer (de-duplication, score filtering, status updates, settings) and configuration loading. They use a temporary database and never call the OpenAI API.

## Limitations

- **Scrapers depend on each site's HTML** and break when layouts change; Indeed currently returns no results. An official job API would be more reliable.
- **Respect each site's terms of use.** This is a low-volume personal tool, not a crawler.
- **LLM scores and drafts can be wrong.** They are a starting point for human review, never sent automatically.
- Single-user and local only: no authentication on the dashboard.

## Tech

Python · Flask · SQLite · OpenAI API · BeautifulSoup · APScheduler · pytest
