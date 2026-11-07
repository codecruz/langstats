#!/usr/bin/env python3
"""Keep a history of the repository's clones and views.

GitHub only keeps 14 days of traffic. This reads the daily figures from the API
and merges them into a CSV, one row per day, so the history goes further back:

    GH_TOKEN=... python3 tools/traffic.py codecruz/langstats traffic.csv

Each Claude Code install or update of the plugin clones the repository, so the
daily unique cloners are a rough measure of active installs. They also count
your own clones and CI checkouts, and one person with several computers counts
several times.
"""

from __future__ import annotations

import csv
import json
import os
import sys
import urllib.request
from pathlib import Path

FIELDS = ["date", "clones", "unique_cloners", "views", "unique_visitors"]


def fetch(repo: str, kind: str, token: str) -> dict:
    request = urllib.request.Request(
        "https://api.github.com/repos/%s/traffic/%s?per=day" % (repo, kind),
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer %s" % token,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def merge(rows: dict[str, dict[str, int]], clones: dict, views: dict) -> dict[str, dict[str, int]]:
    """Fold the API's daily figures into `rows`, keyed by date. A day already
    stored is overwritten: GitHub's latest figure for it is the most complete."""
    for source, (total, unique) in ((clones, ("clones", "unique_cloners")), (views, ("views", "unique_visitors"))):
        for day in source.get(total, []):
            date = day["timestamp"][:10]
            row = rows.setdefault(date, dict.fromkeys(FIELDS[1:], 0))
            row[total] = int(day["count"])
            row[unique] = int(day["uniques"])
    return rows


def read_csv(path: Path) -> dict[str, dict[str, int]]:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8", newline="") as f:
        return {row["date"]: {k: int(row.get(k) or 0) for k in FIELDS[1:]} for row in csv.DictReader(f)}


def write_csv(path: Path, rows: dict[str, dict[str, int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(FIELDS)
        for date in sorted(rows):
            writer.writerow([date] + [rows[date][k] for k in FIELDS[1:]])


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: traffic.py OWNER/REPO FILE.csv", file=sys.stderr)
        return 2
    token = os.environ.get("GH_TOKEN")
    if not token:
        print("traffic: set GH_TOKEN to a token that can read the repository's traffic", file=sys.stderr)
        return 1
    repo, path = argv[0], Path(argv[1])
    rows = merge(read_csv(path), fetch(repo, "clones", token), fetch(repo, "views", token))
    write_csv(path, rows)
    print("traffic: %d days in %s" % (len(rows), path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
