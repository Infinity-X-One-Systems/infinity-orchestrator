"""
Backlog Agent — Maintains the machine-readable backlog ledger.

Responsibilities:
- Read the current backlog from .infinity/ledger/backlog.json
- Accept new items (from signals, alerts, issues, or workflow runs)
- Upsert items idempotently by ID
- Recompute statistics
- Write the updated ledger atomically

Schema fields per item:
  id                  — stable deterministic ID (sha1 of repo+type+title)
  repo                — full_name e.g. "Org/repo"
  type                — bug | security | chore | feature
  priority            — 1 (highest) … 5 (lowest)
  risk                — low | medium | high | critical
  status              — open | in_progress | done | blocked | cancelled
  title               — short human-readable title
  description         — detailed description
  evidence_links      — list of URLs (issues, PRs, alerts)
  created_at          — ISO-8601
  updated_at          — ISO-8601
  policy_decision_ref — TAP decision log entry or "" if not yet recorded
  run_id              — GitHub Actions run_id that created/last updated this item
  workflow            — workflow filename that produced this item
  commit_sha          — git commit SHA at time of update
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(os.environ.get("GENESIS_REPO_PATH", str(Path(__file__).parent.parent.parent)))
_LEDGER_PATH = _REPO_ROOT / ".infinity" / "ledger" / "backlog.json"

_VALID_TYPES = {"bug", "security", "chore", "feature"}
_VALID_RISK = {"low", "medium", "high", "critical"}
_VALID_STATUS = {"open", "in_progress", "done", "blocked", "cancelled"}


# ── Helpers ──────────────────────────────────────────────────────────────────


def _item_id(repo: str, item_type: str, title: str) -> str:
    """Generate a stable, deterministic ID from the item's key fields."""
    raw = f"{repo}:{item_type}:{title}".lower().strip()
    return hashlib.sha1(raw.encode()).hexdigest()[:16]  # noqa: S324 — non-crypto use


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_ledger(path: Path) -> dict[str, Any]:
    """Load the backlog ledger, returning a new empty ledger if absent."""
    if path.exists():
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return {
        "version": "1.0.0",
        "schema": "https://infinity-x-one-systems.github.io/infinity-orchestrator/schemas/backlog-v1.json",
        "last_updated": "1970-01-01T00:00:00Z",
        "generated_by": "backlog_agent.py",
        "note": "Auto-generated backlog ledger. Do not edit manually.",
        "items": [],
        "statistics": {},
    }


def _recompute_stats(items: list[dict]) -> dict:
    stats: dict[str, Any] = {
        "total": len(items),
        "by_status": {"open": 0, "in_progress": 0, "done": 0, "blocked": 0, "cancelled": 0},
        "by_risk": {"low": 0, "medium": 0, "high": 0, "critical": 0},
        "by_type": {"bug": 0, "security": 0, "chore": 0, "feature": 0},
    }
    for item in items:
        status = item.get("status", "open")
        risk = item.get("risk", "low")
        itype = item.get("type", "chore")
        if status in stats["by_status"]:
            stats["by_status"][status] += 1
        if risk in stats["by_risk"]:
            stats["by_risk"][risk] += 1
        if itype in stats["by_type"]:
            stats["by_type"][itype] += 1
    return stats


def _write_ledger(path: Path, ledger: dict) -> None:
    """Write ledger atomically (write to .tmp then rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(ledger, fh, indent=2)
        fh.write("\n")
    tmp.replace(path)


# ── Public API ────────────────────────────────────────────────────────────────


def upsert_item(
    *,
    repo: str,
    item_type: str,
    priority: int,
    risk: str,
    title: str,
    description: str = "",
    evidence_links: list[str] | None = None,
    status: str = "open",
    policy_decision_ref: str = "",
    run_id: str = "",
    workflow: str = "",
    commit_sha: str = "",
    ledger_path: Path = _LEDGER_PATH,
) -> dict:
    """Upsert a single item into the backlog ledger and return the updated item."""
    if item_type not in _VALID_TYPES:
        raise ValueError(f"item_type must be one of {_VALID_TYPES}, got {item_type!r}")
    if risk not in _VALID_RISK:
        raise ValueError(f"risk must be one of {_VALID_RISK}, got {risk!r}")
    if status not in _VALID_STATUS:
        raise ValueError(f"status must be one of {_VALID_STATUS}, got {status!r}")
    if not 1 <= priority <= 5:
        raise ValueError(f"priority must be 1–5, got {priority}")

    item_id = _item_id(repo, item_type, title)
    now = _now()

    ledger = _load_ledger(ledger_path)
    items: list[dict] = ledger.get("items", [])

    # Find existing item
    existing_idx = next((i for i, x in enumerate(items) if x.get("id") == item_id), None)

    if existing_idx is not None:
        existing = items[existing_idx]
        existing.update({
            "repo": repo,
            "type": item_type,
            "priority": priority,
            "risk": risk,
            "status": status,
            "title": title,
            "description": description,
            "evidence_links": evidence_links or existing.get("evidence_links", []),
            "updated_at": now,
            "policy_decision_ref": policy_decision_ref or existing.get("policy_decision_ref", ""),
            "run_id": run_id,
            "workflow": workflow,
            "commit_sha": commit_sha,
        })
        updated_item = existing
    else:
        updated_item = {
            "id": item_id,
            "repo": repo,
            "type": item_type,
            "priority": priority,
            "risk": risk,
            "status": status,
            "title": title,
            "description": description,
            "evidence_links": evidence_links or [],
            "created_at": now,
            "updated_at": now,
            "policy_decision_ref": policy_decision_ref,
            "run_id": run_id,
            "workflow": workflow,
            "commit_sha": commit_sha,
        }
        items.append(updated_item)

    ledger["items"] = items
    ledger["last_updated"] = now
    ledger["statistics"] = _recompute_stats(items)

    _write_ledger(ledger_path, ledger)
    return updated_item


def bulk_upsert(items_data: list[dict], ledger_path: Path = _LEDGER_PATH) -> list[dict]:
    """Upsert multiple items at once and return the updated items."""
    results = []
    for item in items_data:
        updated = upsert_item(
            repo=item["repo"],
            item_type=item["type"],
            priority=item.get("priority", 3),
            risk=item.get("risk", "low"),
            title=item["title"],
            description=item.get("description", ""),
            evidence_links=item.get("evidence_links", []),
            status=item.get("status", "open"),
            policy_decision_ref=item.get("policy_decision_ref", ""),
            run_id=item.get("run_id", ""),
            workflow=item.get("workflow", ""),
            commit_sha=item.get("commit_sha", ""),
            ledger_path=ledger_path,
        )
        results.append(updated)
    return results


def validate_ledger(ledger_path: Path = _LEDGER_PATH) -> tuple[bool, list[str]]:
    """Validate the ledger schema and return (is_valid, list_of_errors)."""
    errors: list[str] = []
    if not ledger_path.exists():
        return False, [f"Ledger file not found: {ledger_path}"]

    try:
        with open(ledger_path, encoding="utf-8") as fh:
            ledger = json.load(fh)
    except json.JSONDecodeError as exc:
        return False, [f"Invalid JSON: {exc}"]

    required_top = {"version", "items", "statistics"}
    for field in required_top:
        if field not in ledger:
            errors.append(f"Missing top-level field: {field!r}")

    items = ledger.get("items", [])
    required_item_fields = {"id", "repo", "type", "priority", "risk", "status", "title", "created_at", "updated_at"}
    for i, item in enumerate(items):
        for field in required_item_fields:
            if field not in item:
                errors.append(f"Item [{i}] missing required field: {field!r}")
        if item.get("type") not in _VALID_TYPES:
            errors.append(f"Item [{i}] invalid type: {item.get('type')!r}")
        if item.get("risk") not in _VALID_RISK:
            errors.append(f"Item [{i}] invalid risk: {item.get('risk')!r}")
        if item.get("status") not in _VALID_STATUS:
            errors.append(f"Item [{i}] invalid status: {item.get('status')!r}")

    return (len(errors) == 0), errors


# ── CLI ───────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Backlog Agent — manage the infinity backlog ledger")
    sub = parser.add_subparsers(dest="command", required=True)

    # upsert subcommand
    upsert_p = sub.add_parser("upsert", help="Add or update a single backlog item")
    upsert_p.add_argument("--repo", required=True)
    upsert_p.add_argument("--type", dest="item_type", required=True, choices=list(_VALID_TYPES))
    upsert_p.add_argument("--priority", type=int, default=3)
    upsert_p.add_argument("--risk", required=True, choices=list(_VALID_RISK))
    upsert_p.add_argument("--title", required=True)
    upsert_p.add_argument("--description", default="")
    upsert_p.add_argument("--evidence-links", nargs="*", default=[])
    upsert_p.add_argument("--status", default="open", choices=list(_VALID_STATUS))
    upsert_p.add_argument("--policy-decision-ref", default="")
    upsert_p.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID", ""))
    upsert_p.add_argument("--workflow", default=os.environ.get("GITHUB_WORKFLOW", ""))
    upsert_p.add_argument("--commit-sha", default=os.environ.get("GITHUB_SHA", ""))
    upsert_p.add_argument("--ledger", default=str(_LEDGER_PATH))

    # bulk subcommand
    bulk_p = sub.add_parser("bulk", help="Upsert multiple items from a JSON file")
    bulk_p.add_argument("--input", required=True, help="Path to JSON array of items")
    bulk_p.add_argument("--ledger", default=str(_LEDGER_PATH))

    # validate subcommand
    val_p = sub.add_parser("validate", help="Validate ledger schema")
    val_p.add_argument("--ledger", default=str(_LEDGER_PATH))

    args = parser.parse_args()

    if args.command == "upsert":
        item = upsert_item(
            repo=args.repo,
            item_type=args.item_type,
            priority=args.priority,
            risk=args.risk,
            title=args.title,
            description=args.description,
            evidence_links=args.evidence_links,
            status=args.status,
            policy_decision_ref=args.policy_decision_ref,
            run_id=args.run_id,
            workflow=args.workflow,
            commit_sha=args.commit_sha,
            ledger_path=Path(args.ledger),
        )
        print(f"[backlog] Upserted item: {item['id']} — {item['title']}")

    elif args.command == "bulk":
        with open(args.input, encoding="utf-8") as fh:
            items_data = json.load(fh)
        updated = bulk_upsert(items_data, ledger_path=Path(args.ledger))
        print(f"[backlog] Bulk upserted {len(updated)} items.")

    elif args.command == "validate":
        valid, errors = validate_ledger(Path(args.ledger))
        if valid:
            print("[backlog] Ledger is valid ✓")
            sys.exit(0)
        else:
            print(f"[backlog] Ledger validation failed with {len(errors)} error(s):")
            for err in errors:
                print(f"  • {err}")
            sys.exit(1)


if __name__ == "__main__":
    main()
