"""
Base Agent — Infinity Agent Class Library
==========================================
All Infinity agents inherit from ``BaseAgent``.

The base class provides:
  * Memory rehydration before each task (P-007 graceful degradation)
  * Structured logging with correlation IDs (P-006)
  * TAP pre-flight checklist enforcement
  * LLM completion helper (Ollama / Groq / Gemini / OpenAI — auto-selected)
  * Audit log entry emission

Usage::

    from stacks.agents.base_agent import BaseAgent

    class MyAgent(BaseAgent):
        name = "my-agent"

        def run(self, task: str) -> dict:
            ctx = self.rehydrate(task)
            prompt = self.build_prompt(ctx, task)
            response = self.complete(prompt)
            self.log_decision(task=task, decision="allowed", justification=response[:200])
            return {"result": response}

    agent = MyAgent()
    result = agent.run("generate a discovery plan")
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Memory subsystem (graceful import — degrades if not installed)
try:
    from stacks.memory.rehydration import rehydrate, build_context_prompt
    from stacks.memory.vector_store import VectorStore
    _MEMORY_AVAILABLE = True
except ImportError:
    _MEMORY_AVAILABLE = False

    def _empty_context(query: str) -> dict[str, Any]:
        return {
            "vector_hits": [],
            "active_memory": {},
            "recent_runs": [],
            "org_repos": [],
            "warnings": ["memory subsystem unavailable"],
            "rehydrated_at": datetime.now(timezone.utc).isoformat(),
            "query": query,
        }

    def rehydrate(query: str, **_kwargs: Any) -> dict[str, Any]:  # type: ignore[misc]
        return _empty_context(query)

    def build_context_prompt(context: dict[str, Any], **_kwargs: Any) -> str:  # type: ignore[misc]
        return f"## Context unavailable\nTask: {context.get('query', '')}"


# ── Environment ───────────────────────────────────────────────────────────────

_REPO_ROOT = Path(os.environ.get("GENESIS_REPO_PATH", str(Path(__file__).parent.parent.parent)))
_AUDIT_LOG_PATH = _REPO_ROOT / "logs" / "audit" / "decisions.jsonl"

# LLM backend selection (in priority order when INFINITY_LLM_BACKEND is not set)
_LLM_BACKEND = os.environ.get("INFINITY_LLM_BACKEND", "auto").lower()

# API keys / base URLs — read only from environment (P-001)
_OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
_GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
_GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
_OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
_OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
_GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
_GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")


# ── LLM completion helpers ────────────────────────────────────────────────────

def _complete_openai(prompt: str, system: str = "") -> str:
    """OpenAI Chat Completions. Returns empty string on failure (P-007)."""
    if not _OPENAI_API_KEY:
        return ""
    try:
        import urllib.request

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = json.dumps({
            "model": _OPENAI_MODEL,
            "messages": messages,
            "max_tokens": 1024,
        }).encode()
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {_OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
    except Exception as exc:  # noqa: BLE001
        print(f"[base_agent] OpenAI completion failed: {exc}", file=sys.stderr)
        return ""


def _complete_groq(prompt: str, system: str = "") -> str:
    """Groq Chat Completions. Returns empty string on failure (P-007)."""
    if not _GROQ_API_KEY:
        return ""
    try:
        import urllib.request

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = json.dumps({
            "model": _GROQ_MODEL,
            "messages": messages,
            "max_tokens": 1024,
        }).encode()
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {_GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
    except Exception as exc:  # noqa: BLE001
        print(f"[base_agent] Groq completion failed: {exc}", file=sys.stderr)
        return ""


def _complete_gemini(prompt: str, system: str = "") -> str:
    """Google Gemini generateContent. Returns empty string on failure (P-007)."""
    if not _GEMINI_API_KEY:
        return ""
    try:
        import urllib.request

        combined = f"{system}\n\n{prompt}" if system else prompt
        payload = json.dumps({
            "contents": [{"parts": [{"text": combined}]}],
            "generationConfig": {"maxOutputTokens": 1024},
        }).encode()
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{_GEMINI_MODEL}:generateContent?key={_GEMINI_API_KEY}"
        )
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as exc:  # noqa: BLE001
        print(f"[base_agent] Gemini completion failed: {exc}", file=sys.stderr)
        return ""


def _complete_ollama(prompt: str, system: str = "") -> str:
    """Ollama /api/chat. Returns empty string on failure (P-007)."""
    try:
        import urllib.request

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = json.dumps({
            "model": _OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
        }).encode()
        req = urllib.request.Request(
            f"{_OLLAMA_BASE_URL}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            return data.get("message", {}).get("content", "")
    except Exception as exc:  # noqa: BLE001
        print(f"[base_agent] Ollama completion failed: {exc}", file=sys.stderr)
        return ""


# ── BaseAgent ─────────────────────────────────────────────────────────────────

class BaseAgent:
    """
    Abstract base class for all Infinity autonomous agents.

    Subclasses must define:
      ``name`` — human-readable agent name

    Subclasses should override:
      ``run(task)`` — execute the agent's primary task
    """

    name: str = "base-agent"

    def __init__(self, *, session_id: str | None = None) -> None:
        self.session_id = session_id or str(uuid.uuid4())
        self._store: "VectorStore | None" = None

    # ── Memory ────────────────────────────────────────────────────────────────

    def rehydrate(self, query: str, top_k: int = 10) -> dict[str, Any]:
        """
        Rehydrate working memory context before a task.
        Always call this at the start of ``run()``.
        """
        return rehydrate(query, top_k=top_k)

    def build_prompt(
        self,
        context: dict[str, Any],
        task_description: str = "",
    ) -> str:
        """Format a rehydrated context as a Markdown prompt block."""
        return build_context_prompt(context, task_description=task_description)

    def remember(
        self,
        doc_id: str,
        content: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Persist a document into the vector store."""
        if not _MEMORY_AVAILABLE:
            return
        if self._store is None:
            self._store = VectorStore()
        self._store.upsert(
            doc_id,
            content,
            metadata={**(metadata or {}), "agent": self.name, "session_id": self.session_id},
            correlation_id=self._new_correlation_id(),
        )

    # ── LLM completion ────────────────────────────────────────────────────────

    def complete(self, prompt: str, *, system: str = "") -> str:
        """
        Call the configured LLM backend and return the completion text.
        Auto-selects the first available backend when INFINITY_LLM_BACKEND=auto.
        Returns empty string on failure (P-007 graceful degradation).
        """
        backend = _LLM_BACKEND

        if backend == "auto":
            # Priority: Ollama (local, free) → Groq → Gemini → OpenAI
            for fn, available in [
                (_complete_ollama, True),
                (_complete_groq, bool(_GROQ_API_KEY)),
                (_complete_gemini, bool(_GEMINI_API_KEY)),
                (_complete_openai, bool(_OPENAI_API_KEY)),
            ]:
                if available:
                    result = fn(prompt, system)
                    if result:
                        return result
            return ""

        dispatch = {
            "openai": _complete_openai,
            "groq": _complete_groq,
            "gemini": _complete_gemini,
            "ollama": _complete_ollama,
        }
        fn = dispatch.get(backend, _complete_openai)
        return fn(prompt, system)

    # ── TAP pre-flight ────────────────────────────────────────────────────────

    def tap_preflight(
        self,
        *,
        action: str,
        policy_rules: list[str] | None = None,
    ) -> bool:
        """
        Run TAP pre-flight checklist (P-001…P-008) before any autonomous action.
        Returns True if all checks pass, False otherwise.
        Logs the decision regardless.
        """
        rules = policy_rules or ["P-001", "P-003", "P-005", "P-006", "P-007"]
        correlation_id = self._new_correlation_id()

        # Basic checks
        issues: list[str] = []

        # P-001: no secrets in action description (case-insensitive)
        action_lower = action.lower()
        secret_patterns = [
            "api_key", "apikey", "private_key", "privatekey",
            "password", "passwd", "token=", "secret=",
            "bearer ", "authorization:",
        ]
        if any(p in action_lower for p in secret_patterns):
            issues.append("P-001: action description contains potential secret reference")

        passed = len(issues) == 0

        self.log_decision(
            task=action,
            decision="allowed" if passed else "denied",
            policy_rules_checked=rules,
            justification="; ".join(issues) if issues else "TAP pre-flight passed",
            correlation_id=correlation_id,
        )

        if not passed:
            print(f"[{self.name}] TAP pre-flight DENIED: {'; '.join(issues)}", file=sys.stderr)

        return passed

    # ── Audit logging ─────────────────────────────────────────────────────────

    def log_decision(
        self,
        *,
        task: str,
        decision: str,
        policy_rules_checked: list[str] | None = None,
        justification: str = "",
        correlation_id: str | None = None,
    ) -> None:
        """
        Emit a TAP decision log entry (P-006).
        Appends to logs/audit/decisions.jsonl.
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": self.name,
            "session_id": self.session_id,
            "action": task,
            "policy_rules_checked": policy_rules_checked or [],
            "decision": decision,
            "correlation_id": correlation_id or self._new_correlation_id(),
            "justification": justification,
            "run_id": os.environ.get("GITHUB_RUN_ID", ""),
        }

        _AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_AUDIT_LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _new_correlation_id(self) -> str:
        return str(uuid.uuid4())

    def log_info(self, message: str) -> None:
        print(f"[{self.name}] {message}")

    def log_warn(self, message: str) -> None:
        print(f"[{self.name}] WARNING: {message}", file=sys.stderr)

    def log_error(self, message: str) -> None:
        print(f"[{self.name}] ERROR: {message}", file=sys.stderr)

    # ── Entry point ───────────────────────────────────────────────────────────

    def run(self, task: str) -> dict[str, Any]:  # pragma: no cover
        """Override in subclasses to implement agent logic."""
        raise NotImplementedError(f"{self.__class__.__name__}.run() must be implemented")
