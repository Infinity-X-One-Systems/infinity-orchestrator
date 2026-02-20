"""
TAP Validator Agent — Phase 4 of the Autonomous Invention Engine.

TAP Protocol: Policy > Authority > Truth

Checks performed:
- README.md exists and has minimum content
- SECURITY.md exists
- ARCHITECTURE.md exists
- No secrets committed (basic patterns)
- .github/workflows/ contains at least one workflow
- Lint: Python files parseable (ast.parse)
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple


class CheckResult(NamedTuple):
    name: str
    ok: bool
    message: str


# ── Individual checks ─────────────────────────────────────────────────────────

def check_readme(root: Path) -> CheckResult:
    readme = root / "README.md"
    if not readme.exists():
        return CheckResult("README.md content", False, "README.md not found")
    content = readme.read_text(encoding="utf-8", errors="replace")
    if len(content.strip()) < 100:
        return CheckResult("README.md content", False, "README.md is too short (<100 chars)")
    return CheckResult("README.md content", True, f"{len(content)} bytes")


def check_security(root: Path) -> CheckResult:
    sec = root / "SECURITY.md"
    if not sec.exists():
        return CheckResult("SECURITY.md exists", False, "SECURITY.md not found")
    return CheckResult("SECURITY.md exists", True, "Present")


def check_architecture(root: Path) -> CheckResult:
    arch = root / "ARCHITECTURE.md"
    if not arch.exists():
        return CheckResult("ARCHITECTURE.md exists", False, "ARCHITECTURE.md not found")
    return CheckResult("ARCHITECTURE.md exists", True, "Present")


def check_workflows(root: Path) -> CheckResult:
    wf_dir = root / ".github" / "workflows"
    if not wf_dir.is_dir():
        return CheckResult("Workflows directory", False, ".github/workflows not found")
    workflows = list(wf_dir.glob("*.yml")) + list(wf_dir.glob("*.yaml"))
    if not workflows:
        return CheckResult("Workflows present", False, "No workflow files found")
    return CheckResult("Workflows present", True, f"{len(workflows)} workflow(s) found")


_SECRET_PATTERN = re.compile(
    r'(?i)(password|api_key|secret|private_key|token)\s*[:=]\s*["\']?[A-Za-z0-9+/\-_.~]{16,}',
)


def check_no_secrets(root: Path) -> CheckResult:
    """Basic check for hardcoded secret patterns in non-.git paths."""
    suspicious: list[str] = []
    for ext in ("*.py", "*.sh", "*.yaml", "*.yml", "*.env", "*.json"):
        for path in root.rglob(ext):
            # Skip .git and node_modules
            if ".git" in path.parts or "node_modules" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for match in _SECRET_PATTERN.finditer(text):
                # Ignore references to GitHub secrets context or env placeholders
                line = text[max(0, match.start() - 50):match.end() + 50]
                if "secrets." in line or "${" in line or "example" in line.lower():
                    continue
                suspicious.append(str(path.relative_to(root)))
                break
    if suspicious:
        return CheckResult(
            "No hardcoded secrets",
            False,
            f"Potential secrets in: {', '.join(suspicious[:5])}",
        )
    return CheckResult("No hardcoded secrets", True, "Clean")


def check_python_syntax(root: Path) -> CheckResult:
    errors: list[str] = []
    for py_file in root.rglob("*.py"):
        if ".git" in py_file.parts or "node_modules" in py_file.parts:
            continue
        try:
            source = py_file.read_text(encoding="utf-8", errors="replace")
            ast.parse(source)
        except SyntaxError as exc:
            errors.append(f"{py_file.relative_to(root)}: {exc}")
    if errors:
        return CheckResult("Python syntax", False, "; ".join(errors[:3]))
    return CheckResult("Python syntax", True, "All files parse cleanly")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="TAP Validator Agent")
    parser.add_argument("--repo-root", required=True, help="Path to the repository root")
    parser.add_argument("--output", required=True, help="Path to write the TAP report JSON")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()

    checks: list[CheckResult] = [
        check_readme(root),
        check_security(root),
        check_architecture(root),
        check_workflows(root),
        check_no_secrets(root),
        check_python_syntax(root),
    ]

    passed = all(c.ok for c in checks)
    failed = [c for c in checks if not c.ok]

    report = {
        "passed": passed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(root),
        "summary": {
            "total": len(checks),
            "passed": len([c for c in checks if c.ok]),
            "failed": len(failed),
        },
        "checks": [
            {"name": c.name, "ok": c.ok, "message": c.message}
            for c in checks
        ],
    }

    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    for check in checks:
        status = "✅" if check.ok else "❌"
        print(f"[tap] {status} {check.name}: {check.message}")

    if passed:
        print("[tap] All checks passed.")
    else:
        print(f"[tap] {len(failed)} check(s) failed.", file=sys.stderr)
        # Non-zero exit but not 1 to distinguish from tool errors
        sys.exit(2)


if __name__ == "__main__":
    main()
