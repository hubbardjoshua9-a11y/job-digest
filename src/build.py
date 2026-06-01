"""
build.py — Builder.

Reads memory/latest.json and writes site/index.html as a fully
self-contained page. All job data is embedded directly in the HTML,
so the hosted page does NO fetching and cannot break on a phone.
"""

import json
import html
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LATEST_PATH = ROOT / "memory" / "latest.json"
OUT_PATH = ROOT / "docs" / "index.html"


def esc(s):
    return html.escape(str(s or ""))


def fmt_date(iso):
    if not iso:
        return ""
    try:
        d = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return d.strftime("%-d %b")
    except Exception:
        return ""


def fmt_salary(j):
    lo, hi = j.get("salary_min"), j.get("salary_max")
    if not lo and not hi:
        return ""
    try:
        if lo and hi and lo != hi:
            return f"${int(lo):,} – ${int(hi):,}"
        v = lo or hi
        return f"${int(v):,}"
    except Exception:
        return ""


def badges(j):
    out = []
    if j.get("remote"):
        out.append('<span class="badge badge-remote">Remote / WFH</span>')
    if j.get("local"):
        out.append('<span class="badge badge-local">NSW 2570 area</span>')
    if j.get("is_new"):
        out.append('<span class="badge badge-new">New</span>')
    return "".join(out)


def job_card(j):
    sal = fmt_salary(j)
    date = fmt_date(j.get("created"))
    return f"""
    <a class="job-card" href="{esc(j.get('url'))}" target="_blank" rel="noopener">
      <div class="job-card-top">
        <div class="job-main">
          <div class="job-title">{esc(j.get('title'))}</div>
          <div class="job-company">{esc(j.get('company') or 'View listing')}{(' · ' + esc(j.get('location'))) if j.get('location') else ''}</div>
        </div>
        <div class="job-meta">
          <div class="date-label">{esc(date)}</div>
          {f'<div class="salary">{esc(sal)}</div>' if sal else ''}
        </div>
      </div>
      <div class="badges">{badges(j)}</div>
      {f'<div class="job-desc">{esc(j.get("desc"))}…</div>' if j.get('desc') else ''}
    </a>"""


def build():
    if not LATEST_PATH.exists():
        raise SystemExit("No memory/latest.json found. Run fetch first (python run.py).")

    data = json.loads(LATEST_PATH.read_text(encoding="utf-8"))
    jobs = data.get("jobs", [])

    gen = data.get("generated_at", "")
    try:
        gen_dt = datetime.datetime.fromisoformat(gen)
        gen_str = gen_dt.strftime("%a %-d %b at %-I:%M %p")
    except Exception:
        gen_str = gen

    remote_jobs = [j for j in jobs if j.get("remote") and not j.get("local")]
    local_jobs = [j for j in jobs if j.get("local")]
    other_jobs = [j for j in jobs if not j.get("remote") and not j.get("local")]

    sections = ""
    if remote_jobs:
        sections += section("Remote / work from home", remote_jobs)
    if local_jobs:
        sections += section("NSW 2570 area", local_jobs)
    if other_jobs:
        sections += section("Other matches", other_jobs)
    if not jobs:
        sections = '<div class="empty">No matching roles in the latest run. Try widening the keywords in config/search.yaml.</div>'

    page = TEMPLATE.format(
        gen_str=esc(gen_str),
        total=data.get("total", 0),
        new=data.get("new", 0),
        remote=data.get("remote", 0),
        local=data.get("local", 0),
        sections=sections,
    )
    OUT_PATH.write_text(page, encoding="utf-8")
    print(f"=> wrote {OUT_PATH} ({len(jobs)} roles)")


def section(title, jobs):
    cards = "".join(job_card(j) for j in jobs)
    return f"""
    <div class="section">
      <div class="section-header">
        <span>{esc(title)}</span>
        <span class="count">{len(jobs)} role{'s' if len(jobs) != 1 else ''}</span>
      </div>
      {cards}
    </div>"""


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daily Job Digest</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f7f7f6; color: #1a1a1a; padding: 16px; line-height: 1.5; }}
.container {{ max-width: 720px; margin: 0 auto; padding: 1.5rem 0; }}
.header {{ margin-bottom: 1.5rem; }}
.header h1 {{ font-size: 20px; font-weight: 600; }}
.header p {{ font-size: 13px; color: #666; margin-top: 4px; }}
.stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 1.75rem; }}
@media (max-width: 480px) {{ .stats {{ grid-template-columns: repeat(2, 1fr); }} }}
.stat {{ background: #efefed; border-radius: 10px; padding: 12px 14px; }}
.stat-label {{ font-size: 12px; color: #666; margin-bottom: 4px; }}
.stat-value {{ font-size: 24px; font-weight: 600; }}
.section {{ margin-bottom: 1.75rem; }}
.section-header {{ display: flex; align-items: center; gap: 8px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #e6e6e4; }}
.section-header span:first-child {{ font-size: 15px; font-weight: 600; }}
.section-header .count {{ font-size: 12px; color: #666; background: #efefed; padding: 2px 10px; border-radius: 20px; }}
.job-card {{ display: block; background: #fff; border: 1px solid #e6e6e4; border-radius: 12px; padding: 14px 16px; margin-bottom: 10px; text-decoration: none; color: inherit; transition: border-color .15s, transform .05s; }}
.job-card:hover {{ border-color: #b0b0ad; }}
.job-card:active {{ transform: scale(0.998); }}
.job-card-top {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }}
.job-main {{ flex: 1; min-width: 0; }}
.job-title {{ font-size: 15px; font-weight: 600; color: #1558b0; margin-bottom: 3px; }}
.job-company {{ font-size: 13px; color: #666; }}
.job-meta {{ text-align: right; flex-shrink: 0; }}
.date-label {{ font-size: 12px; color: #999; white-space: nowrap; }}
.salary {{ font-size: 12px; color: #0F6E56; font-weight: 600; margin-top: 2px; white-space: nowrap; }}
.badges {{ display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px; }}
.badge {{ font-size: 11px; padding: 3px 9px; border-radius: 20px; font-weight: 600; }}
.badge-remote {{ background: #E1F5EE; color: #0F6E56; }}
.badge-local {{ background: #E6F1FB; color: #185FA5; }}
.badge-new {{ background: #FAEEDA; color: #854F0B; }}
.job-desc {{ font-size: 12px; color: #777; margin-top: 10px; line-height: 1.55; }}
.empty {{ text-align: center; padding: 2rem; color: #888; font-size: 14px; }}
.footer {{ margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e6e6e4; font-size: 12px; color: #999; text-align: center; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Daily job digest</h1>
    <p>Updated {gen_str} · refreshed once a day</p>
  </div>

  <div class="stats">
    <div class="stat"><div class="stat-label">Total roles</div><div class="stat-value">{total}</div></div>
    <div class="stat"><div class="stat-label">New today</div><div class="stat-value">{new}</div></div>
    <div class="stat"><div class="stat-label">Remote / WFH</div><div class="stat-value">{remote}</div></div>
    <div class="stat"><div class="stat-label">NSW 2570 area</div><div class="stat-value">{local}</div></div>
  </div>

  {sections}

  <div class="footer">Sourced via Adzuna · aggregates Seek, Indeed &amp; other AU job boards</div>
</div>
</body>
</html>"""


if __name__ == "__main__":
    build()
