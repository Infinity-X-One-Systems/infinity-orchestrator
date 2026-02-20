"""
Scoring Agent — Phase 2 of the Autonomous Invention Engine.

Responsibilities:
- Load the discovery index produced by discovery_agent.py
- Score each signal across five dimensions:
    market_feasibility, build_complexity, revenue_potential, risk_profile, tap_compliance
- Emit a ranked scorecard JSON filtered to signals >= threshold
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from typing import Any


# ── Scoring heuristics ───────────────────────────────────────────────────────

_LANGUAGE_SCORE: dict[str, float] = {
    "python": 0.9,
    "typescript": 0.85,
    "javascript": 0.8,
    "go": 0.85,
    "rust": 0.8,
    "java": 0.7,
    "c#": 0.7,
    "shell": 0.6,
    "unknown": 0.4,
}

_HIGH_VALUE_TOPICS = {
    "ai", "machine-learning", "llm", "automation",
    "orchestration", "api", "saas", "platform",
}


def _score_signal(signal: dict[str, Any]) -> dict[str, Any]:
    """Compute a normalised 0–1 score for a discovery signal."""
    stars: int = signal.get("stars", 0)
    language: str = signal.get("language", "unknown").lower()
    topics: list[str] = [t.lower() for t in signal.get("topics", [])]
    description: str = signal.get("description", "").lower()

    # Market feasibility: logarithmic star count normalised to 0–1
    market_feasibility = min(math.log1p(stars) / math.log1p(10_000), 1.0)

    # Build complexity (lower is better → invert): simpler languages score higher
    build_complexity_raw = _LANGUAGE_SCORE.get(language, 0.5)

    # Revenue potential: topics overlap with high-value categories
    topic_overlap = len(set(topics) & _HIGH_VALUE_TOPICS)
    revenue_potential = min(topic_overlap / 4.0, 1.0)

    # Risk profile: more topics → more breadth, score positively
    risk_profile = min(len(topics) / 8.0, 1.0)

    # TAP compliance (default 1.0 — the validator agent enforces this separately)
    tap_compliance = 1.0

    # Weighted composite score
    score = (
        market_feasibility * 0.25
        + build_complexity_raw * 0.20
        + revenue_potential * 0.30
        + risk_profile * 0.10
        + tap_compliance * 0.15
    )

    return {
        **signal,
        "score": round(score, 4),
        "dimensions": {
            "market_feasibility": round(market_feasibility, 4),
            "build_complexity": round(build_complexity_raw, 4),
            "revenue_potential": round(revenue_potential, 4),
            "risk_profile": round(risk_profile, 4),
            "tap_compliance": tap_compliance,
        },
        "scored_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Scoring Agent")
    parser.add_argument("--input", required=True, help="Path to discovery index JSON")
    parser.add_argument("--output", required=True, help="Path to write scorecard JSON")
    parser.add_argument("--threshold", type=float, default=0.6, help="Minimum score to include")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as fh:
        signals: list[dict] = json.load(fh)

    print(f"[scoring] Scoring {len(signals)} signals…")

    scored = sorted(
        [_score_signal(s) for s in signals],
        key=lambda x: x["score"],
        reverse=True,
    )

    above_threshold = [s for s in scored if s["score"] >= args.threshold]
    print(f"[scoring] {len(above_threshold)}/{len(scored)} signals above threshold {args.threshold}")

    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(scored, fh, indent=2)

    print(f"[scoring] Scorecard written to {args.output}")

    if not above_threshold:
        print("[scoring] No signals above threshold — skipping downstream phases.")
        sys.exit(0)


if __name__ == "__main__":
    main()
