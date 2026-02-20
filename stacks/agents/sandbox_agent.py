"""
Sandbox Agent — Phase 3 of the Autonomous Invention Engine.

Responsibilities:
- Load the top-scored ideas from the scorecard
- For each idea above threshold, scaffold a minimal repo structure
  using the template directory
- Push the scaffold via GitHub API if the org token is present
- Emit a build report JSON
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── GitHub helpers ────────────────────────────────────────────────────────────

def _gh_request(
    method: str,
    path: str,
    token: str,
    body: dict | None = None,
) -> tuple[int, Any]:
    """Make an authenticated GitHub REST API request."""
    url = f"https://api.github.com{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        return exc.code, {}


def _repo_exists(org: str, name: str, token: str) -> bool:
    status, _ = _gh_request("GET", f"/repos/{org}/{name}", token)
    return status == 200


def _create_repo(org: str, name: str, description: str, token: str) -> bool:
    """Create a new private repository in the org."""
    status, _ = _gh_request(
        "POST",
        f"/orgs/{org}/repos",
        token,
        body={
            "name": name,
            "description": description,
            "private": True,
            "auto_init": True,
        },
    )
    return status == 201


# ── Scaffolding ───────────────────────────────────────────────────────────────

def _slugify(title: str) -> str:
    """Convert a signal title to a URL-safe repo name."""
    import re
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title).strip("-").lower()
    return slug[:60] or "idea"


def _build_idea(idea: dict, org: str, token: str, template_dir: Path) -> dict:
    """Attempt to scaffold a repository for a single scored idea."""
    title = idea.get("title", "unknown")
    slug = _slugify(title)
    repo_name = f"sandbox-{slug}"
    description = idea.get("description") or f"Auto-scaffolded from: {title}"

    result: dict = {
        "idea_id": idea.get("id", ""),
        "repo_name": repo_name,
        "score": idea.get("score", 0),
        "status": "skipped",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if not token:
        result["status"] = "skipped"
        result["reason"] = "GH_TOKEN not set — dry run mode"
        return result

    if _repo_exists(org, repo_name, token):
        result["status"] = "exists"
        result["reason"] = f"Repository {org}/{repo_name} already exists"
        return result

    created = _create_repo(org, repo_name, description, token)
    result["status"] = "created" if created else "failed"
    if not created:
        result["reason"] = "GitHub API returned non-201"

    return result


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Sandbox Builder Agent")
    parser.add_argument("--scorecard", required=True, help="Path to idea scorecard JSON")
    parser.add_argument("--org", required=True, help="GitHub organisation")
    parser.add_argument("--template-dir", default="stacks/templates", help="Template directory path")
    parser.add_argument("--threshold", type=float, default=0.6, help="Minimum score to build")
    parser.add_argument("--max-builds", type=int, default=3, help="Max sandboxes per run")
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN", "")
    template_dir = Path(args.template_dir)

    with open(args.scorecard, encoding="utf-8") as fh:
        scored: list[dict] = json.load(fh)

    top_ideas = [s for s in scored if s.get("score", 0) >= args.threshold][: args.max_builds]
    print(f"[sandbox] Building {len(top_ideas)} idea(s) above threshold {args.threshold}")

    build_results: list[dict] = []
    for idea in top_ideas:
        print(f"[sandbox] Processing: {idea.get('title')} (score={idea.get('score')})")
        result = _build_idea(idea, args.org, token, template_dir)
        build_results.append(result)
        print(f"[sandbox]  → status: {result['status']}")

    # Write report
    report_path = "/tmp/sandbox_report.json"
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(build_results, fh, indent=2)

    print(f"[sandbox] Report written to {report_path}")


if __name__ == "__main__":
    main()
