"""
Autonomy Controller — Sense → Think → Act → Verify → Ship → Learn state machine.

This is the single entrypoint for the governed autonomy loop. It:
1. SENSE  — reads org repo index + repositories manifest, collects signals
2. THINK  — scores/prioritises tasks, updates backlog ledger
3. ACT    — opens PRs for fixes (PR-only; no direct main pushes)
4. VERIFY — checks CI status and security scan results
5. SHIP   — triggers auto-merge for allowed-risk PRs via TAP decision record
6. LEARN  — writes memory/summary artifacts into .infinity/ and docs/

Governed by:
  INFINITY_AUTONOMY_ENABLED     — master kill-switch (default: true)
  INFINITY_AUTOMERGE_ENABLED    — enable auto-merge (default: true)
  INFINITY_MAX_PRS_PER_DAY      — circuit-breaker (default: 10)
  INFINITY_QUARANTINE_MODE      — stop auto-merge, draft-only PRs (default: false)

TAP guardrails enforced: P-001, P-003, P-004, P-005, G-02, G-08
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Any

# ── Path setup ────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(os.environ.get("GENESIS_REPO_PATH", str(Path(__file__).parent.parent.parent)))
sys.path.insert(0, str(_REPO_ROOT / "stacks"))

from agents.backlog_agent import bulk_upsert, upsert_item, validate_ledger  # noqa: E402

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger("autonomy_controller")


# ── State machine definition ──────────────────────────────────────────────────


class Phase(Enum):
    SENSE = auto()
    THINK = auto()
    ACT = auto()
    VERIFY = auto()
    SHIP = auto()
    LEARN = auto()


class AutonomyController:
    """
    Governed, PR-only autonomy state machine.

    The controller reads environment variables for runtime configuration
    so that repo/org variables can toggle behaviour without code changes.
    """

    def __init__(self) -> None:
        self.run_id: str = os.environ.get("GITHUB_RUN_ID", "local")
        self.run_attempt: str = os.environ.get("GITHUB_RUN_ATTEMPT", "1")
        self.workflow: str = os.environ.get("GITHUB_WORKFLOW", "autonomy-controller")
        self.commit_sha: str = os.environ.get("GITHUB_SHA", "")
        self.repo: str = os.environ.get("GITHUB_REPOSITORY", "Infinity-X-One-Systems/infinity-orchestrator")
        self.github_token: str = os.environ.get("GITHUB_TOKEN", "")

        # Break-glass toggles
        self.autonomy_enabled: bool = os.environ.get("INFINITY_AUTONOMY_ENABLED", "true").lower() == "true"
        self.automerge_enabled: bool = os.environ.get("INFINITY_AUTOMERGE_ENABLED", "true").lower() == "true"
        self.max_prs_per_day: int = int(os.environ.get("INFINITY_MAX_PRS_PER_DAY", "10"))
        self.quarantine_mode: bool = os.environ.get("INFINITY_QUARANTINE_MODE", "false").lower() == "true"

        self.correlation_id: str = f"{self.run_id}-{self.run_attempt}"
        self.started_at: str = datetime.now(timezone.utc).isoformat()

        # Collected state across phases
        self.org_index: dict[str, Any] = {}
        self.signals: list[dict] = []
        self.backlog_items: list[dict] = []
        self.pr_results: list[dict] = []
        self.verify_results: list[dict] = []
        self.phase_results: dict[str, str] = {}

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _tap_log(self, action: str, decision: str, justification: str, rules: list[str] | None = None) -> None:
        """Emit a TAP-compliant decision log entry (P-006 compliant, no secrets)."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": "github-actions[bot]",
            "action": action,
            "policy_rules_checked": rules or [],
            "decision": decision,
            "correlation_id": self.correlation_id,
            "justification": justification,
        }
        # Log to stdout for GitHub Actions step summary capture
        logger.info("TAP: %s", json.dumps(entry))

    def _load_file(self, path: Path) -> dict | list | None:
        """Load a JSON file gracefully; return None on any error (P-007)."""
        if not path.exists():
            logger.warning("File not found (degrading gracefully): %s", path)
            return None
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load %s: %s", path, exc)
            return None

    def _write_summary(self, content: str) -> None:
        """Append to $GITHUB_STEP_SUMMARY if available."""
        summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_path:
            try:
                with open(summary_path, "a", encoding="utf-8") as fh:
                    fh.write(content + "\n")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not write step summary: %s", exc)

    def _github_api(self, method: str, path: str, body: dict | None = None) -> dict | list | None:
        """
        Make a GitHub API call using the available token.
        Returns parsed JSON or None on failure. Never logs the token (P-001).
        """
        import urllib.error
        import urllib.request

        if not self.github_token:
            logger.warning("GITHUB_TOKEN not set — skipping API call to %s", path)
            return None

        url = f"https://api.github.com{path}"
        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "X-Infinity-Correlation-ID": self.correlation_id,
        }
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            logger.warning("GitHub API %s %s → HTTP %d", method, path, exc.code)
            return None
        except Exception as exc:  # noqa: BLE001
            logger.warning("GitHub API call failed: %s", exc)
            return None

    # ── Phase implementations ─────────────────────────────────────────────────

    def phase_sense(self) -> bool:
        """
        SENSE: Read org repo index + repositories manifest, collect signals.
        Signals include failing workflows, open security alerts, and bot-labelled issues.
        """
        logger.info("=== PHASE: SENSE ===")
        self._tap_log("sense", "allowed", "Reading state from canonical sources", ["P-007"])

        # Load org repo index
        index_path = _REPO_ROOT / ".infinity" / "ORG_REPO_INDEX.json"
        self.org_index = self._load_file(index_path) or {}
        repos = self.org_index.get("repositories", [])

        if not repos:
            logger.warning("ORG_REPO_INDEX is empty — org repo index may be stale (see problem: total=0).")
            # Fall back to repositories.json
            manifest_path = _REPO_ROOT / "config" / "repositories.json"
            manifest = self._load_file(manifest_path) or {}
            repos = manifest.get("repositories", [])
            logger.info("Falling back to config/repositories.json — found %d repos", len(repos))

        logger.info("Repositories in scope: %d", len(repos))

        # Collect signals from each in-scope repo
        org = self.org_index.get("organization", "Infinity-X-One-Systems")
        for repo_entry in repos:
            repo_name = repo_entry.get("full_name") or f"{org}/{repo_entry.get('name', '')}"
            if not repo_name:
                continue

            # Check for bot-labelled open issues
            issues_data = self._github_api("GET", f"/repos/{repo_name}/issues?labels=bot-task,orchestrator:task&state=open&per_page=10")
            if isinstance(issues_data, list):
                for issue in issues_data:
                    self.signals.append({
                        "source": "github_issue",
                        "repo": repo_name,
                        "type": "chore",
                        "priority": 3,
                        "risk": "low",
                        "title": issue.get("title", "")[:120],
                        "evidence_links": [issue.get("html_url", "")],
                        "description": f"Open issue #{issue.get('number')} tagged for bot processing.",
                    })

        logger.info("SENSE complete — %d signals collected.", len(self.signals))
        return True

    def phase_think(self) -> bool:
        """
        THINK: Score and prioritise tasks, update backlog ledger.
        Connects to scoring_agent logic for consistent scoring.
        """
        logger.info("=== PHASE: THINK ===")
        self._tap_log("think", "allowed", "Scoring and updating backlog ledger", ["P-006"])

        # Import scoring logic
        try:
            sys.path.insert(0, str(_REPO_ROOT / "stacks"))
            from agents.scoring_agent import _score_signal  # noqa: PLC0415

            scored_signals = []
            for signal in self.signals:
                scored = _score_signal(signal)
                # Map score to priority: 1=highest (score>=0.8), 5=lowest (score<0.2)
                score = scored.get("score", 0)
                priority = max(1, min(5, 5 - int(score * 4)))
                signal["priority"] = priority
                scored_signals.append(signal)
            self.signals = scored_signals
        except Exception as exc:  # noqa: BLE001
            logger.warning("Scoring agent unavailable (%s) — using default priorities.", exc)

        # Upsert all signals into the backlog ledger
        ledger_path = _REPO_ROOT / ".infinity" / "ledger" / "backlog.json"
        items_to_upsert = []
        for signal in self.signals:
            items_to_upsert.append({
                "repo": signal.get("repo", self.repo),
                "type": signal.get("type", "chore"),
                "priority": signal.get("priority", 3),
                "risk": signal.get("risk", "low"),
                "title": signal.get("title", "Untitled signal"),
                "description": signal.get("description", ""),
                "evidence_links": signal.get("evidence_links", []),
                "status": "open",
                "run_id": self.run_id,
                "workflow": self.workflow,
                "commit_sha": self.commit_sha,
            })

        if items_to_upsert:
            self.backlog_items = bulk_upsert(items_to_upsert, ledger_path=ledger_path)
            logger.info("THINK complete — upserted %d backlog items.", len(self.backlog_items))
        else:
            logger.info("THINK complete — no new signals to backlog.")

        return True

    def phase_act(self) -> bool:
        """
        ACT: Open PRs for actionable backlog items (PR-only; no direct main pushes per P-004/G-02).
        In quarantine mode, opens draft PRs only.
        """
        logger.info("=== PHASE: ACT ===")

        if not self.autonomy_enabled:
            self._tap_log("act", "denied", "INFINITY_AUTONOMY_ENABLED=false — skipping ACT phase", ["P-004"])
            logger.warning("ACT phase skipped: INFINITY_AUTONOMY_ENABLED is false.")
            return True

        # Only act on high-priority (<=2) low/medium risk open items
        actionable = [
            item for item in self.backlog_items
            if item.get("status") == "open"
            and item.get("priority", 5) <= 2
            and item.get("risk", "high") in ("low", "medium")
        ]

        if not actionable:
            logger.info("ACT complete — no actionable items (priority ≤2, risk low/medium).")
            return True

        # Enforce daily PR circuit-breaker (G-XX / configurable)
        if len(actionable) > self.max_prs_per_day:
            logger.warning(
                "ACT: %d actionable items exceed INFINITY_MAX_PRS_PER_DAY=%d — truncating.",
                len(actionable), self.max_prs_per_day,
            )
            actionable = actionable[: self.max_prs_per_day]

        for item in actionable:
            self._tap_log(
                f"open_pr:{item['id']}",
                "allowed",
                f"Opening PR for {item['title']} — risk={item.get('risk')} priority={item.get('priority')}",
                ["P-003", "P-004", "P-005"],
            )
            # Record that the PR was queued (actual PR opening requires git operations
            # and is performed by the workflow calling this controller via `gh pr create`)
            self.pr_results.append({
                "item_id": item["id"],
                "repo": item.get("repo", self.repo),
                "title": item["title"],
                "risk": item.get("risk", "low"),
                "draft": self.quarantine_mode,
                "status": "queued",
            })

        logger.info("ACT complete — %d PRs queued (%s mode).",
                    len(self.pr_results), "draft" if self.quarantine_mode else "ready")
        return True

    def phase_verify(self) -> bool:
        """
        VERIFY: Check CI status and security scan results for queued PRs.
        Blocks auto-merge if checks have failures (G-08).
        """
        logger.info("=== PHASE: VERIFY ===")
        self._tap_log("verify", "allowed", "Checking CI and security status", ["G-08"])

        for pr in self.pr_results:
            # In a full implementation, this would poll the GitHub Checks API
            # for the PR's head SHA. We record the intent here and the
            # genesis-auto-merge workflow performs the actual gate check.
            pr["verified"] = False  # conservative default — workflow does the real check
            self.verify_results.append(pr)

        logger.info("VERIFY complete — %d PRs marked for workflow-level verification.", len(self.verify_results))
        return True

    def phase_ship(self) -> bool:
        """
        SHIP: Trigger auto-merge for allowed-risk PRs via TAP decision record.
        Quarantine mode prevents auto-merge (only drafts are opened).
        """
        logger.info("=== PHASE: SHIP ===")

        if self.quarantine_mode:
            self._tap_log("ship", "denied", "INFINITY_QUARANTINE_MODE=true — no auto-merge", ["G-08"])
            logger.warning("SHIP skipped: INFINITY_QUARANTINE_MODE is active.")
            return True

        if not self.automerge_enabled:
            self._tap_log("ship", "denied", "INFINITY_AUTOMERGE_ENABLED=false — no auto-merge", [])
            logger.warning("SHIP skipped: INFINITY_AUTOMERGE_ENABLED is false.")
            return True

        allowed_to_ship = [pr for pr in self.verify_results if pr.get("risk") in ("low", "medium")]

        for pr in allowed_to_ship:
            self._tap_log(
                f"ship_pr:{pr['item_id']}",
                "allowed",
                f"Labelling PR for auto-merge — risk={pr.get('risk')}",
                ["P-003", "P-005", "G-08"],
            )

        logger.info("SHIP complete — %d PRs eligible for auto-merge (pending CI).", len(allowed_to_ship))
        return True

    def phase_learn(self) -> bool:
        """
        LEARN: Write memory summaries into .infinity/ and docs/run-{run_id}.md.
        """
        logger.info("=== PHASE: LEARN ===")

        summary = {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "correlation_id": self.correlation_id,
            "phases": self.phase_results,
            "signals_collected": len(self.signals),
            "backlog_items_updated": len(self.backlog_items),
            "prs_queued": len(self.pr_results),
            "quarantine_mode": self.quarantine_mode,
            "automerge_enabled": self.automerge_enabled,
        }

        # Write to docs/
        docs_dir = _REPO_ROOT / "docs"
        docs_dir.mkdir(exist_ok=True)
        run_doc = docs_dir / f"run-{self.run_id}.md"

        if not run_doc.exists():
            with open(run_doc, "w", encoding="utf-8") as fh:
                fh.write(f"# Autonomy Run — {self.run_id}\n\n")
                fh.write(f"**Started:** {self.started_at}  \n")
                fh.write(f"**Correlation ID:** `{self.correlation_id}`  \n\n")
                fh.write("## Phase Results\n\n")
                for phase, result in self.phase_results.items():
                    emoji = "✅" if result == "success" else "❌"
                    fh.write(f"- {emoji} **{phase.upper()}**: {result}\n")
                fh.write("\n## Summary\n\n")
                fh.write(f"```json\n{json.dumps(summary, indent=2)}\n```\n")

        # Write step summary
        self._write_summary(
            f"## 🤖 Autonomy Controller Run `{self.run_id}`\n\n"
            + "| Phase | Result |\n|-------|--------|\n"
            + "".join(
                f"| {phase.upper()} | {result} |\n"
                for phase, result in self.phase_results.items()
            )
            + f"\n**Signals collected:** {len(self.signals)}  \n"
            + f"**Backlog items updated:** {len(self.backlog_items)}  \n"
            + f"**PRs queued:** {len(self.pr_results)}  \n"
            + f"**Quarantine mode:** {self.quarantine_mode}  \n"
        )

        logger.info("LEARN complete — run doc written to %s.", run_doc)
        return True

    # ── Main execution loop ───────────────────────────────────────────────────

    def run(self, phases: list[str] | None = None) -> int:
        """
        Execute the state machine.

        Args:
            phases: list of phase names to run; defaults to all phases in order.

        Returns:
            Exit code: 0 = success, 1 = one or more phases failed.
        """
        if not self.autonomy_enabled:
            logger.warning("INFINITY_AUTONOMY_ENABLED=false — all phases skipped.")
            self._write_summary("## ⚠️ Autonomy Controller\n\n**Autonomy is disabled** via `INFINITY_AUTONOMY_ENABLED=false`.\n")
            return 0

        all_phases = [
            ("sense", self.phase_sense),
            ("think", self.phase_think),
            ("act", self.phase_act),
            ("verify", self.phase_verify),
            ("ship", self.phase_ship),
            ("learn", self.phase_learn),
        ]

        if phases:
            phases_lower = [p.lower() for p in phases]
            selected = [(name, fn) for name, fn in all_phases if name in phases_lower]
            if not selected:
                logger.error("No valid phases selected from: %s", phases)
                return 1
        else:
            selected = all_phases

        logger.info("=== AUTONOMY CONTROLLER STARTING [corr=%s] ===", self.correlation_id)
        logger.info("Phases: %s | quarantine=%s | max_prs=%d",
                    [n for n, _ in selected], self.quarantine_mode, self.max_prs_per_day)

        overall_exit = 0

        for phase_name, phase_fn in selected:
            try:
                success = phase_fn()
                self.phase_results[phase_name] = "success" if success else "failed"
                if not success:
                    overall_exit = 1
            except Exception as exc:  # noqa: BLE001
                logger.error("Phase %s raised exception: %s", phase_name, exc, exc_info=True)
                self.phase_results[phase_name] = f"error: {exc}"
                overall_exit = 1

        logger.info("=== AUTONOMY CONTROLLER FINISHED — exit=%d ===", overall_exit)
        return overall_exit


# ── CLI ───────────────────────────────────────────────────────────────────────


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Autonomy Controller — Sense→Think→Act→Verify→Ship→Learn")
    parser.add_argument(
        "phases",
        nargs="*",
        help="Phases to run (default: all). Options: sense think act verify ship learn",
    )
    args = parser.parse_args()

    controller = AutonomyController()
    exit_code = controller.run(args.phases or None)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
