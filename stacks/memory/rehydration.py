"""
Rehydration Engine — Infinity Memory Subsystem
===============================================
Reconstructs working memory context for agents before each task execution.

The rehydration system combines three memory sources:
  1. Vector store — semantic nearest-neighbours from the JSONL store
  2. ACTIVE_MEMORY.md — flat-file snapshot of repo/system state
  3. Recent telemetry — last N telemetry log entries from logs/telemetry/

This mirrors the design described in .infinity/architecture/vector-memory-sync.md.

TAP compliance:
  P-001 — No secrets included in any context output
  P-007 — Degrade gracefully when any memory source is absent

Usage::

    from stacks.memory.rehydration import rehydrate, build_context_prompt

    context = rehydrate("plan a new discovery run", top_k=10)
    prompt  = build_context_prompt(context, task_description="run discovery")
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from stacks.memory.vector_store import VectorStore

# ── Constants ─────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(
    os.environ.get("GENESIS_REPO_PATH", str(Path(__file__).parent.parent.parent))
)
_ACTIVE_MEMORY_PATH = _REPO_ROOT / ".infinity" / "ACTIVE_MEMORY.md"
_TELEMETRY_DIR = _REPO_ROOT / "logs" / "telemetry"
_VECTOR_STORE_PATH = _REPO_ROOT / ".infinity" / "vector-store" / "store.jsonl"

# Freshness threshold: ACTIVE_MEMORY.md older than this triggers a warning (P-007).
# Override with INFINITY_MEMORY_FRESHNESS_HOURS env var (default: 2 hours).
# 2 hours was chosen to match the autonomous-discovery.yml hourly schedule plus
# a one-hour buffer for slow runs or clock skew.
_MEMORY_FRESHNESS_HOURS = float(os.environ.get("INFINITY_MEMORY_FRESHNESS_HOURS", "2"))


# ── Memory source loaders ─────────────────────────────────────────────────────

def _load_active_memory() -> dict[str, Any]:
    """
    Load ACTIVE_MEMORY.md and return structured context.
    Degrades gracefully if the file is absent or stale (P-007).
    """
    result: dict[str, Any] = {
        "available": False,
        "content": "",
        "age_hours": None,
        "warning": None,
    }

    if not _ACTIVE_MEMORY_PATH.exists():
        result["warning"] = "ACTIVE_MEMORY.md absent — graceful degradation (P-007)"
        return result

    try:
        stat = _ACTIVE_MEMORY_PATH.stat()
        mod_time = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        age_hours = (now - mod_time).total_seconds() / 3600
        result["age_hours"] = round(age_hours, 2)

        if age_hours > _MEMORY_FRESHNESS_HOURS:
            result["warning"] = (
                f"ACTIVE_MEMORY.md is {age_hours:.1f}h old "
                f"(threshold: {_MEMORY_FRESHNESS_HOURS}h) — consider running rehydrate.sh"
            )

        content = _ACTIVE_MEMORY_PATH.read_text(encoding="utf-8", errors="replace")
        result["available"] = True
        result["content"] = content
    except OSError as exc:
        result["warning"] = f"Could not read ACTIVE_MEMORY.md: {exc}"

    return result


def _load_recent_telemetry(max_entries: int = 10) -> list[dict[str, Any]]:
    """
    Load the most recent telemetry log entries.
    Returns an empty list when the telemetry dir is absent (P-007).
    """
    if not _TELEMETRY_DIR.exists():
        return []

    log_files = sorted(_TELEMETRY_DIR.glob("run-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    entries: list[dict[str, Any]] = []

    for log_file in log_files[:max_entries]:
        try:
            data = json.loads(log_file.read_text(encoding="utf-8"))
            entries.append(data)
        except Exception:  # noqa: BLE001
            pass

    return entries


def _load_org_index() -> dict[str, Any]:
    """
    Load ORG_REPO_INDEX.json for live repo state.
    Returns empty dict on failure (P-007).
    """
    index_path = _REPO_ROOT / ".infinity" / "ORG_REPO_INDEX.json"
    if not index_path.exists():
        return {}
    try:
        return json.loads(index_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


# ── Rehydration ───────────────────────────────────────────────────────────────

def rehydrate(
    query: str,
    *,
    top_k: int = 10,
    include_active_memory: bool = True,
    include_telemetry: bool = True,
    include_org_index: bool = True,
    store: VectorStore | None = None,
) -> dict[str, Any]:
    """
    Reconstruct working context for an agent prior to a task.

    Returns a context dict with the following keys:
      ``vector_hits``     — list of (score, doc_id, content) from vector search
      ``active_memory``   — structured ACTIVE_MEMORY.md data
      ``recent_runs``     — last N telemetry log entries
      ``org_repos``       — list of repos from ORG_REPO_INDEX.json
      ``warnings``        — list of degradation warnings
      ``rehydrated_at``   — ISO-8601 timestamp
    """
    warnings: list[str] = []

    # 1. Vector store nearest neighbours
    vector_hits: list[dict[str, Any]] = []
    try:
        vs = store or VectorStore(path=_VECTOR_STORE_PATH)
        results = vs.query(query, top_k=top_k)
        for score, doc in results:
            vector_hits.append({
                "score": round(score, 4),
                "id": doc.id,
                "content": doc.content[:400],
                "metadata": doc.metadata,
            })
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"Vector store unavailable: {exc}")

    # 2. ACTIVE_MEMORY.md
    active_memory: dict[str, Any] = {}
    if include_active_memory:
        active_memory = _load_active_memory()
        if active_memory.get("warning"):
            warnings.append(active_memory["warning"])

    # 3. Recent telemetry
    recent_runs: list[dict[str, Any]] = []
    if include_telemetry:
        recent_runs = _load_recent_telemetry(max_entries=5)

    # 4. Live org repo state
    org_repos: list[dict[str, Any]] = []
    if include_org_index:
        org_index = _load_org_index()
        if isinstance(org_index, dict):
            org_repos = org_index.get("repositories", [])
        elif isinstance(org_index, list):
            org_repos = org_index

    return {
        "vector_hits": vector_hits,
        "active_memory": active_memory,
        "recent_runs": recent_runs,
        "org_repos": org_repos,
        "warnings": warnings,
        "rehydrated_at": datetime.now(timezone.utc).isoformat(),
        "query": query,
    }


def build_context_prompt(
    context: dict[str, Any],
    *,
    task_description: str = "",
    max_memory_chars: int = 2000,
    max_hits: int = 5,
) -> str:
    """
    Format a rehydrated context dict into a Markdown prompt block
    suitable for injection into an LLM system prompt.

    Example::

        context = rehydrate("plan discovery run")
        prompt  = build_context_prompt(context, task_description="run discovery agent")
        # Inject `prompt` at the top of the agent's system message
    """
    parts: list[str] = [
        "## 🧠 Rehydrated Working Memory",
        "",
        f"**Task**: {task_description or context.get('query', '')}",
        f"**Rehydrated at**: {context.get('rehydrated_at', '')}",
        "",
    ]

    # Warnings
    for warning in context.get("warnings", []):
        parts.append(f"⚠️ {warning}")
    if context.get("warnings"):
        parts.append("")

    # Vector hits
    hits = context.get("vector_hits", [])[:max_hits]
    if hits:
        parts += ["### Relevant Memory Chunks", ""]
        for i, hit in enumerate(hits, 1):
            parts.append(f"**[{i}]** _(score: {hit['score']:.3f})_ — `{hit['id']}`")
            parts.append(f"> {hit['content'][:300]}")
            parts.append("")

    # ACTIVE_MEMORY excerpt
    active_mem = context.get("active_memory", {})
    if active_mem.get("available") and active_mem.get("content"):
        parts += ["### System State (ACTIVE_MEMORY)", ""]
        content_excerpt = active_mem["content"][:max_memory_chars]
        # Trim to last complete line
        if len(active_mem["content"]) > max_memory_chars:
            content_excerpt = content_excerpt.rsplit("\n", 1)[0] + "\n…"
        parts.append("```markdown")
        parts.append(content_excerpt)
        parts.append("```")
        parts.append("")

    # Org repos summary
    repos = context.get("org_repos", [])
    if repos:
        parts += ["### Live Org Repos", ""]
        for repo in repos[:10]:
            name = repo.get("name") or repo.get("full_name", "?")
            lang = repo.get("language", "")
            updated = repo.get("updated_at", "")[:10]
            parts.append(f"- `{name}` ({lang}) — updated {updated}")
        if len(repos) > 10:
            parts.append(f"- _…and {len(repos) - 10} more_")
        parts.append("")

    # Recent runs summary
    runs = context.get("recent_runs", [])
    if runs:
        parts += ["### Recent Pipeline Runs", ""]
        for run in runs[:3]:
            run_id = run.get("run_id", "?")
            ts = run.get("timestamp", "")[:19]
            phases = run.get("phases", {})
            tap = run.get("metrics", {}).get("tap_passed", "?")
            parts.append(f"- Run `{run_id}` @ {ts} | TAP: {tap} | {phases}")
        parts.append("")

    parts += [
        "---",
        "_Context rehydrated by Infinity Memory Subsystem. Enforce TAP Protocol._",
    ]
    return "\n".join(parts)
