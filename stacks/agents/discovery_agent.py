"""
Discovery Agent — Phase 1 of the Autonomous Invention Engine.

Responsibilities:
- Pull GitHub trending repositories for the org
- Ingest public RSS/news feeds for industry signals
- Emit a structured JSON index of discovered signals
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from typing import Any


# ── Helpers ──────────────────────────────────────────────────────────────────

def _fetch_json(url: str, headers: dict[str, str] | None = None) -> Any:
    """Fetch a URL and return parsed JSON, or an empty list on error."""
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as exc:  # noqa: BLE001
        print(f"[discovery] warn: fetch failed for {url}: {exc}", file=sys.stderr)
        return []


def _github_trending(org: str, token: str) -> list[dict]:
    """Return recently-updated repos in the org as discovery signals."""
    url = (
        f"https://api.github.com/orgs/{org}/repos"
        f"?sort=updated&direction=desc&per_page=30&type=all"
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    repos = _fetch_json(url, headers)
    if not isinstance(repos, list):
        return []

    signals: list[dict] = []
    for repo in repos:
        signals.append(
            {
                "id": f"github-{repo.get('id', '')}",
                "source": "github",
                "type": "repository",
                "title": repo.get("full_name", ""),
                "description": repo.get("description") or "",
                "url": repo.get("html_url", ""),
                "language": repo.get("language") or "unknown",
                "stars": repo.get("stargazers_count", 0),
                "topics": repo.get("topics", []),
                "discovered_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    return signals


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Discovery Agent")
    parser.add_argument("--org", required=True, help="GitHub organisation name")
    parser.add_argument("--output", required=True, help="Path to write the index JSON")
    parser.add_argument("--goal", default="", help="Optional high-level goal for context")
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN", "")
    if not token:
        print("[discovery] warn: GH_TOKEN not set — GitHub API rate limits apply.", file=sys.stderr)

    signals: list[dict] = []

    print(f"[discovery] Discovering signals for org: {args.org}")
    signals.extend(_github_trending(args.org, token))

    print(f"[discovery] Total signals collected: {len(signals)}")

    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(signals, fh, indent=2)

    print(f"[discovery] Index written to {args.output}")


if __name__ == "__main__":
    main()
