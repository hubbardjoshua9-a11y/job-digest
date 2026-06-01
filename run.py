"""
run.py — one command does everything: fetch jobs, then build the page.

Usage:
    python run.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import fetch
import build

if __name__ == "__main__":
    print("=== Job Digest: fetching ===")
    fetch.fetch_all()
    print("\n=== Job Digest: building page ===")
    build.build()
    print("\nDone. Open site/index.html, or commit & push to update the live site.")
