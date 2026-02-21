#!/usr/bin/env python3
"""
validate-ledger.py — standalone ledger schema validation script.

Usage:
    python scripts/validate-ledger.py [--ledger PATH]

Exit codes:
    0 — valid
    1 — invalid or file not found
"""

import sys
from pathlib import Path

# Allow running from repo root without PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent / "stacks"))

from agents.backlog_agent import validate_ledger  # noqa: E402


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Validate the infinity backlog ledger schema")
    parser.add_argument(
        "--ledger",
        default=str(Path(__file__).parent.parent / ".infinity" / "ledger" / "backlog.json"),
        help="Path to backlog.json (default: .infinity/ledger/backlog.json)",
    )
    args = parser.parse_args()

    ledger_path = Path(args.ledger)
    valid, errors = validate_ledger(ledger_path)

    if valid:
        print(f"✅  Ledger is valid: {ledger_path}")
        sys.exit(0)
    else:
        print(f"❌  Ledger validation failed: {ledger_path}")
        print(f"    {len(errors)} error(s):")
        for err in errors:
            print(f"      • {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
