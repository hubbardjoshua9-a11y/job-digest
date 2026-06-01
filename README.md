# Daily Job Digest

A small system that finds graphic-design / digital-marketing roles in Australia
(remote, or near postcode 2570) and publishes them to a free web page that
updates once a day. It does **not** apply to jobs or write resumes — it just
finds and lists matching roles.

It pulls from the **Adzuna API**, a free job-search aggregator that indexes
Seek, Indeed, and hundreds of other Australian job boards. Earlier attempts to
read Seek/Indeed RSS directly failed because those feeds no longer exist —
Adzuna is the legitimate, reliable source.

---

## Folder layout (ICM architecture)

```
job-digest/
├── CLAUDE.md              # Instruction layer — what the system is
├── config/
│   └── search.yaml        # Context layer — EDIT THIS to tune searches
├── memory/
│   ├── seen.json          # Memory — job IDs already shown (flags "new")
│   └── latest.json        # Memory — most recent run's results
├── src/
│   ├── fetch.py           # Calls Adzuna, filters, classifies
│   └── build.py           # Bakes results into site/index.html
├── site/
│   └── index.html         # The hosted page (generated)
├── run.py                 # Run everything: python run.py
└── .github/workflows/
    └── daily.yml          # Auto-runs once a day (optional)
```

---

## One-time setup

### 1. Get free Adzuna API keys (2 minutes)
1. Go to **https://developer.adzuna.com**
2. Sign up for a free account
3. Create an application
4. Copy your **App ID** and **App Key**

### 2. Run it locally
```bash
# install dependencies
pip install -r requirements.txt

# copy the env template and paste your keys into it
cp .env.example .env
# (open .env in a text editor, paste the two keys, save)

# load the keys, then run
#   macOS / Linux:
export $(cat .env | xargs) && python run.py
#   Windows (PowerShell):
#   Get-Content .env | ForEach-Object { $p=$_.split('='); [Environment]::SetEnvironmentVariable($p[0],$p[1]) }; python run.py
```

Open `site/index.html` in your browser. That's the digest.

### 3. Host it free on Netlify
You already have a Netlify project connected to GitHub. To publish:
1. Put this whole folder in your GitHub repo
2. In Netlify, set the **publish directory** to `site`
3. Push — Netlify serves `site/index.html` at your `.netlify.app` URL
4. Bookmark that URL on her phone

---

## Make it update automatically (recommended)

So her computer doesn't need to be on, let GitHub run it daily:

1. In your GitHub repo go to **Settings → Secrets and variables → Actions**
2. Add two repository secrets:
   - `ADZUNA_APP_ID`
   - `ADZUNA_APP_KEY`
3. That's it. The workflow in `.github/workflows/daily.yml` runs every morning,
   rebuilds `site/index.html`, commits it, and Netlify redeploys.
4. To run it on demand, go to the **Actions** tab → **Daily Job Digest** →
   **Run workflow**.

---

## Tuning what gets found

Open `config/search.yaml` — no coding needed. You can:
- add or change **searches** (keywords + location + radius)
- widen/narrow the **relevant_keywords** filter
- add words to **exclude_keywords** to drop noise
- change **max_days_old** (1 = today only, 7 = past week)

Save, re-run `python run.py`, done.
