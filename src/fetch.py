"""
fetch.py — Plumbing + rules layer.

Calls the Adzuna API for each configured search, applies the
relevance / remote / local rules, de-duplicates against memory,
flags brand-new roles, and writes memory/latest.json.

No API key is stored here. Keys come from environment variables:
    ADZUNA_APP_ID
    ADZUNA_APP_KEY
"""

import os
import json
import time
import datetime
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "search.yaml"
SEEN_PATH = ROOT / "memory" / "seen.json"
LATEST_PATH = ROOT / "memory" / "latest.json"

API_BASE = "https://api.adzuna.com/v1/api/jobs/au/search/1"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_seen():
    if SEEN_PATH.exists():
        try:
            return set(json.loads(SEEN_PATH.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()


def save_seen(seen):
    SEEN_PATH.write_text(json.dumps(sorted(seen), indent=2), encoding="utf-8")


def contains_any(text, words):
    t = text.lower()
    return any(w.lower() in t for w in words)


def classify(text, cfg):
    remote = contains_any(text, cfg["remote_keywords"])
    local = contains_any(text, cfg["local_keywords"])
    return remote, local


def run_search(search, cfg, app_id, app_key):
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": cfg.get("results_per_page", 50),
        "max_days_old": cfg.get("max_days_old", 7),
        "sort_by": "date",
        "content-type": "application/json",
    }
    if search.get("what"):
        params["what"] = search["what"]
    if search.get("what_or"):
        params["what_or"] = search["what_or"]
    if search.get("where"):
        params["where"] = search["where"]
    if search.get("distance"):
        params["distance"] = search["distance"]

    try:
        resp = requests.get(API_BASE, params=params, timeout=20)
        resp.raise_for_status()
        return resp.json().get("results", [])
    except Exception as e:
        print(f"  ! search failed ({search.get('what')} @ {search.get('where')}): {e}")
        return []


def fetch_all():
    cfg = load_config()
    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")

    if not app_id or not app_key:
        raise SystemExit(
            "Missing Adzuna credentials.\n"
            "Set ADZUNA_APP_ID and ADZUNA_APP_KEY as environment variables.\n"
            "Get free keys at https://developer.adzuna.com"
        )

    seen = load_seen()
    collected = {}

    for search in cfg["searches"]:
        label = f"{search.get('what', '')} @ {search.get('where', 'anywhere')}"
        print(f"- searching: {label}")
        results = run_search(search, cfg, app_id, app_key)
        print(f"    {len(results)} raw results")

        for r in results:
            title = r.get("title", "") or ""
            desc = r.get("description", "") or ""
            company = (r.get("company") or {}).get("display_name", "") or ""
            location = (r.get("location") or {}).get("display_name", "") or ""
            full_text = " ".join([title, desc, location])

            # relevance gate
            if not contains_any(full_text, cfg["relevant_keywords"]):
                continue
            # exclusion gate
            if cfg.get("exclude_keywords") and contains_any(full_text, cfg["exclude_keywords"]):
                continue

            remote, local = classify(full_text, cfg)
            # A pure "remote" search returns roles even if the word isn't in
            # the text — treat the search intent as a remote signal.
            if search.get("where", "").strip().lower() == "remote":
                remote = True
            if search.get("distance"):
                local = True

            if not (remote or local):
                continue

            job_id = str(r.get("id", "")) or (title + company)[:60]
            if job_id in collected:
                continue

            collected[job_id] = {
                "id": job_id,
                "title": title.strip(),
                "company": company.strip(),
                "location": location.strip(),
                "url": r.get("redirect_url", ""),
                "desc": " ".join(desc.split())[:200],
                "created": r.get("created", ""),
                "salary_min": r.get("salary_min"),
                "salary_max": r.get("salary_max"),
                "remote": remote,
                "local": local,
                "is_new": job_id not in seen,
            }

        time.sleep(0.4)  # be gentle on the API

    jobs = list(collected.values())
    # newest first
    jobs.sort(key=lambda j: j.get("created", ""), reverse=True)

    # update memory
    for j in jobs:
        seen.add(j["id"])
    save_seen(seen)

    payload = {
        "generated_at": datetime.datetime.now().isoformat(),
        "total": len(jobs),
        "new": sum(1 for j in jobs if j["is_new"]),
        "remote": sum(1 for j in jobs if j["remote"]),
        "local": sum(1 for j in jobs if j["local"]),
        "jobs": jobs,
    }
    LATEST_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\n=> {len(jobs)} matching roles ({payload['new']} new). Wrote memory/latest.json")
    return payload


if __name__ == "__main__":
    fetch_all()
