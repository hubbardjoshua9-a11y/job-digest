# Job Digest — Instruction Layer

You are working inside a daily job-search digest system. This file is the **Instruction** layer of an ICM (Instruction / Context / Memory) architecture. Read it first, every session.

## What this system does

Once a day it pulls fresh job listings from the Adzuna API (a free aggregator that indexes Seek, Indeed, and hundreds of other Australian job boards), filters them down to roles that match one person's criteria, and writes a single static `site/index.html` page. That page is hosted free on Netlify and bookmarked on her phone.

The person searching: a graphic designer in NSW 2570 (Camden area), 10 years self-employed. Strong in Canva and admin, comfortable across the full Adobe Suite, reels/video, plus digital marketing — web design, SEO, and writing. She is **not** using her psych degree yet. She wants roles that are remote/WFH anywhere in Australia, OR within ~30 min of postcode 2570.

This system does NOT apply to jobs, write resumes, or write cover letters. It only finds and presents matching roles.

## The three layers

- **Instruction** (this file): what the system is and the rules it follows. Rarely changes.
- **Context** (`config/search.yaml`): the editable search terms, locations, and filters. Change this to tune what gets found.
- **Memory** (`memory/seen.json`): every job ID the system has shown before, so new roles get flagged as "new today". `memory/latest.json` holds the most recent run's results.

## The architecture (60 / 30 / 10)

- **60% plumbing** — `src/fetch.py` calls the API, `src/build.py` writes HTML, GitHub Actions and Netlify handle scheduling and hosting.
- **30% rules** — keyword relevance, remote-vs-local classification, and de-duplication all live in `src/fetch.py` as plain logic.
- **10% AI** — none required. The system runs fully on its own. (Optional: you could add a Claude call to score or summarise roles, but it is not needed to work.)

## Non-negotiable rules

1. Never commit API keys. They live in environment variables (locally in `.env`, in GitHub as repo secrets). `.env` is git-ignored.
2. The hosted page must be self-contained — all job data is baked into `site/index.html` at build time. No client-side fetching. This is why it never breaks on a phone.
3. Keep it lean. If a feature can be a line in `config/search.yaml`, it does not need new code.
4. One run = fetch, then build. `python run.py` does both.

## How to run

```
pip install -r requirements.txt
python run.py
```

This updates `site/index.html`. Commit and push, and Netlify redeploys automatically. Or let the GitHub Action in `.github/workflows/daily.yml` do it on a schedule.
