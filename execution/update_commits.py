#!/usr/bin/env python3
"""
FinFlowAI — Commit Log Updater
Reads the full git log and rewrites COMMITS.md with the latest commits.

Usage:
    python execution/update_commits.py

Run this after every push to keep COMMITS.md up to date.
"""

import subprocess
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / "COMMITS.md"


def get_commits() -> list[dict]:
    """Return all commits as a list of dicts, most recent first."""
    result = subprocess.run(
        [
            "git", "log",
            "--pretty=format:%h|%s|%ad|%b<END>",
            "--date=format:%Y-%m-%d",
        ],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
    )

    if result.returncode != 0:
        print(f"ERROR: git log failed:\n{result.stderr}")
        sys.exit(1)

    commits = []
    raw_entries = result.stdout.split("<END>")
    for entry in raw_entries:
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split("|", 3)
        if len(parts) < 3:
            continue
        commits.append({
            "hash":  parts[0].strip(),
            "subject": parts[1].strip(),
            "date":  parts[2].strip(),
            "body":  parts[3].strip() if len(parts) > 3 else "",
        })

    return commits


def build_markdown(commits: list[dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total = len(commits)

    lines = [
        "# FinFlowAI — Commit Log",
        "",
        f"> This file is updated with every commit pushed to the repository.",
        f"> To regenerate it automatically, run: `python execution/update_commits.py`",
        f"> Last updated: {now}",
        "",
        "---",
        "",
        "## Commits",
        "",
        "| # | Hash | Description | Date |",
        "|---|------|-------------|------|",
    ]

    for i, commit in enumerate(commits):
        num = total - i
        lines.append(
            f"| {num} | `{commit['hash']}` | {commit['subject']} | {commit['date']} |"
        )

    lines += ["", "---", "", "## Details", ""]

    for i, commit in enumerate(commits):
        num = total - i
        lines.append(f"### `{commit['hash']}` — {commit['subject']}")
        lines.append(f"**Date:** {commit['date']}")
        if commit["body"]:
            lines.append(f"**Notes:** {commit['body']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    print("Reading git log...")
    commits = get_commits()
    print(f"Found {len(commits)} commit(s).")

    markdown = build_markdown(commits)

    OUTPUT_FILE.write_text(markdown, encoding="utf-8")
    print(f"COMMITS.md updated at: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
